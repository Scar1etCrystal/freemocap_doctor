"""单目动捕的「度量深度先验」框架（无推理版）。

给 FastSAM3DBody 前端补一路**度量深度**先验，约束根节点 Z 的漂移，
产出 `RootZTrack`（逐帧 z 轨道 + 置信度 + 诊断）。

- 设计/验收标准：`spec.md`
- 冻结契约：`types.py`（**不要改字段名**，全框架按它对接）
- 铁律：只用**度量**深度（米）；相对深度只能走 `priors.affine_align_to_metric`，
  直接当米用会被 `fusion.fuse` 抛 `types.MetricRequired`。

各层分工：
    backend.py  → 深度模型适配（DA V2 Metric-Small）/ SyntheticBackend
    masks.py    → 复用 SAM/FSB 的人体 Mask，取躯干/骨盆深度中位数
    priors.py   → 2D 躯干像素长的透视粗先验 + 相对深度仿射对齐
    fusion.py   → 主项(度量中位数) + 粗项(躯干透视) 鲁棒融合
    filters.py  → One-Euro 时序滤波（慢速强平滑、快速低延迟）
    cli.py      → 命令行（--synthetic 可在无 GPU 环境下跑全链路）

无卡环境：`SyntheticBackend` 是验收通道，不加载权重、不做真推理。
"""

from __future__ import annotations

from .types import (  # noqa: F401
    DEFAULT_CFG,
    DEFAULT_WEIGHTS,
    KIND_METRIC,
    KIND_RELATIVE,
    BackendUnavailable,
    DepthMap,
    FilterDiag,
    FramePrior,
    Intrinsics,
    MetricRequired,
    RegionStat,
    RootZTrack,
    merge_cfg,
)

__all__ = [
    "DEFAULT_CFG", "DEFAULT_WEIGHTS", "KIND_METRIC", "KIND_RELATIVE",
    "BackendUnavailable", "MetricRequired",
    "DepthMap", "FilterDiag", "FramePrior", "Intrinsics", "RegionStat",
    "RootZTrack", "merge_cfg",
]

__version__ = "0.1.0"
