# 剧本 32：力量感 / 重音（restore_accent）

> 配合 `tools_io.md`。动捕滤波会把出拳、跺脚的"冲击"抹软；这个工具把冲击附近的
> 速度曲线重塑得更脆。任务块会写：骨、帧段 [A,B]、（可选）冲击帧。
> 路径占位符 `<套件>` = 套件根目录（任务块给全路径，原样替换）。

## 步骤

1. **找冲击帧**：`analyze_motion bones=[<骨>] frame_range=[A,B]` → `peak_frame`（速度峰）
   或 `stop_frame`（急停=击中）。打击类动作用 stop_frame（到达瞬间），甩动类用 peak_frame。
   记 `data.main.peak_speed`（°/帧）当修前基线。`onset_frame` 找不到（窗口开头不在静止段）对重音
   **不要紧**，忽略那条警告。
2. `claim` 任务块给的 **scope**（骨 × 整个帧段）。然后在 scope 里定 restore_accent 的**写入窗口** [a,b]
   （窗口 ⊂ scope）：ease_reshape 在冲击前 窗口长/3 帧加速、冲击后 窗口长/3 帧重塑（可能出现短暂的
   "冲过头再回落"），两端再各有 blend 帧过渡。所以**冲击帧要放在窗口正中间**：前后各至少留
   `窗口长/3 + blend` 帧。例：冲击 349 → [a,b] ≈ [325, 373]（49 帧）。
   - 冲击后留得太少，回落会挤在最后几帧里，看起来像"弹回来"。
   - 窗口里**还有别的速度峰**（第 1 步的速度序列里另一个 >50% 峰速的尖峰）→ 把窗口对称地缩小到不含它，
     只要两侧仍 ≥ `窗口长/3 + blend`；缩不下去就报告，别把别的动作卷进去。
3. **写入**——data_path 按骨的旋转模式选（**这是最常见的坑**）：

   | 骨 | data_path | index |
   |---|---|---|
   | 四元数骨（hand_fk/手指/spine_fk*/neck/head/foot_ik/torso_root） | `pose.bones["hand_fk.R"].rotation_quaternion` | 不传（四分量整体重塑） |
   | Euler 骨（upper_arm_fk/forearm_fk = XYZ，shoulder = YXZ） | `pose.bones["forearm_fk.R"].rotation_euler` | 0/1/2 **各写一个 op**，参数相同 |
   | 位置（torso_root、foot_ik） | `pose.bones["torso_root"].location` | 不传（三轴整体） |

   ```
   <套件>/tools/agent restore_accent '{"agent_id":"<ME>","frame_range":[A,B],
     "data_path":"pose.bones[\"hand_fk.R\"].rotation_quaternion",
     "method":"ease_reshape","strength":0.5,"impact_frame":<冲击帧>,"blend":4,
     "expect_version":<version>}'
   ```
   注意 JSON 里骨名的双引号要转义成 `\"`。Euler 骨（前臂）完整示例——index 0/1/2 各调一次，参数相同：
   ```
   <套件>/tools/agent restore_accent '{"agent_id":"<ME>","frame_range":[325,373],
     "data_path":"pose.bones[\"forearm_fk.L\"].rotation_euler","index":0,
     "method":"ease_reshape","strength":0.5,"impact_frame":349,"blend":4,"expect_version":<version>}'
   ```
4. **复测**：`analyze_motion` 与第 1 步**完全相同的参数**（同骨、同 frame_range = scope）→
   `data.main.peak_speed` 应上升（典型 +20–60%），`peak_frame` 不应漂移超过 1 帧。
   冲击后可能出现一段短的"冲过头再回落"（打击类 stop_frame 往后挪几帧；甩动类 stop 反而可能提前）——
   都是设计行为。**窗口后段太短的信号**：写入窗口的最后 blend 帧里出现修前没有的速度尖峰（对比修前
   速度序列同一帧；冲击帧后 1–2 帧是峰的下降沿，不算；窗口里原有的峰也不算）→ `reapply` 把
   `frame_range` 往后扩。想单看修复本身的变化：复测加 `"baseline_op":"<你的 op_id>"` 看 `vs_baseline`。
   `effect_check` 对重音常报 `pass:false`（冲击前的采样帧本来就不动）——看 `moved_any:true` 即写上了。
5. `list_ops` → `save` → `release`。

## 参数

- `method`：**`retime`（默认，推荐）**——只做**时间重映射**：把加速段压紧、恢复段拉长，
  **端点固定、姿态集合不变**，所以结构上**不可能**给关节加角度偏移。旋钮 `retime_speed`
  1.2–2.0（加快到达）、`retime_split` 0.2–0.5（加速段占比）。
  `ease_reshape`（**旧的默认，别再当默认用**）：它在冲击前后**加一段角度鼓包**——
  实测 `strength=0.5` 是 9 帧内峰值 **−31.9°**、`strength=1.0` 时总转角 **63.7°**；
  用户 2026-10-06 判定为"错的效应"：**0.5 看不见、1.0 变成"手在那一瞬间多弯一下"**，
  中间没有"更有力"的那一档。**要过冲/回弹效果才显式写它**，并知道自己在要什么。
  `hf_reinject`/`refilter` 需要 `raw_action`（原始未滤波动作名），且**不能 reapply**——一般不用。
- **力量感的正解是"时间"不是"角度"**：加速段更短、到位更硬。`retime` 做这个；
  要更猛就配 `overshoot`（收尾过冲），别靠加关节角。
- `strength` 0.3–0.7（只对 `ease_reshape`/`hf_reinject`/`refilter` 有意义）。>0.8 容易出现"抽搐感"。
- 写入窗口：冲击帧在正中，前后各 ≥ `窗口长/3 + blend` 帧，且整个窗口在 scope 内（见第 2 步）。

## ⚠ `retime` 的硬约束：**速度峰必须落在 split 点上**（2026-10-10 实测三次）

`retime` 把窗口做**一次**分段线性时间弯曲：压缩段的终点 = `窗口起点 + retime_split × 窗口长`，
之后是拉伸段。**重采样会削平落在拉伸段里的尖峰**——不是"效果弱"，是**反着走**：

| 窗口 | 峰所在 | split 点 | 峰速 修前 → 修后 |
|---|---|---|---|
| L[348,366] split .68 | 356 / 361 | **360** ✓ | 6.97→7.98（+15%）、14.25→15.60 |
| L[367,388] split .23 | 378 ✗ | 372 | 14.86→**13.72（−8%）** ✗ |
| ↑ 同一窗口改成 split .52 | 378 ✓ | **378** | 14.86→**18.09（+22%）** ✓ |
| R[356,372] split .71 | 368 ✓ | **367** | 13.09→15.97（+22%）✓ |
| 任务M2 [57,67] split .40 | 61 ✗ | 61 ✓ 但峰仅 1 帧宽 | 6.55→**3.24（−51%）** ✗ 已 revert |

**两条可操作结论**：

1. **先算 `split = (峰帧 − 窗口起点) / 窗口长`**，再写；并且要满足 `retime_speed × split < 1`（否则报错）。
   想让峰更快到达就压缩它**前面**那段，不是随便给个 split。
2. **峰只有 1–2 帧宽的动作，`retime` 会把它抹平** ✗（重采样插值削顶）。这类动作**别用 retime**：
   要么把窗口放宽、让峰两侧各有 ≥3 帧，要么直接报告（手册 §"缩不下去就报告"）。
3. 复测必须**用局部窗口**（覆盖该动作 ±5 帧），用整个大区间测会被区间里更大的峰盖住，看不出真实变化。


## 报告（格式见 tools_io §8；示例）
```
restore_accent forearm_fk.L @[325,373] 冲击 349：峰速 18.2 → 25.4 °/帧（+40%），峰值帧不变；op=…×3 claim=… save=ok；看 329–369 帧
```
