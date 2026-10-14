"""深度后端适配层（w1）。

契约（spec §3）：
    `load(cfg) -> DepthBackend`；`DepthBackend.infer(rgb) -> DepthMap`；`kind` 必须是 `"metric"`。

两个实现：
    * `DepthAnythingV2Metric` —— Depth Anything V2 **Metric-Small**（encoder=vits，
      DPT metric 头，`max_depth=20.0`，输出单位**米**）。惰性 `import torch`；
      缺 torch / 缺权重 / 显式要 CUDA 但没有 CUDA → 抛 `types.BackendUnavailable`
      （**不会**让 ImportError 裸奔，**不会**自动下载权重）。
    * `SyntheticBackend` —— 无卡环境下的**唯一验收通道**：解析式度量深度
      （平面地面 + 前平面盒子 + 站在地面上的平面人体），`kind="metric"`、单位米。
      几何完全闭式，已知像素的深度可手算比对（见 `agent_reports/w1_verify_backend.py`）。

铁律：本模块只产出**度量**深度。没有任何相对深度（仿射不变）路径，
也没有"逐帧 Min/Max 归一化"。

未验证声明（本机无 torch / 无 GPU）：
    * `DepthAnythingV2Metric` 的**前向数值**未验证（不跑真推理）。
    * 已验证：权重存在性检查、缺 torch 时抛 `BackendUnavailable`、
      `model/dpt.py` 的键名/形状与真实 `.pth` 的 239 个键**逐一对齐**、
      `SyntheticBackend` 的解析式精度 < 1e-6。
"""

from __future__ import annotations

import abc
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

try:  # 正常包内导入
    from . import types
    from .model import dpt
except ImportError:  # 直接以脚本方式运行时的兜底
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from depth_prior import types
    from depth_prior.model import dpt

__all__ = [
    "BACKEND_DA_V2_METRIC",
    "BACKEND_SYNTHETIC",
    "DepthAnythingV2Metric",
    "DepthBackend",
    "SyntheticBackend",
    "SYNTHETIC_DEFAULTS",
    "load",
    "load_with_fallback",
]

BACKEND_DA_V2_METRIC = "da_v2_metric_vits"
BACKEND_SYNTHETIC = "synthetic"

# ImageNet 归一化（DA V2 官方 image2tensor 用的就是这三个数）
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


# ---------------------------------------------------------------------------
# 抽象接口


class DepthBackend(abc.ABC):
    """深度后端接口（spec §3）。`kind` 是安全闸门，不是注释。"""

    name: str = "unknown"

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """`"metric"` 才允许进 `fusion.fuse` 主项。"""

    @abc.abstractmethod
    def infer(self, rgb: np.ndarray) -> types.DepthMap:
        """`rgb` (H, W, 3) uint8 → `DepthMap`。"""

    def infer_batch(self, frames: Iterable[np.ndarray]) -> list[types.DepthMap]:
        return [self.infer(f) for f in frames]

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "kind": self.kind}


# ---------------------------------------------------------------------------
# 工具


def _as_uint8_rgb(rgb: np.ndarray, *, what: str = "rgb") -> np.ndarray:
    arr = np.asarray(rgb)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"{what} 必须是 (H, W, 3)，收到 {arr.shape}")
    if arr.dtype == np.uint8:
        return np.ascontiguousarray(arr)
    if arr.dtype.kind == "f":
        arr = arr.astype(np.float32)
        if arr.size and float(np.nanmax(arr)) <= 1.5:      # 0..1 浮点图
            arr = arr * 255.0
    return np.ascontiguousarray(np.clip(arr, 0, 255).astype(np.uint8))


def depth_stats(depth: np.ndarray) -> dict[str, float]:
    """给诊断用的纯 Python 统计量（可直接进 `RootZTrack.diag`）。"""
    d = np.asarray(depth, dtype=np.float64)
    finite = np.isfinite(d)
    vals = d[finite]
    if vals.size == 0:
        return {"min_m": 0.0, "p50_m": 0.0, "mean_m": 0.0, "max_m": 0.0, "finite_frac": 0.0}
    return {
        "min_m": float(vals.min()),
        "p50_m": float(np.median(vals)),
        "mean_m": float(vals.mean()),
        "max_m": float(vals.max()),
        "finite_frac": float(finite.mean()),
    }


def to_plain(obj: Any) -> Any:
    """把 numpy 标量/数组转成可 `repr` 的纯 Python 类型。

    `types.RootZTrack.save` 用 `repr(diag)` 落盘、`eval` 读回，因此 diag 里
    **不能**出现 numpy 对象。
    """
    if isinstance(obj, dict):
        return {str(k): to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_plain(obj.tolist())
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ---------------------------------------------------------------------------
# 真后端：Depth Anything V2 Metric-Small


def _official_model(official_path: str | None, *, encoder: str, features: int,
                    out_channels: Sequence[int], max_depth: float, on_error=None):
    """尝试用【官方】Depth-Anything-V2 metric_depth 实现构造模型。

    返回 None = 不可用（没配路径 / 目录不存在 / 导入或构造失败）：调用方退回自研的
    `model/dpt.py`，原因记进 `official_error`。**刻意不抛异常**——缺官方代码是降级，
    不是致命错误（无卡离线环境仍然要能 import 本模块）。
    """
    p = str(official_path or "").strip()
    if not p:
        return None
    try:
        import sys as _sys
        if Path(p).is_dir() and p not in _sys.path:
            _sys.path.insert(0, p)
        from depth_anything_v2.dpt import DepthAnythingV2 as _Official
        return _Official(encoder=encoder, features=features,
                         out_channels=list(out_channels), max_depth=max_depth)
    except Exception as exc:  # noqa: BLE001 - 降级路径
        if on_error is not None:
            on_error(f"{type(exc).__name__}: {exc}")
        return None


class DepthAnythingV2Metric(DepthBackend):
    """DA V2 Metric-Small 适配器。构造即加载（缺依赖抛 `BackendUnavailable`）。"""

    name = BACKEND_DA_V2_METRIC

    def __init__(
        self,
        *,
        weights: str | Path,
        encoder: str = "vits",
        max_depth: float = 20.0,
        input_size: int = 518,
        device: str = "auto",
        official_path: str | None = None,
        features: int = dpt.DEFAULT_FEATURES,
        out_channels: Sequence[int] = dpt.DEFAULT_OUT_CHANNELS,
        img_size: int = dpt.DEFAULT_IMG_SIZE,
    ) -> None:
        # 1) 权重存在性：先查这一条，报错最具体（无卡环境也拿得到明确原因）
        self.weights = Path(weights)
        if not self.weights.is_file():
            raise types.BackendUnavailable(
                f"权重不存在：{self.weights}（本框架不下载权重；"
                f"无卡环境请改用 SyntheticBackend，或修正 cfg['backend']['weights']）")
        self.weights_bytes = int(self.weights.stat().st_size)

        # 2) 惰性 import torch
        torch = dpt.require_torch()

        # 3) 设备
        dev = str(device or "auto").lower()
        if dev == "auto":
            resolved = "cuda" if torch.cuda.is_available() else "cpu"
        elif dev.startswith("cuda"):
            if not torch.cuda.is_available():
                raise types.BackendUnavailable(
                    f"cfg['backend']['device']={device!r} 要求 CUDA，但 torch.cuda.is_available()=False；"
                    "改成 'auto' 或 'cpu'，或改用 SyntheticBackend")
            resolved = dev
        elif dev == "cpu":
            resolved = "cpu"
        else:
            raise types.BackendUnavailable(
                f"未知 device={device!r}（可选 auto / cpu / cuda / cuda:N）")

        self.encoder = str(encoder)
        self.max_depth = float(max_depth)
        self.input_size = int(input_size)
        self.device = resolved
        self.torch = torch
        self.infer_count = 0
        self.last_stats: dict[str, float] = {}

        # 4) 网络 + 权重
        #    默认优先用【官方】metric_depth 实现。2026-10-10 云端实测（无卡 CPU）：
        #      strict load OK (missing=[] unexpected=[])
        #      真实 take 帧 → min 2.28 p50 6.4~6.8 max 10.4 m（合理的米制物理深度）
        #    自研的 model/dpt.py 只作离线兜底：它能**严格加载**权重（239 键全对），
        #    但**前向数值不对**——特征逐层爆炸（block11 ±34.9、过 LN 后 ±99），
        #    head 原始输出恒 ≤0，经 ReLU 后整张图全 0。本地无 torch 验证不了，
        #    是云端真推理抓到的。详见 agent_reports/DEPTH_PRIOR_框架交付_2026-10-10.md。
        self.impl = "in_tree"
        self.official_error = ""
        self.model = _official_model(
            official_path, encoder=self.encoder, features=features,
            out_channels=out_channels, max_depth=self.max_depth,
            on_error=self._note_official_error)
        if self.model is not None:
            self.impl = "official"
        else:
            try:
                self.model = dpt.create_metric_model(
                    encoder=self.encoder, features=features, out_channels=out_channels,
                    max_depth=self.max_depth, img_size=img_size)
            except types.BackendUnavailable:
                raise
            except Exception as exc:
                raise types.BackendUnavailable(
                    f"构造 DA V2 网络失败（encoder={self.encoder!r}）：{type(exc).__name__}: {exc}") from exc
        state = self._load_checkpoint(self.weights)
        if self.impl == "in_tree":
            dpt.validate_state_dict_spec(
                state, encoder=self.encoder, features=features, out_channels=out_channels,
                img_size=img_size, source=str(self.weights))
        try:
            self.model.load_state_dict(state, strict=True)
        except Exception as exc:  # 键名已校验过，这里只兜底
            raise types.BackendUnavailable(
                f"load_state_dict 失败（impl={self.impl}, {self.weights}）："
                f"{type(exc).__name__}: {exc}") from exc
        self.model.eval()
        self.model.to(self.device)

        mean = torch.tensor(IMAGENET_MEAN, dtype=torch.float32).view(1, 3, 1, 1)
        std = torch.tensor(IMAGENET_STD, dtype=torch.float32).view(1, 3, 1, 1)
        self._mean = mean.to(self.device)
        self._std = std.to(self.device)

    # -- 构造辅助 -----------------------------------------------------------

    @classmethod
    def from_cfg(cls, cfg: dict) -> "DepthAnythingV2Metric":
        """从（已 merge 的）cfg 构造。缺依赖/缺权重时抛 `BackendUnavailable`。"""
        b = dict(cfg.get("backend", {}))
        return cls(
            weights=b.get("weights", str(types.DEFAULT_WEIGHTS)),
            encoder=b.get("encoder", "vits"),
            max_depth=float(b.get("max_depth", 20.0)),
            input_size=int(b.get("input_size", 518)),
            device=b.get("device", "auto"),
            official_path=b.get("official_path") or None,
        )

    def _note_official_error(self, msg: str) -> None:
        self.official_error = msg

    def _load_checkpoint(self, path: Path) -> dict:
        torch = self.torch
        self.unwrapped_key: str | None = None
        try:
            try:
                obj = torch.load(str(path), map_location="cpu", weights_only=True)
            except TypeError:  # torch < 2.0 没有 weights_only
                obj = torch.load(str(path), map_location="cpu")
        except Exception as exc:
            raise types.BackendUnavailable(
                f"torch.load 读取权重失败（{path}）：{type(exc).__name__}: {exc}") from exc
        if not isinstance(obj, dict):
            raise types.BackendUnavailable(
                f"权重格式不认识：{path} 顶层是 {type(obj).__name__}，期望 state_dict(dict)")
        # 常见包装：{'model': sd} / {'state_dict': sd} / {'params': sd}
        if not any(hasattr(v, "shape") for v in obj.values()):
            nested = [(k, v) for k, v in obj.items() if isinstance(v, dict)]
            for key in ("model", "state_dict", "params", "model_state_dict"):
                for k, v in nested:
                    if k == key:
                        self.unwrapped_key = k
                        return v
            if len(nested) == 1:
                self.unwrapped_key = nested[0][0]
                return nested[0][1]
        return obj

    # -- 接口 ---------------------------------------------------------------

    @property
    def kind(self) -> str:
        return types.KIND_METRIC

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "unit": "m",
            "encoder": self.encoder,
            "max_depth_m": self.max_depth,
            "input_size": self.input_size,
            "device": self.device,
            "weights": str(self.weights),
            "weights_bytes": self.weights_bytes,
            "infer_count": self.infer_count,
        }

    def preprocess(self, rgb: np.ndarray):
        """(H,W,3) uint8 → (1,3,input_size,input_size) 归一化张量。

        官方 `image2tensor` 用 `cv2.resize(..., (input_size, input_size))`；
        这里没有 cv2，用 torch 的 bilinear 插值做等价缩放（`align_corners=False`）。
        """
        torch = self.torch
        arr = _as_uint8_rgb(rgb)
        x = torch.from_numpy(arr.astype(np.float32) / 255.0).permute(2, 0, 1)[None]
        if x.shape[-2] != self.input_size or x.shape[-1] != self.input_size:
            x = torch.nn.functional.interpolate(
                x, size=(self.input_size, self.input_size), mode="bilinear", align_corners=False)
        return (x.to(self.device) - self._mean) / self._std

    def infer(self, rgb: np.ndarray) -> types.DepthMap:
        """单帧推理。返回的 depth 单位是**米**，`kind="metric"`。"""
        arr = _as_uint8_rgb(rgb)
        h, w = arr.shape[:2]
        torch = self.torch
        with torch.inference_mode():
            x = self.preprocess(arr)
            out = self.model(x)                                    # (1, h', w') 米
            out = torch.nn.functional.interpolate(
                out[:, None], size=(h, w), mode="bilinear", align_corners=True)[0, 0]
            depth = out.detach().to("cpu").numpy().astype(np.float32, copy=False)
        # metric 头输出 = relu(.) * max_depth ∈ [0, max_depth]；数值兜底
        depth = np.nan_to_num(depth, nan=0.0, posinf=self.max_depth, neginf=0.0)
        np.clip(depth, 0.0, self.max_depth, out=depth)
        self.infer_count += 1
        self.last_stats = depth_stats(depth)
        return types.DepthMap(depth=depth, kind=types.KIND_METRIC, unit="m",
                              backend=BACKEND_DA_V2_METRIC)

    def infer_depth(self, rgb: np.ndarray) -> np.ndarray:
        """只要米制数组时的快捷方式（仍是 (`kind="metric"`) 那一份数据）。"""
        return self.infer(rgb).depth


# ---------------------------------------------------------------------------
# 合成后端（无卡验收通道）

SYNTHETIC_DEFAULTS: dict[str, Any] = {
    # 相机
    "width": 640,
    "height": 480,
    "fx": 800.0,
    "fy": 800.0,
    "cx": None,                 # None → width / 2（像素中心坐标约定 (u+0.5, v+0.5)）
    "cy": None,                 # None → height / 2
    "frames": 60,
    "fps": 30.0,
    # 场景（相机系：X 右、Y 下、Z 前；单位米）
    "cam_height_m": 1.55,       # 相机离地高度
    "bg_depth_m": 25.0,         # 天空/远处截断深度
    "person_height_m": 1.75,
    "person_width_m": 0.46,
    "person_x_m": 0.0,          # 人体横向偏移
    "z_start_m": 3.0,           # 根节点 Z 轨迹（帧 0 → 帧 frames-1 线性）
    "z_end_m": 5.0,
    # 扰动（默认全 0 → 输出是纯解析场，可精确比对）
    "depth_scale": 1.0,         # 整体尺度倍率（模拟"尺度漂了"，2.0 = 全乘 2）
    "drift_frac": 0.0,          # 慢漂（正弦，相对幅度）
    "drift_period_frames": 90.0,
    "noise_m": 0.0,             # 逐帧高斯噪声 σ（米）
    "outlier_frac": 0.0,        # 四肢离群像素占 mask 比例（必须 < 0.5 才不移动中位数）
    "outlier_delta_m": 1.5,     # 离群像素的深度差（米）
    # 前平面盒子（已知 Z 的参照物；默认位置保证落在 640x480 画幅内）
    "box": {"depth_m": 6.0, "x_m": -0.9, "size_m": 0.30, "height_m": 0.50},
    "seed": 20260813,
    "embed_frame_marker": True,  # 在 (0,0)/(0,1) 两个像素写入帧号，便于无状态 infer
}

# 人体关键点的身高比例（从脚底算起）——与 spec §4 的 mask.torso_frac/pelvis_frac 对齐：
#   躯干带 0.50→0.72 恰为 0.22 身高；骨盆带 0.44→0.56 恰为 0.12 身高
BODY_FRACTION: dict[str, float] = {
    "feet": 0.0,
    "ankle": 0.06,
    "knee": 0.28,
    "pelvis": 0.50,
    "hip": 0.50,
    "neck": 0.72,
    "shoulder": 0.72,
    "head": 0.86,
    "head_top": 1.0,
}
NECK_FRACTION = BODY_FRACTION["neck"]
PELVIS_FRACTION = BODY_FRACTION["pelvis"]
HEAD_FRACTION = BODY_FRACTION["neck"]        # 躯干以上算头/颈
PELVIS_BAND = (0.44, 0.56)                   # 0.12 身高（spec mask.pelvis_frac）
HEAD_WIDTH_RATIO = 0.45                      # 头宽 / 身宽
# 人体 mask 的"形状面积"（以 身宽×身高 为单位）：躯干 0.72 + 头 0.45*0.28
MASK_SHAPE_AREA = NECK_FRACTION + HEAD_WIDTH_RATIO * (1.0 - NECK_FRACTION)

MARKER_MAGIC = np.array([0xA5, 0x5A, 0x00], dtype=np.uint8)


class SyntheticBackend(DepthBackend):
    """解析式合成度量深度后端（无卡环境的验收通道）。

    几何（全部闭式，单位米）：
      * 地面：`Z(u,v) = min(cam_height_m / ((v + 0.5 - cy) / fy), bg_depth_m)`（v 在地平线以下）
      * 盒子：前平面 `Z = box.depth_m` 的投影矩形
      * 人体：站在地面上、深度恒为 `z_root(t)` 的前平面；像素高 = `fy * person_height_m / z`
      * 逐像素取**最近**表面（`np.minimum`）——物理上正确的深度图语义
      * 四肢离群像素：显式赋 `z + outlier_delta_m`，占比由 `outlier_frac` 控制（< 0.5）

    `infer(rgb)` 的帧号来源（按优先级）：
      1. `render_rgb(t)` 写在第 (0,0)/(0,1) 两个像素里的帧号标记（无状态）；
      2. 内部计数器（逐帧顺序调用 `infer` 时）。
    `set_frame(t)` / `reset()` 可手工控制计数器。默认噪声为 0，输出完全确定性。
    """

    name = BACKEND_SYNTHETIC

    def __init__(self, cfg: dict | None = None, **overrides: Any) -> None:
        params = dict(SYNTHETIC_DEFAULTS)
        if isinstance(cfg, dict):
            sect = cfg.get("synthetic")
            if not isinstance(sect, dict):
                # 也允许直接传一个"扁平"的合成参数表
                sect = cfg if any(k in cfg for k in ("width", "fx", "z_start_m", "cam_height_m")) else None
            if isinstance(sect, dict):
                for k, v in sect.items():
                    if k == "box" and isinstance(v, dict):
                        box = dict(SYNTHETIC_DEFAULTS["box"])
                        box.update(v)
                        params["box"] = box
                    elif k != "synthetic":
                        params[k] = v
        params.update(overrides)
        self.params = params
        self._validate(params)

        self.width = int(params["width"])
        self.height = int(params["height"])
        self.fx = float(params["fx"])
        self.fy = float(params["fy"])
        self.cx = float(params["cx"]) if params["cx"] is not None else self.width / 2.0
        self.cy = float(params["cy"]) if params["cy"] is not None else self.height / 2.0
        self.frames = max(1, int(params["frames"]))
        self.fps = float(params["fps"])
        self._t = 0
        self.last_frame_index = 0
        self.last_frame_source = "counter"
        self._geo_cache: dict[tuple[int, int], dict[str, Any]] = {}

    @staticmethod
    def _validate(p: dict) -> None:
        if int(p["width"]) < 8 or int(p["height"]) < 8:
            raise ValueError(f"width/height 太小：{p['width']}x{p['height']}")
        if float(p["fx"]) <= 0 or float(p["fy"]) <= 0:
            raise ValueError(f"fx/fy 必须 > 0，收到 {p['fx']}/{p['fy']}")
        if float(p["cam_height_m"]) <= 0:
            raise ValueError(f"cam_height_m 必须 > 0，收到 {p['cam_height_m']}")
        if float(p["person_height_m"]) <= 0 or float(p["person_width_m"]) <= 0:
            raise ValueError("person_height_m / person_width_m 必须 > 0")
        if float(p["z_start_m"]) <= 0 or float(p["z_end_m"]) <= 0:
            raise ValueError("z_start_m / z_end_m 必须 > 0（度量深度单位为米）")
        frac = float(p["outlier_frac"])
        if not (0.0 <= frac < 0.5):
            raise ValueError(
                f"outlier_frac={frac} 必须在 [0, 0.5) —— 超过一半时中位数观测会被离群值带偏，"
                "合成场景失去意义（验收 #4 的前提是 < 50%）")
        if float(p["depth_scale"]) <= 0:
            raise ValueError(f"depth_scale 必须 > 0，收到 {p['depth_scale']}")

    # -- 几何 ---------------------------------------------------------------

    def intrinsics(self, height: int | None = None, width: int | None = None) -> types.Intrinsics:
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        return types.Intrinsics(fx=self.fx, fy=self.fy,
                                cx=(self.cx if w == self.width else w / 2.0),
                                cy=(self.cy if h == self.height else h / 2.0),
                                width=w, height=h)

    def _geometry(self, height: int, width: int) -> dict[str, Any]:
        """按给定画幅算一次静态几何（地面场 + 盒子矩形），带缓存。"""
        key = (int(height), int(width))
        geo = self._geo_cache.get(key)
        if geo is not None:
            return geo
        p = self.params
        intr = self.intrinsics(key[0], key[1])
        u = (np.arange(intr.width, dtype=np.float64) + 0.5)[None, :]
        v = (np.arange(intr.height, dtype=np.float64) + 0.5)[:, None]
        x_ray = np.broadcast_to((u - intr.cx) / intr.fx, (intr.height, intr.width))
        y_ray = np.broadcast_to((v - intr.cy) / intr.fy, (intr.height, intr.width))
        cam_h = float(p["cam_height_m"])
        bg = float(p["bg_depth_m"])
        with np.errstate(divide="ignore", invalid="ignore"):
            ground = cam_h / y_ray
        ground = np.where(y_ray > 0, ground, bg)
        ground = np.minimum(ground, bg).astype(np.float64)
        # 不变量自检：地面场必须是完整的 (H, W)。历史上这里退化成 (H,1)，
        # 下游若用 depth.shape 反推几何就会把 bug 藏住（见 2026-08-13 的 w4 验收报告）。
        if ground.shape != (intr.height, intr.width):
            raise RuntimeError(
                f"内部错误：地面场形状 {ground.shape} != {(intr.height, intr.width)}")
        geo = {"intrinsics": intr, "ground": ground,
               "x_ray": x_ray, "y_ray": y_ray, "box_rect": None}
        box = p.get("box")
        if isinstance(box, dict):
            bz = float(box["depth_m"])
            bx = float(box["x_m"])
            half = float(box["size_m"]) / 2.0
            y_bottom = cam_h
            y_top = cam_h - float(box["height_m"])
            geo["box_rect"] = (intr.cx + intr.fx * (bx - half) / bz,
                               intr.cy + intr.fy * y_top / bz,
                               intr.cx + intr.fx * (bx + half) / bz,
                               intr.cy + intr.fy * y_bottom / bz)
        self._geo_cache[key] = geo
        return geo

    def z_root(self, t: int) -> float:
        """真值：第 t 帧根节点 Z（米，线性 z_start→z_end）。"""
        p = self.params
        t = int(np.clip(int(t), 0, self.frames - 1))
        if self.frames <= 1:
            return float(p["z_start_m"])
        alpha = t / (self.frames - 1)
        return float(p["z_start_m"] + (float(p["z_end_m"]) - float(p["z_start_m"])) * alpha)

    def depth_scale_at(self, t: int) -> float:
        """第 t 帧的尺度因子（`depth_scale` × 正弦慢漂）。默认恒为 1。"""
        p = self.params
        factor = float(p["depth_scale"])
        drift = float(p["drift_frac"])
        if drift:
            period = max(1e-6, float(p["drift_period_frames"]))
            factor *= 1.0 + drift * math.sin(2.0 * math.pi * int(t) / period)
        return factor

    def _project(self, x_m: float, y_m: float, z_m: float, intr: types.Intrinsics):
        return intr.cx + intr.fx * x_m / z_m, intr.cy + intr.fy * y_m / z_m

    def _pixel_bounds(self, geo: dict[str, Any], t: int) -> dict[str, Any]:
        """人体各部件的像素行/列区间（int，已裁剪到画幅内）。"""
        p = self.params
        intr: types.Intrinsics = geo["intrinsics"]
        z = max(1e-6, self.z_root(t))
        cam_h = float(p["cam_height_m"])
        body_h = float(p["person_height_m"])
        body_w = float(p["person_width_m"])
        x_c = float(p["person_x_m"])

        def _span(v0: float, v1: float, u0: float, u1: float):
            r0 = int(np.clip(math.floor(v0), 0, intr.height))
            r1 = int(np.clip(math.ceil(v1), 0, intr.height))
            c0 = int(np.clip(math.floor(u0), 0, intr.width))
            c1 = int(np.clip(math.ceil(u1), 0, intr.width))
            return slice(r0, r1), slice(c0, c1)

        v_feet = intr.cy + intr.fy * cam_h / z
        v_neck = intr.cy + intr.fy * (cam_h - NECK_FRACTION * body_h) / z
        v_top = intr.cy + intr.fy * (cam_h - body_h) / z
        u_c = intr.cx + intr.fx * x_c / z
        half_w = intr.fx * (body_w / 2.0) / z
        half_head = intr.fx * (body_w * HEAD_WIDTH_RATIO / 2.0) / z
        body_rows, body_cols = _span(v_neck, v_feet, u_c - half_w, u_c + half_w)
        head_rows, head_cols = _span(v_top, v_neck, u_c - half_head, u_c + half_head)
        # 每条手臂的像素宽：让"手臂像素 / mask 像素总数" = outlier_frac
        # mask 面积（以身体宽 u=2*half_w、身体高 H 为单位）：
        #   body = 0.72*H*u ; head = 0.45u*0.28H ; 合计 mask_shape_area*u*H
        # 两条手臂面积 = 2*arm_w*0.72H  →  arm_w = frac * mask_shape_area / (2*0.72) * u
        arm_w = (float(p["outlier_frac"]) * MASK_SHAPE_AREA / (2.0 * NECK_FRACTION)) * (2.0 * half_w)
        if arm_w > 0.0:
            arm_a = _span(v_neck, v_feet, u_c - half_w, u_c - half_w + arm_w)
            arm_b = _span(v_neck, v_feet, u_c + half_w - arm_w, u_c + half_w)
        else:  # outlier_frac == 0 → 没有离群像素（不要在像素取整后留下 1px 的假手臂）
            empty = (slice(0, 0), slice(0, 0))
            arm_a = arm_b = empty
        return {
            "z_m": z, "body_rows": body_rows, "body_cols": body_cols,
            "head_rows": head_rows, "head_cols": head_cols,
            "arms": [arm_a, arm_b], "u_c": u_c, "v_feet": v_feet, "v_top": v_top,
            "v_neck": v_neck, "half_w_px": half_w,
        }

    # -- 真值/渲染 ----------------------------------------------------------

    def analytic_depth(self, t: int = 0, *, height: int | None = None,
                       width: int | None = None) -> np.ndarray:
        """第 t 帧的**纯几何**米制深度场（无噪声、无尺度扰动），float32。

        已知像素的深度可用闭式手算比对，例如地面像素：
            `cam_height_m * fy / (v + 0.5 - cy)`
        """
        geo = self._geometry(int(height if height is not None else self.height),
                             int(width if width is not None else self.width))
        depth = geo["ground"].copy()
        rect = geo["box_rect"]
        if rect is not None:
            rows, cols = self._clip_rect(geo, rect)
            np.minimum(depth[rows, cols], float(self.params["box"]["depth_m"]),
                       out=depth[rows, cols])
        parts = self._pixel_bounds(geo, int(t))
        z = float(parts["z_m"])
        for rows, cols in ((parts["body_rows"], parts["body_cols"]),
                           (parts["head_rows"], parts["head_cols"])):
            if rows.stop > rows.start and cols.stop > cols.start:
                np.minimum(depth[rows, cols], z, out=depth[rows, cols])
        # 四肢离群像素：显式覆盖（合成场景里就是"mask 内 30% 像素深度差 1.5 m"）
        if float(self.params["outlier_frac"]) > 0.0 and self.params.get("outlier_delta_m"):
            z_out = z + float(self.params["outlier_delta_m"])
            for rows, cols in parts["arms"]:
                if rows.stop > rows.start and cols.stop > cols.start:
                    depth[rows, cols] = z_out
        return depth.astype(np.float32)

    def _clip_rect(self, geo: dict[str, Any], rect: Sequence[float]):
        intr: types.Intrinsics = geo["intrinsics"]
        u0, v0, u1, v1 = rect
        r0 = int(np.clip(math.floor(v0), 0, intr.height))
        r1 = int(np.clip(math.ceil(v1), 0, intr.height))
        c0 = int(np.clip(math.floor(u0), 0, intr.width))
        c1 = int(np.clip(math.ceil(u1), 0, intr.width))
        return slice(r0, r1), slice(c0, c1)

    # -- 覆盖层位置（显式给出，便于交叉验证，不要靠 depth.shape 反推）---------

    def ground_depth_at(self, u: float, v: float, *, height: int | None = None,
                        width: int | None = None) -> float:
        """闭式地面深度（米）：`cam_height_m / ((v + 0.5 - cy) / fy)`，地平线以上返回 bg。"""
        intr = self.intrinsics(height, width)
        y = (float(v) + 0.5 - intr.cy) / intr.fy
        if y <= 0:
            return float(self.params["bg_depth_m"])
        return float(min(float(self.params["cam_height_m"]) / y, float(self.params["bg_depth_m"])))

    def box_rect_px(self, *, height: int | None = None,
                    width: int | None = None) -> tuple[float, float, float, float] | None:
        """盒子可见前平面的像素矩形 `(u0, v0, u1, v1)`；无盒子返回 None（未裁剪到画幅）。"""
        geo = self._geometry(int(height if height is not None else self.height),
                             int(width if width is not None else self.width))
        return geo["box_rect"]

    def person_rect_px(self, t: int = 0, *, height: int | None = None,
                       width: int | None = None) -> tuple[float, float, float, float]:
        """人体外接矩形 `(u0, v0, u1, v1)`（未裁剪到画幅；含头）。"""
        geo = self._geometry(int(height if height is not None else self.height),
                             int(width if width is not None else self.width))
        parts = self._pixel_bounds(geo, int(t))
        u_c, half = parts["u_c"], parts["half_w_px"]
        return (u_c - half, parts["v_top"], u_c + half, parts["v_feet"])

    def arm_rects_px(self, t: int = 0, *, height: int | None = None,
                     width: int | None = None) -> list[tuple[int, int, int, int]]:
        """四肢离群像素的两个矩形 `(r0, r1, c0, c1)`（已裁剪；`outlier_frac=0` 时宽度为 0）。"""
        geo = self._geometry(int(height if height is not None else self.height),
                             int(width if width is not None else self.width))
        parts = self._pixel_bounds(geo, int(t))
        return [(r.start, r.stop, c.start, c.stop) for r, c in parts["arms"]]

    def outlier_fraction_realized(self, t: int = 0, *, height: int | None = None,
                                  width: int | None = None) -> float:
        """实测的离群像素占 mask 比例（像素取整后与 `outlier_frac` 略有出入，这里给真值）。"""
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        mask = self.render_mask(int(t), height=h, width=w)
        total = int(mask.sum())
        if total == 0:
            return 0.0
        depth = self.analytic_depth(int(t), height=h, width=w)
        base = float(self.z_root(int(t)))
        outliers = mask & (depth > base + 0.5 * float(self.params["outlier_delta_m"]))
        return float(outliers.sum()) / float(total)

    def reference_points(self, t: int = 0, *, height: int | None = None,
                         width: int | None = None) -> list[dict[str, Any]]:
        """已知深度的采样点（像素 + 解析期望值），供交叉验证用。

        每个点是 `{"name", "uv" (u,v int), "expected_m", "source"}`；`source` 说明期望值
        来自哪个闭式（地面 / 人体 / 盒子），与实现里的覆盖顺序无关。
        """
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        geo = self._geometry(h, w)
        intr: types.Intrinsics = geo["intrinsics"]
        parts = self._pixel_bounds(geo, int(t))
        pts: list[dict[str, Any]] = []

        # 1) 地面：右下角（远离人体与盒子）
        u_g, v_g = intr.width - 3, intr.height - 3
        pts.append({"name": "ground_bottom_right", "uv": (u_g, v_g),
                    "expected_m": self.ground_depth_at(u_g, v_g, height=h, width=w),
                    "source": "cam_height/((v+0.5-cy)/fy)"})
        # 2) 人体躯干中心（0.61 身高处，避开两侧手臂带）
        z = float(parts["z_m"])
        y_torso = float(self.params["cam_height_m"]) - 0.61 * float(self.params["person_height_m"])
        u_p, v_p = parts["u_c"], intr.cy + intr.fy * y_torso / z
        pts.append({"name": "person_torso_center", "uv": (int(round(u_p)), int(round(v_p))),
                    "expected_m": z, "source": "z_root(t)"})
        # 3) 盒子前平面中心
        rect = geo["box_rect"]
        if rect is not None:
            u_b, v_b = (rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0
            pts.append({"name": "box_front_center", "uv": (int(round(u_b)), int(round(v_b))),
                        "expected_m": float(self.params["box"]["depth_m"]),
                        "source": "box.depth_m"})
        # 4) 四肢离群像素中心
        if float(self.params["outlier_frac"]) > 0.0:
            for i, (r0, r1, c0, c1) in enumerate(self.arm_rects_px(int(t), height=h, width=w)):
                if r1 > r0 and c1 > c0:
                    pts.append({"name": f"limb_outlier_{i}", "uv": ((c0 + c1) // 2, (r0 + r1) // 2),
                                "expected_m": z + float(self.params["outlier_delta_m"]),
                                "source": "z_root(t)+outlier_delta_m"})
        return pts

    def _depth_field(self, t: int, height: int, width: int) -> np.ndarray:
        """`analytic_depth` + 尺度/慢漂 + 噪声（`infer` 实际返回的那一份）。"""
        field = self.analytic_depth(int(t), height=height, width=width).astype(np.float64)
        factor = self.depth_scale_at(int(t))
        if factor != 1.0:
            field = field * factor
        noise = float(self.params["noise_m"])
        if noise > 0.0:
            rng = np.random.default_rng(int(self.params["seed"]) + int(t))
            field = field + rng.normal(0.0, noise, size=field.shape)
        return np.maximum(field, 0.0).astype(np.float32)

    def render_mask(self, t: int = 0, *, height: int | None = None,
                    width: int | None = None) -> np.ndarray:
        """人体 Mask（bool），含头/躯干/四肢——四肢像素就是注入的离群深度像素。"""
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        geo = self._geometry(h, w)
        parts = self._pixel_bounds(geo, int(t))
        mask = np.zeros((h, w), dtype=bool)
        for rows, cols in ((parts["body_rows"], parts["body_cols"]),
                           (parts["head_rows"], parts["head_cols"])):
            mask[rows, cols] = True
        return mask

    person_mask = render_mask

    def render_keypoints_px(self, t: int = 0, *, height: int | None = None,
                            width: int | None = None) -> dict[str, tuple[float, float]]:
        """关键点（像素坐标，浮点）。`neck → pelvis` 的像素长就是 spec 的 `torso_px`。"""
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        geo = self._geometry(h, w)
        intr: types.Intrinsics = geo["intrinsics"]
        p = self.params
        z = max(1e-6, self.z_root(int(t)))
        cam_h = float(p["cam_height_m"])
        body_h = float(p["person_height_m"])
        x_c = float(p["person_x_m"])
        half_shoulder = float(p["person_width_m"]) * 0.42
        half_hip = float(p["person_width_m"]) * 0.30

        def pt(frac: float, dx: float = 0.0):
            return self._project(x_c + dx, cam_h - frac * body_h, z, intr)

        kp: dict[str, tuple[float, float]] = {
            "feet": pt(BODY_FRACTION["feet"]),
            "pelvis": pt(PELVIS_FRACTION),
            "neck": pt(NECK_FRACTION),
            "head": pt(BODY_FRACTION["head"]),
            "head_top": pt(BODY_FRACTION["head_top"]),
        }
        for side, sign in (("l", -1.0), ("r", 1.0)):
            kp[f"shoulder_{side}"] = pt(BODY_FRACTION["shoulder"], sign * half_shoulder)
            kp[f"hip_{side}"] = pt(BODY_FRACTION["hip"], sign * half_hip)
            kp[f"knee_{side}"] = pt(BODY_FRACTION["knee"], sign * half_hip * 0.8)
            kp[f"ankle_{side}"] = pt(BODY_FRACTION["ankle"], sign * half_hip * 0.6)
        # 常见别名（别家代码可能用这些键名）
        kp["left_shoulder"], kp["right_shoulder"] = kp["shoulder_l"], kp["shoulder_r"]
        kp["left_hip"], kp["right_hip"] = kp["hip_l"], kp["hip_r"]
        kp["left_knee"], kp["right_knee"] = kp["knee_l"], kp["knee_r"]
        kp["left_ankle"], kp["right_ankle"] = kp["ankle_l"], kp["ankle_r"]
        kp["root"] = kp["pelvis"]
        return kp

    def render_rgb(self, t: int = 0, *, height: int | None = None,
                   width: int | None = None) -> np.ndarray:
        """生成 (H,W,3) uint8 的假 RGB 帧（含帧号标记像素，供无状态 `infer` 使用）。"""
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        depth = self.analytic_depth(int(t), height=h, width=w).astype(np.float64)
        g = np.clip(255.0 - depth * 8.0, 40.0, 235.0).astype(np.uint8)
        img = np.empty((h, w, 3), dtype=np.uint8)
        img[..., 0] = np.clip(g.astype(np.int16) - 30, 0, 255).astype(np.uint8)
        img[..., 1] = g
        img[..., 2] = np.clip(g.astype(np.int16) - 60, 0, 255).astype(np.uint8)
        geo = self._geometry(h, w)
        rect = geo["box_rect"]
        if rect is not None:
            rows, cols = self._clip_rect(geo, rect)
            img[rows, cols] = (70, 90, 205)
        mask = self.render_mask(int(t), height=h, width=w)
        img[mask] = (205, 170, 145)
        if bool(self.params.get("embed_frame_marker", True)) and h > 1 and w > 2:
            idx = int(t) % 65536
            img[0, 0] = (idx & 0xFF, (idx >> 8) & 0xFF, 0xFF)
            img[0, 1] = MARKER_MAGIC
        return img

    def frame_bundle(self, t: int = 0, *, height: int | None = None,
                     width: int | None = None) -> dict[str, Any]:
        """一帧的全套合成真值：rgb / mask / keypoints / depth / 真值 Z。"""
        h = int(height if height is not None else self.height)
        w = int(width if width is not None else self.width)
        return {
            "frame": int(t),
            "rgb": self.render_rgb(int(t), height=h, width=w),
            "mask": self.render_mask(int(t), height=h, width=w),
            "keypoints_px": self.render_keypoints_px(int(t), height=h, width=w),
            "depth": self.analytic_depth(int(t), height=h, width=w),
            "z_truth_m": self.z_root(int(t)),
            "intrinsics": self.intrinsics(h, w),
        }

    # -- 帧号 ---------------------------------------------------------------

    def set_frame(self, t: int) -> None:
        self._t = int(t)

    def reset(self) -> None:
        self._t = 0

    def _read_frame_marker(self, arr: np.ndarray) -> int | None:
        if arr.shape[0] > 1 and arr.shape[1] > 1 and np.array_equal(arr[0, 1], MARKER_MAGIC):
            return int(arr[0, 0, 0]) | (int(arr[0, 0, 1]) << 8)
        return None

    # -- 接口 ---------------------------------------------------------------

    @property
    def kind(self) -> str:
        return types.KIND_METRIC

    def describe(self) -> dict[str, Any]:
        p = self.params
        return {
            "name": self.name,
            "kind": self.kind,
            "unit": "m",
            "frames": self.frames,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "cam_height_m": float(p["cam_height_m"]),
            "z_start_m": float(p["z_start_m"]),
            "z_end_m": float(p["z_end_m"]),
            "depth_scale": float(p["depth_scale"]),
            "drift_frac": float(p["drift_frac"]),
            "noise_m": float(p["noise_m"]),
            "outlier_frac": float(p["outlier_frac"]),
            "outlier_delta_m": float(p["outlier_delta_m"]),
            "note": "解析式合成真值；无物理模型、无推理",
        }

    def infer(self, rgb: np.ndarray) -> types.DepthMap:
        """对一帧做"推理"：返回解析式米制深度（形状与输入一致）。"""
        arr = _as_uint8_rgb(rgb)
        h, w = arr.shape[:2]
        marked = self._read_frame_marker(arr)
        if marked is not None:
            t, source = marked, "marker"
        else:
            t, source = self._t, "counter"
        depth = self._depth_field(t, h, w)
        if depth.shape != (h, w):
            raise RuntimeError(
                f"内部错误：合成深度形状 {depth.shape} != 输入画幅 {(h, w)}")
        self.last_frame_index = int(t)
        self.last_frame_source = source
        self._t = int(t) + 1
        return types.DepthMap(depth=depth, kind=types.KIND_METRIC, unit="m",
                              backend=BACKEND_SYNTHETIC)


# ---------------------------------------------------------------------------
# 工厂


def _is_synthetic_kind(kind: str) -> bool:
    return str(kind).lower() in ("synthetic", "synth", "fake")


def load(cfg: dict | None = None) -> DepthBackend:
    """按 cfg 构造后端（spec §3 冻结签名）。

    * 默认走真后端 `DepthAnythingV2Metric`：缺 torch / 缺权重 / 显式要 CUDA 但没有 CUDA
      → 抛 `types.BackendUnavailable`。**不会**自动下载权重，**不会**静默回退。
    * `cfg["backend"]["kind"] == "synthetic"` 时返回 `SyntheticBackend`（显式选择）。

    调用方若想在无卡环境自动降级，请显式使用 `load_with_fallback(cfg)`，
    它会把降级原因一并返回（不静默）。
    """
    merged = types.merge_cfg(cfg)
    b = dict(merged.get("backend", {}))
    kind = str(b.get("kind", "da_v2")).lower()
    if _is_synthetic_kind(kind):
        return SyntheticBackend(merged)
    if kind not in ("da_v2", "da_v2_metric", "metric", "auto"):
        raise types.BackendUnavailable(
            f"未知 backend.kind={kind!r}（可选 'da_v2'（默认）/ 'synthetic'）")
    return DepthAnythingV2Metric.from_cfg(merged)


def load_with_fallback(cfg: dict | None = None) -> tuple[DepthBackend, str]:
    """先试真后端；`BackendUnavailable` 时**显式**回退 `SyntheticBackend`。

    返回 `(backend, reason)`；`reason == ""` 表示真后端可用。
    """
    try:
        return load(cfg), ""
    except types.BackendUnavailable as exc:
        merged = types.merge_cfg(cfg)
        return SyntheticBackend(merged), str(exc)


def make_synthetic(cfg: dict | None = None, **overrides: Any) -> SyntheticBackend:
    """便捷构造 `SyntheticBackend`（cfg 里的 `synthetic` 段 + 关键字覆盖）。"""
    return SyntheticBackend(types.merge_cfg(cfg), **overrides)
