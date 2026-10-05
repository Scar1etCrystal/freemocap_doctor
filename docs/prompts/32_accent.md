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

- `method`：`ease_reshape`（默认，推荐）；`retime`（`retime_speed` 1.2–2.0 加快到达，
  `retime_split` 0.2–0.5 加速段占比）；`hf_reinject`/`refilter` 需要 `raw_action`
  （原始未滤波动作名），且**不能 reapply**——一般不用。
- `strength` 0.3–0.7。>0.8 容易出现"抽搐感"。
- 写入窗口：冲击帧在正中，前后各 ≥ `窗口长/3 + blend` 帧，且整个窗口在 scope 内（见第 2 步）。

## 报告（格式见 tools_io §8；示例）
```
restore_accent forearm_fk.L @[325,373] 冲击 349：峰速 18.2 → 25.4 °/帧（+40%），峰值帧不变；op=…×3 claim=… save=ok；看 329–369 帧
```
