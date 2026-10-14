# depth_prior — 单目动捕的度量深度先验

给 **FastSAM3DBody（FSB）** 前端补一路深度先验，约束根节点 **Z 轴**的漂移
（前/后、竖直方向的慢慢跑偏），最后交给 `hand_body_merge.py` → Blender 那条链路。

**当前状态：框架 + 契约 + 合成验收（15/15 全绿）+ 云端真模型跑通。**

真推理走**官方** Depth-Anything-V2 度量实现：把 `cfg["backend"]["official_path"]`
指向它仓库的 `metric_depth/` 目录即可；留空才退回自研的 `model/dpt.py`
（**那个前向数值不对、输出全 0，别用**）。
云端装了什么、放哪、怎么跑、实测数字 → 见 [`SETUP_CLOUD.md`](SETUP_CLOUD.md)。
权重 `depth_anything_v2_metric_hypersim_vits.pth` 在仓库根（99 MB）。

## 为什么不能用相对深度

相对深度模型的输出是**仿射不变**的：每帧的 Min/Max 取决于画面里最近和最远的物体。
人一挥手、一踢腿，或者镜头边缘稍微变一点，同一位置的深度数值就跳。
直接逐帧拿它约束 Z，**Z 会漂得更怪**，不是更稳。

所以本框架的立身之本是：

1. **主先验 = 度量深度**（Depth Anything V2 **Metric-Small**，Hypersim-metric 头），
   输出单位是米、尺度绝对锚定。
2. **取躯干/骨盆区域的深度中位数**，不是拿人体像素值当深度——
   中位数天然滤掉四肢大幅摆动带来的深度离群点。
3. **2D 躯干像素长做粗项**：`Depth ∝ 1/躯干像素长`（小孔成像），零计算开销，
   只用来做**慢变**一致性约束，不是绝对量。
4. **One-Euro 滤波**收尾：慢速时强平滑（消灭原地抖动），快速时低延迟（不拖累跑跳）。

## 目录

| 文件 | 作用 |
|---|---|
| `spec.md` | 设计与验收标准（**先读这个**） |
| `types.py` | 冻结契约：数据结构 + 默认参数表（全框架共用） |
| `backend.py` | DA V2 Metric-Small 适配 + `SyntheticBackend`（无卡验收用） |
| `masks.py` | SAM/FSB 人体 Mask → 躯干/骨盆深度中位数 |
| `priors.py` | 2D 躯干透视粗先验 + 相对深度仿射对齐（仅相对路径用） |
| `fusion.py` | 主项 + 粗项鲁棒融合，**拒绝相对深度** |
| `filters.py` | One-Euro 时序滤波 |
| `cli.py` | 命令行；`--synthetic` 可在无 GPU 下跑通全链路 |
| `tests/` | 合成真值验收（纯 unittest，不依赖 torch/GPU/pytest） |

## 跑测试（无需 GPU、无需权重）

```powershell
cd F:\mocap_ai_doctor
python -m depth_prior.tests.run_tests
```

## 跑合成链路

```powershell
python -m depth_prior.cli --synthetic --out depth_prior.npz
```

产出的 `.npz` 字段与 `types.RootZTrack` 一致，可用 `RootZTrack.load()` 读回。

## 怎么接进现有链路

深度先验是在 **FSB 前端**这一步用的，不碰 `mocap_doctor/` 的 Blender 扩展：

```
视频帧 ─► [depth_prior] ─► RootZTrack(root_z) ─► FSB 根节点 Z 约束 ─► pkl ─► Blender
```

需要 FSB 侧提供：每帧的相机内参（`Intrinsics`）、人体 Mask、以及（可选）颈/骨盆的像素坐标。
拿不到关键点时 `masks.py` 会退化成"人体框上部"的带，精度下降但不会崩。
