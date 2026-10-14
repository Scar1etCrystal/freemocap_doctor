"""DA V2 Metric 后端的最小网络定义（w1 写作用域 `depth_prior/model/`）。

本包在**没有 torch** 的环境下也能被导入：
    >>> from depth_prior.model import expected_state_dict_spec
    >>> len(expected_state_dict_spec())          # 官方 metric-vits checkpoint 的键数
    239

只有真正构造 `nn.Module` 时才需要 torch，缺依赖抛 `types.BackendUnavailable`。
"""

from __future__ import annotations

from .dpt import (  # noqa: F401  (re-export)
    DEFAULT_FEATURES,
    DEFAULT_IMG_SIZE,
    DEFAULT_OUT_CHANNELS,
    ENCODER_CFG,
    create_metric_model,
    expected_state_dict_spec,
    get_class,
    torch_available,
    validate_state_dict_spec,
)

__all__ = [
    "DEFAULT_FEATURES",
    "DEFAULT_IMG_SIZE",
    "DEFAULT_OUT_CHANNELS",
    "ENCODER_CFG",
    "create_metric_model",
    "expected_state_dict_spec",
    "get_class",
    "torch_available",
    "validate_state_dict_spec",
]
