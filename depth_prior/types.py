"""契约层（Lead 冻结）：深度先验框架的所有共享类型与默认参数。

设计见 `spec.md`。**不要修改本文件的字段名**——backend / masks / priors /
fusion / filters / tests 全部按这里的签名对接。需要新字段请在
`agent_reports/` 里提，由 Lead 统一加。

铁律：`DepthMap.kind == "metric"` 才允许进 `fusion.fuse`；
`kind == "relative"` 只能走 `priors.affine_align_to_metric`，否则必须 raise。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# 权重默认位置（仓库根，与工作目录同级）

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS = REPO_ROOT / "depth_anything_v2_metric_hypersim_vits.pth"

KIND_METRIC = "metric"
KIND_RELATIVE = "relative"


class BackendUnavailable(RuntimeError):
    """后端不可用（缺 torch / 缺权重 / 缺 CUDA）。调用方应回退 SyntheticBackend。"""


class MetricRequired(RuntimeError):
    """拿到的是相对深度，但这条路径只接受度量深度。"""


# ---------------------------------------------------------------------------
# 默认参数：一张表，全部可被 cfg 覆盖（spec §4）。不许把阈值硬编码进函数。


DEFAULT_CFG: dict[str, Any] = {
    "backend": {
        "weights": str(DEFAULT_WEIGHTS),
        "encoder": "vits",
        "max_depth": 20.0,          # Hypersim-metric 头
        "input_size": 518,
        "device": "auto",           # auto | cpu | cuda
        # 官方 Depth-Anything-V2 metric_depth 的仓库路径（含 depth_anything_v2/ 的那一层）。
        # 2026-10-10 云端实测：官方实现 strict 加载通过、真实帧跑出 2.3–10.4 m 合理深度；
        # 自研 model/dpt.py 前向数值不对（输出全 0），所以**默认应该填这里**。
        # 留空 = 用自研实现（只在没有官方代码时兜底）。
        "official_path": "",
    },
    "mask": {
        "torso_frac": 0.22,
        "pelvis_frac": 0.12,
        "min_px": 400,
        # w2 的区域几何（2026-10-10 由 Lead 收编进默认表，之前散在 masks.py 常量里）
        "bbox_top_frac": 0.18,          # 无关键点时：躯干带从人体框顶部下移这么多
        "torso_width_ratio": 0.40,      # 躯干带宽 / 人体框宽
        "pelvis_width_ratio": 0.80,     # 骨盆带宽 / 人体框宽
        "fallback_torso_width_frac": 0.45,   # 无关键点退化路径的躯干带高占比
        "fallback_pelvis_width_frac": 0.36,  # 无关键点退化路径的骨盆带宽占比
        "min_torso_px": 0.0,            # 躯干带最少像素（0 = 不限）
    },
    "fusion": {
        "iqr_max_m": 0.35,
        "torso_tol": 0.25,
        "w_depth": 1.0,
        "w_persp": 0.15,
        "scale_alarm": 0.2,         # 整体尺度漂移报警阈值（相对）
    },
    "filter": {
        "min_cutoff": 0.8,
        "beta": 0.02,
        "d_cutoff": 1.0,
        "fps": 30.0,
    },
}


def merge_cfg(overrides: dict | None) -> dict:
    """深合并用户覆盖项到 DEFAULT_CFG（浅拷贝每层，不改默认表）。"""
    import copy

    cfg = copy.deepcopy(DEFAULT_CFG)
    for section, values in (overrides or {}).items():
        if isinstance(values, dict) and isinstance(cfg.get(section), dict):
            cfg[section].update(values)
        else:
            cfg[section] = values
    return cfg


# ---------------------------------------------------------------------------
# 数据结构（spec §3）


@dataclass(frozen=True)
class Intrinsics:
    """针孔相机内参，单位像素。"""

    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    def as_matrix(self) -> np.ndarray:
        return np.array([[self.fx, 0.0, self.cx],
                         [0.0, self.fy, self.cy],
                         [0.0, 0.0, 1.0]], dtype=np.float64)


@dataclass
class DepthMap:
    """一帧深度图。`kind` 是安全闸门，不是注释。"""

    depth: np.ndarray            # (H, W) float32
    kind: str = KIND_METRIC      # "metric" | "relative"
    unit: str = "m"              # "m" | "normalized"
    backend: str = "unknown"

    def __post_init__(self) -> None:
        self.depth = np.asarray(self.depth, dtype=np.float32)
        if self.depth.ndim != 2:
            raise ValueError(f"depth 必须是 (H, W)，收到 {self.depth.shape}")
        if self.kind not in (KIND_METRIC, KIND_RELATIVE):
            raise ValueError(f"kind 只能是 {KIND_METRIC!r}/{KIND_RELATIVE!r}，收到 {self.kind!r}")

    @property
    def is_metric(self) -> bool:
        return self.kind == KIND_METRIC

    def at_mask(self, mask: np.ndarray) -> np.ndarray:
        """取掩膜内、有限且为正的深度样本（一维）。"""
        m = np.asarray(mask, dtype=bool)
        if m.shape != self.depth.shape:
            raise ValueError(f"mask {m.shape} 与 depth {self.depth.shape} 不一致")
        vals = self.depth[m]
        return vals[np.isfinite(vals) & (vals > 0.0)]


@dataclass
class RegionStat:
    """一个人体区域（躯干 / 骨盆）的度量深度统计。"""

    name: str
    frac: float
    px: int
    depth_median_m: float
    depth_p10_m: float
    depth_p90_m: float

    @property
    def iqr_m(self) -> float:
        return float(self.depth_p90_m - self.depth_p10_m)


@dataclass
class FramePrior:
    """逐帧先验：度量中位数 + 躯干像素长（粗项）。"""

    frame: int
    depth_median_m: float
    iqr_m: float
    torso_px: float
    perspective_m: float
    mask_frac: float
    valid: bool
    reason: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class FilterDiag:
    name: str
    min_cutoff: float
    beta: float
    d_cutoff: float
    lag_frames_p50: float = float("nan")
    residual_rms_m: float = float("nan")


@dataclass
class RootZTrack:
    """产出物：逐帧根节点 Z 轨道（相机系，米）。"""

    frames: np.ndarray
    z_raw_m: np.ndarray
    z_m: np.ndarray
    confidence: np.ndarray
    diag: dict = field(default_factory=dict)

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            p,
            frames=np.asarray(self.frames, dtype=np.int64),
            z_raw_m=np.asarray(self.z_raw_m, dtype=np.float64),
            z_m=np.asarray(self.z_m, dtype=np.float64),
            confidence=np.asarray(self.confidence, dtype=np.float64),
            meta=np.array([repr(self.diag)], dtype=object),
        )
        return p

    @classmethod
    def load(cls, path: str | Path) -> "RootZTrack":
        with np.load(Path(path), allow_pickle=True) as d:
            meta = d["meta"]
            diag = eval(str(meta[0])) if meta.size else {}   # noqa: S307 - 自家写出的 repr
            return cls(frames=d["frames"], z_raw_m=d["z_raw_m"],
                       z_m=d["z_m"], confidence=d["confidence"], diag=diag)
