# MoCap Doctor · Agent 工具手册（subagent 提示词用）

socket 服务：`127.0.0.1:6211`，JSON-lines，一问一答。客户端：
`/home/sb/remote_kit_1.7.1/tools/agent <tool> '<json-args>'`（远程套件，任何 shell/目录可用，
自带 `--pretty`）或 `python tools/agent_client.py <tool> '<json-args>' --pretty`。
**先 `ping`**——服务默认不开，没开就让用户去 N 面板 → Agent 协作 → 启动服务
（远程：`bash tools/mcd.sh server-start <blend>`）。
**每个调用带 `"agent_id":"<你的名字>"`**（多 agent 协作的身份；见"并发协议"）。
子 agent 的任务提示词在 `docs/prompts/`（`tools_io.md` + 剧本 30–36）。

返回包络：`{ok, tool, version, summary, data, warnings, truncated, hint, error:{code,message,fix}}`。
错误码：`E_STALE`（你读之后别人改了与你范围相交的骨/祖先骨/帧，重读再写）`E_CLAIMED`（该骨×帧被别的
agent 认领）`E_OWNER`（改别人的 op）`E_SCOPE`（超界）`E_UNKNOWN`（名字不存在）`E_RANGE`（帧范围非法）
`E_TOOL`（执行异常；message 里常带"建议 frame_range=[a,b]"）。

## 铁律（违反即失败）

1. **只走 socket 工具写**。绝不直接碰 bpy/NLA——绕过桥的 strip 是"未登记"孤儿，
   修不回、撤不掉，还会污染别人的修复。
2. **全部 preview，绝不 commit**。commit 是用户的权力。
3. **写完立刻 `list_ops` 自查**：你的 op 在不在、status=preview、track/strip 实名、
   alive=true。不在 = 没写上，别汇报成功。
4. **修后独立复测**：probe_anatomy 带 `toward` 重测（它从几何重新推导，不是
   用你写入时的假设自证）。报数：`修前 X° → 修后 Y°，看 A–B 帧`。
5. **一次一帧段一意图**。多件事分多个 op。
6. 别碰源骨架（`Armature`/f_avg）——它是废案，写了 Teto 上看不见。全部写 RIG。

## 语义修复标准流程（手心朝前类）

```
probe_anatomy  part=palm side=L frame_range=[149,223] toward=[0,-1,0]
   → data.local_axis + data.secondary_axis + data.hold_pose_args
   → data.err_max_deg = 修前偏差（复测基线）
hold_pose      bones=["hand_fk.L"] target="world_dir"
               world_axis=<local_axis>  secondary_axis=<secondary_axis>
               world_dir=[0,-1,0]  frame_range=[149,223]
   → metrics.bones.*.align_max_deg / skipped_flip_frames
probe_anatomy  同上参数再来一遍 → data.err_max_deg = 修后偏差
list_ops       确认新 op 在册
```

- **永远不猜 world_axis**。两种给法：
  - `"probe:<part>.<side>"`（**首选**）：求解器逐帧从几何现推局部轴——
    解剖朝向相对控制骨会随帧变（手指有自己的动画，实测散布 71°），
    均值轴会留几十度残差。例：`world_axis="probe:palm.L"`、
    `secondary_axis="probe:finger_dir.L"`。
  - `probe_anatomy` 返回的 `local_axis`/`secondary_axis` 静态向量：
    只在 `local_spread_deg` 小（<15°）时可用。
- **secondary_axis 一定要传**：双轴解算把扭转钉住，掌心 180° 翻转是绕
  次轴的干净滚转；不传就是最小旋转，近 180° 时轴向随机，会把手翻进手里。
- `confidence < 0.5`：别硬修。`alternatives` 里是两个候选方向——各写一个
  preview op 让用户 A/B；或者改用空物体让用户摆方向。

## 工具全表

### 探查（只读）

| 工具 | 参数 | 返回要点 |
|---|---|---|
| `ping` | — | version/tools 列表 |
| `get_overview` | `force_refresh` | 骨架/通道/bake 缺失/角色名表 |
| `list_intervals` | `kind`(contact.L/contact.R/air/jitter.L/jitter.R) `frame_range` `tag` | 标注区间 |
| `describe` | `target`("contact.L:0"或帧段) `channels` `context` | 区间摘要 |
| `get_series` | `channels` `frame_range` `max_points` `agg` | 通道采样序列 |
| `find_events` | `cond` `frame_range` | 条件事件 |
| `compare` | `channel` `a` `b` | 两区间对比 |
| `snapshot` | `frame` `roles` | 单帧骨骼世界姿态 |
| `get_joint_angles` | `bones` `frame_range` `max_points` | 关节角序列 |
| `bake_range` | `frame_range` `roles` `point_ids` | 世界位置/四元数原始数组 |
| `eval_bpy` | `expr` | 现场求值（**只读**，env 有 bpy/scene/armature/pb；无 setattr/`__import__`，要设置用 `obj.__setattr__`） |
| `validate` | `frame_range` | 穿地/抖动校验 |

### `probe_anatomy` —— 语义层入口（**朝向类修复第一步必调**）

参数：`part` `side`(L/R) `bone` `finger` `frame_range` `toward` `max_frames`

| part | 推导 | owner 骨 |
|---|---|---|
| `palm` | 掌心朝向（指根连线×手指向定平面，指弯曲向定号） | hand_fk.{s} |
| `back_of_hand` | 手背 | hand_fk.{s} |
| `finger_dir` | 手指指向 | hand_fk.{s} |
| `knuckle` | 指根连线方向 | hand_fk.{s} |
| `sole` | 脚底法线（三点定面，小腿在脚背侧定号） | foot_ik.{s} |
| `instep` / `toe` | 脚背 / 脚尖 | foot_ik.{s} |
| `knee_front` | 膝前（大小腿夹角凸出向） | thigh_fk.{s} |
| `elbow_front` | 肘前 | upper_arm_fk.{s} |
| `body_forward` | 身体前方（脚尖+肩线+相机交叉） | — |
| `bone_axis` | 任意骨六根主轴世界向（`bone=`） | 该骨 |

返回：`world_dir`（当前朝向，世界系）、`local_axis`（owner 骨局部向量，
喂 world_axis）、`secondary_axis`+`secondary_name`（喂 secondary_axis）、
`confidence`、`evidence`（数值证据）、`alternatives`（低置信时两候选）、
`hold_pose_args`（可直接展开进 hold_pose 的参数字典；用的是全段平均的固定局部轴——肘/膝这类局部方向随帧
变的部位，逐帧的 `world_axis:"probe:<part>.<side>"` 更准，见 `docs/prompts/30_orientation.md`）、
`toward_resolved`/`err_max_deg`/`err_mean_deg`（带 toward 时）。

`toward` 取值：`[x,y,z]` 向量 / `"up" "down" "forward" "camera"` /
物体名（SINGLE_ARROW 空物体=箭头 +Z 轴方向；其它物体=骨指向它）。

### 写入（全走 NLA delta strip，preview）

| 工具 | 关键参数 | 干什么 |
|---|---|---|
| `hold_pose` | `bones` `frame_range` `target`+`values`/`ref_frame`/`world_dir` `world_axis` `secondary_axis` `dir_object` `dir_mode`(arrow/aim) `flip_guard_deg` `mode`(replace/clamp/outlier) `threshold_deg` `strength` `blend` `op_mode` `track_name` | 姿态保持/方向对齐（四元数骨与 Euler 手臂骨都支持；strength 只作用一次，0.5=一半，>1 超量） |
| `reapply` | `op_id` `overrides`（params 局部覆盖 dict） | 同轨重写该 op：删旧 strip 写新的，op_id 不变 |
| `clean_jitter` | `frame_range` `bone`\|`paths` `strength` `width` `blend` | 零相位平滑 |
| `restore_accent` | `frame_range` `data_path` `index` `method`(ease_reshape/retime/hf_reinject/refilter) `strength` `impact_frame` `retime_speed` `retime_split` `raw_action` `blend` | 力量感（quat 四分量整体重塑） |
| `fix_ground` | `frame_range` `side` `loc_path` `mode`（`pen` 推上穿地帧 / `lift` 拉下悬空帧 / `float` 整段钉住；**没有 snap**，旧版此处写错）`rest_clearance`（米：脚底关节点正常着地离地高度，穿鞋模型不是 0——用 `ground_report` 的 `fix_ground_args`）`pin_xy` `blend` | 脚底贴地（按快照高度算） |
| `solve_pelvis` | `frame_range` `pelvis_path` `pelvis_dz` `blend` | 骨盆高度曲线 |
| `apply_exemplar` | `frame_range` `ex_id` `loc_path` `quat_path` `target_pos` `target_quat` `anchor_yaw_deg` `yaw_scale` `mirror` `blend` | 模板残差重放 |
| `reapply` | `op_id` `overrides`(params 局部覆盖) | 同轨重写该 op（调参） |

### 管理

| 工具 | 参数 | 干什么 |
|---|---|---|
| `list_ops` | — | ops 全量 + fixes 行（status/track/strip/alive/exponent） |
| `effect_check` | `track_name`/`op_id` `bones` `frames` | 该 strip 到底动了没有 |
| `set_influence` | `value` `op_id`\|`track_name` | delta^value 力度（>1 超量） |
| `set_preview` | `frame_range` | 设预览帧段 |
| `ab_toggle` | — | 全部 agent 轨静音/放响 |
| `revert` | `op_id` | 删 strip+action+轨+记录 |
| `commit` | `op_id` | 标记已提交（**别调，用户的事**） |

### 读工具：快照类 vs 实时类（2026-10-03 补）

| 类别 | 工具 | 数据来源 |
|---|---|---|
| 快照类 | describe / get_series / find_events / compare / snapshot / bake_range / get_joint_angles / list_intervals / validate / get_overview | 最初烘焙的 npz（原始动作），**修复后不变** |
| 实时类 | probe_anatomy / analyze_motion / compare_motion / chain_lag / slide_report / ground_report / effect_check | 当前可见姿态（含全部修复）——**修后复测只用这些** |

### 新工具（2026-10-03）

| 工具 | 类型 | 关键参数 | 干什么 / 验收看什么 |
|---|---|---|---|
| `analyze_motion` | 读 | `bones`/`chain` `frame_range` `main_bone` `onset_frame` `stop_frame` `baseline_op` | 主通道 onset/peak/stop、幅度、反向位移、过冲、每骨 `jitter_deg`；`suggest.<工具>.args` 可直接用 |
| `compare_motion` | 读 | `a:{bones/chain,frame_range}` `b:{…}` `mirror` `bone_map` `space` `trim` | 两段动作逐帧角差 `err_inner_deg`（复制/镜像验收；a 放目标窗） |
| `chain_lag` | 读 | `bones`/`chain` `frame_range` `max_lag` `signal` | 每骨相对链内父骨的滞后帧数（只信 `reliable=true`） |
| `slide_report` | 读 | `side` `frame_range` `threshold_mm` | 每段接触 foot_ik 水平漂移 `drift_mm`（**毫米**），flagged 行带 foot_lock 参数 |
| `ground_report` | 读 | `frame_range` `side` `threshold_mm`(默认 10) `detail` | 实时脚底高度（DEF-foot 头/尾 + DEF-toe 尾取最低，与快照同一组点）。先从全片 contact 标注标定每只脚"正常着地"高度 `contact_height_mm`（关节中心不是鞋底，穿鞋模型踩实时也离地几厘米），再按相对值判：`pen_max_mm`/`pen_frames`（下沉）、`contacts[].floating`（悬空）；`fix_ground_args` 带好 `mode` 和 `rest_clearance`（米）；`snapshot_diff_max_mm` > 1 mm = 快照已过时，fix_ground 会按旧高度算 |
| `motion_copy` | 写 | `bones`/`chain` `src_range` `dst_start`/`dst_range`/`time_scale` `mirror` `bone_map` `space`(local/world) `channels`(rot/rot+loc) `mode`(replace/add) | 动作搬到别的时间/另一侧/别的部位；镜像用 rest 标定的 F=Rest_src⁻¹·S·Rest_dst |
| `anticipation` | 写 | `bones`/`chain` `frame_range` `main_bone` `amount` `lead` `delay` | 发力前反向小动 + 起点后移 + 时间重映射补回总时长 |
| `follow_through` | 写 | 同上 + `stop_frame` `amount` `period` `decay` `cycles` `propagate` | 停止点后衰减振荡 |
| `overshoot` | 写 | 同上 + `amount` `peak_after` `settle` | 停太急 → 冲过头一点再回位（单瓣） |
| `overlap` | 写 | `bones`/`chain` `frame_range` `delay` `max_delay` `depths` | 骨链错时：子骨取 t−lag 的局部旋转，lag=min(深度×delay,max_delay) |
| `time_warp` | 写 | `bones`/`chain` `frame_range` `map` 或 `speed`+`pivot` `ease` | 时间重映射，窗口两端恒等 |
| `foot_lock` | 写 | `interval`("contact.R:7") 或 `side`+`frame_range`, `lock`(xy/xy+rot/pos/pos+rot) `ref` | foot_ik 在接触段钉在参考帧世界位置（xy 默认保留高度） |
| `claim` / `release` / `list_claims` | 管理 | `bones`/`chain` `frames` `ttl_s` `strict` `check_only` | 并发租约（见下） |
| `plan_scopes` | 读 | `tasks:[{name, bones/chain, frames}]` | 派单前体检：两两冲突 + 建议并行批次 |

所有新写工具：只写 `frame_range`（motion_copy 是目标窗）以内；支持 `dry_run:true`；参数全录可
`reapply`；四元数骨与 Euler 骨都支持。

### 并发协议（任务1，2026-10-03）

- **claim**（咨询性租约，不是锁）：`{"agent_id","bones"|"chain","frames":[a,b],"ttl_s":900}`。
  同骨 + 帧重叠的别人 → 不批（`granted=false` + `conflicts`）；父子骨重叠 → 批但给 related
  警告（`strict:true` 则不批）；`check_only:true` 只查不占。15 分钟无活动自动过期；你的每次
  claim/写入都续期。
- **写入**：落在别人 claim 里 → `E_CLAIMED`；你没 claim 但范围空闲 → 自动认领（warnings 提示）。
- **expect_version**：写工具按 scope 判定——期间只有别人改了**同骨或其祖先骨、帧重叠**的东西
  （或 GUI 里的外部编辑）才 `E_STALE`；别人在别处写会放行。读工具仍严格。读工具（工具内部的
  frame_set）不再推高版本号。
- **owner**：op 记录写它的 agent_id；别人 revert/reapply/set_influence → `E_OWNER`。
  `ab_toggle` 带 agent_id 只拨自己的轨。
- **plan_scopes**：协调者派单前把计划的 scope 过一遍，按 `waves` 分批（父骨任务先做）。

## RIG 角色名 → 骨名（`bones` 参数用角色名或字面骨名皆可）

`hips→torso_root, root→root, spine1→spine_fk, spine2→spine_fk.001,
spine3→spine_fk.003, neck→neck, head→head,
left/right_shoulder→shoulder.L/R, left/right_upper_arm→upper_arm_fk.L/R,
left/right_forearm→forearm_fk.L/R, left/right_hand→hand_fk.L/R,
left/right_hip→thigh_fk.L/R, left/right_knee→shin_fk.L/R,
left/right_foot→foot_ik.L/R, left/right_heel→DEF-foot.L/R,
finger_{l,r}_{index,middle,ring,pinky}{1..3}→f_*.0N.{L,R},
finger_{l,r}_thumb{1..3}→thumb.0N.{L,R}`（thumb 无 f_ 前缀）

## 坑（都是踩过的）

- NLA delta 是 **COMBINE 右乘**：写 `delta = conj(base) ⊗ desired`，工具内已做
- `strip.influence` ≤1.0：超过 1 的力度用 `set_influence`（角轴缩放曲线）
- NLA strip **没有 IDProperties**：元数据只写进 op log/action
- 结构性 NLA 编辑后 RNA 指针即失效：一律按名字重新取
- hold_pose 一次最多 24 骨；帧段至少 2 帧
- `world_dir` 单轴模式有翻转护栏：需转 >150° 的帧跳过并计
  `skipped_flip_frames`——看到这个数字就该上传 secondary_axis 而不是硬转
- 复测看 `err_inner_deg`/`err_per_frame`：strip 两端 taper 帧保留原姿态
  是设计行为，err_max 会把它算进去误报
- 同一根骨上叠多个 op 时，新 op 的 delta 是 `conj(base)⊗desired`——
  叠在旧 delta 上不是精确 desired（stacking 近似）；要精确就 reapply 改
  旧 op，别叠新 op
- 方向物体：`dir_object="mcd_dir_x"` + `dir_mode="arrow"`（+Z 轴=箭头向）
  或 `"aim"`（骨指向物体位置）；物体可 k 帧 → 逐帧目标
- 力量感只认"已滤波后的曲线"：源数据的高频找不回来，用 ease_reshape
- 修完一定 re-probe 报 err 数值 + 告诉用户看哪几帧；"看到才算数"

### 2026-10-03 实测补充（骨架事实 + 已修复的 bug）

- **旋转模式不统一**：`upper_arm_fk/forearm_fk` = Euler XYZ，`shoulder` = Euler YXZ，其余控制骨是四元数。
  COMBINE 下四元数 delta 右乘、Euler/位置 delta 相加。restore_accent 对 Euler 骨用
  `rotation_euler` + `index`（逐分量）。
- **腿是 IK**（thigh_parent["IK_FK"]=0）：有效腿部控制骨只有 `foot_ik.L/R`，`thigh_fk/shin_fk/foot_fk`
  写了看不见。手臂是 FK。
- **手指不是 hand_fk 的子骨**（中间是 MCH-*_drv ← ORG-hand，ORG-hand 复制 hand_fk）；上臂也不是
  shoulder 的子骨。链深度/祖先关系用"语义父骨"（agent_pose.semantic_parent）。
- 已修复：clean_jitter 对四元数骨写分量差（会把骨转 150°+，抖动反增 20–120 倍）；clean_jitter 对
  Euler 骨漏掉旋转；hold_pose strength 被作用两次；hold_pose 拒绝 Euler 骨；set_influence 不缩放
  Euler/位置 delta；**NLA auto-blend**（部分重叠的两条修复会互相削弱：实测旧修复偏 16°、新修复
  差 53°——现在所有 strip 的 blend 恒为 0，写入前后快照还原）；effect_check 默认采样落在 taper
  端点（必报"1/3 帧有变化"）；Linux 上 `F:/…` 数据目录被当成相对路径（op 日志写进怪名目录，
  blend 里的修复全变"未登记"）。
