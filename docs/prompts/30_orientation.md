# 剧本 30：朝向修复（掌心 / 手背 / 手指 / 脚底 / 膝 / 肘）

> 给 socket agent 的任务提示词。配合 `tools_io.md`（通用协议 + 单位）一起发。
> 你的任务块里会写：部位、侧、帧段 [A,B]、目标方向。

## 你要做的事（按顺序，别跳步）

```
C="python3 /home/sb/remote_kit_1.7.1/tools/agent_client.py"
ME=<你的 agent_id>
```

1. **探查（修前基线）**
   ```
   $C probe_anatomy '{"agent_id":"'$ME'","part":"palm","side":"L","frame_range":[A,B],"toward":[0,-1,0]}' --pretty
   ```
   记下：`data.err_inner_deg`（修前误差）、`data.owner_bone`、`data.confidence`、
   `data.secondary_axis`、响应顶层 `version`。
   - `confidence < 0.5` 或返回里有 `alternatives` → **不要修**，在报告里写"低置信度，
     需要用户确认方向"，附两个候选，结束。
   - `err_inner_deg < 5` → 已经对了，报告"无需修复"，结束。

2. **认领**
   ```
   $C claim '{"agent_id":"'$ME'","bones":["<owner_bone>"],"frames":[A,B]}' --pretty
   ```
   `data.granted=false` → 有人在改，报告冲突对象（`data.conflicts`），结束。不要 force。

3. **写入**（world_dir + 逐帧 probe 轴 + 双轴）
   ```
   $C hold_pose '{"agent_id":"'$ME'","bones":["<owner_bone>"],"frame_range":[A,B],
     "target":"world_dir","world_dir":[0,-1,0],
     "world_axis":"probe:palm.L","secondary_axis":"probe:finger_dir.L",
     "mode":"replace","blend":4,"expect_version":<version>}' --pretty
   ```
   主轴/次轴对照表（**照抄，别自己发明**）：

   | part | world_axis | secondary_axis |
   |---|---|---|
   | palm / back_of_hand | `"probe:palm.L"` / `"probe:back_of_hand.L"` | `"probe:finger_dir.L"` |
   | finger_dir / knuckle | `"probe:finger_dir.L"` / `"probe:knuckle.L"` | `"probe:palm.L"` |
   | sole / instep | `"probe:sole.L"` / `"probe:instep.L"` | `"probe:toe.L"` |
   | toe | `"probe:toe.L"` | `"probe:sole.L"` |
   | knee_front / elbow_front | `"probe:knee_front.L"` / `"probe:elbow_front.L"` | 第 1 步返回的 `secondary_axis` **数组**（没有 `probe:s1` 这种写法） |

   记下返回的 `data.op_id` 和顶层 `version`。

4. **复测（必须独立）**：把第 1 步原样再调一遍 → `err_inner_deg`（修后）。
   目标 < 5°。若 5–15°：`reapply` 调参（见下），**不要再叠一个 hold_pose**。
5. **自查**：`$C list_ops '{"agent_id":"'$ME'"}'` → 你的 op 在 `fixes` 里、`status=preview`、`alive=true`、`owner=$ME`。
6. **存盘 + 释放**：`$C save '{"agent_id":"'$ME'"}'`，`$C release '{"agent_id":"'$ME'"}'`。

## 调参（reapply，op_id 不变）

```
$C reapply '{"agent_id":"'$ME'","op_id":"<op_id>","overrides":{"blend":8}}' --pretty
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

## 报告（不变通）

```
朝向 <part>.<side> @[A,B] <owner_bone>：
修前 X° → 修后 Y°（err_inner）；op=<op_id> claim=<claim_id> save=<路径>；看 A–B 帧
```
