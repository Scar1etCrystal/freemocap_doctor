"""`priors.py` — 2D 躯干透视粗先验 + 相对深度→度量锚定的仿射对齐（spec §0/§1(C)/§3/§4）。

铁律（本框架的立身之本）
------------------------
相对深度（`DepthMap.kind == "relative"`）有 scale-shift 不确定性，
**绝不能拿人体像素值当深度**。相对深度在本框架里唯一被允许的去路是：

    (a, b) = affine_align_to_metric(rel, anchors, anchor_depth_m)   # 到绝对锚点做最小二乘
    metric = relative_to_metric(depthmap, anchors, anchor_depth_m)  # 显式产出 kind="metric" 的新图

`perspective_prior()` 给的躯干透视量是**单调的相对量**（`Depth ∝ 1/躯干像素长`），
只用于 fusion 的慢变一致性检查/平滑项，**不提供绝对尺度**。

键点输入约定
------------
`keypoints_px` 是 `{名字: (x, y)}` 的字典，值为像素坐标（图像系，x 向右、y 向下）。
取点对名字大小写、`_`/`-` 分隔不敏感（见 `KEYPOINT_ALIASES`），也接受 `{"x":..,"y":..}`
或长度 >= 2 的序列（多余的置信度分量会被忽略）。缺 `neck` 时退回左右肩中点、
缺 `pelvis` 时退回左右髋中点；取不到就是 `None`，由调用方决定不可信。
"""

from __future__ import annotations

from typing import Any

import numpy as np

if __package__:
    from .types import KIND_METRIC, DepthMap
else:  # pragma: no cover - 允许直接按文件路径运行（避免把 depth_prior/ 加进 sys.path 而遮蔽 stdlib `types`）
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from depth_prior.types import KIND_METRIC, DepthMap

__all__ = [
    "KEYPOINT_ALIASES",
    "resolve_keypoint",
    "torso_px_length",
    "perspective_prior",
    "affine_align_to_metric",
    "apply_affine",
    "relative_to_metric",
]

#: 关键点别名表（归一化后比较：转小写、去掉所有非字母数字字符）。
KEYPOINT_ALIASES: dict[str, tuple[str, ...]] = {
    "neck": (
        "neck", "neck_px", "neck2d", "neck_2d", "upper_neck", "neck_center",
        "neck_mid", "spine2", "spine_2", "spine2_px", "head_neck", "neck_base",
    ),
    "pelvis": (
        "pelvis", "pelvis_px", "pelvis2d", "pelvis_2d", "pelvis_center", "pelvis_joint",
        "pelvis_mid", "pelvis_root", "mid_pelvis",
        "hips", "hip", "hips_px", "hips2d", "hips_2d", "hip2d", "hip_2d", "hip_center",
        "hip_mid", "mid_hip", "midhip", "mid_hips", "midhips",
        "root", "root_pelvis", "torso_root",
    ),
    "left_shoulder": ("left_shoulder", "l_shoulder", "shoulder_l", "shoulder_left", "lshoulder"),
    "right_shoulder": ("right_shoulder", "r_shoulder", "shoulder_r", "shoulder_right", "rshoulder"),
    "left_hip": ("left_hip", "l_hip", "hip_l", "hip_left", "left_hip_joint"),
    "right_hip": ("right_hip", "r_hip", "hip_r", "hip_right", "right_hip_joint"),
}

#: 主点缺失时的成对退化（取两侧中点）。
_PAIR_FALLBACK: dict[str, tuple[str, str]] = {
    "neck": ("left_shoulder", "right_shoulder"),
    "pelvis": ("left_hip", "right_hip"),
}


def _norm(name: Any) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


_NORMALIZED: dict[str, tuple[str, ...]] = {
    key: tuple(_norm(alias) for alias in aliases) for key, aliases in KEYPOINT_ALIASES.items()
}


def _as_xy(value: Any) -> np.ndarray | None:
    """把任意"二维点"表示解析成 float64 (2,) = (x, y)；解析不了返回 None。"""
    if isinstance(value, dict):
        try:
            value = [value["x"], value["y"]]
        except (KeyError, TypeError):
            return None
    try:
        arr = np.asarray(value, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError):
        return None
    if arr.size < 2:
        return None
    xy = arr[:2]
    if not np.all(np.isfinite(xy)):
        return None
    return np.ascontiguousarray(xy)


def resolve_keypoint(keypoints_px: dict | None, which: str) -> np.ndarray | None:
    """从 `keypoints_px` 里取 `which` 点的像素坐标 (x, y)；取不到返回 None。

    `which` ∈ {"neck", "pelvis", "left_shoulder", "right_shoulder", "left_hip", "right_hip"}。
    neck/pelvis 在缺失时会退化到左右肩/左右髋的中点。
    """
    if not isinstance(keypoints_px, dict) or not keypoints_px:
        return None

    lookup: dict[str, Any] = {}
    for raw_key, raw_val in keypoints_px.items():
        lookup.setdefault(_norm(raw_key), raw_val)

    for alias in _NORMALIZED.get(which, ()):  # 精确别名
        if alias in lookup:
            xy = _as_xy(lookup[alias])
            if xy is not None:
                return xy

    pair = _PAIR_FALLBACK.get(which)  # 成对中点
    if pair:
        pts = [xy for xy in (resolve_keypoint(keypoints_px, p) for p in pair) if xy is not None]
        if len(pts) == 2:
            return 0.5 * (pts[0] + pts[1])
    return None


def torso_px_length(keypoints_px: dict, cfg: dict | None = None) -> float | None:
    """颈→骨盆的 2D 像素长（spec §3）。取不到关键点、长度非正/非有限返回 None。

    可选 cfg 键 `mask.min_torso_px`（默认 0.0）：长度小于它时也返回 None。
    """
    neck = resolve_keypoint(keypoints_px, "neck")
    pelvis = resolve_keypoint(keypoints_px, "pelvis")
    if neck is None or pelvis is None:
        return None
    length = float(np.hypot(pelvis[0] - neck[0], pelvis[1] - neck[1]))
    if not np.isfinite(length) or length <= 0.0:
        return None
    min_px = 0.0
    if isinstance(cfg, dict) and isinstance(cfg.get("mask"), dict):
        raw = cfg["mask"].get("min_torso_px", 0.0)
        try:
            min_px = float(raw)
        except (TypeError, ValueError):
            min_px = 0.0
    if length < min_px:
        return None
    return length


def perspective_prior(torso_px: float, ref_px: float, ref_z_m: float) -> float:
    """躯干透视粗先验：小孔成像 `Depth ∝ 1/躯干像素长`，锚定到参考帧。

        perspective_prior(torso_px, ref_px, ref_z_m) = ref_z_m * ref_px / torso_px

    返回值的尺度由参考帧 `(ref_px, ref_z_m)` 决定，**不是米**（除非参考帧本身是米、
    且人体只做纯深度平移）；供 fusion 的慢变项使用。像素长翻倍 → 输出减半。

    三个参数都必须是有限正数（人体在画面内、深度 > 0 才有定义），否则 `ValueError`。
    """
    torso = float(torso_px)
    ref = float(ref_px)
    ref_z = float(ref_z_m)
    for name, value in (("torso_px", torso), ("ref_px", ref), ("ref_z_m", ref_z)):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"perspective_prior: {name} 必须是有限正数，收到 {value!r}"
                "（躯干透视先验只在人体在画面内、参考深度 > 0 时有定义）"
            )
    return float(ref_z * ref / torso)


def _select_anchor_values(rel: np.ndarray, anchors: np.ndarray | None, n_target: int) -> np.ndarray:
    """从 `rel` 里按 `anchors` 取出参与拟合的相对深度样本（一维，长度应为 n_target）。

    支持的 `anchors` 形式（按优先级）：
      1. None / 空 → `rel` 展平后本身就是逐锚点样本；
      2. bool 掩膜（形状同 `rel` 或与 `rel` 同长）；
      3. (N,2) / (2,N) 像素坐标 (x, y) —— `rel` 是 2D 相对深度图；
      4. 一维整数索引 → `rel` 展平后的下标；
      5. `rel` 已经是逐锚点采样值（一维、长度 == N）→ `anchors` 仅作数量校验。
    """
    flat = rel.reshape(-1)
    if anchors is None or anchors.size == 0:
        return flat

    # 2. bool 掩膜
    if anchors.dtype == bool:
        try:
            if anchors.shape == rel.shape:
                return rel[anchors].reshape(-1)
            if anchors.shape == flat.shape:
                return flat[anchors]
            return rel[anchors].reshape(-1)
        except IndexError as exc:
            raise ValueError(f"anchors 布尔掩膜 {anchors.shape} 无法索引 rel {rel.shape}") from exc

    # 3. 像素坐标
    coords: np.ndarray | None = None
    if anchors.ndim == 2 and anchors.shape[1] == 2:
        coords = anchors
    elif anchors.ndim == 2 and anchors.shape[0] == 2 and anchors.shape[1] != 2:
        coords = anchors.T
    if coords is not None:
        if rel.ndim == 2 and coords.shape[0] == n_target:
            height, width = rel.shape
            xs = np.rint(np.asarray(coords[:, 0], dtype=np.float64)).astype(np.int64)
            ys = np.rint(np.asarray(coords[:, 1], dtype=np.float64)).astype(np.int64)
            if np.any(xs < 0) or np.any(xs >= width) or np.any(ys < 0) or np.any(ys >= height):
                raise ValueError(
                    f"anchors 像素坐标越界（图像 {height}x{width}，坐标必须 (x, y) 在画面内）"
                )
            return rel[ys, xs]
        if rel.ndim == 1 and rel.size == n_target:
            return rel  # rel 已是逐锚点采样值，anchors 只是坐标

    # 4. 一维整数索引
    if anchors.ndim == 1 and anchors.dtype.kind in "iu":
        idx = np.asarray(anchors, dtype=np.int64)
        if np.any(idx < 0) or np.any(idx >= flat.size):
            raise ValueError(f"anchors 索引越界：rel 展平后 {flat.size} 个样本，收到 [{idx.min()}, {idx.max()}]")
        return flat[idx]

    # 5. rel 已是逐锚点采样值（浮点 anchors 只当坐标/标识）
    if rel.ndim == 1 and rel.size == n_target:
        return rel

    raise ValueError(
        "无法解释 anchors 的形式：支持 bool 掩膜 / (N,2) 像素坐标 / 一维整数索引 / "
        f"rel 本身即逐锚点采样值（收到 anchors.shape={anchors.shape}, rel.shape={rel.shape}, "
        f"anchor_depth_m.size={n_target}）"
    )


def affine_align_to_metric(
    rel: np.ndarray, anchors: np.ndarray | None = None, anchor_depth_m: np.ndarray | None = None
) -> tuple[float, float]:
    """相对深度 → 度量尺度的仿射对齐（**只给相对深度用**，spec §0/§3）。

    最小二乘拟合 `a * rel + b ≈ anchor_depth_m`，返回 `(a, b)`：

        a, b = affine_align_to_metric(rel_map, anchors_px, anchor_depth_m)
        metric = a * rel_map + b          # 或直接用 apply_affine / relative_to_metric

    `anchors` 的合法形式见 `_select_anchor_values`（bool 掩膜 / (N,2) 像素坐标 /
    一维整数索引 / None=用整个 rel）。只有有限、> 0 的锚点对参与拟合。

    相对深度**不许**绕过本函数直接当米用。锚点不足 2 个、或锚点相对深度没有变化
    （scale 不可辨识）时 `ValueError`。
    """
    if anchor_depth_m is None:
        raise ValueError("affine_align_to_metric 必须给 anchor_depth_m（锚点的绝对度量深度，米）")
    rel_arr = np.asarray(rel, dtype=np.float64)
    if rel_arr.size == 0:
        raise ValueError("rel 为空，无法拟合仿射")
    anchors_arr = None if anchors is None else np.asarray(anchors)
    target = np.asarray(anchor_depth_m, dtype=np.float64).reshape(-1)
    if target.size == 0:
        raise ValueError("anchor_depth_m 为空，无法拟合仿射")

    values = _select_anchor_values(rel_arr, anchors_arr, target.size)
    if values.size != target.size:
        raise ValueError(
            f"锚点数量不一致：从 rel 取到 {values.size} 个样本，anchor_depth_m 有 {target.size} 个"
        )

    ok = np.isfinite(values) & np.isfinite(target) & (target > 0.0)
    values = values[ok]
    target = target[ok]
    if values.size < 2:
        raise ValueError(f"有效锚点只有 {values.size} 个（要求 >= 2 且深度有限为正），仿射不可辨识")
    if float(np.ptp(values)) <= 0.0:
        raise ValueError("锚点的相对深度全等（无变化），scale 不可辨识")

    design = np.stack([values, np.ones_like(values)], axis=1)
    solution, *_ = np.linalg.lstsq(design, target, rcond=None)
    scale = float(solution[0])
    shift = float(solution[1])
    if not (np.isfinite(scale) and np.isfinite(shift)):
        raise ValueError("最小二乘解非有限，锚点数据有问题")
    return scale, shift


def apply_affine(rel: np.ndarray, scale: float, shift: float) -> np.ndarray:
    """把 `affine_align_to_metric` 得到的 (scale, shift) 应用到相对深度上（float64）。"""
    arr = np.asarray(rel, dtype=np.float64)
    return arr * float(scale) + float(shift)


def relative_to_metric(
    depth: DepthMap,
    anchors: np.ndarray | None = None,
    anchor_depth_m: np.ndarray | None = None,
) -> DepthMap:
    """**唯一被允许的 relative → metric 通道**（spec §0）。

    用绝对锚点拟合仿射后应用到整张相对深度图，返回 `kind="metric"`、单位米的新 `DepthMap`
    （backend 标记为 `<原 backend>+affine`）。非有限值保持 NaN、非正值置 NaN，
    交给 `DepthMap.at_mask` 之类的既有过滤逻辑。已经是 metric 的输入原样返回。
    """
    if not isinstance(depth, DepthMap):
        raise TypeError(f"relative_to_metric 需要 types.DepthMap，收到 {type(depth).__name__}")
    if depth.is_metric:
        return depth
    scale, shift = affine_align_to_metric(depth.depth, anchors, anchor_depth_m)
    aligned = apply_affine(depth.depth, scale, shift)
    aligned[~np.isfinite(aligned)] = np.nan
    aligned[aligned <= 0.0] = np.nan
    return DepthMap(
        depth=aligned.astype(np.float32),
        kind=KIND_METRIC,
        unit="m",
        backend=f"{depth.backend}+affine",
    )
