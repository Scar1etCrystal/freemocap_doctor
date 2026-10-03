# 剧本 35：预备 / 跟随 / 过冲（anticipation · follow_through · overshoot · analyze_motion）

> 配合 `tools_io.md`。动画原理三件套，都在一个部位（一组骨）上做。任务块会写：部位（链/骨）、
> 大概的帧段、要哪一种效果。

| 工具 | 效果 | 用户原话 |
|---|---|---|
| `anticipation` | 发力前先反向小动一下，起点稍后挪，总时长不变 | "找到发力起点…前面几帧加反方向小位移（约峰值 10~20%），起点稍往后挪，总时长用时间重映射补回来" |
| `follow_through` | 停下后衰减振荡（甩一下再回来，回几次） | "在停止点（速度归零）之后加衰减振荡" |
| `overshoot` | 停太急，冲过头一点再回来（单次，不振荡） | "模拟人停下太快，过冲后回来一点" |

## 第 1 步永远是 analyze_motion（输入工具）

```
$C analyze_motion '{"agent_id":"'$ME'","chain":"arm_nofingers.R","frame_range":[550,603],
  "main_bone":"upper_arm_fk.R"}' --pretty
```
- **显式给 `main_bone`**（主通道 = 动作的主角骨）。不给时自动选峰速最大的骨——这份数据是舞蹈，
  手几乎一直在转，自动选到手往往不对。挥臂类选 `upper_arm_fk.*`，甩小臂选 `forearm_fk.*`。
- 看 `data.main`：`onset_frame`（发力起点）、`peak_frame`/`peak_speed`（°/帧）、`stop_frame`
  （速度归零）、`amplitude_deg`（动作幅度）。
- `data.suggest.anticipation/follow_through/overshoot.args` 是**可以原样发送**的参数（帧段已留好
  lead/blend 余量），`.expect` / `.retest` 写着修后看什么。**优先用 suggest。**
- `peak_speed < 2°/帧` 或 `amplitude_deg < 5°`：动作太小，加了也看不出来，报告后跳过。

## 第 2 步：认领 + 写入（每种一个 op）

```
# 预备（amount 0.10–0.20；lead=提前几帧开始反向；delay=起点后挪几帧）
{"chain":"arm_nofingers.R","frame_range":[550,603],"main_bone":"upper_arm_fk.R",
 "amount":0.15,"lead":6,"delay":2,"blend":3}
# 跟随（amount=第一瓣/幅度；period=摆动周期帧数；decay=衰减快慢；cycles=摆几次）
{"chain":"arm_nofingers.R","frame_range":[684,742],"main_bone":"forearm_fk.R",
 "onset_frame":689,"stop_frame":721,"amount":0.12,"period":8,"decay":6,"cycles":2,"blend":3}
# 过冲（amount=冲过头的比例；peak_after=停后几帧达峰；settle=几帧回位）
{"chain":"arm_nofingers.R","frame_range":[684,745],"main_bone":"forearm_fk.R",
 "amount":0.08,"peak_after":2,"settle":6}
```
- 写失败时 `error.message` 常带"**建议 frame_range=[a, b]**"——照着改了重试（窗口要容得下
  lead/振荡/taper）。
- 跟随加 `"propagate":1` = 链上每深一级晚 1 帧起振（末端甩得更晚）；这时窗口末端要相应延长。

## 第 3 步：复测（再调 analyze_motion，规则不一样，照抄）

| 工具 | 复测怎么调 | 达标 |
|---|---|---|
| anticipation | 与第 1 步**完全相同**（**不要**钉 onset_frame） | `main.onset_frame` ≈ 原值+delay（±1）；`main.counter_move_deg` ≈ amount×amplitude（±35%）；`main.counter_dir_cos` ≈ −1 |
| follow_through | 钉住**修前的** `onset_frame`、`stop_frame`，再加 `"baseline_op":"<op_id>"` | `vs_baseline.bones[主骨]`：`approach_lobes[0]` ≈ +amount×amplitude；`approach_sign_changes ≥ 2`；`before_stop_max_deg ≈ 0` |
| overshoot | 钉住修前的 `stop_frame`，加 `baseline_op` | `approach_peak_deg` ≈ amount×amplitude；峰在 stop+peak_after；`approach_sign_changes == 0` |

为什么要钉：跟随/过冲本身改变了停下时的速度曲线，不钉的话重新检测出的 stop 会被挪走。

## 调参

```
$C reapply '{"agent_id":"'$ME'","op_id":"<id>","overrides":{"amount":0.10}}' --pretty
```
然后按第 3 步同样复测。太夸张 → amount 降；看不出来 → amount 升（上限 0.5）。

## 陷阱

- 预备的时间重映射会**整体**挪动这组骨的节奏（手的自转也被延后），这是设计行为。
- 小动作（峰速 < 8°/帧）的 stop 会检测偏晚：可以根据 `analyze_motion` 的速度序列手动给
  `stop_frame`。
- 同一段同一组骨：三个工具可以都加，但**一种一个 op**；顺序：预备 → 过冲/跟随。
  跟随和过冲在同一个停止点上**二选一**（都加会打架）。

## 报告
```
anticipation <链>@[A,B] 主骨 <bone>：起点 564→566，反向 10.9°（幅度 80.8° 的 13%）；op=<id>；看 556–570 帧
follow_through …：瓣 +12.8/−6.6/+2.9°；op=<id>；看 721–737 帧
```
