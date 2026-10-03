# 剧本 32：力量感 / 重音（restore_accent）

> 配合 `tools_io.md`。动捕滤波会把出拳、跺脚的"冲击"抹软；这个工具把冲击附近的
> 速度曲线重塑得更脆。任务块会写：骨、帧段 [A,B]、（可选）冲击帧。

## 步骤

1. **找冲击帧**：`analyze_motion bones=[<骨>] frame_range=[A,B]` → `peak_frame`（速度峰）
   或 `stop_frame`（急停=击中）。打击类动作用 stop_frame（到达瞬间），甩动类用 peak_frame。
   记 `peak_speed_deg` 当修前基线。
2. `claim` 该骨 × [A,B]。
3. **写入**——data_path 按骨的旋转模式选（**这是最常见的坑**）：

   | 骨 | data_path | index |
   |---|---|---|
   | 四元数骨（hand_fk/手指/spine_fk*/neck/head/foot_ik/torso_root） | `pose.bones["hand_fk.R"].rotation_quaternion` | 不传（四分量整体重塑） |
   | Euler 骨（upper_arm_fk/forearm_fk = XYZ，shoulder = YXZ） | `pose.bones["forearm_fk.R"].rotation_euler` | 0/1/2 **各写一个 op**，参数相同 |
   | 位置（torso_root、foot_ik） | `pose.bones["torso_root"].location` | 不传（三轴整体） |

   ```
   /home/sb/remote_kit_1.7.1/tools/agent restore_accent '{"agent_id":"<ME>","frame_range":[A,B],
     "data_path":"pose.bones[\"hand_fk.R\"].rotation_quaternion",
     "method":"ease_reshape","strength":0.5,"impact_frame":<冲击帧>,"blend":4,
     "expect_version":<version>}'
   ```
   注意 JSON 里骨名的双引号要转义成 `\"`。
4. **复测**：`analyze_motion` 同参数 → 冲击帧附近 `peak_speed_deg` 应上升（典型 +20–60%），
   `peak_frame` 不应漂移超过 1 帧。
5. `list_ops` → `save` → `release`。

## 参数

- `method`：`ease_reshape`（默认，推荐）；`retime`（`retime_speed` 1.2–2.0 加快到达，
  `retime_split` 0.2–0.5 加速段占比）；`hf_reinject`/`refilter` 需要 `raw_action`
  （原始未滤波动作名），且**不能 reapply**——一般不用。
- `strength` 0.3–0.7。>0.8 容易出现"抽搐感"。
- 帧段 [A,B] 要把冲击帧放在中间偏后，前后各留 ≥ blend 帧。

## 报告
```
重音 <骨> @[A,B] 冲击帧 F：峰速 X → Y °/f；method=…；op=<id>；看 F−5–F+5 帧
```
