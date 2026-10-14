# 单目动捕的「度量深度先验」框架 — 设计与接口契约

> 目标：给 FastSAM3DBody（FSB）前端补一路**度量深度**先验，约束根节点 Z（相机系前后/竖直漂移），
> 产出可被 FSB→`hand_body_merge.py`→Blender 这条链路直接消费的 `root_z` 轨道。
>
> **不含推理**：本框架只负责"接上模型 + 融合 + 滤波 + 产出契约"，
> 权重在仓库根 `depth_anything_v2_metric_hypersim_vits.pth`，跑不跑得动由调用方决定；
> 没有 torch/GPU 时走 `SyntheticBackend`，全部测试用合成真值，**零推理可验**。

## 0 铁律：只用度量深度，不用相对深度

- 相对深度模型的输出是仿射不变的（每帧 Min/Max 由画面最近/最远物体决定）。
  人挥手、踢腿、画面边缘一变，同一位置的深度数值就跳 —— **Z 轴会漂得更怪**。
- 所以本框架的**唯一主先验**是 `Depth Anything V2 Metric-Small`（ViT-S，Hypersim-metric 头），
  输出单位是**米**、尺度绝对锚定。
- `backend.load()` 必须显式声明 `kind`：
  - `kind="metric"` → 允许进入融合主项；
  - `kind="relative"` → **只允许**走 `priors.affine_align_to_metric()`（帧间仿射对齐到某个绝对锚点）
    **或**被拒绝；`fusion` 对 relative 输入必须 `raise`，不许静默当米用。

## 1 数据流

```
视频帧 / 帧目录
   │
   ├─(A) backend.py ────────► DepthMap(kind="metric", depth_m HxW 米)
   │
   ├─(B) masks.py ──────────► 人体 Mask（复用 FSB/SAM 的 person mask）
   │                            └► torso/pelvis 区域 → 中位数 → Z_depth（米）
   │
   ├─(C) priors.py ─────────► 2D 躯干像素长 → 透视粗先验 Depth ∝ 1/躯干px
   │
   ├─(D) fusion.py ─────────► 逐帧根节点 Z：主项=Z_depth，粗项=躯干透视，鲁棒加权
   │
   ├─(E) filters.py ────────► One-Euro 时序滤波（慢速强平滑 / 快速低延迟）
   │
   └─(F) cli.py / pipeline ─► depth_prior.npz（root_z 轨道 + 置信度 + 诊断）
```

**(D) 为什么两项互补**：度量深度给绝对锚定但逐帧有噪声；躯干像素长是零成本、单调但只是相对量。
用躯干先验做**慢变（低频）一致性检查**、用度量中位数做**绝对锚定**，两者残差超阈值就报警。

**(E) 为什么 One-Euro**：慢速移动时强平滑（消灭原地抖动），快速移动时低延迟（不拖累跑跳）。
不用普通低通——那会把落地/出拳的响应一起抹平。

## 2 模块与写作用域（互不重叠）

| 文件 | 负责 | 说明 |
|---|---|---|
| `depth_prior/spec.md`、`types.py`、`README.md` | **Lead** | 契约，别人不许改 |
| `depth_prior/backend.py`、`model/`、`cli.py` | w1 | DA V2 适配 + 合成后端 + 命令行 |
| `depth_prior/masks.py`、`priors.py` | w2 | Mask 取深度 + 躯干透视先验 |
| `depth_prior/fusion.py`、`filters.py` | w3 | 融合求解 + One-Euro |
| `depth_prior/tests/` | w4 | 合成真值测试（对着 spec 写，可与实现并行） |

`types.py` 是唯一共享的接口文件，**由 Lead 冻结**；worker 需要新字段就在 `agent_reports/` 里提，别改它。

> ⚠️ **`depth_prior/types.py` 会遮蔽标准库 `types`**：只要把 `depth_prior/` 目录本身塞进
> `sys.path`，连 `import numpy` 都会炸（`ImportError: cannot import name 'MappingProxyType' from 'types'`）。
> 正确用法只有一种：**从仓库根** `import depth_prior.xxx` / `python -m depth_prior.tests.run_tests`。
> 别写把 `depth_prior/` 加进 `sys.path` 的 conftest / 启动脚本。

## 3 接口契约（`types.py`，冻结）

```python
@dataclass(frozen=True)
class Intrinsics:            # 像素
    fx: float; fy: float; cx: float; cy: float
    width: int; height: int

@dataclass
class DepthMap:
    depth: np.ndarray        # (H, W) float32
    kind: str                # "metric" | "relative"
    unit: str                # "m" | "normalized"
    backend: str             # "da_v2_metric_vits" | "synthetic" | ...

@dataclass
class RegionStat:
    name: str                # "torso" | "pelvis"
    frac: float              # 该区域占画面比例
    px: int                  # 像素数
    depth_median_m: float
    depth_p10_m: float
    depth_p90_m: float
    iqr_m: float             # p90-p10，用来判可信度

@dataclass
class FramePrior:
    frame: int
    depth_median_m: float    # 根节点 Z 的度量观测（米）
    iqr_m: float
    torso_px: float          # 2D 躯干像素长（颈→骨盆）
    perspective_m: float     # 由躯干像素长推的粗相对深度（任意尺度，仅供平滑项）
    mask_frac: float
    valid: bool
    reason: str              # 不可信的原因

@dataclass
class FilterDiag:
    name: str
    min_cutoff: float; beta: float; d_cutoff: float
    lag_frames_p50: float    # 阶跃响应延迟（帧）
    residual_rms_m: float    # 滤波前后残差

@dataclass
class RootZTrack:
    frames: np.ndarray       # (T,) int
    z_raw_m: np.ndarray      # (T,) 融合后、滤波前
    z_m: np.ndarray          # (T,) 滤波后
    confidence: np.ndarray   # (T,) 0..1
    diag: dict               # 含 FilterDiag、报警、超参
```

**函数签名（冻结）**

```python
# backend.py
def load(cfg) -> DepthBackend                     # 惰性 import torch；缺依赖抛 BackendUnavailable
class DepthBackend:
    def infer(self, rgb: np.ndarray) -> DepthMap  # rgb (H,W,3) uint8
    @property
    def kind(self) -> str                         # 必须 "metric"，否则 fusion 拒绝

# masks.py
def torso_pelvis_stats(depth: DepthMap, mask: np.ndarray,
                       keypoints_px: dict | None, cfg) -> list[RegionStat]

# priors.py
def torso_px_length(keypoints_px: dict, cfg) -> float | None   # 颈→骨盆像素长
def perspective_prior(torso_px: float, ref_px: float, ref_z_m: float) -> float
def affine_align_to_metric(rel: np.ndarray, anchors: np.ndarray,
                           anchor_depth_m: np.ndarray) -> tuple[float, float]

# fusion.py
def fuse(frames: list[FramePrior], cfg) -> tuple[np.ndarray, np.ndarray]
    # -> (z_raw_m, confidence)，relative 输入必须 raise

# filters.py
def one_euro(x: np.ndarray, *, fps: float, min_cutoff: float, beta: float,
             d_cutoff: float) -> tuple[np.ndarray, FilterDiag]
```

## 4 参数（`cfg`，全部可覆盖，不许硬编码在函数里）

| 键 | 默认 | 含义 |
|---|---|---|
| `backend.weights` | 仓库根 `depth_anything_v2_metric_hypersim_vits.pth` | 权重路径 |
| `backend.encoder` | `vits` | DA V2 编码器 |
| `backend.max_depth` | `20.0` | Hypersim-metric 头的最大深度（米） |
| `backend.input_size` | `518` | 推理边长 |
| `mask.torso_frac` | `0.22` | 躯干椭圆相对人体框的高占比 |
| `mask.pelvis_frac` | `0.12` | 骨盆带高占比 |
| `mask.min_px` | `400` | 少于这么多像素判不可信 |
| `fusion.iqr_max_m` | `0.35` | IQR 超此值降权 |
| `fusion.torso_tol` | `0.25` | 度量 vs 躯干透视的相对偏差报警阈值 |
| `fusion.w_depth` / `w_persp` | `1.0` / `0.15` | 两项权重 |
| `filter.min_cutoff` | `0.8` | One-Euro 慢速截止（Hz） |
| `filter.beta` | `0.02` | 速度系数（**见 §5.6 的偏离说明**） |
| `filter.d_cutoff` | `1.0` | 微分截止（Hz） |

## 5 验收（w4 负责，全部合成真值，无推理）

1. **度量契约**：`load()` 在无 torch 时抛 `BackendUnavailable` 而不是 `ImportError` 裸奔；
   `SyntheticBackend(kind="metric")` 能跑通全链路。
2. **拒绝相对深度**：伪造 `kind="relative"` 的 DepthMap 进 `fusion.fuse` → 必须 raise（回归测试，防退化）。
3. **尺度锚定**：合成场景里根节点 Z 从 3.0 m 走到 5.0 m，`z_raw_m` 的最大误差 < 2%；
   把整体深度乘 2 再喂进去（模拟"尺度漂了"）→ 必须报警且不静默通过。
4. **中位数抗离群**：Mask 内塞 30% 的四肢离群像素（深度差 1.5 m）→ 中位数观测偏移 < 0.05 m。
5. **躯干透视互补**：给度量项注入 ±8% 慢漂 → 融合后用躯干项把慢漂压到 < 3%。
6. **One-Euro 行为**：静止段残余抖动 RMS 比输入降 > 60%；
   阶跃响应延迟 < 3 帧（fps=30）；且**不得**比普通低通更慢。

   > ⚠️ **对标准 One-Euro 的刻意偏离（w3 发现，Lead 拍板保留）**
   > 论文原式 `cutoff = min_cutoff + beta·|dx|` 在**米制** Z 下会退化：
   > 走路 1–2 m/s、`beta=0.02` 只把截止抬高 0.0001–0.04 Hz，
   > 于是等效成固定 0.8 Hz 低通，50% 上升时间 = 0.693τ ≈ **4.1 帧 > 3 帧**，
   > 与本条验收**数学上互斥**（§4 的参数表原本就不自洽，是 spec 的错，不是实现的错）。
   > 现在 `filters.py` 把速度项**按信号自身的导数噪声基线归一化**（分母由粗糙度解析推出）
   > 并加幂次响应曲线，`beta=0` 仍**严格**退化为普通一阶低通（逐点相同，3e-15）。
   > 因此实现**不是**逐字的论文 One-Euro，而是保留其设计意图（慢速强平滑 / 快速低延迟）
   > 的带单位变体。**不要把它当成标准 One-Euro 引用。**
   > 实测：静止降抖 71.3%（mean，10 seeds）、阶跃 lag **0 帧** vs 同截止低通 **4 帧**、
   > 2 m/s 斜坡跟随误差 0.0077 m vs 低通 0.3973 m。

7. **端到端**：`cli.py --synthetic` 生成 `depth_prior.npz`，字段与 `RootZTrack` 一致，可被重新读回。

## 6 已知限制（写清楚，别假装没有）

1. **均匀尺度漂移内部检测不了 —— 但对本案的用途没有影响，不用当限制看。**
   （技术事实：整张深度图统一乘常数 `k` 时，主项与粗项一起被缩放，`q = z/p` 不变，
   框架判"无漂移"。`--depth-scale 2.0` 实测 confidence 仍 1.000。）
   **为什么无所谓**：我们要的是**帧间尺度稳定**（同一身体位置跨帧不跳、
   慢漂能看出来），**不是绝对米制准确**。`k` 在漂移检测里自己约掉——
   漂移是 `q` 的**相对变化**，常数因子不参与。相对深度之所以被排除（§0），
   是因为它**每帧**都在变尺度 ✗，而不是因为它不是米。
   → 真正承重的是"整条片子一个常数尺度"，DA V2 Metric 满足它 ✓。
   **唯一会显形的地方**：把 `z_raw` 整体替换根节点 Z 时，`k` 会按比例缩放前后移动幅度。
   实测 `k ≈ 1`（真实 take：躯干中位数 8.32–8.65 m，深度 2.16–10.42 m，合乎物理），
   所以不是活的问题；真要较真，一次已知身高校准即可锁死
   （`fusion.anchor_z_m=` 已实现；`fusion.external_scale_m` 仍是待办登记）。
   **只有"配错还自信满满"这一类才值得防**：`max_depth` 填错会带着高置信度输出错尺度
   ——接真实数据时拿已知身高对一次即可。

   **推论（w3 实测）**：慢漂校正锚在 `q = z/p` 的中位数上，所以**残留是一个常数尺度偏置**。
   对称漂移（sin、`linspace(-8%,+8%)`）残留 ≈ 1.1–1.5% ✓；
   **单调** `linspace(0,+8%)` 残留 **4.69%** ✗ —— 这是"粗项不提供绝对锚点"的必然结果，
   任何相对方法都做不到 <3%（除非把粗项当绝对量，那违反 §0 铁律）。
   要处理单调漂移就得给 `fusion.anchor_z_m=`（w3 已实现该 kwarg）。

2. **CLI 的 diag 里目前只带 CLI 自己的 alarms**：`fusion.fuse_detailed()` 的
   `scale_offset` / `torso_mismatch` 等**没有合并进 npz 的 `diag["alarms"]`**。
   API 层面没有静默（`fuse_detailed` 与 `fusion.LAST_ALARMS` 都拿得到），
   但产物 npz 上会漏。**待办：`cli.py` 加两行合并即可**（w1 的作用域）。

2. ~~真实模型未跑过推理~~ → **2026-10-10 已在云端（AutoDL，无卡 CPU）跑通真推理**，
   细节与复现命令见 `SETUP_CLOUD.md`。结论两条，都要记住：
   - ✅ **走官方实现**（`cfg["backend"]["official_path"]` 指向 Depth-Anything-V2 仓库的
     `metric_depth/`）：`strict load OK (missing=[] unexpected=[])`，真实 take 帧跑出
     **min 2.16 / p50 6.3–6.8 / max 10.4 m** 的合理米制深度；端到端 10 帧躯干中位数
     8.32–8.65 m 稳定。
   - ❌ **自研 `model/dpt.py` 前向数值不对**：它能严格加载权重（239 键全对、张量逐位相同），
     但特征逐层爆炸（block11 ±34.9 → 过 LN 后 ±99），head 原始输出恒 ≤0，
     经 ReLU 后**整张图全 0**。已修一处真 bug（`get_intermediate_layers` 的
     `(cls, patches)` 顺序应为 `(patches, cls)`），修完仍全 0 ⇒ 还有更深的问题，
     **未继续纠，一律用官方实现**。自研实现只当没有官方代码时的占位。
   - 仍未验证：`cv2.resize` 与 torch bilinear 的等价性、CUDA 路径（无卡模式）、
     真实 FSB/SAM mask（端到端用的是随手画的椭圆，所以 `conf` 只有 0.078、
     并正确报出 `perspective_unavailable` —— 见 §5 的置信度设计在真实数据上生效了）。

3. **真实 FSB/SAM 的接口未联调**：关键点命名、mask 来源只用合成数据验过。
   真实链路要接时，先确认 `keypoints_px` 的键名（`masks.resolve_keypoint` 支持别名与
   左右肩/髋中点退化），拿不到关键点会退化成"人体框上部"的带（精度降、不崩）。

4. **不做的事**：不下载权重、不跑真模型、不碰 `mocap_doctor/` 的 Blender 扩展、
   不把相对深度当米用、不做逐帧 Min/Max 归一化后拿人体像素当深度。

