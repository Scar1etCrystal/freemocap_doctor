# 让 HaMeR 那一步吐出"手有没有被看见"

## 为什么需要

`PoseCapture_Pack/HAMER/hamer_video.py` 的手部裁剪框**不是**手部检测器给的，而是
ViTPose 手部关键点（21 点/手）置信度 > 0.5 的那些点的外接框：

```python
for is_right, kps in ((0, vpose["keypoints"][-42:-21]), (1, vpose["keypoints"][-21:])):
    if kps[:, 2].max() <= 0.5:      # ← 这帧这只手没有可信关键点
        continue
    valid = kps[:, 2] > 0.5
    hand_cands.append({"bbox": ..., "is_right": is_right})
```

关键问题在后面：

```python
bboxes = [... for f in frame_indices]
interp_func = interp1d(frame_indices, bboxes, axis=0, kind="linear", fill_value="extrapolate")
for frame_idx in range(min(frame_indices), max(frame_indices) + 1):
    all_tasks.append({..., "bbox": interp_func(frame_idx), ...})   # ← 没检测到的帧，框是插值出来的
```

**手看不见的帧，框被线性插值补出来，照样喂给 HaMeR，HaMeR 照样输出一只手。** 所以
`merge_debug.txt` 里永远是 `L valid: 1499, R valid: 1499` —— 而 `hand_body_merge.py` 里
作者**写好的** `fill_missing_hand_detections(--hold_missing_frames 6 --interp_missing_frames 15)`
那条路径因此从来没有触发过。

**我们要的就是 `kps[:, 2].max()` 这个数** —— 它衡量"这一帧这只手在画面里看不看得见"，
是判断 HaMeR 输出可不可信的直接依据。

## 改法（两个文件）

### 一、`HAMER/hamer_video.py`

**1)** 第 245 行 `detected_boxes = {}` 下面加一行：

```python
    detected_boxes = {}
    hand_keypoint_conf = {}          # (frame_idx, is_right) -> 该帧该手的关键点最高置信度
```

**2)** 检测循环里（约 264 行），把置信度记下来**再**判断：

```python
        hand_cands = []
        for vpose in vit_out:
            for is_right, kps in ((0, vpose["keypoints"][-42:-21]), (1, vpose["keypoints"][-21:])):
                frame_conf = float(kps[:, 2].max())
                key = (frame_idx, int(is_right))
                hand_keypoint_conf[key] = max(hand_keypoint_conf.get(key, 0.0), frame_conf)
                if frame_conf <= 0.5:
                    continue
                valid = kps[:, 2] > 0.5
                hand_cands.append(
                    {
                        "bbox": np.array(
                            [kps[valid, 0].min(), kps[valid, 1].min(), kps[valid, 0].max(), kps[valid, 1].max()],
                            dtype=np.float32,
                        ),
                        "is_right": is_right,
                    }
                )
        detected_boxes[frame_idx] = hand_cands
```

**3)** 建任务时（约 280-286 行）标出哪些帧是真的检测到的：

```python
    all_tasks = []
    for hand_type in [0, 1]:
        frame_indices = [f for f in sorted(detected_boxes.keys()) if any(h["is_right"] == hand_type for h in detected_boxes[f])]
        if not frame_indices:
            continue
        detected_frames = set(frame_indices)                       # 新增
        bboxes = [next(h["bbox"] for h in detected_boxes[f] if h["is_right"] == hand_type) for f in frame_indices]
        interp_func = interp1d(frame_indices, bboxes, axis=0, kind="linear", fill_value="extrapolate")
        for frame_idx in range(min(frame_indices), max(frame_indices) + 1):
            all_tasks.append({
                "frame_idx": frame_idx,
                "bbox": interp_func(frame_idx),
                "is_right": hand_type,
                "detected": frame_idx in detected_frames,          # 新增
                "results": {},
            })
```

**4)** `export_data` 字典里加一个新数组（约 362 行）：

```python
        "global_orient_abs_lr": np.zeros((num_frames, 2, 3, 3), dtype=np.float32),
        "hand_keypoint_conf": np.zeros((num_frames, 2), dtype=np.float32),      # 新增
```

**5)** 导出循环里，把**无条件**置 1 改成如实填写（约 385 行）：

```python
            export_data["global_orient_valid"][frame_idx, hand_idx] = 1 if det.get("detected", True) else 0
```

**6)** 存盘之前（约 398 行 `pkl_path = ...` 之前）写入置信度：

```python
    for (frame_idx, hand_idx), value in hand_keypoint_conf.items():
        if 0 <= frame_idx < num_frames:
            export_data["hand_keypoint_conf"][frame_idx, hand_idx] = value

    pkl_path = out_dir / f"{video_path.stem}_hamer_data.pkl"
```

### 二、`HAMER/hand_body_merge.py`

把新数组带进 merged pkl。在 `params["right_hand_is_detected"] = r_det` 那两行**下面**加：

```python
        params["left_hand_is_detected"] = l_det
        params["right_hand_is_detected"] = r_det

        # 可见性原始分数：不受 hold/interp 填充影响，插件用它划"手不可信"的区间
        if isinstance(hamer_raw, dict) and "hand_keypoint_conf" in hamer_raw:
            conf = np.asarray(hamer_raw["hand_keypoint_conf"], dtype=np.float32)
            if len(conf) >= n:
                params["left_hand_keypoint_conf"] = conf[:n, 0]
                params["right_hand_keypoint_conf"] = conf[:n, 1]
```

（`hamer_raw` 和 `n` 在那个位置都已经在作用域里。）

## 跑法

改完以后，对那条 take **重跑 HaMeR 那一步和 merge 那一步**（身体那部分不用重跑）：

```bat
HAMER\envs\python.exe HAMER\hamer_video.py --video_path <输入视频> --out_folder <输出目录> --skip_render
HAMER\envs\python.exe HAMER\hand_body_merge.py ^
    --gvhmr_pkl <take>\gvhmr\hmr4d_results.pt_person-0.pkl ^
    --hamer_pkl <输出目录>\<视频名>_hamer_data.pkl ^
    --output <take>\<take 名>.pkl ^
    --smooth one_euro --wrist_cutoff 1.0 --wrist_beta 0.007 ^
    --finger_cutoff 2.0 --finger_beta 0.01 --max_jump_deg 90 ^
    --hold_missing_frames 6 --interp_missing_frames 15
```

（参数照抄 `merge_debug.txt` 里原来那行 `cmd=`，只换路径。）

## 两个必须知道的后果

1. **这次 `global_orient_valid` 会第一次变成真的**，于是
   `filter_hand_jump_frames` 和 `fill_missing_hand_detections` 会**第一次真正执行**。
   这条路径在整合包里从来没跑过。第一次跑建议**先拿已经处理过的那条 take**
   （`0001-0999`，我们有它的原始 merged pkl 可以对比），确认头尾和中间没有异常再说。

2. **hold/interp 填充会把 `is_detected` 重新置回 True**，所以合并后的
   `*_hand_is_detected` 仍然区分不出被填过的帧。这就是为什么要单独带一份
   `*_hand_keypoint_conf` —— 它**不被填充影响**，是我们复核用的原始真相。

## 插件侧

拿到带 `left/right_hand_keypoint_conf` 的 merged pkl 之后，`core/occlusion.py` 只要再加一个
读这个数组的入口，其余（跟 ViTPose 手腕代理同一套 5% 分位 + 区间合并、并进自动提示轨道、
NLA 复核、修复）**原样复用**，不需要改工作流。
