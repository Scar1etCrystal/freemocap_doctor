# 云端搭建清单（AutoDL，2026-10-10 实测跑通）

本框架在**本地无卡**也能跑（`SyntheticBackend`，15 条测试全绿），
但**真模型推理必须在有 torch 的机器上跑**。这份记录云端到底装了什么、放哪、怎么跑，
数据盘（`autodl-tmp`）关机不丢，下次直接照着复现。

## 那台机器

```
ssh -p 28602 root@connect.westd.seetacloud.com
容器: autodl-container-p59d40xzu4-78285282   磁盘: /root/autodl-tmp 50G
```

**无卡模式**（`nvidia-smi -L` 为空 → `torch.cuda.is_available()=False`），所以推理走 CPU。
实测速度：ViT-S @518×518 **约 27–32 秒/帧**（宿主负载 10–19，被挤占）。

## 已经装好的四样东西

| 放哪 | 是什么 | 怎么来的 |
|---|---|---|
| `/root/autodl-tmp/depth_prior/` | 本框架整套代码 | 从本机 `pscp` 上传 |
| `/root/autodl-tmp/depth_anything_v2_metric_hypersim_vits.pth` | 权重 99.2 MB | 从本机 `pscp` 上传（本机仓库根有一份） |
| `/root/autodl-tmp/Depth-Anything-V2-main/metric_depth/` | **官方** DA V2 度量实现 | `curl -sL https://github.com/DepthAnything/Depth-Anything-V2/archive/refs/heads/main.tar.gz` 解开 |
| `/root/autodl-tmp/envs/fast_sam_3d_body/bin/python` | 环境：**torch 2.5.1+cu124**、numpy 1.26.4、cv2 5.0.0、pillow 10.3.0、timm 1.0.30 | FSB 那套现成的，直接用，**没另装任何东西** |

> ⚠️ 官方仓库根目录的 `depth_anything_v2/dpt.py` 是**相对深度**版（构造没有 `max_depth`）。
> **度量版在 `metric_depth/` 子目录下**，必须用那个。

## 怎么跑

```bash
cd /root/autodl-tmp
OFFICIAL=/root/autodl-tmp/Depth-Anything-V2-main/metric_depth
OMP_NUM_THREADS=8 /root/autodl-tmp/envs/fast_sam_3d_body/bin/python -u - <<'PY'
import sys, numpy as np, torch
from PIL import Image
sys.path.insert(0, "/root/autodl-tmp")
from depth_prior import types, backend as B
cfg = types.merge_cfg({"backend": {
    "weights": "/root/autodl-tmp/depth_anything_v2_metric_hypersim_vits.pth",
    "official_path": "/root/autodl-tmp/Depth-Anything-V2-main/metric_depth"}})
be = B.load(cfg); print("impl =", be.impl)          # → official
img = np.asarray(Image.open("/root/autodl-tmp/fsb_work/frames_t999/00020.jpg").convert("RGB"))
dm = be.infer(img)
print(dm.kind, dm.unit, dm.depth.shape, float(np.median(dm.depth)))
PY
```

`official_path` 就是 `types.DEFAULT_CFG["backend"]["official_path"]` 那个键。
**填了就用官方实现；留空才退回自研的 `model/dpt.py`（前向数值不对，见下）。**

现成的两个脚本（已上传在 `/root/autodl-tmp/depth_prior/`）：
- `cloud_pipeline.py` —— 端到端：官方后端 → Mask 中位数 → 融合 → One-Euro → 写 `RootZTrack.npz`
- `official_smoke.py` —— 只用官方实现跑 3 帧，确认米制深度正常

## 实测结果（2026-10-10）

```
strict load OK (missing=[] unexpected=[])      官方实现与权重严格吻合
00020.jpg  min=2.333 p50=6.655 max=9.957 m     中心带 p50=6.739 m
00126.jpg  min=2.276 p50=6.801 max=9.638 m     中心带 p50=7.714 m
00233.jpg  min=2.277 p50=6.427 max=10.425 m    中心带 p50=6.407 m
```

端到端 10 帧（`fsb_work/frames_t999/`）：躯干中位数 8.32–8.65 m（稳定）
→ 融合 `z_raw` 同区间 → One-Euro 后 8.33–8.48 m → `RootZTrack` 往返正常。

## ⚠️ 自研 `model/dpt.py` 前向有 bug（云端抓到的）

它**能严格加载**权重（239 键逐一对上、抽查张量完全相同），但**前向数值不对**：

- 特征逐层爆炸：`block[11]` ±34.9，过最终 LayerNorm 后 `±99`、`|mean|=2.33`
  （正常应接近零均值单位方差）
- `depth_head` 原始输出**恒 ≤ 0** → 最后那层 `ReLU` → **整张图全 0**
- 权重本身没问题（与官方对比逐键相同）：**是前向实现的问题**，不是加载问题

已修的一处（真 bug）：`get_intermediate_layers(return_class_token=True)` 曾返回
`(cls, patches)`，而官方与 head 的约定是 **`(patches, cls)`** —— patch 必须在前。
这个修完前向才能跑，但**修完仍然是全 0** ⇒ 还有更深的问题，未继续纠（改用官方实现）。

**结论：真推理一律用 `official_path` 指向官方实现；自研实现只当没有官方代码时的占位。**
