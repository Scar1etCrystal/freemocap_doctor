# 剧本 30：朝向修复（掌心 / 手背 / 手指 / 脚底 / 脸 / 胸 / 骨盆；膝 / 肘见 B 节）

> 给 socket agent 的任务提示词。配合 `tools_io.md`（通用协议 + 单位）一起发。
> 你的任务块里会写：部位、侧（**角色自己的** L/R）、帧段 [A,B]、目标方向。
> 路径占位符 `<套件>` = 套件根目录（任务块给全路径，原样替换）。

**目标方向写方向词**（工具每帧现算）：`"forward"`（角色躯干的前，不是世界 −Y——角色会转身）、`"back"`、`"char_left"`/`"char_right"`、
`"up"`/`"down"`、`"camera"`（从部位指向镜头）、`"away"`、`"screen_left"`…、`"viewer"`（用户的视口）。任务块给的是向量就用向量；
给了箭头物体名见下。不确定现状"人眼看起来"是什么样：`orient_report {"part":…,"side":…,"frame":…}` 给一句人话。

## A. 掌心 / 手背 / 手指 / 脚底 / 脸 / 胸 / 骨盆（hold_pose）

## 你要做的事（按顺序，别跳步）

1. **探查（修前基线）**
   ```
   <套件>/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"palm","side":"L","frame_range":[A,B],"toward":"forward"}'
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
   <套件>/tools/agent claim '{"agent_id":"<ME>","bones":["<owner_bone>"],"frames":[A-4,B+4]}'
   ```
   `data.granted=false` → 有人在改，报告冲突对象（`data.conflicts`），结束。不要 force。

3. **写入**（world_dir + 逐帧 probe 轴 + 双轴）
   ```
   <套件>/tools/agent hold_pose '{"agent_id":"<ME>","bones":["<owner_bone>"],"frame_range":[A,B],
     "target":"world_dir","world_dir":"forward",
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
   | face / chest / pelvis | 第 1 步返回的 `hold_pose_args`（静态局部轴：这三处相对 owner 骨刚性） | 同左 |

   膝 / 肘**不在这张表里**：见 B 节（swivel）。

   记下返回的 `data.op_id` 和顶层 `version`。返回 `metrics.bones.<骨>` 各字段含义：
   `err_max_before_deg/err_max_after_deg`（求解器自评，全帧口径，**不作验收**）、
   `align_max_deg/align_mean_deg`（主轴需要转多少，信息项）、`flipped_frames`（需转 >150° 的帧数，
   双轴时正常）、`skipped_flip_frames`（**应为 0**；>0 说明漏传 secondary_axis）、
   `secondary_keep_deg`（次轴为对准主轴被带动的最大角，信息项，翻转类修复几十度正常）、
   `probe_fallback_frames`（某帧推不出解剖方向、沿用上一帧；>0 时在报告里提一句）。

   **3b. 方向物体版写入（用户摆了箭头时必须用这个，替代第 3 步的 `world_dir`）**

   用户说"朝 `<某个空物体>` 的箭头方向"时，**不要自己猜那个方向的世界向量**——
   让工具每帧现读它的朝向。用户绑在骨上的方向标记就是 `MCD_palm.L`/`MCD_sole.L` 这类
   SINGLE_ARROW（`markers` 建的或收编的；probe 回 `evidence.palm_source:"marker"` 就是以它为准，
   同一个名字直接进 hold_pose）：

   ```
   <套件>/tools/agent hold_pose '{"agent_id":"<ME>","bones":["<owner_bone>"],"frame_range":[A-4,B+4],
     "target":"world_dir",
     "dir_object":"<空物体名，原样照抄>","dir_mode":"arrow",
     "world_axis":"probe:palm.L","secondary_axis":"probe:hand_axis.L",
     "mode":"replace","blend":4,"expect_version":<version>}'
   ```

   | 参数 | 取值 | 含义 |
   |---|---|---|
   | `dir_object` | 场景里的空物体名（`MCD_palm.L`、用户自己绑的 `Empty.001` …） | 目标方向的来源 |
   | `dir_mode` | `"arrow"`（默认） | 空物体**局部 +Z 轴** = 要对准的方向（SINGLE_ARROW 显示的箭头就是 +Z） |
   | | `"aim"` | 骨头发射向**该物体的位置**（"指向某点"，不是"平行于箭头"） |

   - 空物体**可以 k 动画**：每帧现取朝向 → 逐帧变化的目标免费支持。
   - 用户拖动/转动方向物体后**不用重写 op**：桥里的监视器发现矩阵变了会自动 reapply 刷新；
     也可以手动 `reapply {"op_id":…,"overrides":{"dir_object":"…","dir_mode":"arrow"}}`。
   - 第 1 步 probe 里 `"toward":"<箭头名>"` 读的是同一个 +Z（方向词/向量/物体名三选一）。
   - **别人摆的方向物体不要抢**：`MCD_*` 是用户/协调者共用的方向定义，挪它会影响所有引用它的 op；
     自己建的按 tools_io 命名纪律加前缀。
   - ⚠ 常见错误：`dir_object` 填了、`world_axis` 却留默认 `"Y"`——那等于把骨的局部 Y 当掌心，
     方向完全不对。方向物体只管"目标方向"，**主轴/次轴照旧必须用上面表里的 `probe:` 写法**。
   - ⚠ `dir_object` 只在 `target="world_dir"` 下生效；空物体本身不要动（它是用户的表达方式）。

4. **复测（必须独立）**：把第 1 步原样再调一遍 → `err_inner_deg`（修后）。帧段长（>60 帧）
   或动作快时加 `"max_frames":31` 采密一点（修前修后用同一个值）。
   目标 < 5°。若 5–15°：`reapply` 调参（见下），**不要再叠一个 hold_pose**。
5. **自查**：`<套件>/tools/agent list_ops '{"agent_id":"<ME>","owner":"<ME>","compact":true}'` → 你的 op 在 `fixes` 里、`status=preview`、`alive=true`、`owner=<ME>`。
6. **存盘 + 释放**：`<套件>/tools/agent save '{"agent_id":"<ME>"}'`，`<套件>/tools/agent release '{"agent_id":"<ME>"}'`。

## 调参（reapply，op_id 不变）

```
<套件>/tools/agent reapply '{"agent_id":"<ME>","op_id":"<op_id>","overrides":{"blend":8}}'
```
- 两端过渡太生硬 → `blend` 加大（4→8）。
- 只想压住偶发的坏帧、保留原动作 → `{"mode":"clamp","threshold_deg":10}` 或 `{"mode":"outlier","threshold_deg":15}`。
- 力度 → `{"strength":0.7}`（0–2，1=完全到位；只作用一次，0.5 就是一半）。
- 用户换了方向物体 / 换成手填向量 → `{"dir_object":"Empty.002","dir_mode":"arrow"}`
  或 `{"dir_object":null,"world_dir":"forward"}`。
- `frame_range` 也能改：`{"frame_range":[A,B]}`（用户说"再多修几帧"时用，别叠新 op）。

## 陷阱（都有人踩过）

- `toward`/`world_dir` 是**目标**方向，不是现在错的方向。前方 = `[0,-1,0]`，上 = `[0,0,1]`。
- **只看 `err_inner_deg`**。`err_max_deg` 包含两端 taper 帧，必然偏大，是设计行为。
- `metrics.bones.*.skipped_flip_frames > 0` → 你漏传了 `secondary_axis`。
- 手臂 `upper_arm_fk / forearm_fk / shoulder` 是 Euler 骨——hold_pose 现在支持（写 Euler 增量），照常用即可。
- 腿是 IK：`thigh_fk/shin_fk/foot_fk` 写了**看不见**，hold_pose 现在直接拒绝；膝朝向用 B 节的 swivel。
- 给的是世界向量、而这段角色躯干朝别处时，probe/hold_pose 的 warnings 会说"'朝前'用 forward"——任务块的原话是"朝前"
  就换成方向词重做第 1 步。
- `describe/get_series/get_joint_angles` 读的是**最初烘焙的快照**，修完不会变——
  别用它们复测，用 `probe_anatomy`。

## B. 膝 / 肘（swivel）

膝盖朝哪、肘尖朝哪只有一个能改的自由度：**绕 髋→踝 / 肩→腕 连线的转角**（脚、手的位置和朝向不动）。
`swivel` 就改这一个：IK 腿写 `thigh_ik.<侧>` 的 Y 旋转（膝绕连线转），FK 胳膊转上臂并把手反转回去。
`knee_front` = 膝盖骨朝向；`elbow_front` = **肘尖（鹰嘴）**——用户说"肘窝朝前" = 肘尖朝后 = `"toward":"back"`；
"膝盖/肘朝外" = 左侧 `char_left`、右侧 `char_right`；"膝盖别内扣" 通常 = 朝前或略朝外，拿不准报告。

1. **修前**（用户帧段）：
   ```
   <套件>/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"knee_front","side":"L","frame_range":[A,B],"toward":"forward"}'
   ```
   `err_metric:"swivel"` = 误差是"绕连线还差多少度"；`swivel_degenerate_frames` = 目标几乎沿着连线、量不了的帧数。
   `evidence.knee_source`：`marker`（用户的 MCD_knee 箭头，以它为准）/ `hinge`（全片标定）/ `bend`（标定失败、直腿帧没定义——报告）。
2. `claim` 回包里 `swivel_args` 对应的控制骨：IK 腿 `thigh_ik.<侧>`；FK 胳膊 `upper_arm_fk.<侧>` + `hand_fk.<侧>`（× [A−4, B+4]）。
3. **写**：
   ```
   <套件>/tools/agent swivel '{"agent_id":"<ME>","joint":"knee","side":"L","frame_range":[A-4,B+4],"toward":"forward","expect_version":<第 1 步的 version>}'
   ```
   回包 `metrics`：`err_after_inner_deg`（自评）、`end_drift_mm`（脚踝/手腕应 < 0.5）、`end_rot_change_max_deg`（脚/手朝向应 ≈ 0）。
   warnings "要绕连线转 1xx°" = 目标在背面，先核对方向说法；"N 帧目标几乎平行于连线" = 那几帧转不出来（用插值补），写进遗留。
4. **复测**：第 1 步原样 → `err_inner_deg` < 5。没到：`reapply` `{"blend":8}` 或 `{"strength":…}`，别叠新 op。
5. list_ops → save → release。

## 报告

格式见 tools_io §8（唯一格式），示例：

```
hold_pose @[A−4,B+4] <owner_bone>（<part>.<side>，toward=forward）：修前 X° → 修后 Y°（err_inner_deg，probe 在 [A,B] 上量）；op=<op_id> claim=<claim_id> save=ok；看 A–B 帧
swivel @[A−4,B+4] thigh_ik.L（knee_front.L，toward=forward）：修前 X° → 修后 Y°（err_inner_deg，swivel 平面）；op=… save=ok；看 A–B 帧
```
