# 剧本 31：去抖（clean_jitter）

> 配合 `tools_io.md` 一起发。任务块会写：部位（角色名/骨名）、帧段 [A,B]。

## 步骤

```
C="python3 /home/sb/remote_kit_1.7.1/tools/agent_client.py"; ME=<你的 agent_id>
```
1. **量修前抖动**（实时工具，读的是当前可见姿态）：
   ```
   $C analyze_motion '{"agent_id":"'$ME'","bones":["left_hand"],"frame_range":[A,B]}' --pretty
   ```
   记 `data.bones.<骨>.jitter_deg`（每帧偏离前后两帧中点的平均角度，度；匀速转动≈0，越小越稳）和 `version`。
2. `claim` 该骨 × [A,B]（`granted=false` 就停，报告冲突）。
3. **写入**：
   ```
   $C clean_jitter '{"agent_id":"'$ME'","frame_range":[A,B],"bone":"left_hand",
     "strength":1.0,"width":5,"blend":4,"expect_version":<version>}' --pretty
   ```
4. **复测**：第 1 步原样再调 → `jitter_deg` 应明显下降（通常降到 30–70%）。
   同时看 `peak_speed_deg`：降得比 jitter 还多 = 你把动作本身抹平了（width 太大）→
   `reapply` 把 width 调小。
5. `list_ops` 自查 → `save` → `release`。

## 参数怎么选

| 情况 | width | strength |
|---|---|---|
| 细碎高频抖（手指、手腕） | 5 | 1.0 |
| 明显的跳帧/毛刺 | 7 | 1.0 |
| 想保留爆发力（出拳、甩手） | 3–5 | 0.6–0.8 |

- 只在抖的那一段做，别整条动作一把抹（会削掉所有峰值）。找抖的段：`analyze_motion` 看
  `jitter_deg` 高的骨、或用户给的帧段。
- 手臂 Euler 骨（`upper_arm_fk/forearm_fk/shoulder`）与四元数骨都支持（`bone=` 会自动
  选对的旋转通道）。腿是 IK：抖的腿改 `foot_ik.L/R`。
- **已修复的历史 bug**：2026-10-03 前 clean_jitter 对四元数骨（手、脊柱）写的是
  分量差，会把骨头转 150°+。如果在旧文件里看到 `agent_jitter_*` strip 让手乱翻，
  那是旧 bug 的产物——报告给用户，别在上面叠修。

## 报告

```
去抖 <骨> @[A,B]：jitter X° → Y°（峰速 P→Q °/f）；width=W strength=S；op=<id>；看 A–B 帧
```
