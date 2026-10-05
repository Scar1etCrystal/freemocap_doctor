# 剧本 31：去抖（clean_jitter）

> 配合 `tools_io.md` 一起发。任务块会写：部位（角色名/骨名）、帧段 [A,B]。
> 路径占位符 `<套件>` = 套件根目录（任务块给全路径，原样替换）。

## 步骤

1. **量修前抖动**（实时工具，读的是当前可见姿态）：
   ```
   <套件>/tools/agent analyze_motion '{"agent_id":"<ME>","bones":["left_hand"],"frame_range":[A,B]}'
   ```
   记 `data.bones.<骨>.jitter_deg`（每帧偏离前后两帧中点的平均角度，度；匀速转动≈0，越小越稳）和 `version`。
2. `claim` 该骨 × [A,B]（`granted=false` 就停，报告冲突）。去抖验收**只看** `data.bones.<骨>` 的 `jitter_deg` 和
   `peak_speed`；`data.main`（onset/stop/幅度）和它的 warnings 是动作分析用的，去抖后主事件常会换一笔，别管它。
3. **写入**：
   ```
   <套件>/tools/agent clean_jitter '{"agent_id":"<ME>","frame_range":[A,B],"bone":"left_hand",
     "strength":1.0,"width":5,"blend":4,"expect_version":<version>}'
   ```
4. **复测**：第 1 步原样再调 → `jitter_deg` 应明显下降（通常降到 30–70%）。修前修后都用**有效区**
   `[A+blend, B−blend]` 量（窗口两端的 taper 帧没被修，峰速会被它们顶替）。
   同时看 `peak_speed`（°/帧，在 `data.bones.<骨>` 里）：**相对**降幅（%）比 jitter 的相对降幅还大 = 你把动作本身抹平了
   （width 太大）→ `reapply` 把 width 调小。**变差了**（jitter 不降反升）：先
   `list_ops {"frames":[A,B],"live":true,"compact":true}` 看这根骨上是不是叠着别的同类修复（写入响应的
   warnings 也会提示"同类修复"）——是就 revert 你自己的、停手报告；不是就 reapply 降 strength 试一次，
   还不行就 revert 自己的 op → save → release → 报告"未达标"。
5. `list_ops` 自查 → `save` → `release`。

## 参数怎么选

| 情况 | width | strength |
|---|---|---|
| 细碎高频抖（手指、手腕） | 5 | 1.0 |
| 明显的跳帧/毛刺 | 7 | 1.0 |
| 想保留爆发力（出拳、甩手） | 3–5 | 0.6–0.8 |
| 窗口里**既有**细碎抖动**又有**真实的快速甩动（常见） | 3–5 | 0.6–0.8，或把 frame_range 缩到抖的那几段 |

- 只在抖的那一段做，别整条动作一把抹（会削掉所有峰值）。找抖的段：`analyze_motion` 的
  `bones.<骨>.jitter_top_frames`（最抖的 5 帧及其抖动角）；加 `"brief":true` 可省掉速度序列。
  注意：真实的快速甩手本身也会让 jitter_deg 偏高（曲率大），别把它当抖动抹掉。
- 手臂 Euler 骨（`upper_arm_fk/forearm_fk/shoulder`）与四元数骨都支持（`bone=` 平滑该骨的**位置 + 旋转**通道，
  旋转按骨的模式自动选；所以写入响应的 touched 里会有 location）。腿是 IK：抖的腿改 `foot_ik.L/R`
  （`thigh_fk/shin_fk/foot_fk` 写了看不见，现在会直接报错）。
- **已修复的历史 bug**：2026-10-03 前 clean_jitter 对四元数骨（手、脊柱）写的是
  分量差，会把骨头转 150°+。如果在旧文件里看到 `agent_jitter_*` strip 让手乱翻，
  那是旧 bug 的产物——报告给用户，别在上面叠修。

## 报告

```
去抖 <骨> @[A,B]：jitter X° → Y°（峰速 P→Q °/f）；width=W strength=S；op=<id>；看 A–B 帧
```
