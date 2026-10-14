"""`masks.py` — 人体躯干/骨盆区域的**度量深度中位数**（spec §1(B)/§3/§4）。

铁律（本框架的立身之本）
------------------------
相对深度模型有 scale-shift 不确定性，**绝不能拿人体像素值当深度**。
本模块只做一件事：在人体 Mask 的躯干 / 骨盆区域内取 `DepthMap.depth`（米）的
**中位数**，作为根节点 Z 的度量观测（`RegionStat.depth_median_m`）。

为什么必须是中位数而不是均值：挥手 / 踢腿 / 拿道具时，四肢像素会落进躯干区域内，
其深度与躯干差可达 1 m 量级；中位数对这些离群点免疫，均值会被直接拖走。
合成自验（躯干区域内塞 30% 离群、偏差 1.5 m）：
    中位数偏移 0.000 m（要求 < 0.05），均值偏移 0.450 m（要求 > 0.3）。

区域几何（`cfg["mask"]`：spec §4 三键 + 可选键）
------------------------------------------------
有人体关键点（`neck`、`pelvis`，像素坐标）时：
    以 neck→骨盆 连线为中轴 `u`，`v` 为其法向，`L = |axis|`；
    torso  椭圆：中心在连线中点，沿 u 半轴 = `0.5*torso_frac*bbox_h`（上限 `0.5*L`），
                沿 v 半轴 = `torso_width_ratio*L`；
    pelvis 椭圆：中心在骨盆点，沿 u 半轴 = `0.5*pelvis_frac*bbox_h`（上限 `0.5*L`），
                沿 v 半轴 = `pelvis_width_ratio * torso半轴`。
    轴长上限保证椭圆不越出 neck..pelvis 这一段（躯干就是这一段）。
没有关键点时退化为人体框（bbox 由 Mask 自己算）内的水平矩形带：
    torso  = 从 `y0 + bbox_top_frac*h` 起，高 `torso_frac*h`，横向居中 `bbox 宽 * fallback_torso_width_frac`；
    pelvis = 紧接 torso 带之下，高 `pelvis_frac*h`，横向居中 `bbox 宽 * fallback_pelvis_width_frac`。
两种情况下区域都与人体 Mask **求交**，绝不采到背景/地面。

可选 cfg 键（`DEFAULT_CFG` 里没有，缺省用本模块常量；要进 `DEFAULT_CFG` 请找 Lead，
`types.py` 冻结）：
    mask.bbox_top_frac               0.18   退化路径：跳过头部后躯干带起点
    mask.torso_width_ratio           0.40   关键点路径：躯干横向半宽 / L
    mask.pelvis_width_ratio          0.80   关键点路径：骨盆横向半宽 / 躯干半宽
    mask.fallback_torso_width_frac   0.45   退化路径：躯干带宽 / bbox 宽
    mask.fallback_pelvis_width_frac  0.36   退化路径：骨盆带宽 / bbox 宽

统计口径：`RegionStat.px` = 区域 ∩ 人体 Mask 内**有效深度样本数**（有限且 > 0），
`RegionStat.frac = px / (H*W)`（占画面比例），`iqr_m = p90 - p10`。区域有效像素
少于 `mask.min_px` 时该区域被丢弃；躯干是主区域（`stats[0]`），全部丢弃时返回 `[]`。
"""

from __future__ import annotations

from typing import Any

import numpy as np

if __package__:
    from .priors import resolve_keypoint, torso_px_length
    from .types import DepthMap, MetricRequired, RegionStat, merge_cfg
else:  # pragma: no cover - 允许直接按文件路径运行（不把 depth_prior/ 加进 sys.path，避免遮蔽 stdlib `types`）
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from depth_prior.priors import resolve_keypoint, torso_px_length
    from depth_prior.types import DepthMap, MetricRequired, RegionStat, merge_cfg

__all__ = [
    "DEFAULT_BBOX_TOP_FRAC",
    "DEFAULT_TORSO_WIDTH_RATIO",
    "DEFAULT_PELVIS_WIDTH_RATIO",
    "DEFAULT_FALLBACK_TORSO_WIDTH_FRAC",
    "DEFAULT_FALLBACK_PELVIS_WIDTH_FRAC",
    "REGION_NAMES",
    "person_bbox",
    "region_masks",
    "region_stat",
    "torso_pelvis_stats",
    "stat_by_name",
    "primary_stat",
    "frame_observation",
]

DEFAULT_BBOX_TOP_FRAC = 0.18
DEFAULT_TORSO_WIDTH_RATIO = 0.40
DEFAULT_PELVIS_WIDTH_RATIO = 0.80
DEFAULT_FALLBACK_TORSO_WIDTH_FRAC = 0.45
DEFAULT_FALLBACK_PELVIS_WIDTH_FRAC = 0.36

REGION_NAMES: tuple[str, str] = ("torso", "pelvis")
_EPS = 1e-6


# ---------------------------------------------------------------------------
# cfg / 输入校验


def _mask_cfg(cfg: dict | None) -> dict[str, Any]:
    """取 `cfg["mask"]`，以 `types.DEFAULT_CFG` 为底（spec §4 三键必有）。"""
    base: dict[str, Any] = dict(merge_cfg(None)["mask"])
    if isinstance(cfg, dict) and isinstance(cfg.get("mask"), dict):
        base.update(cfg["mask"])
    return base


def _opt_float(mcfg: dict[str, Any], key: str, default: float) -> float:
    raw = mcfg.get(key, default)
    try:
        value = float(default if raw is None else raw)
    except (TypeError, ValueError):
        return float(default)
    return value if np.isfinite(value) else float(default)


def _require_metric_depth(depth: DepthMap) -> DepthMap:
    """只接受带 `kind` 闸门的 `DepthMap`，且必须是 `kind == "metric"`（spec §0）。"""
    if not isinstance(depth, DepthMap):
        raise TypeError(
            f"需要 types.DepthMap（带 kind 闸门），收到 {type(depth).__name__}；"
            "裸数组请包一层 DepthMap(depth=arr, kind='metric', unit='m')"
        )
    if not depth.is_metric:
        raise MetricRequired(
            f"masks 只能吃 kind='metric' 的深度图，收到 kind={depth.kind!r}/unit={depth.unit!r}："
            "相对深度不许当米用，请先 priors.affine_align_to_metric() 对齐再构造 kind='metric' 的 DepthMap"
        )
    return depth


def _as_mask(mask: np.ndarray, shape: tuple[int, ...], what: str = "mask") -> np.ndarray:
    arr = np.asarray(mask)
    if arr.shape != tuple(shape):
        raise ValueError(
            f"{what} {arr.shape} 与 depth {tuple(shape)} 不一致（必须是同一帧、同分辨率）；"
            "若来自 FSB/SAM，请先 resize 到深度图分辨率"
        )
    if arr.dtype != bool:
        arr = arr.astype(bool, copy=False)
    return arr


# ---------------------------------------------------------------------------
# 区域几何


def person_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """人体 Mask 的紧包围框 `(x0, y0, x1, y1)`（闭区间）；空 Mask 返回 None。"""
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 2 or not m.any():
        return None
    cols = np.flatnonzero(m.any(axis=0))
    rows = np.flatnonzero(m.any(axis=1))
    return int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])


def _axis_frame(neck: np.ndarray, pelvis: np.ndarray) -> tuple[np.ndarray, np.ndarray, float] | None:
    """neck→pelvis 的正交标架 `(u, v, L)`；退化（重合/非有限）返回 None。"""
    axis = np.asarray(pelvis, dtype=np.float64) - np.asarray(neck, dtype=np.float64)
    length = float(np.hypot(axis[0], axis[1]))
    if not np.isfinite(length) or length <= _EPS:
        return None
    u = axis / length
    v = np.array([-u[1], u[0]], dtype=np.float64)
    return u, v, length


def _ellipse_mask(
    shape: tuple[int, int],
    center: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    half_along: float,
    half_across: float,
) -> np.ndarray:
    """中心 `center`、轴 `u`/`v`、半轴 `half_along`/`half_across` 的椭圆。

    只在椭圆的包围盒里算（1080p 整帧生成坐标网格是纯浪费；结果与整帧计算一致）。
    """
    height, width = int(shape[0]), int(shape[1])
    cx, cy = float(center[0]), float(center[1])
    ux, uy = float(u[0]), float(u[1])
    vx, vy = float(v[0]), float(v[1])
    a = max(float(half_along), _EPS)
    b = max(float(half_across), _EPS)
    half_w = abs(a * ux) + abs(b * vx)                    # 椭圆在 x 方向的半宽
    half_h = abs(a * uy) + abs(b * vy)                    # 椭圆在 y 方向的半高
    x0 = max(int(np.floor(cx - half_w)), 0)
    x1 = min(int(np.ceil(cx + half_w)) + 1, width)
    y0 = max(int(np.floor(cy - half_h)), 0)
    y1 = min(int(np.ceil(cy + half_h)) + 1, height)

    out = np.zeros((height, width), dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return out
    ys = np.arange(y0, y1, dtype=np.float32)[:, None]
    xs = np.arange(x0, x1, dtype=np.float32)[None, :]
    t = (xs - cx) * ux + (ys - cy) * uy                   # 沿躯干轴
    s = (xs - cx) * vx + (ys - cy) * vy                   # 法向
    out[y0:y1, x0:x1] = (t / a) ** 2 + (s / b) ** 2 <= 1.0
    return out


def _region_masks_with(
    mask: np.ndarray, keypoints_px: dict | None, mcfg: dict[str, Any]
) -> dict[str, np.ndarray]:
    """已解析 cfg 的区域几何实现（内部用，避免 cfg 二次解析）。"""
    m = np.asarray(mask, dtype=bool)
    shape = (int(m.shape[0]), int(m.shape[1]))
    empty = np.zeros(shape, dtype=bool)

    torso_frac = _opt_float(mcfg, "torso_frac", 0.22)
    pelvis_frac = _opt_float(mcfg, "pelvis_frac", 0.12)

    neck = resolve_keypoint(keypoints_px, "neck")
    pelvis_pt = resolve_keypoint(keypoints_px, "pelvis")
    frame = _axis_frame(neck, pelvis_pt) if (neck is not None and pelvis_pt is not None) else None

    if frame is not None:
        u, v, length = frame
        bbox = person_bbox(m)
        bbox_h = float(bbox[3] - bbox[1] + 1) if bbox is not None else float(shape[0])
        torso_half_across = max(_opt_float(mcfg, "torso_width_ratio", DEFAULT_TORSO_WIDTH_RATIO) * length, _EPS)
        pelvis_half_across = max(_opt_float(mcfg, "pelvis_width_ratio", DEFAULT_PELVIS_WIDTH_RATIO) * torso_half_across, _EPS)
        torso_half_along = min(0.5 * torso_frac * bbox_h, 0.5 * length)
        pelvis_half_along = min(0.5 * pelvis_frac * bbox_h, 0.5 * length)
        torso = _ellipse_mask(shape, 0.5 * (np.asarray(neck, float) + np.asarray(pelvis_pt, float)),
                              u, v, torso_half_along, torso_half_across) & m
        pelvis = _ellipse_mask(shape, np.asarray(pelvis_pt, float), u, v,
                               pelvis_half_along, pelvis_half_across) & m
        return {"torso": torso, "pelvis": pelvis}

    # 退化路径：无关键点 → 人体框内水平矩形带
    bbox = person_bbox(m)
    if bbox is None:
        return {"torso": empty, "pelvis": empty}
    x0, y0, x1, y1 = bbox
    box_w = float(x1 - x0 + 1)
    box_h = float(y1 - y0 + 1)
    xc = x0 + 0.5 * box_w
    top = y0 + _opt_float(mcfg, "bbox_top_frac", DEFAULT_BBOX_TOP_FRAC) * box_h

    torso_w = _opt_float(mcfg, "fallback_torso_width_frac", DEFAULT_FALLBACK_TORSO_WIDTH_FRAC) * box_w
    pelvis_w = _opt_float(mcfg, "fallback_pelvis_width_frac", DEFAULT_FALLBACK_PELVIS_WIDTH_FRAC) * box_w
    torso_center = np.array([xc, top + 0.5 * torso_frac * box_h], dtype=np.float64)
    pelvis_center = np.array([xc, top + torso_frac * box_h + 0.5 * pelvis_frac * box_h], dtype=np.float64)
    u = np.array([0.0, 1.0], dtype=np.float64)   # 图像 y 向下 = 身体向下
    v = np.array([1.0, 0.0], dtype=np.float64)
    torso = _ellipse_mask(shape, torso_center, u, v, 0.5 * torso_frac * box_h, 0.5 * torso_w) & m
    pelvis = _ellipse_mask(shape, pelvis_center, u, v, 0.5 * pelvis_frac * box_h, 0.5 * pelvis_w) & m
    return {"torso": torso, "pelvis": pelvis}


def region_masks(
    mask: np.ndarray, keypoints_px: dict | None = None, cfg: dict | None = None
) -> dict[str, np.ndarray]:
    """躯干 / 骨盆的区域掩膜 `{"torso": bool(H,W), "pelvis": bool(H,W)}`（已与人体 Mask 求交）。

    关键点路径为沿 neck→pelvis 的椭圆，退化路径为人体框内的水平带；几何见模块 docstring。
    """
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 2:
        raise ValueError(f"mask 必须是 (H, W)，收到 {m.shape}")
    return _region_masks_with(m, keypoints_px, _mask_cfg(cfg))


# ---------------------------------------------------------------------------
# 统计（中位数是主输出）


def _region_stat_core(depth: DepthMap, region: np.ndarray, name: str, min_px: int) -> RegionStat | None:
    values = depth.at_mask(region)          # 有限且 > 0 的样本
    px = int(values.size)
    if px == 0 or px < min_px:
        return None
    p10, p90 = np.percentile(values, [10.0, 90.0])
    height, width = depth.depth.shape
    total = float(height) * float(width)
    return RegionStat(
        name=str(name),
        frac=(float(px) / total) if total > 0 else 0.0,
        px=px,
        depth_median_m=float(np.median(values)),   # ← 立身之本：中位数，不是均值
        depth_p10_m=float(p10),
        depth_p90_m=float(p90),
    )


def region_stat(
    depth: DepthMap, region: np.ndarray, name: str, min_px: int
) -> RegionStat | None:
    """单个区域的中位数统计；有效像素 `< min_px` 返回 None（`min_px` 由调用方给，见 cfg）。"""
    d = _require_metric_depth(depth)
    reg = _as_mask(region, d.depth.shape, what="region")
    return _region_stat_core(d, reg, name, int(min_px))


def _stats_from_mask(
    depth: DepthMap, mask: np.ndarray, keypoints_px: dict | None, mcfg: dict[str, Any]
) -> list[RegionStat]:
    regions = _region_masks_with(mask, keypoints_px, mcfg)
    min_px = int(_opt_float(mcfg, "min_px", 400.0))
    stats: list[RegionStat] = []
    for name in REGION_NAMES:
        stat = _region_stat_core(depth, regions[name], name, min_px)
        if stat is not None:
            stats.append(stat)
    return stats


def torso_pelvis_stats(
    depth: DepthMap, mask: np.ndarray, keypoints_px: dict | None = None, cfg: dict | None = None
) -> list[RegionStat]:
    """躯干 / 骨盆区域的度量深度统计（spec §3）。

    返回 `[torso, pelvis]`（顺序固定，躯干在前）；某区域有效像素 < `cfg["mask"]["min_px"]`
    就被丢弃，两个都不可信时返回 `[]`。`depth` 必须是 `kind="metric"`，否则 `MetricRequired`。

    每个 `RegionStat.depth_median_m` 就是该区域的**深度中位数（米）**——融合用的根节点 Z 观测。
    """
    d = _require_metric_depth(depth)
    m = _as_mask(mask, d.depth.shape)
    return _stats_from_mask(d, m, keypoints_px, _mask_cfg(cfg))


def stat_by_name(stats: list[RegionStat], name: str) -> RegionStat | None:
    """按名字取统计（'torso' / 'pelvis'），没有返回 None。"""
    for stat in stats or []:
        if stat.name == name:
            return stat
    return None


def primary_stat(stats: list[RegionStat]) -> RegionStat | None:
    """主观测区域：躯干优先，退化到骨盆；都没有返回 None。"""
    return stat_by_name(stats, "torso") or stat_by_name(stats, "pelvis")


# ---------------------------------------------------------------------------
# 便捷封装：直接给出构造 `FramePrior` 需要的数字（cli / fusion 可用）


def frame_observation(
    depth: DepthMap, mask: np.ndarray, keypoints_px: dict | None = None, cfg: dict | None = None
) -> dict[str, Any]:
    """一帧的深度观测汇总（构造 `FramePrior` 的原料，`frame`/`perspective_m` 由调用方补）。

    返回 dict：
        depth_median_m : 主区域（躯干→骨盆）的深度中位数（米）；不可信时 NaN
        iqr_m          : 主区域的 p90-p10；不可信时 NaN
        torso_px       : 颈→骨盆像素长（`priors.torso_px_length`）；取不到时 NaN
        mask_frac      : 人体 Mask 像素占画面比例（mask.sum()/(H*W)）
        valid / reason : 可信标志与不可信原因（中文，可直接进 `FramePrior.reason`）
        region         : 实际采用的主区域名（'' 表示都不可信）
        stats          : `torso_pelvis_stats()` 的原始结果
    """
    d = _require_metric_depth(depth)
    m = _as_mask(mask, d.depth.shape)
    mcfg = _mask_cfg(cfg)
    min_px = int(_opt_float(mcfg, "min_px", 400.0))
    height, width = d.depth.shape
    total = float(height) * float(width)

    stats = _stats_from_mask(d, m, keypoints_px, mcfg)
    ref = primary_stat(stats)
    valid = ref is not None
    if valid:
        reason = ""
    elif not m.any():
        reason = "人体 mask 全为 False"
    else:
        regions = _region_masks_with(m, keypoints_px, mcfg)
        counts = {name: int(d.at_mask(regions[name]).size) for name in REGION_NAMES}
        reason = (
            f"躯干/骨盆区域有效深度像素均 < mask.min_px={min_px}"
            f"（torso={counts['torso']}px, pelvis={counts['pelvis']}px）"
        )

    torso_px = torso_px_length(keypoints_px, cfg)
    return {
        "depth_median_m": float(ref.depth_median_m) if ref is not None else float("nan"),
        "iqr_m": float(ref.iqr_m) if ref is not None else float("nan"),
        "torso_px": float("nan") if torso_px is None else float(torso_px),
        "mask_frac": (float(m.sum()) / total) if total > 0 else 0.0,
        "valid": bool(valid),
        "reason": reason,
        "region": ref.name if ref is not None else "",
        "stats": stats,
    }
