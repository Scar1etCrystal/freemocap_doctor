# 剧本 36：重叠（骨链错时）· 时间重映射（overlap · time_warp · 验收 chain_lag）

> 配合 `tools_io.md`。任务块会写：链、帧段、要"重叠"还是"改节奏"。
> 路径占位符 `<套件>` = 套件根目录（任务块给全路径，原样替换）。

## A. overlap（重叠：子骨比父骨晚，越往末端越晚）

用户原话："让骨链错时，子骨骼比父骨骼晚 1~3 帧（脊柱→脖子→头、上臂→前臂→手→手指），越往末端越晚。"
做法：每根骨在 t 帧取"原动作在 t − lag 帧"的**局部**旋转，lag = min(深度×delay, max_delay)，
链根不动。小数 delay 用 slerp 插值。**`delay` 是每级的延迟**（用户说的"晚 1~3 帧"指每级）；
默认 `max_delay` 不封顶（= 最深一级×delay）、`blend` 自动取 ≥2×最大延迟——**这两个一般不用传**。

1. **dry_run 拿内段**（不写）：
   ```
   <套件>/tools/agent overlap '{"agent_id":"<ME>","chain":"arm.R","frame_range":[20,110],"delay":1.0,
     "max_delay":3.0,"blend":4,"dry_run":true}'
   ```
   记 `data.metrics.inner_frames`（= 有效区）、每骨 `lag_frames`、`skipped_bones`、`warnings`。
2. **修前测滞后**：
   ```
   <套件>/tools/agent chain_lag '{"agent_id":"<ME>","chain":"arm.R","frame_range":<inner_frames>}'
   ```
   记每级 `levels[*].lag_frames` 和 `reliable`。
3. `claim` 链 × [A,B]，然后去掉 dry_run、加 expect_version 写入。
4. **复测**：第 2 步原样再调。**只看 `reliable=true` 的级**：每级滞后的**增量 ≈ 该骨 lag − 父骨 lag**
   （两者都在 dry_run 的 `metrics.bones[*].lag_frames` 里；不封顶时就是 ≈ delay），容差 ±0.5。
   被你手动 `max_delay` 钳住的级，增量≈0 是对的。标 `reliable=false` 的级别信，也别因为它去调参。
5. `list_ops` → `save` → `release`。

参数：
- `delay` 0.5–1.5（每级帧数，用户说的 1~3 帧上限）。`max_delay`：不传 = 不封顶；想让末端别拖太久
  才传（例：带手指的 arm.L 深 6 级，delay=1 时指尖晚 6 帧；嫌多就 `max_delay:4`）。
- `blend`：不传 = 自动（≥2×最大延迟）。taper 区的有效时间速率 ≈ 1 − 1.5·lag/blend：手动给小了
  （< 1.5×lag）末端会在窗口开头**倒放**、结尾快进——工具会在 warnings 里提示。
- 自动 blend 变大后有效区 `inner_frames` 会变窄：复测窗口用返回里的 `inner_frames`。
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
- 验收：`metrics.speed_into_pivot` ≈ speed、`metrics.pivot_time_old` == pivot、`data.metrics.warnings` 为空
  （响应顶层 warnings 里的"版本 vX→vY…已放行"是并发提示，不算）。
- 独立复测：`analyze_motion` 同窗、同 `main_bone`，并**钉住修前的 `onset_frame`/`stop_frame`**——改了节奏后
  自动分段常会换到窗口里的另一笔，不钉就是拿两笔不同的动作在比。修前先跑一次不钉的拿到这三个值。
- **副作用（设计如此，报告里提一句）**：time_warp 在小数帧上用 slerp 重采样，单帧的速度尖峰（甩腕、抖动）
  会被摊到相邻两帧——同一笔的峰速可能比映射斜率能解释的再低 20% 左右，抖动也会变小。要保住打击感：
  窗口只包住要变速的那段，或者变速之后在冲击帧上补一个 `restore_accent`（剧本 32）。
- 参数非法（不单调、越界）会报错并告诉你怎么改。

## 报告
```
overlap arm.R @[20,110] delay=1：可信级滞后增量 +1.00/+1.02/+0.93 帧；op=<id>；看 24–106 帧
time_warp arm_nofingers.L @[440,530] speed=1.5 pivot=478：到达速度 1.5×；op=<id>
```
