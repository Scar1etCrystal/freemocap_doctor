# 剧本 36：重叠（骨链错时）· 时间重映射（overlap · time_warp · 验收 chain_lag）

> 配合 `tools_io.md`。任务块会写：链、帧段、要"重叠"还是"改节奏"。

## A. overlap（重叠：子骨比父骨晚，越往末端越晚）

用户原话："让骨链错时，子骨骼比父骨骼晚 1~3 帧（脊柱→脖子→头、上臂→前臂→手→手指），越往末端越晚。"
做法：每根骨在 t 帧取"原动作在 t − lag 帧"的**局部**旋转，lag = min(深度×delay, max_delay)，
链根不动。小数 delay 用 slerp 插值。

```
C="python3 /home/sb/remote_kit_1.7.1/tools/agent_client.py"; ME=<你的 agent_id>
```
1. **dry_run 拿内段**（不写）：
   ```
   $C overlap '{"agent_id":"'$ME'","chain":"arm.R","frame_range":[20,110],"delay":1.0,
     "max_delay":3.0,"blend":4,"dry_run":true}' --pretty
   ```
   记 `data.metrics.inner_frames`（= 有效区）、每骨 `lag_frames`、`skipped_bones`、`warnings`。
2. **修前测滞后**：
   ```
   $C chain_lag '{"agent_id":"'$ME'","chain":"arm.R","frame_range":<inner_frames>}' --pretty
   ```
   记每级 `levels[*].lag_frames` 和 `reliable`。
3. `claim` 链 × [A,B]，然后去掉 dry_run、加 expect_version 写入。
4. **复测**：第 2 步原样再调。**只看 `reliable=true` 的级**：每级滞后应**增加** ≈ delay（±0.5）。
   标 `reliable=false` 的级（相关性低/峰在边界）别信，也别因为它去调参。
5. `list_ops` → `save` → `release`。

参数：
- `delay` 0.5–1.5（每级帧数），`max_delay` 2–3。默认 1 / 3。
- `arm.L` 默认会把五指都钳在 max_delay（手已经 3 级深）。想要手指**逐节**错开：单独做
  `chain:"fingers.L"`，或 `max_delay` ≥ 4.5。
- 窗口两端各 blend 帧里延迟从 0 爬到满值：那几帧会显得先放慢、后加快。帧段两端尽量落在
  动作较静的地方，或把 blend 调大。
- 推荐链：`arm.L/R`、`arm_nofingers.L/R`、`spine_head`（脊柱→脖子→头）、`fingers.L/R`。
  **腿是 IK**：`leg.*` 写了看不见（会警告）。
- 改延迟：`reapply {"op_id":…, "overrides":{"delay":0.5}}`。

## B. time_warp（时间重映射：改节奏，窗口两端不动）

两种给法：
```
# 便捷：让 [A, pivot] 这一段以 1.5 倍速"到达" pivot（出拳更快）；A、pivot、B 三帧的姿态时刻不变
{"chain":"arm_nofingers.L","frame_range":[440,530],"speed":1.5,"pivot":478}
# 精确：控制点 [[新时刻, 原时刻], ...]（单调；窗口两端自动恒等）
{"bones":["left_upper_arm","left_forearm","left_hand"],"frame_range":[440,530],
 "map":[[460,452],[500,510]],"ease":"linear"}
```
- `ease`：`"smooth"`（默认，速度连续）或 `"linear"`（分段匀速）。smooth 时 pivot 之后会先略
  超前再收回（s=1.5 最多约 4 帧）；要 pivot 之后完全不动就用 `"linear"`，或把 B 设得离 pivot 近些。
- speed > 2.8 时为保持单调会被限幅：**看 `metrics.speed_into_pivot`**（实际到达速度）。
- 验收：`metrics.speed_into_pivot` ≈ speed、`metrics.pivot_time_old` == pivot、`warnings` 为空；
  独立复测用 `analyze_motion`（同窗、同 main_bone）看 `peak_frame`/`peak_speed` 的变化。
- 参数非法（不单调、越界）会报错并告诉你怎么改。

## 报告
```
overlap arm.R @[20,110] delay=1：可信级滞后增量 +1.00/+1.02/+0.93 帧；op=<id>；看 24–106 帧
time_warp arm_nofingers.L @[440,530] speed=1.5 pivot=478：到达速度 1.5×；op=<id>
```
