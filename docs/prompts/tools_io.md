# 工具速查（每个 subagent 必读全文；读完就能开工）

## 1. 连接与身份

**每个工具调用都是一条完整的命令**（照抄格式，把 `<ME>` 换成你的 agent_id 字面量）：
```
/home/sb/remote_kit_1.7.1/tools/agent ping '{"agent_id":"<ME>"}'
/home/sb/remote_kit_1.7.1/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"palm","side":"L","frame_range":[300,360]}'
```
- **不要用 shell 变量**（`ME=…`、`C=…`、`$C …`）：每条命令都在新 shell 里跑，变量不保留 →
  agent_id 会变成空字符串（匿名写入、没有 owner）；本机 shell 是 zsh，带空格的 `$C` 还会直接
  报 "no such file"。JSON 用**单引号**包住；JSON 里骨名的双引号写成 `\"`（例：
  `"data_path":"pose.bones[\"hand_fk.R\"].rotation_quaternion"`）。
- zsh 里带 `*` 的参数要加引号（`grep --include='*.md'`），否则直接报 "no matches found"、命令根本没跑。
- 每个调用都带 `"agent_id":"<ME>"`。不带 = 匿名，会被别人的 claim 挡住，写的 op 也没有 owner。
- `ping` 的 `data.tools` 里没有你要的工具 → 服务没重启/代码没部署：停下报告，别绕路。
- 服务是 headless Blender（没人看视口）。**验收只看数字。不要启动 Blender、不要跑 mcd.sh**
  （内存只够 1 个 Blender，服务已经占着）。
- 连接被拒（`Connection refused`）= 服务停了：不要重启、不要绕路，把已经拿到的数字写进报告结束。

## 2. 响应与错误码

响应：`{ok, tool, version, summary, data, warnings, error:{code,message,fix}}`。
先看 `ok`，再看 `warnings`（放行提示、层级冲突提示都在这里），出错先读 `error.fix`。

| code | 含义 | 你该做什么 |
|---|---|---|
| `E_CLAIMED` | 你要写的骨×帧被别的 agent 占着 | 换骨/帧段，或停下报告。**不要 force** |
| `E_OWNER` | 你在改别人的 op | 只改自己的（`list_ops` 看 owner） |
| `E_STALE` | 你上次读之后，别人改了**和你范围相交**的东西（同骨或祖先骨） | 重新调读工具拿新 `version`，重新算参数再写 |
| `E_UNKNOWN` | 名字不存在（工具/骨） | 看 `fix` 里的可用列表 |
| `E_RANGE` / `E_SCOPE` | 帧段/范围非法 | 按 message 改 |
| `E_TOOL` | 工具内部报错 | message 一般写了原因和建议（常见：给出"建议 frame_range=[a,b]"——照着重试；"不认识参数 ['amout']（amout → amount？）"——参数名拼错了，照提示改名重发） |

## 3. 单位与约定（违反即错）

- 角度一律**度**；四元数 `(w,x,y,z)`；位置**米**（例外：`slide_report` 用**毫米**）；30 fps。
- `frame_range` **含两端**：[A,B] = A 到 B 每一帧。
- 世界：前方 = **−Y**，上 = **+Z**，左右镜像面 X=0。`toward`/`world_dir` 写**目标**方向。
- `get_series` 取的是**派生信号名**（`get_overview` 的信号表里列着，如 `"pelvis.speed"`、
  `"left_hand.rot_speed"`、`"foot.L.sole_h"`），**不是** fcurve 路径；它和 `get_joint_angles` 都默认最多
  60 个点（`max_points`），帧数更多时按步长聚合（响应 `truncated:true`）——要逐帧就把 max_points 调大。
  两者都属快照类（§5）：读的是原始动作。看当前姿态的角速度/抖动用 `analyze_motion`。
- 写入都是 NLA delta strip、`op_mode=preview`。**绝不 commit**（commit 是用户的事）。
- strip 两端各 `blend` 帧是渐入渐出（taper），有效区是 `[A+blend, B−blend]`。复测看内段：
  `err_inner_deg`，别看 `err_max_deg`。
- **骨架事实（实测）**：
  - 手臂 `shoulder.*`（Euler YXZ）、`upper_arm_fk.*`/`forearm_fk.*`（Euler XYZ）；其余（手、手指、
    脊柱、头颈、foot_ik）是四元数。所有写工具都已支持两种。
  - **腿是 IK**：有效控制骨只有 `foot_ik.L/R`。`thigh_fk/shin_fk/foot_fk` 写了看不见。
  - 源骨架 `Armature`/`f_avg_*` 是废案，别碰。
- 角色名（`bones` 参数可写角色名或骨名）：`hips→torso_root, spine1→spine_fk, spine2→spine_fk.001,
  spine3→spine_fk.003, neck, head, left_shoulder→shoulder.L, left_upper_arm→upper_arm_fk.L,
  left_forearm→forearm_fk.L, left_hand→hand_fk.L, left_foot→foot_ik.L,
  finger_l_index1..3→f_index.01..03.L（middle/ring/pinky 同理）, finger_l_thumb1..3→thumb.01..03.L`，右侧把 l/L 换成 r/R。
- 骨链预设（`chain` 参数）：`arm.L`（肩→上臂→前臂→手→五指）、`arm_nofingers.L`、`fingers.L`、
  `spine`（torso_root→…→head）、`spine_head`（spine_fk→…→head）、`leg.L`（FK，IK 腿上无效）。

## 4. 并发协议（3–5 个 agent 同时干活时的规矩）

```
ping → 读/探查（确定 scope 和修前基线）→ claim → 写（带 expect_version）→ 复测 → list_ops 自查 → save → release
```
0. **修前基线以"写入前最后一次读"为准**（同一 version 下的数字；期间只有和你**不相交**的写入——写入时 warnings
   会说"已放行"——就不用重读）。别的 agent 写入、
   服务端维护都可能让实时数字在你两次读之间变化——报告里的"修前"用最后那次。
1. **先看现场**：`list_ops {"agent_id":"<ME>","frames":[A,B],"live":true,"compact":true}`——你的骨在这段
   帧上如果已经有**别人的同类修复**（同工具、同骨），**不要再叠一层**：报告给协调者（除非任务明确要求叠加）。
   不同类的修复（比如别人的朝向修复 + 你的去抖）可以共存。
2. `claim {"agent_id":"<ME>","bones":[...],"frames":[A,B]}`（`frames` 也可写 `frame_range`；骨也可用
   `"chain":"arm.R"`，会展开成整条链）。`dry_run` 只算不写，**不需要 claim**。
   `data.granted=false` → `data.conflicts` 写着谁占了哪里：换范围或停下报告。
   `warnings` 里出现"层级相关"= 你和别人是父子骨（比如你改前臂、他改手）——可以写，但
   写完在报告里点名对方要复测。
3. 写调用带 `"expect_version":<你据以算写入参数的那次读（通常是修前基线）的 version>`——claim/release 不改数据，
   **不用**它们回的 version（用了会漏掉"基线读之后、claim 之前"别人的改动）。version 是全局计数：任何人在任何地方写入都会
   让它 +1（claim/release/读工具不会）。别人在**不相交**的地方写不会让你过期
   （会在 warnings 里看到"已放行"）。
4. 你没 claim 就写也行——会**自动认领**（warnings 提示），但别人先占了就 `E_CLAIMED`。
5. 租约 15 分钟没动静自动过期；你的每次 claim/写入都会续期。干完 `release`。
6. 只碰自己的 op：`reapply`/`revert`/`set_influence` 别人的 op → `E_OWNER`。**无 owner 的 op**（用户或旧版写的）
   也受保护——遇到挡路的无主 op，报告协调者处理，别绕。
   写入响应 warnings 里出现"同骨同帧已有同类修复"= 你刚刚叠了第二层：不该叠就 revert 你这条并报告。
7. `ab_toggle` 带 agent_id 只静音/恢复**你自己的**修复（它算写操作：会按你的 op 范围自动认领）；
   不带会动所有人的（别人有 claim 时被拒）。A/B 完一定再调一次恢复。
8. **段落完成必须 `save`**（`{"agent_id":"<ME>"}`，不用别的参数）——headless 进程一关，没存盘的全丢。
   save 存的是**大家共用的同一个 .blend**（含所有 agent 的 preview），这是协议允许的写文件操作；
   报告里写 `save=ok` 即可。`release {"agent_id":"<ME>"}` 释放你的全部租约。
9. **写完如何确认没影响别人**：写入响应的 `warnings` 里没有"层级相关"就没有碰到别人租约的
   父子骨；有的话在报告里点名那个 agent。
10. **scope 边界**：工具建议的帧段（`suggest`、`interval` 自动外扩的 blend）超出你的 scope 时，
   **不写**——缩到 scope 内重新 dry_run，或在报告里写清楚需要的范围交给协调者。

## 5. 读工具：快照类 vs 实时类（最容易踩的坑）

| 类别 | 工具 | 读的是什么 | 用途 |
|---|---|---|---|
| **快照类** | `describe` `get_series` `find_events` `compare` `snapshot` `bake_range` `get_joint_angles` `list_intervals` `validate` `get_overview` | **最初烘焙的原始动作**（npz 缓存），**修完不会变** | 了解原动作、找问题帧段 |
| **实时类** | `probe_anatomy` `analyze_motion` `compare_motion` `chain_lag` `slide_report` `ground_report` `effect_check` | **当前可见姿态**（含所有修复） | **修后复测只能用这些** |

修完用快照类工具看"没变化" = 正常现象，不是没写上。别因此再叠一层修复。

## 6. 工具全表

### 读（实时类）
| 工具 | 关键参数 | 看什么 |
|---|---|---|
| `probe_anatomy` | `part`：palm 掌心 / back_of_hand 手背 / finger_dir 指尖方向 / knuckle 指关节 / sole 脚底 / instep 脚背 / toe 脚尖 / knee_front 膝盖（髌骨）朝向 / **elbow_front 肘尖（鹰嘴）朝向——不是肘窝，肘窝 = 它的反方向** / body_forward / bone_axis；`side` `frame_range` `toward` (`bone`/`finger`) `max_frames`(默认 9) | `err_inner_deg` `owner_bone` `confidence` `secondary_axis` `hold_pose_args`（可直接展开）；均匀采样 max_frames 帧，inner **只去掉首尾各一个采样点、不认识 blend**——所以修前修后都在**用户帧段**（有效区）上量，别用外扩后的写入窗；长段/快动作把 max_frames 调到 31 |
| `analyze_motion` | `bones`/`chain` `frame_range` `main_bone` (`onset_frame` `stop_frame` `baseline_op`=你的某个 op_id，结果多一节 `vs_baseline`=修后−该 op 之前) | `data.main`: onset/peak/stop 帧、`peak_speed`(°/帧)、`amplitude_deg`、`counter_move_deg`；每骨 `jitter_deg`；`data.suggest.<工具>.args` 可直接用（帧段若超出你的 scope 见 §4 第 10 条）。`truncated:true` 只表示速度序列按 max_points 抽样，数字不受影响；只要数字时加 `"brief":true`（去掉速度序列，省约 6 KB） |
| `compare_motion` | `op_id`（验收某个 motion_copy，最省事）或 `a:{bones/chain, frame_range}` `b:{…}` `mirror` `bone_map` `space` `trim` | `err_inner_deg`（复制/镜像是否到位） |
| `chain_lag` | `bones`/`chain` `frame_range` | 每骨相对链内父骨的滞后帧数 |
| `slide_report` | `side` `frame_range` `threshold_mm` | 每段接触的 `drift_mm`、`flagged`、`foot_lock_args` |
| `ground_report` | `frame_range` `side` `threshold_mm`(默认 10) `detail` | `contact_height_mm`（这只脚正常着地时脚底关节点的高度，自动标定）、`pen_max_mm`/`pen_frames`（比它低 = 下沉）、`contacts[].floating`（接触期比它高 = 悬空）、`fix_ground_args`（去掉 why 原样用）；`snapshot_diff_max_mm` > 1 = 快照已过时（fix_ground 会算错） |
| `effect_check` | `op_id` | 在 [A+blend, 中点, B−blend] 三帧上该 op 到底动没动：**写上了 = `moved_any:true`**；`pass` 要求三帧都动，局部修复（重音、跟随、踩实）`pass:false` 是正常的。只答"动了没"，不答"对不对" |
| `dry_run:true` | 同写工具 | 只算不写，返回 `dry_run:true` + metrics（clean_jitter/hold_pose 给 `pred_rot_change_max_deg`）。**支持的**：hold_pose、clean_jitter、restore_accent 和全部新写工具；其它（fix_ground/solve_pelvis/apply_exemplar）会**直接报错**而不是偷偷写。响应里没有 `dry_run:true` 就说明真写了 |
| `list_ops` | `owner`（"none"=无主历史） `op_id` `live`（去掉日志里 reverted 的历史） `frames` `bones`（只要写了这些骨的修复） `compact`（只回场景对账行，带 `bones`；复制类 op 的源被别人改过时行里带 `stale`） | **自查用** `{"agent_id":"<ME>","owner":"<ME>","compact":true}`（只回你的 fixes 行，几百字节）；不带过滤 = 全量（可能 50KB+）。fixes 行用 `op_id`，日志行用 `id` |
| `list_claims` | – | 租约表 + 每个 agent 名下的 op |

### 写（全部 preview delta strip，可 revert；除 fix_ground / solve_pelvis / apply_exemplar 外都支持 `dry_run:true` 先看效果）
| 工具 | 关键参数 | 剧本 |
|---|---|---|
| `hold_pose` | `bones` `frame_range` `target`(values/from_frame/world_dir) `world_dir` `world_axis` `secondary_axis` `mode` `strength` `blend` | 30 |
| `clean_jitter` | `frame_range` `bone` `strength` `width` `blend` | 31 |
| `restore_accent` | `frame_range` `data_path` (`index`) `method` `strength` `impact_frame` | 32 |
| `foot_lock` | `interval`("contact.R:7") 或 `side`+`frame_range`, `lock`(xy/xy+rot/pos/pos+rot) | 33 |
| `fix_ground` | `frame_range` `side` `loc_path` `mode`(pen/lift/float，**没有 snap**) `rest_clearance`(米，用 ground_report 给的) | 33 |
| `motion_copy` | `bones`/`chain` `src_range` `dst_start`/`dst_range` `mirror` `bone_map` `space`(local/world) `mode`(replace/add) `channels`(rot/rot+loc) | 34 |
| `anticipation` | `bones`/`chain` `frame_range` `main_bone` `amount`(0.10–0.20) `lead` `delay` | 35 |
| `follow_through` | 同上 + `stop_frame` `amount` `period` `decay` `cycles` `propagate` | 35 |
| `overshoot` | 同上 + `stop_frame` `amount` `peak_after` `settle` | 35 |
| `overlap` | `bones`/`chain` `frame_range` `delay`(每级帧) `max_delay` | 36 |
| `time_warp` | `bones`/`chain` `frame_range` `map`/`speed`+`pivot` | 36 |
| `solve_pelvis` / `apply_exemplar` | 高级，需要自己算数组，任务里明确要求才用 | – |

### 管理
| 工具 | 用途 |
|---|---|
| `reapply {op_id, overrides:{…}, expect_version}` | 改参数重写同一条修复（op_id 不变）。它也是写调用（带 expect_version）。`overrides:{}` = 不改参数、按当前现场重算一次。**同骨同帧段要改，一律 reapply，别叠新 op** |
| `revert {op_id}` | 撤销你自己的 op |
| `set_influence {op_id, value}` | 力度（0.5 = 一半，1.5 = 超量） |
| `claim` / `release` / `list_claims` | 并发租约 |
| `plan_scopes` | 协调者派单前用（工人不用）；任务可带 `reads`（复制的源窗），写-读重叠报 `kind:"read"`、写者先做 |
| `eval_bpy` / `set_preview` / `ab_toggle` | 调试/GUI 用，工人任务里**不要用**（ab_toggle 见 §4 第 7 条） |
| `save` | 落盘（段落完成必调） |
| `commit` | **禁用** |

## 7. 剧本索引

| 任务 | 剧本 |
|---|---|
| 掌心/手背/手指/脚底/膝/肘朝向不对 | `30_orientation.md` |
| 抖 | `31_jitter.md` |
| 打击感/重音软了 | `32_accent.md` |
| 脚滑/穿地/悬空 | `33_contact_ground.md` |
| 把一段动作搬到别的时间/另一侧/另一部位 | `34_motion_copy.md` |
| 加预备/跟随/过冲 | `35_principles.md` |
| 骨链错时（重叠）/改节奏（时间重映射） | `36_overlap_timewarp.md` |

## 8. 报告格式（**唯一**格式；剧本里的报告行只是填好的示例，数字因数据而异，不是目标值）

```
<工具> @[A,B] <骨/链>：修前 X → 修后 Y（<指标名>）；op=<op_id> claim=<claim_id> save=ok；看 <有效区 a–b> 帧
遗留：<无 / 没做完的、低置信度、超出 scope 的段、层级冲突要谁复测>
```
- "修前 X" = 写入前最后一次同口径实时读数；"修后 Y" = 同一工具同参数复测。
- `@[A,B]` = 你的**写入窗**（工具的 frame_range）。"看 a–b 帧" = 有效区：`[A+blend, B−blend]`；剧本里另有规定的
  （跟随/过冲用主骨的 `vs_baseline.changed_frames`）按剧本，工具返回里有 `inner_frames` 就用它。
- 没写（被租约挡住、发现别人已有同类修复、超出 scope）也要报告：第一行写
  `<工具> @[A,B] <骨>：未写入（<原因>）`，把你量到的数字和建议写在"遗留"里。
看不到数字 = 没验成。报数字，不报感觉。最后附"提示词反馈"（若任务块要求）。
