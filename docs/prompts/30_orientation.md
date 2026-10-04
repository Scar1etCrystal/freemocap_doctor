# 剧本 30：朝向修复（掌心 / 手背 / 手指 / 脚底 / 膝 / 肘）

> 给 socket agent 的任务提示词。配合 `tools_io.md`（通用协议 + 单位）一起发。
> 你的任务块里会写：部位、侧、帧段 [A,B]、目标方向。

## 你要做的事（按顺序，别跳步）

1. **探查（修前基线）**
   ```
   /home/sb/remote_kit_1.7.1/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"palm","side":"L","frame_range":[A,B],"toward":[0,-1,0]}'
   ```
   记下：`data.err_inner_deg`（修前误差）、`data.owner_bone`、`data.confidence`、
   `data.secondary_axis`。（返回里的 `hold_pose_args` 已经是第 3 步表里的 `probe:` 逐帧轴写法，可以直接展开进 hold_pose。）
   - 掌心/手背/脚底先看 `data.evidence.palm_source`（脚：`sole_source`）：`marker` = 用户绑在骨上的箭头
     `MCD_palm.L`（**以它为准**，用户看到的就是它）；`mesh` = 目标网格标定的掌心皮肤法线（可信）；`fingers` = 没标定成，
     按手指几何猜的——弯指时与视口里的掌心差几十度，**不要修**，把 warnings 原文写进报告。
   - 任务块给的目标是箭头物体名时：probe 用 `"toward":"<箭头名>"`（取它的 +Z），hold_pose 用
     `"dir_object":"<箭头名>","dir_mode":"arrow"` 代替 `world_dir`（箭头有动画也跟得上）。
   - `confidence < 0.5` 或返回里有 `alternatives` → **不要修**，在报告里写"低置信度，
     需要用户确认方向"，附两个候选，结束。
   - `err_inner_deg < 5` → 已经对了，报告"无需修复"，结束。

2. **认领**
   ```
   /home/sb/remote_kit_1.7.1/tools/agent claim '{"agent_id":"<ME>","bones":["<owner_bone>"],"frames":[A-4,B+4]}'
   ```
   `data.granted=false` → 有人在改，报告冲突对象（`data.conflicts`），结束。不要 force。

3. **写入**（world_dir + 逐帧 probe 轴 + 双轴）
   ```
   /home/sb/remote_kit_1.7.1/tools/agent hold_pose '{"agent_id":"<ME>","bones":["<owner_bone>"],"frame_range":[A,B],
     "target":"world_dir","world_dir":[0,-1,0],
     "world_axis":"probe:palm.L","secondary_axis":"probe:hand_axis.L",
     "mode":"replace","blend":4,"expect_version":<第 1 步 probe 响应的 version（据以算参数的那次读；不是 claim 回的）>}'
   ```
   `frame_range` 写**外扩后的写入窗** `[A−4, B+4]`（blend 4 帧过渡落在用户帧段外面）；claim 也用它。第 1、4 步的
   probe 始终用用户帧段 `[A,B]`（probe 的 inner 不认识 blend，用写入窗量会把过渡帧算进去）。
   主轴/次轴对照表（**照抄，别自己发明**）：

   | part | world_axis | secondary_axis |
   |---|---|---|
   | palm / back_of_hand | `"probe:palm.L"` / `"probe:back_of_hand.L"` | `"probe:hand_axis.L"`（腕→指根，刚性；别用 finger_dir——手攥紧时它倒向掌心法线，滚转就没了依据） |
   | finger_dir / knuckle | `"probe:finger_dir.L"` / `"probe:knuckle.L"` | `"probe:palm.L"` |
   | sole / instep | `"probe:sole.L"` / `"probe:instep.L"` | `"probe:toe.L"` |
   | toe | `"probe:toe.L"` | `"probe:sole.L"` |
   | knee_front / elbow_front | `"probe:knee_front.L"` / `"probe:elbow_front.L"` | 第 1 步返回的 `secondary_axis` **数组**（没有 `probe:s1` 这种写法） |

   ⚠ `elbow_front` 是**肘尖（鹰嘴）**的指向（两段骨夹角的凸出侧）；用户说"肘窝朝前"= elbow_front 朝**后**，toward 取反。
   `knee_front` 是膝盖（髌骨）朝向，与直觉一致。

   记下返回的 `data.op_id` 和顶层 `version`。返回 `metrics.bones.<骨>` 各字段含义：
   `err_max_before_deg/err_max_after_deg`（求解器自评，全帧口径，**不作验收**）、
   `align_max_deg/align_mean_deg`（主轴需要转多少，信息项）、`flipped_frames`（需转 >150° 的帧数，
   双轴时正常）、`skipped_flip_frames`（**应为 0**；>0 说明漏传 secondary_axis）、
   `secondary_keep_deg`（次轴为对准主轴被带动的最大角，信息项，翻转类修复几十度正常）、
   `probe_fallback_frames`（某帧推不出解剖方向、沿用上一帧；>0 时在报告里提一句）。

4. **复测（必须独立）**：把第 1 步原样再调一遍 → `err_inner_deg`（修后）。帧段长（>60 帧）
   或动作快时加 `"max_frames":31` 采密一点（修前修后用同一个值）。
   目标 < 5°。若 5–15°：`reapply` 调参（见下），**不要再叠一个 hold_pose**。
5. **自查**：`/home/sb/remote_kit_1.7.1/tools/agent list_ops '{"agent_id":"<ME>","owner":"<ME>","compact":true}'` → 你的 op 在 `fixes` 里、`status=preview`、`alive=true`、`owner=<ME>`。
6. **存盘 + 释放**：`/home/sb/remote_kit_1.7.1/tools/agent save '{"agent_id":"<ME>"}'`，`/home/sb/remote_kit_1.7.1/tools/agent release '{"agent_id":"<ME>"}'`。

## 调参（reapply，op_id 不变）

```
/home/sb/remote_kit_1.7.1/tools/agent reapply '{"agent_id":"<ME>","op_id":"<op_id>","overrides":{"blend":8}}'
```
- 两端过渡太生硬 → `blend` 加大（4→8）。
- 只想压住偶发的坏帧、保留原动作 → `{"mode":"clamp","threshold_deg":10}` 或 `{"mode":"outlier","threshold_deg":15}`。
- 力度 → `{"strength":0.7}`（0–2，1=完全到位；只作用一次，0.5 就是一半）。

## 陷阱（都有人踩过）

- `toward`/`world_dir` 是**目标**方向，不是现在错的方向。前方 = `[0,-1,0]`，上 = `[0,0,1]`。
- **只看 `err_inner_deg`**。`err_max_deg` 包含两端 taper 帧，必然偏大，是设计行为。
- `metrics.bones.*.skipped_flip_frames > 0` → 你漏传了 `secondary_axis`。
- 手臂 `upper_arm_fk / forearm_fk / shoulder` 是 Euler 骨——hold_pose 现在支持（写 Euler 增量），
  照常用即可。腿是 IK：膝的 owner 是 `thigh_fk`，但 IK 腿上 FK 骨改了**看不见**——
  膝朝向要改就改 `foot_ik`（脚的位置/朝向带动膝），或报告"需要用户切 FK"。
- `describe/get_series/get_joint_angles` 读的是**最初烘焙的快照**，修完不会变——
  别用它们复测，用 `probe_anatomy`。

## 报告

格式见 tools_io §8（唯一格式），示例：

```
hold_pose @[A−4,B+4] <owner_bone>（<part>.<side>，toward=[x,y,z]）：修前 X° → 修后 Y°（err_inner_deg，probe 在 [A,B] 上量）；op=<op_id> claim=<claim_id> save=ok；看 A–B 帧
```
