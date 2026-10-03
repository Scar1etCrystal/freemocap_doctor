# 工具速查（每个 subagent 必读全文；读完就能开工）

## 1. 连接与身份

```bash
C="python3 /home/sb/remote_kit_1.7.1/tools/agent_client.py"   # 任何目录都能跑
ME="<你的 agent_id>"                                            # 协调者给的名字，全程不变
$C ping '{"agent_id":"'$ME'"}' --pretty                         # 第一步：确认服务在、工具在册
```
- **每个调用都带 `"agent_id":"$ME"`**。不带 = 匿名，会被别人的 claim 挡住，写的 op 也没有 owner。
- `ping` 的 `data.tools` 里没有你要的工具 → 服务没重启/代码没部署：停下报告，别绕路。
- 服务是 headless Blender（没人看视口）。**验收只看数字。**

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
| `E_TOOL` | 工具内部报错 | message 一般写了原因和建议（常见：给出"建议 frame_range=[a,b]"——照着重试） |

## 3. 单位与约定（违反即错）

- 角度一律**度**；四元数 `(w,x,y,z)`；位置**米**（例外：`slide_report` 用**毫米**）；30 fps。
- `frame_range` **含两端**：[A,B] = A 到 B 每一帧。
- 世界：前方 = **−Y**，上 = **+Z**，左右镜像面 X=0。`toward`/`world_dir` 写**目标**方向。
- `get_series` 里 euler 通道是**弧度**（原始 fcurve 值）；要度用 `get_joint_angles`/`analyze_motion`。
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
ping → claim（你的骨×帧）→ 读（拿 version）→ 写（带 expect_version）→ 复测 → list_ops 自查 → save → release
```
1. `claim {"agent_id":ME,"bones":[...],"frames":[A,B]}`（也可 `"chain":"arm.R"`）。
   `data.granted=false` → `data.conflicts` 写着谁占了哪里：换范围或停下报告。
   `warnings` 里出现"层级相关"= 你和别人是父子骨（比如你改前臂、他改手）——可以写，但
   写完在报告里点名对方要复测。
2. 写调用带 `"expect_version":<上一个响应的 version>`。别人在**不相交**的地方写不会让你过期
   （会在 warnings 里看到"已放行"）。
3. 你没 claim 就写也行——会**自动认领**（warnings 提示），但别人先占了就 `E_CLAIMED`。
4. 租约 15 分钟没动静自动过期；你的每次 claim/写入都会续期。干完 `release`。
5. 只碰自己的 op：`reapply`/`revert`/`set_influence` 别人的 op → `E_OWNER`。
6. `ab_toggle` 带 agent_id 只静音/恢复**你自己的**修复；不带会动所有人的（别人有 claim 时被拒）。
7. **段落完成必须 `save`**——headless 进程一关，没存盘的全丢。

## 5. 读工具：快照类 vs 实时类（最容易踩的坑）

| 类别 | 工具 | 读的是什么 | 用途 |
|---|---|---|---|
| **快照类** | `describe` `get_series` `find_events` `compare` `snapshot` `bake_range` `get_joint_angles` `list_intervals` `validate` `get_overview` | **最初烘焙的原始动作**（npz 缓存），**修完不会变** | 了解原动作、找问题帧段 |
| **实时类** | `probe_anatomy` `analyze_motion` `compare_motion` `chain_lag` `slide_report` `effect_check` | **当前可见姿态**（含所有修复） | **修后复测只能用这些** |

修完用快照类工具看"没变化" = 正常现象，不是没写上。别因此再叠一层修复。

## 6. 工具全表

### 读（实时类）
| 工具 | 关键参数 | 看什么 |
|---|---|---|
| `probe_anatomy` | `part` `side` `frame_range` `toward` (`bone`/`finger`) | `err_inner_deg` `owner_bone` `confidence` `secondary_axis` |
| `analyze_motion` | `bones`/`chain` `frame_range` `main_bone` (`onset_frame` `stop_frame` `baseline_op`) | `data.main`: onset/peak/stop 帧、`peak_speed`(°/帧)、`amplitude_deg`、`counter_move_deg`；每骨 `jitter_deg`；`data.suggest.<工具>.args` 可直接用 |
| `compare_motion` | `a:{bones/chain, frame_range}` `b:{…}` `mirror` `bone_map` `space` `trim` | `err_inner_deg`（复制/镜像是否到位） |
| `chain_lag` | `bones`/`chain` `frame_range` | 每骨相对链内父骨的滞后帧数 |
| `slide_report` | `side` `frame_range` `threshold_mm` | 每段接触的 `drift_mm`、`flagged`、`foot_lock_args` |
| `effect_check` | `op_id` | 该 op 在内段采样帧上到底动没动（只答"动了没"，不答"对不对"） |
| `list_ops` / `list_claims` | – | op（含 owner/alive/status）/ 租约表 |

### 写（全部 preview delta strip，可 reapply / revert，都支持 `dry_run:true` 先看效果）
| 工具 | 关键参数 | 剧本 |
|---|---|---|
| `hold_pose` | `bones` `frame_range` `target`(values/from_frame/world_dir) `world_dir` `world_axis` `secondary_axis` `mode` `strength` `blend` | 30 |
| `clean_jitter` | `frame_range` `bone` `strength` `width` `blend` | 31 |
| `restore_accent` | `frame_range` `data_path` (`index`) `method` `strength` `impact_frame` | 32 |
| `foot_lock` | `interval`("contact.R:7") 或 `side`+`frame_range`, `lock`(xy/xy+rot/pos/pos+rot) | 33 |
| `fix_ground` | `frame_range` `side` `loc_path` `mode`(lift/snap) | 33 |
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
| `reapply {op_id, overrides:{…}}` | 改参数重写同一条修复（op_id 不变）。**同骨同帧段要改，一律 reapply，别叠新 op** |
| `revert {op_id}` | 撤销你自己的 op |
| `set_influence {op_id, value}` | 力度（0.5 = 一半，1.5 = 超量） |
| `claim` / `release` / `list_claims` | 并发租约 |
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

## 8. 报告格式（所有剧本通用）

```
<工具> @[A,B] <骨/链>：修前 X → 修后 Y（<哪个指标>）；op=<op_id> claim=<claim_id> save=<路径>；看 A–B 帧
遗留：<没做完/低置信度/层级冲突要谁复测>
```
看不到数字 = 没验成。报数字，不报感觉。
