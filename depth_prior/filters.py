"""One-Euro 时序滤波（w3，写作用域：本文件；spec §1(E) / §5.6）。

目标行为
--------
- **慢速移动 → 强平滑**：站在原地时的逐帧抖动被压掉（残余 RMS 降 > 60%）。
- **快速移动 → 低延迟**：落地、出拳、跑跳这类事件不被抹平；阶跃响应延迟
  < 3 帧（fps=30），且比**同截止频率的普通一阶低通**更快。
- **无效帧安全**：NaN / 显式无效帧不参与滤波更新，NaN 永不进入滤波器内部状态。

与论文版 One-Euro 的唯一差别（必须写清楚，否则是"改了别人的算法不吭声"）
------------------------------------------------------------------------
论文（Casiez et al., CHI 2012）的自适应项是::

    cutoff = min_cutoff + beta * |edx|          # edx 单位 = 信号单位/秒

对鼠标像素坐标（速度数百 px/s）成立；对**米制根节点 Z** 不成立：人走路 1~2 m/s、
静止漂移 0.005~0.02 m/s，beta=0.02 时自适应项只有 0.0001~0.04 Hz，
`min_cutoff=0.8` 的一阶环节 50% 上升时间 = 0.693·tau = 4.1 帧 ——
**与 spec §5.6"阶跃响应延迟 < 3 帧 / 不得比普通低通更慢"数学上矛盾**。

本实现因此把速度项写成"相对本段信号自身噪声基线的速度裕度"：:

    sn     = |edx| / speed_baseline           # 无量纲裕度
    cutoff = min_cutoff + beta * min(sn, speed_cap) ** speed_power

    speed_baseline = max(sigma_edx_hat, speed_floor)       # 噪声基线解析推出，离线算

其中速度基线**不是手调常数**，而是从信号自身的"粗糙度"（二阶差分 = 高频含量）
解析推出的导数噪声水平（见 `_noise_baseline` 的推导）：抖动（高频、粗糙）→ 基线大、
sn ≈ 1 → 强平滑；平滑运动（二阶差分≈0）→ 基线落到绝对下限 → sn ≫ 1 → 低延迟。

- 抖动（任何幅度）：sn ≈ 1 → cutoff ≈ min_cutoff + beta → 强平滑，
  且**平滑强度不随抖动幅度变化**（固定 speed_ref 做不到这点，见自验数字）。
- 阶跃/大幅运动：sn ≫ 1，幂次响应曲线把 cutoff 迅速抬到几十 Hz → alpha → 1，
  延迟 0~1 帧（阶跃幅度 ≳ 6σ_x 时；小于该可辨识裕度的"阶跃"与抖动原理上无法区分）。
- 稳态快速运动（斜坡 / 大幅平滑摆动）：二阶差分 ≈ 0 → 基线 = 下限 → 低延迟跟随，
  远好于同截止普通低通（见自验里的斜坡误差与延迟对比）。
- 单帧尖峰：速度估计的 3 点居中中值（speed_smooth=3）让孤立尖峰不抬高 cutoff
  （尖峰的前后帧速度正常），因此离群点仍被平滑掉。
- `beta=0` 时本实现与截止 = `min_cutoff` 的固定一阶低通**逐点完全相同**（可回归验证）。

`first_order_lpf()` 提供"同截止普通低通"对照组，`step_response_lag_frames()`
是延迟测量口径（阶跃后响应首次到达 level·(y1-y0) 的帧数）。
"""

from __future__ import annotations

import math

import numpy as np

try:  # 包内导入（`from depth_prior import filters`）
    from . import types as _types
except ImportError:  # 直接按文件路径/顶层模块导入时的回退
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from depth_prior import types as _types

FilterDiag = _types.FilterDiag

# 速度归一化默认参数（关键字可覆盖；不是 spec §4 的冻结键，故留在这里）
DEFAULT_SPEED_FLOOR = 0.05   # m/s：Z 轴上"慢速"的绝对下限（5 cm/s）
DEFAULT_SPEED_CAP = 20.0     # 裕度上限（再快也不改 alpha）
DEFAULT_SPEED_POWER = 5.0    # 裕度 → 截止频率的响应曲线指数
DEFAULT_SPEED_SMOOTH = 3     # 速度估计的居中中值窗（奇数；1 = 不平滑）

_FILL_NAN = "nan"
_FILL_HOLD = "hold"


# ---------------------------------------------------------------------------
# 内部工具


def _check_finite_positive(name: str, value: float) -> float:
    v = float(value)
    if not np.isfinite(v) or v <= 0.0:
        raise ValueError(f"{name} 必须是有限正数，收到 {value!r}")
    return v


def _check_non_negative(name: str, value: float) -> float:
    v = float(value)
    if not np.isfinite(v) or v < 0.0:
        raise ValueError(f"{name} 必须是非负有限数，收到 {value!r}")
    return v


def _tau(cutoff_hz: float) -> float:
    return 1.0 / (2.0 * math.pi * cutoff_hz)


def _alpha(tau: float, dt: float) -> float:
    """一阶环节的混合系数：dt = te 时退化为论文里的 1/(1+tau/te)。"""
    return 1.0 / (1.0 + tau / dt)


def _noise_baseline(
    x: np.ndarray, valid: np.ndarray, *, fps: float, d_cutoff: float, speed_floor: float
) -> float:
    """导数估计 `edx` 的噪声基线（解析推导，无手调拟合常数）。

    白噪声 σ_x 下逐项推：

    - 二阶差分 ``d2_i = x_{i+1} - 2x_i + x_{i-1}``：``std(d2) = sqrt(6)·σ_x``
      → ``σ̂_x = 1.4826·MAD(d2) / sqrt(6)``（MAD 对孤立尖峰/阶跃稳健，
      这正是"用粗糙度而不是速度"的关键：平滑运动会自动落到 0）。
    - 一阶差分 ``dx_i = Δx_i·fps``：``std(dx) = sqrt(2)·σ_x·fps``。
    - `edx` 是 dx 的一阶低通（系数 ``a = alpha_d``）：白输入稳态增益
      ``g = sqrt(a/(2-a))`` → ``σ̂_edx = sqrt(2)·σ̂_x·fps·g``。
    - 基线 ``= max(σ̂_edx, speed_floor)``；抖动时 ``|edx|`` 的中位数 ≈ σ̂_edx，
      因此 sn ≈ 1（保持慢速截止）；平滑运动时 σ̂_edx → speed_floor，sn ≫ 1。

    二阶差分只用**连续**有效帧（跨无效帧的伪尖峰不算）。
    """
    idx = np.flatnonzero(valid)
    if idx.size >= 3:
        # 只保留 (i-1, i, i+1) 三帧都连续的中间帧
        a, b, c = idx[:-2], idx[1:-1], idx[2:]
        mid = b[(b - a == 1) & (c - b == 1)]
        if mid.size:
            d2 = x[mid + 1] - 2.0 * x[mid] + x[mid - 1]
            d2 = d2[np.isfinite(d2)]
            if d2.size:
                mad = float(np.median(np.abs(d2 - np.median(d2))))
                sigma_x = 1.4826 * mad / math.sqrt(6.0)
                a_d = _alpha(_tau(d_cutoff), 1.0 / fps)
                gain = math.sqrt(a_d / (2.0 - a_d))
                sigma_edx = math.sqrt(2.0) * sigma_x * fps * gain
                if math.isfinite(sigma_edx):
                    return max(float(sigma_edx), float(speed_floor))
    return float(speed_floor)


def _run(
    x: np.ndarray,
    valid: np.ndarray,
    *,
    fps: float,
    min_cutoff: float,
    beta: float,
    d_cutoff: float,
    speed_floor: float,
    speed_cap: float,
    speed_power: float,
    speed_smooth: int,
    fill: str,
) -> tuple[np.ndarray, np.ndarray]:
    """One-Euro 主体。返回 (y, edx)。

    两遍：第一遍只算导数状态 edx（它只依赖 d_cutoff，与主 alpha 路径无关），
    第二遍用 edx 的裕度驱动截止频率。
    """
    n = int(x.size)
    y = np.full(n, np.nan, dtype=np.float64)
    edx_arr = np.full(n, np.nan, dtype=np.float64)
    if n == 0:
        return y, edx_arr

    te = 1.0 / fps
    dt_floor = te * 1e-3

    # --- 第一遍：导数低通（invalid 帧完全跳过，状态不变） ---
    edx = 0.0
    prev: float | None = None
    t_prev = 0.0
    for i in range(n):
        if not valid[i]:
            continue
        xi = float(x[i])
        ti = i * te
        if prev is None:
            prev, t_prev, edx = xi, ti, 0.0
            edx_arr[i] = 0.0
            continue
        dt = max(ti - t_prev, dt_floor)
        dx = (xi - prev) / dt
        a_d = _alpha(_tau(d_cutoff), dt)
        edx = a_d * dx + (1.0 - a_d) * edx
        edx_arr[i] = edx
        prev, t_prev = xi, ti

    # 速度估计再做一次 3 点居中中值（只在中值窗内取有效帧）：
    # 单帧速度尖峰不该把 alpha 直接抬到 1（真正的加速/阶跃是连续多帧的，不受影响）。
    if int(speed_smooth) > 1:
        idx = np.flatnonzero(valid)
        if idx.size:
            half = int(speed_smooth) // 2
            sm = np.full(n, np.nan, dtype=np.float64)
            for i in idx:
                lo = int(np.searchsorted(idx, i - half, side="left"))
                hi = int(np.searchsorted(idx, i + half, side="right"))
                sm[i] = float(np.median(edx_arr[idx[lo:hi]]))
            edx_arr = sm

    baseline = _noise_baseline(
        x, valid, fps=fps, d_cutoff=d_cutoff, speed_floor=speed_floor
    )

    # --- 第二遍：主滤波 ---
    y_prev: float | None = None
    prev = None
    t_prev = 0.0
    for i in range(n):
        if not valid[i]:
            if fill == _FILL_HOLD and y_prev is not None:
                y[i] = y_prev
            continue
        xi = float(x[i])
        ti = i * te
        if y_prev is None:
            y_prev, prev, t_prev = xi, xi, ti
            y[i] = xi
            continue
        dt = max(ti - t_prev, dt_floor)
        sn = min(abs(float(edx_arr[i])) / baseline, speed_cap)
        cutoff = min_cutoff + beta * (sn ** speed_power)
        a = _alpha(_tau(cutoff), dt)
        yi = a * xi + (1.0 - a) * y_prev
        y[i] = yi
        y_prev, prev, t_prev = yi, xi, ti

    return y, edx_arr


# ---------------------------------------------------------------------------
# 公开 API


def one_euro(
    x: np.ndarray,
    *,
    fps: float,
    min_cutoff: float,
    beta: float,
    d_cutoff: float,
    speed_floor: float = DEFAULT_SPEED_FLOOR,
    speed_cap: float = DEFAULT_SPEED_CAP,
    speed_power: float = DEFAULT_SPEED_POWER,
    speed_smooth: int = DEFAULT_SPEED_SMOOTH,
    mask: np.ndarray | None = None,
    fill: str = _FILL_NAN,
) -> tuple[np.ndarray, FilterDiag]:
    """One-Euro 滤波（spec §3 的冻结签名 + 若干可选关键字扩展）。

    Parameters
    ----------
    x : (T,) 序列。非有限值视为无效帧。
    fps : 采样率（Hz），必须为正。
    min_cutoff, beta, d_cutoff : One-Euro 三个参数（含义见模块 docstring 与 spec §4）。
    speed_floor, speed_cap, speed_power, speed_smooth : 速度归一化参数，默认见模块常量。
    mask : 可选 (T,) bool，显式标出有效帧（与有限性求交）。
    fill : 无效帧的输出策略——`"nan"`（默认，诚实：没有观测就不编造）或
        `"hold"`（保持上一帧滤波值，供需要连续轨道的消费方使用）。
        两种策略下**无效帧都不更新滤波器内部状态**。

    Returns
    -------
    (y, diag) : y (T,) float64（无效帧按 `fill` 处理）；diag 记录实际使用的
        三个参数、阶跃响应延迟（帧）与滤波前后残差 RMS。
    """
    xs = np.asarray(x, dtype=np.float64)
    if xs.ndim != 1:
        raise ValueError(f"x 必须是一维序列，收到 shape={xs.shape}")
    fps = _check_finite_positive("fps", fps)
    min_cutoff = _check_finite_positive("min_cutoff", min_cutoff)
    d_cutoff = _check_finite_positive("d_cutoff", d_cutoff)
    beta = _check_non_negative("beta", beta)
    speed_floor = _check_finite_positive("speed_floor", speed_floor)
    speed_cap = _check_finite_positive("speed_cap", speed_cap)
    speed_power = _check_finite_positive("speed_power", speed_power)
    if int(speed_smooth) < 1:
        raise ValueError(f"speed_smooth 必须 >= 1，收到 {speed_smooth!r}")
    speed_smooth = int(speed_smooth)
    if fill not in (_FILL_NAN, _FILL_HOLD):
        raise ValueError(f"fill 只能是 {_FILL_NAN!r}/{_FILL_HOLD!r}，收到 {fill!r}")

    if mask is None:
        valid = np.isfinite(xs)
    else:
        m = np.asarray(mask, dtype=bool)
        if m.shape != xs.shape:
            raise ValueError(f"mask {m.shape} 与 x {xs.shape} 不一致")
        valid = m & np.isfinite(xs)

    y, _ = _run(
        xs, valid,
        fps=fps, min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff,
        speed_floor=speed_floor, speed_cap=speed_cap, speed_power=speed_power,
        speed_smooth=speed_smooth, fill=fill,
    )

    lag = _canonical_step_lag(
        fps=fps, min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff,
        speed_floor=speed_floor, speed_cap=speed_cap, speed_power=speed_power,
        speed_smooth=speed_smooth, level=0.5,
    )
    if np.any(valid):
        resid = float(np.sqrt(np.mean((xs[valid] - y[valid]) ** 2)))
    else:
        resid = float("nan")

    diag = FilterDiag(
        name="one_euro",
        min_cutoff=float(min_cutoff),
        beta=float(beta),
        d_cutoff=float(d_cutoff),
        lag_frames_p50=float(lag),
        residual_rms_m=resid,
    )
    return y, diag


def first_order_lpf(
    x: np.ndarray,
    *,
    fps: float,
    cutoff: float,
    mask: np.ndarray | None = None,
    fill: str = _FILL_NAN,
) -> np.ndarray:
    """对照组：截止频率 = cutoff 的普通一阶低通（alpha 恒定，无速度自适应）。

    用于证明 One-Euro 在**同一截止频率**下比普通低通快（spec §5.6）。
    无效帧处理与 `one_euro` 一致（不更新状态）。
    """
    xs = np.asarray(x, dtype=np.float64)
    if xs.ndim != 1:
        raise ValueError(f"x 必须是一维序列，收到 shape={xs.shape}")
    fps = _check_finite_positive("fps", fps)
    cutoff = _check_finite_positive("cutoff", cutoff)
    if fill not in (_FILL_NAN, _FILL_HOLD):
        raise ValueError(f"fill 只能是 {_FILL_NAN!r}/{_FILL_HOLD!r}，收到 {fill!r}")
    if mask is None:
        valid = np.isfinite(xs)
    else:
        m = np.asarray(mask, dtype=bool)
        if m.shape != xs.shape:
            raise ValueError(f"mask {m.shape} 与 x {xs.shape} 不一致")
        valid = m & np.isfinite(xs)

    te = 1.0 / fps
    a = _alpha(_tau(cutoff), te)
    y = np.full(xs.size, np.nan, dtype=np.float64)
    y_prev: float | None = None
    for i in range(xs.size):
        if not valid[i]:
            if fill == _FILL_HOLD and y_prev is not None:
                y[i] = y_prev
            continue
        xi = float(xs[i])
        if y_prev is None:
            y_prev = xi
            y[i] = xi
            continue
        y_prev = a * xi + (1.0 - a) * y_prev
        y[i] = y_prev
    return y


def step_response_lag_frames(
    y: np.ndarray, step_index: int, *, level: float = 0.5, y0: float = 0.0, y1: float = 1.0
) -> float:
    """阶跃响应延迟（帧）：响应首次到达 y0 + level*(y1-y0) 距阶跃帧的帧数。

    口径与 `FilterDiag.lag_frames_p50` 一致（level=0.5）。响应永远到不了该
    电平则返回 NaN（不假装通过）。
    """
    ys = np.asarray(y, dtype=np.float64)
    if ys.ndim != 1:
        raise ValueError(f"y 必须是一维序列，收到 shape={ys.shape}")
    k = int(step_index)
    if k < 0 or k >= ys.size:
        raise ValueError(f"step_index={step_index} 越界（y 长度 {ys.size}）")
    target = float(y0) + float(level) * (float(y1) - float(y0))
    for i in range(k, ys.size):
        v = ys[i]
        if np.isfinite(v) and v >= target:
            return float(i - k)
    return float("nan")


def _canonical_step_lag(
    *,
    fps: float,
    min_cutoff: float,
    beta: float,
    d_cutoff: float,
    speed_floor: float,
    speed_cap: float,
    speed_power: float,
    speed_smooth: int,
    level: float = 0.5,
    pre_s: float = 1.0,
    post_s: float = 4.0,
) -> float:
    """用同一组参数跑一条 0→1 的标准阶跃，量出 50% 上升延迟（帧）。"""
    pre = max(2, int(round(pre_s * fps)))
    post = max(4, int(round(post_s * fps)))
    x = np.concatenate([np.zeros(pre), np.ones(post)])
    y, _ = _run(
        x, np.ones(x.size, dtype=bool),
        fps=fps, min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff,
        speed_floor=speed_floor, speed_cap=speed_cap, speed_power=speed_power,
        speed_smooth=speed_smooth, fill=_FILL_NAN,
    )
    return step_response_lag_frames(y, pre, level=level, y0=0.0, y1=1.0)


__all__ = [
    "one_euro",
    "first_order_lpf",
    "step_response_lag_frames",
    "DEFAULT_SPEED_FLOOR",
    "DEFAULT_SPEED_CAP",
    "DEFAULT_SPEED_POWER",
    "DEFAULT_SPEED_SMOOTH",
]
