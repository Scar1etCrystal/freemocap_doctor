"""w4 验收测试的共享工具：惰性导入实现模块 + 合成场景构造。

只被 `depth_prior/tests/` 使用；不 import torch，不读 .blend / 权重文件。
"""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# 惰性导入：模块/属性还没实现 → SkipTest（带明确原因），不假装通过


def require_module(name: str):
    """导入 `depth_prior.<name>`；失败时 SkipTest 并说明缺什么。"""
    full = f"depth_prior.{name}"
    try:
        return importlib.import_module(full)
    except unittest.SkipTest:
        raise
    except BaseException as exc:  # noqa: BLE001 - 任何导入期异常都算"未就绪"
        raise unittest.SkipTest(
            f"[skip] 实现模块 {full} 尚不可用：{type(exc).__name__}: {exc}"
        ) from None


def require_attr(mod, attr: str, hint: str = ""):
    """实现模块在但函数/类还没有 → SkipTest。"""
    if not hasattr(mod, attr):
        raise unittest.SkipTest(f"[skip] {mod.__name__}.{attr} 还没实现{('（' + hint + '）') if hint else ''}")
    return getattr(mod, attr)


def require_callable(mod, attr: str, hint: str = ""):
    obj = require_attr(mod, attr, hint)
    if not callable(obj):
        raise AssertionError(f"{mod.__name__}.{attr} 存在但不可调用：{type(obj).__name__}")
    return obj


# ---------------------------------------------------------------------------
# cfg：一律用冻结契约的 merge_cfg，不硬编码阈值


def cfg(**sections) -> dict:
    from depth_prior.types import merge_cfg

    return merge_cfg(dict(sections))


# ---------------------------------------------------------------------------
# 合成真值场景（解析式，无外部数据）


def root_z_ramp(n: int, z0: float = 3.0, z1: float = 5.0) -> np.ndarray:
    """根节点 Z 从 z0 线性走到 z1（spec §5.3 的 3.0 → 5.0 m）。"""
    return np.linspace(float(z0), float(z1), int(n), dtype=np.float64)


def torso_px_from_z(z: np.ndarray, ref_z: float = 4.0, ref_px: float = 180.0) -> np.ndarray:
    """躯干像素长 ∝ 1/z（透视粗先验的物理关系，spec §1(C)）。"""
    return float(ref_px) * float(ref_z) / np.asarray(z, dtype=np.float64)


def frame_priors(
    z_true: np.ndarray,
    *,
    depth_median: np.ndarray | None = None,
    perspective: np.ndarray | None = None,
    iqr_m: float = 0.05,
    mask_frac: float = 0.18,
    valid: bool = True,
    reason: str = "",
    first_frame: int = 0,
):
    """造 `list[FramePrior]`：默认度量中位数与躯干透视都锚在真值上。

    `depth_median` / `perspective` 可单独注入（模拟慢漂、整体尺度漂）。
    """
    from depth_prior.types import FramePrior

    z_true = np.asarray(z_true, dtype=np.float64)
    n = z_true.size
    dm = z_true if depth_median is None else np.asarray(depth_median, dtype=np.float64)
    pm = z_true if perspective is None else np.asarray(perspective, dtype=np.float64)
    px = torso_px_from_z(z_true)
    out = []
    for i in range(n):
        out.append(
            FramePrior(
                frame=int(first_frame) + i,
                depth_median_m=float(dm[i]),
                iqr_m=float(iqr_m),
                torso_px=float(px[i]),
                perspective_m=float(pm[i]),
                mask_frac=float(mask_frac),
                valid=bool(valid),
                reason=str(reason),
            )
        )
    return out


def relative_depthmap(h: int = 240, w: int = 320, backend: str = "fake_relative"):
    """伪造一张 `kind="relative"` 的深度图（防退化回归测试用，spec §0 / §5.2）。"""
    from depth_prior.types import DepthMap, KIND_RELATIVE

    yy, xx = np.mgrid[0:h, 0:w]
    depth = 0.2 + 0.8 * (yy / max(h - 1, 1))  # 归一化"相对深度"，单位不是米
    return DepthMap(depth=depth.astype(np.float32), kind=KIND_RELATIVE,
                    unit="normalized", backend=backend)


def metric_depthmap(value: float = 4.0, h: int = 240, w: int = 320, backend: str = "synthetic"):
    """同样的形状，但是合法度量深度（阳性对照：闸门不能把所有输入都拒掉）。"""
    from depth_prior.types import DepthMap, KIND_METRIC

    return DepthMap(depth=np.full((h, w), float(value), dtype=np.float32),
                    kind=KIND_METRIC, unit="m", backend=backend)


def relative_ratio(values: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """z/truth，用于量"相对漂移"。"""
    return np.asarray(values, dtype=np.float64) / np.asarray(truth, dtype=np.float64)


def pct(x: float) -> str:
    return f"{100.0 * float(x):.2f}%"


def announce(tag: str, **nums) -> None:
    """把关键数字打到 stdout（成功时也可见，报告要数字不只要绿灯）。"""
    parts = []
    for k, v in nums.items():
        if isinstance(v, float):
            parts.append(f"{k}={v:.6g}")
        else:
            parts.append(f"{k}={v}")
    print(f"    · {tag}: " + "  ".join(parts))
