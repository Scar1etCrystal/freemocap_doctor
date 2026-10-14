"""Depth Anything V2 **Metric-Small** 的最小网络定义（w1 后端层）。

为什么自己写一份最简定义：
    官方 `depth_anything_v2` 包依赖 `torch.hub` 去下载 DINOv2 预训练权重（需要联网），
    而本框架的铁律是「不下载权重、无卡不推理」。这里只保留**结构**：DINOv2 ViT-S/14
    主干（对应 state_dict 前缀 `pretrained.`）+ DPT metric 头（前缀 `depth_head.`，
    `features=64`、`out_channels=[48,96,192,384]`），形状与仓库根
    `depth_anything_v2_metric_hypersim_vits.pth` 的 239 个键**逐一对齐**。

依赖策略：
    本模块**不在导入期** `import torch`。没有 torch 时仍然可以：
      * `import depth_prior.model`
      * 调用 `expected_state_dict_spec(...)` 拿到纯 Python 的 (键名 -> 形状) 表，
        与真实 `.pth` 做静态比对（见 `agent_reports/w1_verify_backend.py`）；
      * 调用 `validate_state_dict_spec()` 做集合/形状校验。
    只有构造真正的 `nn.Module` 时才需要 torch，缺依赖抛 `types.BackendUnavailable`
    （**不是** ImportError 裸奔）。

未验证声明：
    本机没有 torch/GPU，因此**网络前向的数值正确性未经验证**；已验证的是
    「键名 + 形状与官方 metric-checkpoint 完全一致」（静态比对，见 agent_reports）。
"""

from __future__ import annotations

import math
from collections import OrderedDict
from typing import Any, Iterable, Mapping, Sequence

try:  # 正常包内导入（python -m depth_prior.cli / import depth_prior.model.dpt）
    from ..types import BackendUnavailable
except ImportError:  # 以脚本方式直接运行时兜底（把仓库根加进 sys.path）
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from depth_prior.types import BackendUnavailable

# ---------------------------------------------------------------------------
# 架构常量：与官方 DepthAnythingV2 / DINOv2 对齐

DEFAULT_IMG_SIZE = 518          # 官方 518x518 -> 37x37 patch -> pos_embed 1370
DEFAULT_FEATURES = 64           # DPT 头特征数（vits metric 用 64）
DEFAULT_OUT_CHANNELS = (48, 96, 192, 384)

# spec §4: backend.encoder = vits（本框架只走 metric-small）
ENCODER_CFG: dict[str, dict[str, Any]] = {
    "vits": {"embed_dim": 384, "depth": 12, "num_heads": 6, "patch_size": 14,
             "mlp_ratio": 4.0, "intermediate": (2, 5, 8, 11)},
    "vitb": {"embed_dim": 768, "depth": 12, "num_heads": 12, "patch_size": 14,
             "mlp_ratio": 4.0, "intermediate": (2, 5, 8, 11)},
    "vitl": {"embed_dim": 1024, "depth": 24, "num_heads": 16, "patch_size": 14,
             "mlp_ratio": 4.0, "intermediate": (4, 11, 17, 23)},
}

__all__ = [
    "DEFAULT_FEATURES",
    "DEFAULT_IMG_SIZE",
    "DEFAULT_OUT_CHANNELS",
    "ENCODER_CFG",
    "create_metric_model",
    "expected_state_dict_spec",
    "torch_available",
    "validate_state_dict_spec",
    "DepthAnythingV2Metric",
    "DPTHeadMetric",
    "DINOv2ViT",
    "get_class",
]


# ---------------------------------------------------------------------------
# 1) 纯 Python 的架构描述（无 torch 可用）——真实 .pth 的静态比对基准


def expected_state_dict_spec(
    *,
    encoder: str = "vits",
    features: int = DEFAULT_FEATURES,
    out_channels: Sequence[int] = DEFAULT_OUT_CHANNELS,
    img_size: int = DEFAULT_IMG_SIZE,
) -> "OrderedDict[str, tuple[int, ...]]":
    """返回该架构应有的 `{state_dict 键: 形状}`（纯 Python，不需要 torch）。

    这份表是 `_build_classes()` 里 nn.Module 定义的镜像；两者用同一组常量写成。
    有 torch 的机器上可由 `validate_state_dict_spec(model.state_dict(), ...)` 交叉校验。
    """
    if encoder not in ENCODER_CFG:
        raise ValueError(f"未知 encoder {encoder!r}，可选 {sorted(ENCODER_CFG)}")
    cfg = ENCODER_CFG[encoder]
    dim = int(cfg["embed_dim"])
    n_layer = int(cfg["depth"])
    patch = int(cfg["patch_size"])
    mlp_hidden = int(dim * float(cfg["mlp_ratio"]))
    out_channels = tuple(int(c) for c in out_channels)
    if len(out_channels) != 4:
        raise ValueError(f"out_channels 必须是 4 个，收到 {out_channels!r}")
    if int(img_size) % patch != 0:
        raise ValueError(f"img_size={img_size} 必须能被 patch_size={patch} 整除")
    n_patch = (int(img_size) // patch) ** 2

    spec: "OrderedDict[str, tuple[int, ...]]" = OrderedDict()
    # --- DINOv2 主干：模型属性名必须是 pretrained.* ---
    spec["pretrained.cls_token"] = (1, 1, dim)
    spec["pretrained.pos_embed"] = (1, n_patch + 1, dim)
    spec["pretrained.mask_token"] = (1, dim)
    spec["pretrained.patch_embed.proj.weight"] = (dim, 3, patch, patch)
    spec["pretrained.patch_embed.proj.bias"] = (dim,)
    for i in range(n_layer):
        p = f"pretrained.blocks.{i}."
        spec[p + "norm1.weight"] = (dim,)
        spec[p + "norm1.bias"] = (dim,)
        spec[p + "attn.qkv.weight"] = (3 * dim, dim)
        spec[p + "attn.qkv.bias"] = (3 * dim,)
        spec[p + "attn.proj.weight"] = (dim, dim)
        spec[p + "attn.proj.bias"] = (dim,)
        spec[p + "ls1.gamma"] = (dim,)
        spec[p + "norm2.weight"] = (dim,)
        spec[p + "norm2.bias"] = (dim,)
        spec[p + "mlp.fc1.weight"] = (mlp_hidden, dim)
        spec[p + "mlp.fc1.bias"] = (mlp_hidden,)
        spec[p + "mlp.fc2.weight"] = (dim, mlp_hidden)
        spec[p + "mlp.fc2.bias"] = (dim,)
        spec[p + "ls2.gamma"] = (dim,)
    spec["pretrained.norm.weight"] = (dim,)
    spec["pretrained.norm.bias"] = (dim,)

    # --- DPT metric 头 ---
    for i, oc in enumerate(out_channels):
        spec[f"depth_head.projects.{i}.weight"] = (oc, dim, 1, 1)
        spec[f"depth_head.projects.{i}.bias"] = (oc,)
    spec["depth_head.resize_layers.0.weight"] = (out_channels[0], out_channels[0], 4, 4)
    spec["depth_head.resize_layers.0.bias"] = (out_channels[0],)
    spec["depth_head.resize_layers.1.weight"] = (out_channels[1], out_channels[1], 2, 2)
    spec["depth_head.resize_layers.1.bias"] = (out_channels[1],)
    # resize_layers.2 是 nn.Identity()，无参数
    spec["depth_head.resize_layers.3.weight"] = (out_channels[3], out_channels[3], 3, 3)
    spec["depth_head.resize_layers.3.bias"] = (out_channels[3],)
    for i, oc in enumerate(out_channels):
        # bias=False（与 checkpoint 一致：layer*_rn 没有 .bias）
        spec[f"depth_head.scratch.layer{i + 1}_rn.weight"] = (features, oc, 3, 3)
    for i in range(1, 5):
        p = f"depth_head.scratch.refinenet{i}."
        spec[p + "out_conv.weight"] = (features, features, 1, 1)
        spec[p + "out_conv.bias"] = (features,)
        for unit in ("resConfUnit1", "resConfUnit2"):
            spec[f"{p}{unit}.conv1.weight"] = (features, features, 3, 3)
            spec[f"{p}{unit}.conv1.bias"] = (features,)
            spec[f"{p}{unit}.conv2.weight"] = (features, features, 3, 3)
            spec[f"{p}{unit}.conv2.bias"] = (features,)
    head_1 = int(features)
    head_2 = 32
    spec["depth_head.scratch.output_conv1.weight"] = (head_1 // 2, head_1, 3, 3)
    spec["depth_head.scratch.output_conv1.bias"] = (head_1 // 2,)
    spec["depth_head.scratch.output_conv2.0.weight"] = (head_2, head_1 // 2, 3, 3)
    spec["depth_head.scratch.output_conv2.0.bias"] = (head_2,)
    spec["depth_head.scratch.output_conv2.2.weight"] = (1, head_2, 1, 1)
    spec["depth_head.scratch.output_conv2.2.bias"] = (1,)
    return spec


def validate_state_dict_spec(
    state_dict: Mapping[str, Any],
    *,
    expected: Mapping[str, tuple[int, ...]] | None = None,
    encoder: str = "vits",
    features: int = DEFAULT_FEATURES,
    out_channels: Sequence[int] = DEFAULT_OUT_CHANNELS,
    img_size: int = DEFAULT_IMG_SIZE,
    source: str = "<state_dict>",
    max_report: int = 8,
) -> None:
    """把一份 state_dict（键 -> tensor 或形状）与架构表逐键比对，不一致抛 BackendUnavailable。

    报错信息里给出 missing / unexpected / shape-mismatch 的**前若干条**与总数，方便定位。
    """
    if any(hasattr(v, "shape") for v in state_dict.values()):
        given: dict[str, tuple[int, ...]] = {
            str(k): tuple(int(s) for s in getattr(v, "shape", ())) for k, v in state_dict.items()
        }
    else:
        given = {str(k): tuple(int(s) for s in v) for k, v in state_dict.items()}
    want = dict(expected) if expected is not None else dict(expected_state_dict_spec(
        encoder=encoder, features=features, out_channels=out_channels, img_size=img_size))

    missing = [k for k in want if k not in given]
    unexpected = [k for k in given if k not in want]
    mismatch = [(k, given[k], want[k]) for k in want if k in given and given[k] != want[k]]
    if not (missing or unexpected or mismatch):
        return

    def _fmt(items: Iterable[Any], n: int = max_report) -> str:
        items = list(items)
        head = ", ".join(str(x) for x in items[:n])
        return f"{head}{f' …(+{len(items) - n})' if len(items) > n else ''}"

    parts = [
        f"state_dict 与架构不匹配 (source={source})：",
        f"  期望 {len(want)} 个键，实际 {len(given)} 个；",
    ]
    if missing:
        parts.append(f"  缺少 {len(missing)} 个: {_fmt(missing)}")
    if unexpected:
        parts.append(f"  多出 {len(unexpected)} 个: {_fmt(unexpected)}")
    if mismatch:
        parts.append(f"  形状不符 {len(mismatch)} 个: " + _fmt(
            [f"{k}{tuple(a)}!={tuple(b)}" for k, a, b in mismatch]))
    raise BackendUnavailable("\n".join(parts))


# ---------------------------------------------------------------------------
# 2) torch 惰性加载


def torch_available() -> bool:
    """不抛异常地探测 torch 是否可用（不做任何推理）。"""
    try:
        import torch  # noqa: F401
    except Exception:
        return False
    return True


def require_torch():
    """惰性 `import torch`；缺依赖抛 BackendUnavailable（不是 ImportError）。"""
    try:
        import torch
    except Exception as exc:  # ImportError / OSError(DLL) / 任何导入期异常
        raise BackendUnavailable(
            "构造 DA V2 网络需要 torch，当前环境导入失败："
            f"{type(exc).__name__}: {exc}；无卡环境请改用 SyntheticBackend"
        ) from exc
    return torch


# ---------------------------------------------------------------------------
# 3) nn.Module 定义（首次调用时才依赖 torch）


_CLASSES: dict[str, type] = {}


def _build_classes() -> dict[str, type]:
    """定义并缓存 nn.Module 子类。第一次调用需要 torch。"""
    if _CLASSES:
        return _CLASSES
    torch = require_torch()
    nn = torch.nn
    F = nn.functional

    class LayerScale(nn.Module):
        """DINOv2 的 layer scale（参数名必须是 gamma）。"""

        def __init__(self, dim: int, init_values: float = 1e-5):
            super().__init__()
            self.gamma = nn.Parameter(init_values * torch.ones(dim))

        def forward(self, x):
            return x * self.gamma

    class Mlp(nn.Module):
        def __init__(self, in_features: int, hidden_features: int):
            super().__init__()
            self.fc1 = nn.Linear(in_features, hidden_features, bias=True)
            self.act = nn.GELU()
            self.fc2 = nn.Linear(hidden_features, in_features, bias=True)

        def forward(self, x):
            return self.fc2(self.act(self.fc1(x)))

    class Attention(nn.Module):
        """标准 MHSA；qkv / proj 都是带 bias 的 Linear（与 checkpoint 键一致）。"""

        def __init__(self, dim: int, num_heads: int):
            super().__init__()
            if dim % num_heads:
                raise ValueError(f"dim={dim} 必须能被 num_heads={num_heads} 整除")
            self.num_heads = num_heads
            self.head_dim = dim // num_heads
            self.scale = self.head_dim ** -0.5
            self.qkv = nn.Linear(dim, dim * 3, bias=True)
            self.proj = nn.Linear(dim, dim, bias=True)

        def forward(self, x):
            b, n, c = x.shape
            qkv = self.qkv(x).reshape(b, n, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
            q, k, v = qkv[0], qkv[1], qkv[2]
            attn = (q * self.scale) @ k.transpose(-2, -1)
            attn = attn.softmax(dim=-1)
            x = (attn @ v).transpose(1, 2).reshape(b, n, c)
            return self.proj(x)

    class Block(nn.Module):
        def __init__(self, dim: int, num_heads: int, mlp_hidden: int):
            super().__init__()
            self.norm1 = nn.LayerNorm(dim)
            self.attn = Attention(dim, num_heads)
            self.ls1 = LayerScale(dim)
            self.norm2 = nn.LayerNorm(dim)
            self.mlp = Mlp(dim, mlp_hidden)
            self.ls2 = LayerScale(dim)

        def forward(self, x):
            x = x + self.ls1(self.attn(self.norm1(x)))
            x = x + self.ls2(self.mlp(self.norm2(x)))
            return x

    class PatchEmbed(nn.Module):
        def __init__(self, patch_size: int, in_chans: int, embed_dim: int):
            super().__init__()
            self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

        def forward(self, x):
            x = self.proj(x)                       # (B, C, gh, gw)
            return x.flatten(2).transpose(1, 2)    # (B, N, C)

    class DINOv2ViT(nn.Module):
        """DINOv2 ViT（无 head）；属性名/顺序对齐 checkpoint 的 `pretrained.*`。"""

        def __init__(self, cfg: Mapping[str, Any], img_size: int = DEFAULT_IMG_SIZE):
            super().__init__()
            dim = int(cfg["embed_dim"])
            patch = int(cfg["patch_size"])
            self.patch_size = patch
            self.embed_dim = dim
            self.num_heads = int(cfg["num_heads"])
            self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))
            n_patch = (int(img_size) // patch) ** 2
            # img_size=518 时恰好 1370，与官方 checkpoint 的 pos_embed 形状一致
            self.pos_embed = nn.Parameter(torch.zeros(1, n_patch + 1, dim))
            self.mask_token = nn.Parameter(torch.zeros(1, dim))
            self.patch_embed = PatchEmbed(patch, 3, dim)
            mlp_hidden = int(dim * float(cfg["mlp_ratio"]))
            self.blocks = nn.ModuleList(
                [Block(dim, self.num_heads, mlp_hidden) for _ in range(int(cfg["depth"]))])
            self.norm = nn.LayerNorm(dim)

        def interpolate_pos_encoding(self, x, h: int, w: int):
            """输入尺寸变了就 bicubic 插值 pos_embed（官方 dinov2 的同一套 recipe）。"""
            n_patch = x.shape[1] - 1
            n_ref = self.pos_embed.shape[1] - 1
            if n_patch == n_ref and w == h:
                return self.pos_embed
            pos_embed = self.pos_embed.float()
            class_pos = pos_embed[:, 0]
            patch_pos = pos_embed[:, 1:]
            dim = x.shape[-1]
            w0 = w // self.patch_size
            h0 = h // self.patch_size
            w0, h0 = w0 + 0.1, h0 + 0.1
            side = int(math.sqrt(n_ref))
            patch_pos = F.interpolate(
                patch_pos.reshape(1, side, side, dim).permute(0, 3, 1, 2),
                scale_factor=(w0 / side, h0 / side), mode="bicubic", align_corners=False)
            patch_pos = patch_pos.permute(0, 2, 3, 1).view(1, -1, dim)
            return torch.cat((class_pos.unsqueeze(0), patch_pos), dim=1).to(self.pos_embed.dtype)

        def get_intermediate_layers(self, x, n: Sequence[int], return_class_token: bool = True):
            """返回第 n 个 block 的 patch token（已过最终 LayerNorm），与 dinov2 语义一致。"""
            b, _, h, w = x.shape
            if h % self.patch_size or w % self.patch_size:
                raise ValueError(
                    f"输入 {h}x{w} 必须能被 patch_size={self.patch_size} 整除")
            x = self.patch_embed(x)
            cls = self.cls_token.expand(b, -1, -1)
            x = torch.cat((cls, x), dim=1)
            x = x + self.interpolate_pos_encoding(x, h, w)
            outs = []
            for i, blk in enumerate(self.blocks):
                x = blk(x)
                if i in n:
                    outs.append(x)
            outs = [self.norm(o) for o in outs]
            if return_class_token:
                # ⚠ 顺序必须是 (patch_tokens, cls_token)——与官方 dinov2 的
                # `return_class_token=True` 一致，depth head 里 `x = feat[0]` 取的是 patches。
                # 2026-10-10 云端真推理抓到：这里曾写成 (cls, patches)，于是 head 拿到的
                # `x` 是 (B, C) 二维张量，在 `x.permute(0, 2, 1)` 处报
                # "input.dim() = 2 is not equal to len(dims) = 3"。
                return [(o[:, 1:], o[:, 0]) for o in outs]
            return [o[:, 1:] for o in outs]

    class ResidualConvUnit(nn.Module):
        def __init__(self, features: int):
            super().__init__()
            self.conv1 = nn.Conv2d(features, features, 3, stride=1, padding=1, bias=True)
            self.conv2 = nn.Conv2d(features, features, 3, stride=1, padding=1, bias=True)
            self.act = nn.ReLU(inplace=True)

        def forward(self, x):
            return self.conv2(self.act(self.conv1(self.act(x))))

    class FeatureFusionBlock(nn.Module):
        def __init__(self, features: int):
            super().__init__()
            self.out_conv = nn.Conv2d(features, features, 1, stride=1, padding=0, bias=True)
            self.resConfUnit1 = ResidualConvUnit(features)
            self.resConfUnit2 = ResidualConvUnit(features)

        def forward(self, *xs, size=None):
            output = xs[0]
            if len(xs) == 2:
                output = output + self.resConfUnit1(xs[1])
            output = self.resConfUnit2(output)
            if size is not None and (output.shape[-2] != size[0] or output.shape[-1] != size[1]):
                output = F.interpolate(output, size=size, mode="bilinear", align_corners=True)
            return self.out_conv(output)

    class DPTHeadMetric(nn.Module):
        """DPT 头（metric 分支：末层 ReLU，输出 (B,1,H,W) ∈ [0,1]，外层乘 max_depth）。"""

        def __init__(self, in_channels: int, features: int = DEFAULT_FEATURES,
                     out_channels: Sequence[int] = DEFAULT_OUT_CHANNELS, use_clstoken: bool = False):
            super().__init__()
            out_channels = tuple(int(c) for c in out_channels)
            if len(out_channels) != 4:
                raise ValueError(f"out_channels 必须是 4 个，收到 {out_channels!r}")
            self.use_clstoken = bool(use_clstoken)
            self.projects = nn.ModuleList(
                [nn.Conv2d(in_channels, oc, kernel_size=1, stride=1, padding=0) for oc in out_channels])
            self.resize_layers = nn.ModuleList([
                nn.ConvTranspose2d(out_channels[0], out_channels[0], kernel_size=4, stride=4, padding=0),
                nn.ConvTranspose2d(out_channels[1], out_channels[1], kernel_size=2, stride=2, padding=0),
                nn.Identity(),
                nn.Conv2d(out_channels[3], out_channels[3], kernel_size=3, stride=2, padding=1),
            ])
            scratch = nn.Module()
            for i, oc in enumerate(out_channels):
                setattr(scratch, f"layer{i + 1}_rn",
                        nn.Conv2d(oc, features, kernel_size=3, stride=1, padding=1, bias=False))
            for i in range(1, 5):
                setattr(scratch, f"refinenet{i}", FeatureFusionBlock(features))
            head_1 = int(features)
            head_2 = 32
            scratch.output_conv1 = nn.Conv2d(head_1, head_1 // 2, kernel_size=3, stride=1, padding=1)
            scratch.output_conv2 = nn.Sequential(
                nn.Conv2d(head_1 // 2, head_2, kernel_size=3, stride=1, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(head_2, 1, kernel_size=1, stride=1, padding=0),
                nn.ReLU(inplace=True),
            )
            self.scratch = scratch

        def forward(self, out_features, patch_h: int, patch_w: int):
            out = []
            for i, feat in enumerate(out_features):
                if self.use_clstoken:
                    x, cls_token = feat[0], feat[1]
                    x = torch.cat((x, cls_token.unsqueeze(1)), dim=1)  # 与官方一致：拼在末尾
                else:
                    x = feat[0]
                if x.dim() != 3:
                    raise RuntimeError(
                        f"depth head 收到 {x.dim()} 维 token 张量（期望 (B, N, C)）："
                        "backbone.get_intermediate_layers(return_class_token=True) "
                        "必须返回 (patch_tokens, cls_token)，patch 在前。"
                        f" 实际 feat 类型={type(feat).__name__}")
                x = x.permute(0, 2, 1).reshape((x.shape[0], x.shape[-1], patch_h, patch_w))
                x = self.projects[i](x)
                x = self.resize_layers[i](x)
                out.append(x)
            layer_1, layer_2, layer_3, layer_4 = out
            layer_1_rn = self.scratch.layer1_rn(layer_1)
            layer_2_rn = self.scratch.layer2_rn(layer_2)
            layer_3_rn = self.scratch.layer3_rn(layer_3)
            layer_4_rn = self.scratch.layer4_rn(layer_4)
            path_4 = self.scratch.refinenet4(layer_4_rn, size=layer_3_rn.shape[2:])
            path_3 = self.scratch.refinenet3(path_4, layer_3_rn, size=layer_2_rn.shape[2:])
            path_2 = self.scratch.refinenet2(path_3, layer_2_rn, size=layer_1_rn.shape[2:])
            path_1 = self.scratch.refinenet1(path_2, layer_1_rn)
            out = self.scratch.output_conv1(path_1)
            out = F.interpolate(out, (patch_h * 14, patch_w * 14), mode="bilinear", align_corners=True)
            return self.scratch.output_conv2(out)

    class DepthAnythingV2Metric(nn.Module):
        """Depth Anything V2 Metric-Small（encoder=vits）。

        `forward(x)` 输入 (B,3,H,W) 已归一化张量，输出 (B,H,W) **米**（内部乘 `max_depth`）。
        """

        def __init__(self, encoder: str = "vits", features: int = DEFAULT_FEATURES,
                     out_channels: Sequence[int] = DEFAULT_OUT_CHANNELS, max_depth: float = 20.0,
                     img_size: int = DEFAULT_IMG_SIZE, use_clstoken: bool = False):
            super().__init__()
            if encoder not in ENCODER_CFG:
                raise ValueError(f"未知 encoder {encoder!r}，可选 {sorted(ENCODER_CFG)}")
            cfg = ENCODER_CFG[encoder]
            self.encoder = encoder
            self.max_depth = float(max_depth)
            self.patch_size = int(cfg["patch_size"])
            self.intermediate_layer_idx = tuple(cfg["intermediate"])
            self.use_clstoken = bool(use_clstoken)
            self.pretrained = DINOv2ViT(cfg, img_size=img_size)
            self.depth_head = DPTHeadMetric(cfg["embed_dim"], features=features,
                                            out_channels=out_channels, use_clstoken=use_clstoken)

        def forward(self, x):
            patch_h = x.shape[-2] // self.patch_size
            patch_w = x.shape[-1] // self.patch_size
            feats = self.pretrained.get_intermediate_layers(
                x, self.intermediate_layer_idx, return_class_token=True)
            depth = self.depth_head(feats, patch_h, patch_w) * self.max_depth
            return depth.squeeze(1)

    _CLASSES.update({
        "DepthAnythingV2Metric": DepthAnythingV2Metric,
        "DPTHeadMetric": DPTHeadMetric,
        "DINOv2ViT": DINOv2ViT,
        "FeatureFusionBlock": FeatureFusionBlock,
        "ResidualConvUnit": ResidualConvUnit,
        "Block": Block,
        "Attention": Attention,
        "PatchEmbed": PatchEmbed,
        "LayerScale": LayerScale,
        "Mlp": Mlp,
    })
    return _CLASSES


def get_class(name: str) -> type:
    """按名字取 nn.Module 子类（需要 torch）。"""
    classes = _build_classes()
    if name not in classes:
        raise KeyError(f"未知模型类 {name!r}，可选 {sorted(classes)}")
    return classes[name]


def create_metric_model(*, encoder: str = "vits", features: int = DEFAULT_FEATURES,
                        out_channels: Sequence[int] = DEFAULT_OUT_CHANNELS,
                        max_depth: float = 20.0, img_size: int = DEFAULT_IMG_SIZE,
                        use_clstoken: bool = False):
    """构造未加载权重的 `DepthAnythingV2Metric`（需要 torch；缺依赖抛 BackendUnavailable）。"""
    cls = get_class("DepthAnythingV2Metric")
    return cls(encoder=encoder, features=features, out_channels=out_channels,
               max_depth=max_depth, img_size=img_size, use_clstoken=use_clstoken)


def __getattr__(name: str):
    """`dpt.DepthAnythingV2Metric` 这类访问在需要时才构造类（缺 torch 抛 BackendUnavailable）。"""
    if name in ("DepthAnythingV2Metric", "DPTHeadMetric", "DINOv2ViT"):
        return get_class(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
