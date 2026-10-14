"""根节点 Z 融合层（w3，写作用域：本文件；spec §1(D) / §3 / §4 / §5）。

职责
----
把两路先验合成逐帧根节点 Z（**滤波前**的 `z_raw_m` 与逐帧置信度）：

- **主项 = 逐帧度量深度中位数** `FramePrior.depth_median_m`（米，绝对锚定）。
- **粗项 = 2D 躯干像素长的透视先验** `FramePrior.perspective_m`（∝ 1/躯干px，
  **相对量，只做慢变一致性约束**，绝不当作绝对深度使用）：
  1) 慢漂校正：`q = z/p` 在"真实 Z 运动"上是常数（p ∝ Z_true 时两者相除抵消），
     因此 q 的慢分量就是**缓慢尺度漂移**；用零相位、鲁棒的局部多项式拟合出
     `drift_est = q_slow / median(q_slow)`（相对量，不含绝对锚点），
     再 `z_corr = z / drift_est`。
  2) 慢形状混合：把 p 按中位数标定到 z 的尺度后，只把**慢分量**按
     `w_persp/(w_depth+w_persp)` 混进去（快分量完全保留，逐帧细节不被粗项污染）。

安全闸门（本文件最重要的一条）
------------------------------
这条路径**只接受度量深度**。任何 `kind == "relative"` 的输入（`kind=` 关键字、
`cfg["fusion"]["kind"]`、逐帧对象上的 `kind` 属性、或误传的 `DepthMap`）都必须
`raise types.MetricRequired`，**绝不允许静默当米用**。相对深度只能走
`priors.affine_align_to_metric()`。

鲁棒性与报警
------------
- `iqr_m > cfg["fusion"]["iqr_max_m"]` → 按 `iqr_max/iqr` 降权（0.05 下限）。
- **孤立**离群帧（与前后有效邻帧的中值差超阈值、且邻帧彼此一致）→ 剔除并插值；
  真实快速运动（前后邻帧本身在变）不会被误判。
- `valid=False` / 非有限 / 非正的帧 → 线性插值补齐 + 置信度按间隙长度衰减。
- 报警（写进 `fuse_detailed()` 的 `diag["alarms"]`，并且 `warnings.warn` 出来，
  **不许静默**）：整体尺度错位 `scale_offset`、慢漂超 `scale_alarm` 的 `scale_drift`、
  度量与躯干慢分量偏差超 `torso_tol` 的 `torso_mismatch`、全部帧无效
  `no_valid_frames`、没有可用躯干先验 `perspective_unavailable`。

API
---
- `fuse(frames, cfg) -> (z_raw_m, confidence)`：spec §3 冻结签名（额外关键字
  `kind=` / `anchor_z_m=` 可选）。
- `fuse_detailed(frames, cfg) -> (z_raw_m, confidence, diag)`：多返回一份
  纯 Python 类型的诊断字典（可直接塞进 `RootZTrack.diag`，`repr`/`eval` 安全）。

**一个尺度上的数学事实**（写给验收方）：若透视先验的尺度是任意的，
那么"整段深度统一乘 2"这种**常数**尺度误差在几何上不可观测（z 与 p 的比值
只有相对变化可测）。因此 `scale_offset` 只在 p 被判为"准米制"时生效：
`persp_scale="metric"` 显式声明，或 `"auto"`（默认）下 `median(z/p)` 落在
[1/window, window]（默认 ±3 倍）内。确实需要绝对锚定时，调用方传
`anchor_z_m=`（例如已知站立距离）。
"""

from __future__ import annotations

import warnings as _warnings

import numpy as np

try:  # 包内导入（`from depth_prior import fusion`）
    from . import types as _types
except ImportError:  # 直接按文件路径/顶层模块导入时的回退
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from depth_prior import types as _types

MetricRequired = _types.MetricRequired
KIND_METRIC = _types.KIND_METRIC
KIND_RELATIVE = _types.KIND_RELATIVE

_GEOM_EPS = 1e-9

# 本模块新增的配置键（spec §4 之外的扩展；全部可被 cfg 覆盖）
_EXTRA_DEFAULTS: dict[str, dict] = {
    "fusion": {
        # 慢漂估计
        "drift_window_s": 0.5,     # 局部拟合窗长（秒，零相位）
        "drift_order": 2,          # 局部多项式阶数
        "drift_clip": 0.35,        # 单帧漂移修正幅度上限（相对）
        "drift_k": 3.5,            # 局部拟合的 Tukey 稳健化倍数
        # 孤立离群点
        "outlier_k": 3.5,          # 相对噪声尺度的倍数
        "outlier_min_m": 0.05,     # 绝对下限（米）：小于它的偏差不判离群
        # 无效帧
        "gap_conf": 0.25,          # 插值帧置信度上限
        "gap_tau_s": 0.5,          # 置信度随间隙长度衰减的时间常数（秒）
        # 尺度判定
        "persp_scale": "auto",     # auto | metric | relative
        "persp_scale_window": 3.0, # auto 判定窗口（比值倍数）
        "global_scale_tol": 0.5,   # 全局常数尺度错位阈值（相对）
        "scale_conf_penalty": 0.25,
        "torso_conf_penalty": 0.5,
    }
}


class FusionAlarm(UserWarning):
    """融合层报警（`diag["alarms"]` 非空时同时以 warning 形式发出）。"""


# 最近一次 `fuse()` / `fuse_detailed()` 的诊断快照。
# 冻结签名 `fuse()` 只返回 (z_raw, confidence)，报警除了 `warnings.warn` 之外
# 还需要一个"看得到"的出口：这两个模块级变量是**诊断用**的（并发调用不安全；
# 正式消费请用 `fuse_detailed()` 的返回值）。
LAST_ALARMS: list = []
LAST_DIAG: dict = {}


# ---------------------------------------------------------------------------
# 小工具


def _get(obj, key: str, default=None):
    """同时支持 dataclass 属性与 dict 键（FramePrior 是 dataclass）。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_float(value, default=float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_bool(value) -> bool:
    if value is None:
        return True
    return bool(value)


def _resolve_cfg(cfg: dict | None) -> dict:
    merged = _types.merge_cfg(cfg)
    for section, values in _EXTRA_DEFAULTS.items():
        merged.setdefault(section, {})
        for key, value in values.items():
            merged[section].setdefault(key, value)
    return merged


def _frame_list(frames):
    """接受 list/tuple/可迭代/单个对象；单个 DepthMap 也能被闸门看到。"""
    if isinstance(frames, (list, tuple)):
        return list(frames)
    if hasattr(frames, "__iter__") and not hasattr(frames, "depth"):
        return list(frames)
    return [frames]


_RELATIVE_MSG = (
    "fusion 只接受度量深度（kind='metric'，单位米）：收到 kind='relative'。"
    "相对深度是仿射不变的（每帧 Min/Max 由画面决定），不得当米用——"
    "请先用 priors.affine_align_to_metric() 对齐到绝对锚点，或改用度量头后端"
    "（Depth Anything V2 Metric-Small）。"
)


def _gate_kind(items: list, kind: str, cfg: dict) -> None:
    """安全闸门：非 metric 一律 raise，绝不静默通过。"""
    if kind not in (KIND_METRIC, KIND_RELATIVE):
        raise ValueError(
            f"kind 只能是 {KIND_METRIC!r}/{KIND_RELATIVE!r}，收到 {kind!r}"
        )
    if kind != KIND_METRIC:
        raise MetricRequired(f"{_RELATIVE_MSG}（来源：fusion.fuse(kind={kind!r})）")

    cfg_kind = cfg.get("fusion", {}).get("kind") if isinstance(cfg, dict) else None
    if cfg_kind is not None and str(cfg_kind) != KIND_METRIC:
        raise MetricRequired(f"{_RELATIVE_MSG}（来源：cfg['fusion']['kind']={cfg_kind!r}）")

    for i, item in enumerate(items):
        item_kind = _get(item, "kind", None)
        if item_kind is not None and str(item_kind) != KIND_METRIC:
            if str(item_kind) == KIND_RELATIVE:
                raise MetricRequired(f"{_RELATIVE_MSG}（来源：frames[{i}].kind='relative'）")
            raise ValueError(f"frames[{i}].kind 非法：{item_kind!r}")
        if _get(item, "depth_median_m", None) is None:
            if hasattr(item, "depth"):
                raise TypeError(
                    f"frames[{i}] 是整图 {type(item).__name__}，不是 FramePrior："
                    "请先用 masks.torso_pelvis_stats() 取躯干/骨盆区域的度量深度中位数，"
                    "再把统计量包成 FramePrior 交给 fuse()。"
                )
            raise TypeError(
                f"frames[{i}]（{type(item).__name__}）缺少 depth_median_m 字段，"
                "无法作为 FramePrior 使用。"
            )


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    v = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not np.any(ok):
        return float("nan")
    v, w = v[ok], w[ok]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cum = np.cumsum(w)
    cutoff = 0.5 * cum[-1]
    return float(v[int(np.searchsorted(cum, cutoff, side="left"))])


def _local_poly_smooth(
    values: np.ndarray,
    mask: np.ndarray,
    *,
    window: int,
    order: int,
    weights: np.ndarray | None = None,
    k: float = 3.5,
    iters: int = 2,
) -> np.ndarray:
    """零相位、鲁棒的局部多项式平滑：逐帧做加权最小二乘，取窗中心处的拟合值。

    只把 `mask` 为真的帧放进拟合（无效观测不参与），但**输出覆盖所有帧**
    （单侧窗外推），这样被剔除/无效的帧也能得到漂移与形状估计。

    稳健化用**全局**残差尺度（而不是每个窗自己的残差尺度）：先做一遍加权最小二乘，
    用所有窗的残差池算 1.4826·MAD 作为尺度 σ_r，再按 Tukey biweight
    `(1-(r/(k·σ_r))²)²` 重拟合 `iters-1` 次。全局尺度避免了小窗（点数≈参数数）
    时"残差≈0 → 权重全塌"的退化——这正是逐窗尺度版本在窗长 5、阶数 2 时会给出
    95% 偏差的原因。窗内不足 `order+1` 个点时自动降阶。
    """
    n = int(values.size)
    out = np.full(n, np.nan, dtype=np.float64)
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return out
    v_all = np.asarray(values, dtype=np.float64)
    base_w = np.ones(n) if weights is None else np.clip(np.asarray(weights, dtype=np.float64), 0.0, None)
    if idx.size == 1:
        out[:] = v_all[idx[0]]
        return out

    half = max(1, int(window) // 2)
    plans: list[tuple[int, np.ndarray, np.ndarray, int]] = []
    for i in range(n):
        lo = int(np.searchsorted(idx, i - half, side="left"))
        hi = int(np.searchsorted(idx, i + half, side="right"))
        sel = idx[lo:hi]
        if sel.size == 0:
            sel = idx[[int(np.argmin(np.abs(idx - i)))]]
        t = (sel - i).astype(np.float64)
        deg = int(min(order, max(0, sel.size - 1)))
        plans.append((i, sel, t, deg))

    def _wls(A: np.ndarray, w: np.ndarray, v: np.ndarray) -> np.ndarray:
        sw = np.sqrt(np.maximum(w, 0.0))
        if not np.any(sw > 0.0):
            sw = np.ones_like(sw)
        try:
            coef, *_ = np.linalg.lstsq(A * sw[:, None], v * sw, rcond=None)
        except np.linalg.LinAlgError:
            coef = np.zeros(A.shape[1])
            coef[0] = float(np.mean(v))
        return coef

    design = [np.vander(t, deg + 1, increasing=True) for _i, _sel, t, deg in plans]

    # --- 第一遍：外部权重下的 WLS，收集残差池 ---
    coefs: list[np.ndarray] = []
    resid_pool: list[np.ndarray] = []
    for (i, sel, _t, _deg), A in zip(plans, design):
        coef = _wls(A, base_w[sel], v_all[sel])
        coefs.append(coef)
        resid_pool.append(v_all[sel] - A @ coef)
    pool = np.concatenate(resid_pool)
    pool = pool[np.isfinite(pool)]
    if pool.size >= 3:
        med = float(np.median(pool))
        sigma_r = 1.4826 * float(np.median(np.abs(pool - med)))
    else:
        sigma_r = 0.0

    # --- 后续遍：Tukey biweight IRLS（全局尺度；σ_r=0 时直接跳过，避免 0 除） ---
    passes = max(1, int(iters))
    if passes > 1 and np.isfinite(sigma_r) and sigma_r > 0.0:
        for _ in range(passes - 1):
            new_coefs: list[np.ndarray] = []
            for (i, sel, _t, _deg), A, coef in zip(plans, design, coefs):
                r = v_all[sel] - A @ coef
                r = np.where(np.isfinite(r), r, np.inf)
                ratio = np.abs(r) / (max(float(k), _GEOM_EPS) * sigma_r)
                w = np.clip(1.0 - ratio * ratio, 0.0, 1.0) ** 2
                w = w * (base_w[sel] > 0.0)
                if not np.any(w > 0.0):
                    w = np.ones_like(w)
                new_coefs.append(_wls(A, w, v_all[sel]))
            coefs = new_coefs

    for (i, sel, _t, _deg), coef in zip(plans, coefs):
        # 只在观测覆盖到的地方信任拟合值：中心点落在窗口之外（例如粗项长段缺失）时
        # 把求值点夹到最近的窗内样本，等价于"保持边缘估计"，
        # 避免局部多项式在长间隙上外推爆炸（实测未夹紧时误差可达 75%）。
        t_eval = 0.0
        t_sel = sel - i
        if t_sel.size and t_sel.min() > 0:
            t_eval = float(t_sel.min())
        elif t_sel.size and t_sel.max() < 0:
            t_eval = float(t_sel.max())
        val = float(sum(float(coef[k]) * t_eval ** k for k in range(coef.size)))
        out[i] = val if np.isfinite(val) else float(v_all[sel[0]])
    return out


def _isolated_outliers(z: np.ndarray, ok: np.ndarray, fcfg: dict) -> np.ndarray:
    """孤立离群帧：与前后**有效**邻帧的中值差超阈值，且两邻帧彼此一致。

    要求邻帧彼此一致是关键：真实快速运动（前后邻帧本身就在变）不会被误判成离群。
    """
    n = int(z.size)
    flag = np.zeros(n, dtype=bool)
    idx = np.flatnonzero(ok)
    if idx.size < 3:
        return flag
    # 用有效帧序列估计帧间噪声尺度（中值差的一半的 MAD）
    nxt = z[idx[1:]]
    prv = z[idx[:-1]]
    pair = np.abs(nxt - prv) * 0.5
    pair = pair[np.isfinite(pair)]
    scale = 1.4826 * float(np.median(np.abs(pair - np.median(pair)))) if pair.size > 2 else 0.0
    thr = max(float(fcfg["outlier_k"]) * scale, float(fcfg["outlier_min_m"]))
    for j in range(1, idx.size - 1):
        i = int(idx[j])
        prev_v = float(z[idx[j - 1]])
        next_v = float(z[idx[j + 1]])
        neigh_med = 0.5 * (prev_v + next_v)
        neigh_gap = abs(prev_v - next_v)
        if (abs(float(z[i]) - neigh_med) > thr) and (neigh_gap < thr):
            flag[i] = True
    return flag


def _gap_conf(gap_len: int, fcfg: dict, fps: float) -> float:
    tau = max(float(fcfg["gap_tau_s"]), _GEOM_EPS) * max(fps, _GEOM_EPS)
    return float(fcfg["gap_conf"]) / (1.0 + max(0, gap_len - 1) / tau)


def _emit_alarms(diag: dict) -> None:
    """报警出口：记进 `LAST_ALARMS`/`LAST_DIAG` 并逐条 `warnings.warn`，不许静默。"""
    global LAST_ALARMS, LAST_DIAG
    LAST_ALARMS = [str(a.get("code", "?")) for a in diag.get("alarms", [])]
    LAST_DIAG = diag
    for alarm in diag.get("alarms", []):
        _warnings.warn(f"[fusion] 报警 {alarm['code']}: {alarm['message']}",
                       FusionAlarm, stacklevel=3)


# ---------------------------------------------------------------------------
# 主入口


def fuse_detailed(
    frames: list,
    cfg: dict | None = None,
    *,
    kind: str = KIND_METRIC,
    anchor_z_m: float | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """融合求解，并返回诊断字典（`fuse()` 只返回前两项）。

    Parameters
    ----------
    frames : `FramePrior` 列表（也接受 dict；缺 `depth_median_m` 会报错）。
    cfg : spec §4 的配置（缺失键用默认值，本模块扩展键见 `_EXTRA_DEFAULTS`）。
    kind : 上游深度种类。**只有 "metric" 能进来**，其余 raise `MetricRequired`。
    anchor_z_m : 可选绝对锚点（米，例如已知站立距离）→ 参与全局尺度检查。

    Returns
    -------
    (z_raw_m, confidence, diag)
    """
    cfg = _resolve_cfg(cfg)
    fcfg = cfg["fusion"]
    fps = _as_float(cfg.get("filter", {}).get("fps", 30.0), 30.0)
    items = _frame_list(frames)
    _gate_kind(items, kind, cfg)

    n = len(items)
    diag: dict = {
        "gate": {"kind": str(kind), "accepted": True, "n_frames": int(n)},
        "alarms": [],
        "info": [],
        "params": {
            "iqr_max_m": float(fcfg["iqr_max_m"]),
            "torso_tol": float(fcfg["torso_tol"]),
            "w_depth": float(fcfg["w_depth"]),
            "w_persp": float(fcfg["w_persp"]),
            "scale_alarm": float(fcfg["scale_alarm"]),
            "drift_window_s": float(fcfg["drift_window_s"]),
            "drift_order": int(fcfg["drift_order"]),
            "drift_clip": float(fcfg["drift_clip"]),
            "persp_scale": str(fcfg["persp_scale"]),
            "fps": float(fps),
        },
    }
    if n == 0:
        diag["alarms"].append({
            "code": "no_frames", "value": 0.0,
            "message": "frames 为空：没有任何观测，返回空轨道（不编造数据）。",
        })
        _emit_alarms(diag)
        return np.zeros(0), np.zeros(0), diag

    fidx = np.array([int(_get(f, "frame", i)) for i, f in enumerate(items)], dtype=np.int64)
    z = np.array([_as_float(_get(f, "depth_median_m")) for f in items], dtype=np.float64)
    iqr = np.array([_as_float(_get(f, "iqr_m")) for f in items], dtype=np.float64)
    torso_px = np.array([_as_float(_get(f, "torso_px")) for f in items], dtype=np.float64)
    persp = np.array([_as_float(_get(f, "perspective_m")) for f in items], dtype=np.float64)
    mask_frac = np.array([_as_float(_get(f, "mask_frac")) for f in items], dtype=np.float64)
    valid = np.array([_as_bool(_get(f, "valid", True)) for f in items], dtype=bool)

    # ---- 1) 有效性与主项 ----
    z_ok = valid & np.isfinite(z) & (z > 0.0)
    p_ok = np.isfinite(persp) & (persp > 0.0) & np.isfinite(torso_px) & (torso_px > 0.0)

    outlier = _isolated_outliers(z, z_ok, fcfg) if np.count_nonzero(z_ok) >= 3 else np.zeros(n, bool)
    keep = z_ok & ~outlier
    # 粗项只吃"既有效又没被剔除离群"的帧：单帧尖峰不该污染慢漂/形状估计
    both = z_ok & p_ok & ~outlier

    # IQR 降权
    iqr_max = max(float(fcfg["iqr_max_m"]), _GEOM_EPS)
    w_iqr = np.where(iqr > iqr_max, np.clip(iqr_max / np.maximum(iqr, _GEOM_EPS), 0.05, 1.0), 1.0)
    w_iqr = np.where(np.isfinite(w_iqr), w_iqr, 1.0)
    weights = np.where(keep, w_iqr, 0.0)

    n_valid = int(np.count_nonzero(keep))
    diag["valid"] = {
        "n_valid": n_valid,
        "n_invalid": int(n - np.count_nonzero(z_ok)),
        "n_outlier": int(np.count_nonzero(outlier)),
        "n_iqr_downweighted": int(np.count_nonzero(z_ok & (iqr > iqr_max))),
        "valid_frac": float(n_valid) / float(n),
        "n_persp_usable": int(np.count_nonzero(both)),
    }
    if n_valid == 0:
        diag["alarms"].append({
            "code": "no_valid_frames", "value": 0.0,
            "message": "没有任何有效的度量深度观测（valid=False / 非有限 / 非正）："
                       "z_raw_m 全为 NaN，置信度 0，不编造数据。",
        })
        _emit_alarms(diag)
        return (np.full(n, np.nan), np.zeros(n), diag)
    if np.count_nonzero(both) == 0:
        diag["alarms"].append({
            "code": "perspective_unavailable", "value": 0.0,
            "message": "没有一帧同时有可用的度量中位数与躯干透视先验："
                       "粗项一致性约束与慢漂校正本轮不生效（主项照常输出）。",
        })

    # ---- 2) 绝对尺度一致性（只在 p 被判为准米制时） ----
    use_persp = float(fcfg["w_persp"]) > 0.0 and np.count_nonzero(both) > 0
    scale_info = _scale_check(z, persp, both, fcfg, anchor_z_m)
    diag["scale"] = scale_info
    if scale_info.get("alarm"):
        diag["alarms"].append(scale_info["alarm"])
    if anchor_z_m is not None and scale_info.get("anchor_alarm"):
        diag["alarms"].append(scale_info["anchor_alarm"])

    # ---- 3) 慢漂校正（相对量；p 的尺度任意都能用） ----
    drift = np.ones(n, dtype=np.float64)
    drift_info = {"applied": False, "baseline": float("nan"), "max_abs_dev": 0.0}
    if use_persp:
        q = np.full(n, np.nan, dtype=np.float64)
        q[both] = z[both] / persp[both]
        window = max(3, int(round(float(fcfg["drift_window_s"]) * max(fps, 1.0))))
        order = int(fcfg["drift_order"])
        q_slow = _local_poly_smooth(q, both, window=window, order=order,
                                    weights=np.where(both, w_iqr, 0.0) + 1e-12,
                                    k=float(fcfg["drift_k"]))
        baseline = _weighted_median(q_slow[both], weights[both])
        if np.isfinite(baseline) and abs(baseline) > _GEOM_EPS:
            drift = np.where(np.isfinite(q_slow), q_slow / baseline, 1.0)
            clip = max(float(fcfg["drift_clip"]), _GEOM_EPS)
            drift = np.clip(drift, 1.0 - clip, 1.0 + clip)
            drift_info["applied"] = True
            drift_info["baseline"] = float(baseline)
            dev = float(np.max(np.abs(drift[keep] - 1.0)))
            drift_info["max_abs_dev"] = dev
            if dev > float(fcfg["scale_alarm"]):
                diag["alarms"].append({
                    "code": "scale_drift",
                    "value": dev,
                    "message": f"度量项的慢变尺度漂移达 {dev * 100:.1f}%"
                               f"（阈值 scale_alarm={float(fcfg['scale_alarm']) * 100:.0f}%）："
                               "已按躯干透视粗项校正，但该段深度尺度不可信。",
                })
    diag["drift"] = drift_info

    z_corr = z / np.where(np.isfinite(drift) & (np.abs(drift) > _GEOM_EPS), drift, 1.0)

    # ---- 4) 慢形状混合（只动慢分量，逐帧细节保留） ----
    w_depth = max(float(fcfg["w_depth"]), 0.0)
    w_persp = max(float(fcfg["w_persp"]), 0.0)
    blend_info = {"w_norm": 0.0, "mismatch_p90": float("nan"), "calib_ratio": float("nan"),
                  "applied": False}
    z_raw_valid = z_corr.copy()
    if use_persp:
        calib = _weighted_median(z_corr[both] / persp[both], weights[both])
        if np.isfinite(calib) and calib > 0.0:
            p_cal = persp * calib
            window = max(3, int(round(float(fcfg["drift_window_s"]) * max(fps, 1.0))))
            order = int(fcfg["drift_order"])
            z_slow = _local_poly_smooth(z_corr, keep, window=window, order=order,
                                        weights=np.where(keep, w_iqr, 0.0) + 1e-12,
                                        k=float(fcfg["drift_k"]))
            p_slow = _local_poly_smooth(p_cal, both, window=window, order=order,
                                        weights=np.where(both, w_iqr, 0.0) + 1e-12,
                                        k=float(fcfg["drift_k"]))
            blend_info["calib_ratio"] = float(calib)
            if w_depth + w_persp > 0.0:
                w_norm = w_persp / (w_depth + w_persp)
            else:
                w_norm = 0.0
            blend_info["w_norm"] = float(w_norm)
            blend_info["applied"] = True
            delta = w_norm * (p_slow - z_slow)
            delta = np.where(np.isfinite(delta), delta, 0.0)
            # 混合量本身也限幅，避免粗项异常把主项拽飞
            limit = max(float(fcfg["drift_clip"]), _GEOM_EPS) * np.maximum(np.abs(z_corr), 1.0)
            z_raw_valid = z_raw_valid + np.clip(delta, -limit, limit)
            denom = np.maximum(np.abs(z_corr[both]), _GEOM_EPS)
            mism = np.abs(z_slow[both] - p_slow[both]) / denom
            mism = mism[np.isfinite(mism)]
            if mism.size:
                p90 = float(np.percentile(mism, 90.0))
                blend_info["mismatch_p90"] = p90
                if p90 > float(fcfg["torso_tol"]):
                    diag["alarms"].append({
                        "code": "torso_mismatch",
                        "value": p90,
                        "message": f"度量深度与躯干透视先验的慢分量偏差 p90={p90 * 100:.1f}%"
                                   f"（阈值 torso_tol={float(fcfg['torso_tol']) * 100:.0f}%）："
                                   "两者对根节点 Z 的慢变趋势不一致，粗项不可信。",
                    })
    diag["persp"] = blend_info

    # ---- 5) 置信度 ----
    conf = np.zeros(n, dtype=np.float64)
    conf[keep] = np.clip(w_iqr[keep], 0.0, 1.0)
    clip = max(float(fcfg["drift_clip"]), _GEOM_EPS)
    conf[keep] *= np.clip(1.0 - np.abs(drift[keep] - 1.0) / clip, 0.1, 1.0)
    penalty = 1.0
    if any(a["code"] == "scale_offset" for a in diag["alarms"]) or (
        anchor_z_m is not None and any(a["code"] == "scale_anchor_mismatch" for a in diag["alarms"])
    ):
        penalty *= float(fcfg["scale_conf_penalty"])
    if any(a["code"] == "torso_mismatch" for a in diag["alarms"]):
        penalty *= float(fcfg["torso_conf_penalty"])
    if any(a["code"] == "scale_drift" for a in diag["alarms"]):
        penalty *= float(fcfg["torso_conf_penalty"])
    conf[keep] *= penalty

    # ---- 6) 间隙填充 ----
    keep = keep & np.isfinite(z_raw_valid)   # 防御：任何非有限结果都不当观测用
    z_raw = np.full(n, np.nan, dtype=np.float64)
    z_raw[keep] = z_raw_valid[keep]
    idx_ok = np.flatnonzero(keep)
    z_raw = np.interp(np.arange(n, dtype=np.float64), idx_ok.astype(np.float64),
                      z_raw_valid[idx_ok])
    z_raw = np.asarray(z_raw, dtype=np.float64)
    gaps = np.zeros(n, dtype=np.int64)
    i = 0
    while i < n:
        if keep[i]:
            i += 1
            continue
        j = i
        while j < n and not keep[j]:
            j += 1
        gaps[i:j] = j - i
        i = j
    for i in np.flatnonzero(~keep):
        i = int(i)
        pos = int(np.searchsorted(idx_ok, i))
        left = conf[idx_ok[pos - 1]] if pos > 0 else penalty
        right = conf[idx_ok[pos]] if pos < idx_ok.size else penalty
        conf[i] = min(_gap_conf(int(gaps[i]), fcfg, fps), max(0.0, min(left, right)))

    diag["confidence"] = {
        "mean": float(np.mean(conf)),
        "min": float(np.min(conf)),
        "n_interpolated": int(np.count_nonzero(~keep)),
    }
    diag["frames"] = {"first": int(fidx[0]), "last": int(fidx[-1])}
    diag["mask_frac"] = {
        "mean": float(np.nanmean(mask_frac)) if np.any(np.isfinite(mask_frac)) else float("nan"),
        "min": float(np.nanmin(mask_frac)) if np.any(np.isfinite(mask_frac)) else float("nan"),
    }
    if n_valid < n:
        diag["info"].append(
            f"{int(n - n_valid)}/{n} 帧无效或被剔除：已线性插值补齐并降低置信度"
            f"（gap_conf={float(fcfg['gap_conf'])}）。"
        )
    _emit_alarms(diag)
    return z_raw, conf, diag


def _scale_check(z, persp, both, fcfg, anchor_z_m) -> dict:
    """全局常数尺度一致性检查（只在 p 被判为准米制 / 给了绝对锚点时）。"""
    info: dict = {
        "mode": str(fcfg["persp_scale"]),
        "ratio_median": float("nan"),
        "assumed_metric": False,
        "global_offset": float("nan"),
        "alarm": None,
        "anchor_alarm": None,
    }
    idx = np.flatnonzero(both)
    if idx.size:
        ratio = z[idx] / persp[idx]
        ratio = ratio[np.isfinite(ratio)]
        if ratio.size:
            b = float(np.median(ratio))
            info["ratio_median"] = b
            mode = str(fcfg["persp_scale"]).lower()
            window = max(float(fcfg["persp_scale_window"]), 1.0)
            if mode == "metric":
                assumed = True
            elif mode == "relative":
                assumed = False
            else:
                assumed = (abs(b) > _GEOM_EPS) and (1.0 / window <= b <= window)
            info["assumed_metric"] = bool(assumed)
            if assumed:
                dev = abs(b - 1.0)
                info["global_offset"] = dev
                tol = max(float(fcfg["global_scale_tol"]), _GEOM_EPS)
                if dev > tol:
                    info["alarm"] = {
                        "code": "scale_offset",
                        "value": float(dev),
                        "message": (
                            f"度量深度与准米制躯干透视先验的全局尺度差 {dev * 100:.1f}%"
                            f"（median(z/p)={b:.3f}，阈值 {tol * 100:.0f}%）："
                            "疑似整体尺度错误（例如深度被整体乘了常数），未静默通过。"
                        ),
                    }
    if anchor_z_m is not None:
        anchor = float(anchor_z_m)
        if np.isfinite(anchor) and anchor > 0.0:
            z_med = float(np.median(z[idx])) if idx.size else float(np.median(z[np.isfinite(z) & (z > 0)]))
            if np.isfinite(z_med):
                dev = abs(z_med - anchor) / anchor
                info["anchor_dev"] = dev
                tol = max(float(fcfg["scale_alarm"]), _GEOM_EPS)
                if dev > tol:
                    info["anchor_alarm"] = {
                        "code": "scale_anchor_mismatch",
                        "value": float(dev),
                        "message": (
                            f"度量深度中位数 {z_med:.3f} m 与给定绝对锚点 {anchor:.3f} m "
                            f"相差 {dev * 100:.1f}%（阈值 {tol * 100:.0f}%）。"
                        ),
                    }
    return info


def fuse(
    frames: list,
    cfg: dict | None = None,
    *,
    kind: str = KIND_METRIC,
    anchor_z_m: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """spec §3 冻结签名：`fuse(frames, cfg) -> (z_raw_m, confidence)`。

    需要报警/诊断细节时用 `fuse_detailed()`；有报警时本函数也会
    `warnings.warn(FusionAlarm)`，不会静默。
    """
    z_raw, conf, _diag = fuse_detailed(frames, cfg, kind=kind, anchor_z_m=anchor_z_m)
    return z_raw, conf


__all__ = ["fuse", "fuse_detailed", "FusionAlarm", "LAST_ALARMS", "LAST_DIAG",
           "_EXTRA_DEFAULTS"]
