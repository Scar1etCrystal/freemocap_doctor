# 快速上手（弱模型版）：一页读完就能修

> 给 Haiku / Sonnet 级别的 agent。读完这一页 + 任务块就开工；不用读别的文件。
> 本页每条命令都在 fixture 上逐条跑过（`tests/e2e_quickstart.py`），照抄格式不会错。
> 参考手册是 `docs/工具手册_agent.md`，剧本 30–36 是各类修复的详细版——遇到本页没写的情况才去翻。

## 0. 三条铁律

1. **只用下面这条命令调工具**，不碰 bpy、不启动 Blender、不跑 mcd.sh、不 commit。
2. **修前、修后用同一个实时读工具、同一组参数量一次**，报两个数字。没有数字 = 没做完。
3. **一段帧、一个意图、一个 op**。要改参数就 `reapply` 那个 op，别再叠一个。

## 1. 命令格式（照抄）

```
<套件>/tools/agent ping '{"agent_id":"<ME>"}'
```
- `<套件>` 换成套件根目录、`<ME>` 换成你的名字（任务块里都给全路径），**每条命令都带**。不要用 shell 变量（`ME=…`、`$C`），每条命令都在新 shell 里跑。
- JSON 用**单引号**包住；骨名里的双引号写成 `\"`：`"data_path":"pose.bones[\"hand_fk.R\"].rotation_quaternion"`。
- 回包先看 `ok`，再看 `warnings`，出错读 `error.message` 和 `error.fix`（常带"建议 frame_range=[a,b]"或"拼错的参数名 → 正确名"）。
- `Connection refused` = 服务停了：别重启、别绕路，把已有数字写进报告结束。

## 2. 开工先跑一次 conventions（这份文件的约定）

```
<套件>/tools/agent conventions '{"agent_id":"<ME>","frame":200}'
```
它告诉你：这一帧角色面朝哪（角色会转身，前方不一定是世界 −Y）、镜头和视口在角色哪一侧、
画面左右和角色左右是不是镜像、哪条腿/胳膊是 IK、帧号怎么对应视频、有哪些标记箭头。

想知道某个部位"人眼看起来"朝哪，用 orient_report（只读，人话）：
```
<套件>/tools/agent orient_report '{"agent_id":"<ME>","part":"palm","side":"R","frame":135}'
```
回包 `summary` 就是一句人话，比如"右掌心 @135：朝镜头，偏画面右 42°…；画面上指向右下（4 点钟）；朝角色前方偏左 59°"。

用户说"第 N 帧那一下"之前，先看他有没有在时间轴上标好（他按 M 键放的命名标记）：
```
<套件>/tools/agent list_timeline_markers '{"agent_id":"<ME>"}'
```
回包 `summary` 形如"2 个时间轴标记：505 出拳、620 落地"；每条还带 `covered_by`＝覆盖那一帧的标注区间
（contact.L/R、air、jitter.L/R），所以"出拳 505"到手就已经接上"那几帧左脚是 planted"。
**标记帧是"用户指的那一下"，不是写入窗的端点**——仍要用 `analyze_motion` 在它附近取 onset/stop。
没有标记时 hint 会说下一步怎么办，别自己猜帧号。

## 3. 用户的话 → 方向词（`toward` / `world_dir` 都收这些词，工具每帧现算）

| 用户说 | 写成 | 说明 |
|---|---|---|
| 朝前 / 向前 | `"forward"` | **角色自己的前**（躯干朝向，逐帧）。不要写 `[0,-1,0]`——角色转身了就错 |
| 朝后 | `"back"` | |
| 朝角色的左 / 右 | `"char_left"` / `"char_right"` | L/R 永远是**角色自己的**左右（`.L` 骨那一侧） |
| 掌心/手肘朝外 | 左侧 `"char_left"`，右侧 `"char_right"` | 朝里 = 反过来 |
| **膝盖**内扣、别内扣、朝外、对着脚尖 | `"toes"` | 膝盖对着**同侧脚尖**（工具按 side 取那只脚）。别写 char_left/right——那是让膝盖正对侧面，会拧 90°（Haiku 实测踩过） |
| 朝上 / 朝下 | `"up"` / `"down"` | 世界上下 |
| 朝镜头 / 对着镜头 | `"camera"` | 从这个部位指向镜头（scene.camera） |
| 背对镜头 | `"away"` | |
| 画面左 / 右 / 上 / 下 | `"screen_left"` … `"screen_down"` | 镜头画面里的方向（正面镜头里画面左 = 角色的右！） |
| 朝屏幕 / 朝我（用户在视口里看） | `"viewer"` | 用户的 3D 视口，不是渲染相机 |
| 肘窝朝前 | 肘 `"back"` | `elbow_front` 是**肘尖**，肘窝在它反面 |
| 只说"左""右" | **先问清**：角色左还是画面左 | 裸 `"left"`/`"right"` 会直接报错 |

## 4. 单位（违反即错）

| 量 | 单位 |
|---|---|
| 角度、`err_*_deg`、`jitter_deg`、`amplitude_deg` | 度 |
| `peak_speed` | 度/帧（30 fps） |
| 位置、`rest_clearance`、`pelvis_dz` | **米** |
| `drift_mm`（slide_report）、`*_mm`（ground_report、effect_check 的 `pos_mm`） | **毫米** |
| 帧号 | Blender 时间轴帧号，`frame_range` **含两端**；视频/pkl 第 i 帧（从 0 数）= Blender 第 i+1 帧（conventions 里写着） |
| 四元数 | (w, x, y, z) |

## 5. 标准流程（每个任务都一样）

1. `ping` → 确认要用的工具在 `data.tools` 里。
2. **修前量**（表里"验收"那一列的工具，用**用户给的帧段** [A,B]）。记下数字和回包顶层的 `version`。
3. `claim` 你要写的骨 × 写入窗（`frame_range` 和 `frames` 两种写法都收）：
   `<套件>/tools/agent claim '{"agent_id":"<ME>","bones":["hand_fk.R"],"frame_range":[116,154]}'`
   `data.granted=false` → 有人在改，停下报告，**不要 force**。
4. **写**：写入窗 = 用户帧段两端各外扩 4 帧（`blend` 默认 4，两端是渐入渐出；复制类源窗/目标窗都外扩；overlap 例外，见 §7.14）。
   可以先加 `"dry_run":true` 看一眼（不写）。
   写调用可以带 `"expect_version":<第 2 步的 version 数字>`；回 `E_STALE` = 别人改了你相关的东西：重新量、重新写。
5. **修后量**：第 2 步原样再调一次（同工具、同参数、用户帧段）。没达标 → `reapply` 改参数（见表），**别叠新 op**；两次还不行 → `revert` 你的 op，报告卡在哪。
6. 自查 + 收尾：
   ```
   <套件>/tools/agent list_ops '{"agent_id":"<ME>","owner":"<ME>","compact":true}'
   <套件>/tools/agent save '{"agent_id":"<ME>"}'
   <套件>/tools/agent release '{"agent_id":"<ME>"}'
   ```
   你的 op 要在 `fixes` 里、`status=preview`、`alive=true`。

## 6. 决策表：症状 → 工具 → 验收

| 用户的问题 | 写工具 | 验收（修前修后各量一次） | 达标 |
|---|---|---|---|
| 掌心/手背/脚底朝向不对 | `hold_pose`（§7.1） | `probe_anatomy` 同部位 + `toward` | `err_inner_deg` < 5 |
| 膝盖/肘尖朝向不对（"膝盖朝前""肘朝外"） | `swivel`（§7.2） | `probe_anatomy part=knee_front/elbow_front` + `toward` | `err_inner_deg` < 5 |
| 头/脸、胸、骨盆朝向 | `hold_pose`（§7.3） | `probe_anatomy part=face/chest/pelvis` + `toward` | `err_inner_deg` < 5 |
| 抖 | `clean_jitter`（§7.4） | `analyze_motion` → `bones.<骨>.jitter_deg` | 降到修前的 30–70%，峰速降幅不大于抖动降幅 |
| 打击感软（出拳/跺脚不脆） | `restore_accent`（§7.5） | `analyze_motion` → `main.peak_speed` | 升 20–60%，峰值帧不漂 |
| 脚在地上滑 | `foot_lock`（§7.6） | `slide_report` → 该段 `drift_mm` | < 1 mm |
| 脚陷进地里 / 该着地却悬空 | `fix_ground`（§7.7） | `ground_report` → `pen_max_mm` / 该段 `rel_max_mm` | ≤ 1 mm |
| 整段骨盆太高/太低 | `solve_pelvis`（§7.8） | `effect_check op_id` → `pos_mm` | ≈ 你给的高度差 |
| 套用一段做好的脚步模板 | `apply_exemplar`（§7.9） | — | 这个文件里**没有模板**：报告，别用 |
| 把一段动作复制到别的时间/镜像到另一侧 | `motion_copy`（§7.10） | `compare_motion op_id` | `err_inner_deg` < 0.05 |
| 发力前没有预备（出拳前不回收） | `anticipation`（§7.11） | `analyze_motion` 同参数 | `onset_frame` ≈ 写入回的 `new_onset_frame`，`counter_move_deg` ≈ amount×修前幅度 |
| 停下太死、没有甩动余韵 | `follow_through`（§7.12） | `analyze_motion` + `baseline_op` | `vs_baseline` 第一瓣 ≈ amount×幅度 |
| 停得太急、该冲过头一点 | `overshoot`（§7.13） | `analyze_motion` + `baseline_op` | `approach_peak_deg` ≈ amount×幅度 |
| 骨链一起动太僵（该一节节带过去） | `overlap`（§7.14） | `chain_lag` | 每级滞后 +delay（±0.5 帧） |
| 某一下太慢/太快 | `time_warp`（§7.15） | 写入回的 `metrics.speed_into_pivot` | ≈ 你给的 speed |
| 要给用户/自己看的方向箭头 | `markers`（§7.16） | `markers check` | 你的箭头 `status=ok` |
| 改参数 | `reapply`（§7.17） | 同原工具 | 同原工具 |
| 力度太大/太小 | `set_influence`（§7.18） | 同原工具 | |
| 撤销自己的修复 | `revert`（§7.19） | `list_ops` 里变 reverted | |
| 静音自己的修复对比原样 | `ab_toggle`（§7.20） | 调两次（静音 → 恢复） | 最后一定恢复 |

## 7. 每个工具一条可复制的例子（数字换成你的任务；例子在 fixture 上都跑通）

### 7.1 掌心朝向（hold_pose）——例：右手掌心 120–150 帧朝镜头
修前/修后量（用户帧段）：
```
<套件>/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"palm","side":"R","frame_range":[120,150],"toward":"camera"}'
```
写（写入窗 = [120−4, 150+4]）：
```
<套件>/tools/agent hold_pose '{"agent_id":"<ME>","bones":["hand_fk.R"],"frame_range":[116,154],"target":"world_dir","world_dir":"camera","world_axis":"probe:palm.R","secondary_axis":"probe:hand_axis.R","blend":4}'
```
- 主轴/次轴照抄：掌心 `probe:palm.<侧>` + `probe:hand_axis.<侧>`；手背 `probe:back_of_hand.<侧>` + `probe:hand_axis.<侧>`；
  脚底 `probe:sole.<侧>` + `probe:toe.<侧>`（骨 `foot_ik.<侧>`）。
- 修前 `err_inner_deg` < 5 → 已经对了，报"无需修复"。`evidence.palm_source` 是 `fingers` → 掌心没标定成，**别修**，报告。
- `metrics.bones.<骨>.skipped_flip_frames` > 0 → 漏了 `secondary_axis`。

### 7.2 膝盖/肘尖朝向（swivel）——例：左膝 200–260 帧朝前
```
<套件>/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"knee_front","side":"L","frame_range":[200,260],"toward":"forward"}'
<套件>/tools/agent swivel '{"agent_id":"<ME>","joint":"knee","side":"L","frame_range":[196,264],"toward":"forward"}'
```
- swivel 绕"髋→踝 / 肩→腕"连线转整条腿/胳膊：脚、手的位置和朝向不动。腿是 IK 时它改 `thigh_ik`；**不要用 hold_pose 改 thigh_fk**（写了看不见，会被拒）。
- "膝盖内扣/别内扣/朝外" → `"toward":"toes"`（膝盖对着同侧脚尖），验收 probe 也用 `"toward":"toes"`。只有用户明说"正对前方"才用 `"forward"`。
- 肘：`"joint":"elbow"`，验收用 `part=elbow_front`。`elbow_front` 是**肘尖**；"肘窝朝前" = `"toward":"back"`。
- 写入回包 `metrics.err_after_inner_deg` 是工具自评；验收以你自己重跑的 probe 为准。
- warnings 说"要绕连线转 1xx°"= 目标在背面，先确认方向说法；"目标几乎平行于连线" = 那几帧转不出来（比如手臂下垂还要肘尖朝下），报告。

### 7.3 脸/胸/骨盆朝向（hold_pose）——例：150–190 帧脸朝前
```
<套件>/tools/agent probe_anatomy '{"agent_id":"<ME>","part":"face","frame_range":[150,190],"toward":"forward"}'
```
把回包里的 `hold_pose_args` 原样展开，再补上 `frame_range`（外扩 4 帧）、`target`、`world_dir`：
```
<套件>/tools/agent hold_pose '{"agent_id":"<ME>","bones":["head"],"frame_range":[146,194],"target":"world_dir","world_dir":"forward","world_axis":[-0.0,-0.0259,0.9997],"secondary_axis":[-0.0006,0.9997,0.0259],"blend":4}'
```
（`world_axis`/`secondary_axis` 用**你自己** probe 回的 `hold_pose_args` 里的数，上面是这个文件的。胸 = `part=chest`（骨 spine_fk.003），骨盆 = `part=pelvis`（骨 torso_root）。）

### 7.4 去抖（clean_jitter）——例：右手 300–340 帧抖
```
<套件>/tools/agent analyze_motion '{"agent_id":"<ME>","bones":["hand_fk.R"],"frame_range":[300,340],"brief":true}'
<套件>/tools/agent clean_jitter '{"agent_id":"<ME>","frame_range":[296,344],"bone":"hand_fk.R","strength":1.0,"width":5,"blend":4}'
```
- 看 `data.bones.hand_fk.R.jitter_deg`（不是 `data.main`）。降幅不够 → `reapply` `{"width":7}`；动作被抹平（峰速降得比抖动还多）→ `{"width":3,"strength":0.7}`。
- 腿抖改 `foot_ik.<侧>`；手臂 `upper_arm_fk/forearm_fk` 也能直接用。

### 7.5 打击感（restore_accent）——例：右手 349 帧那一下
```
<套件>/tools/agent analyze_motion '{"agent_id":"<ME>","bones":["hand_fk.R"],"frame_range":[325,373],"brief":true}'
<套件>/tools/agent restore_accent '{"agent_id":"<ME>","frame_range":[325,373],"data_path":"pose.bones[\"hand_fk.R\"].rotation_quaternion","method":"ease_reshape","strength":0.5,"impact_frame":349,"blend":4}'
```
- 冲击帧放在窗口**正中**。Euler 骨（`upper_arm_fk/forearm_fk` = `rotation_euler`）要 `"index":0`、`1`、`2` 各写一次。

### 7.6 脚滑（foot_lock）——例：左脚 400–450 帧着地别滑
```
<套件>/tools/agent slide_report '{"agent_id":"<ME>","side":"L","frame_range":[400,450]}'
<套件>/tools/agent foot_lock '{"agent_id":"<ME>","interval":"contact.L:13","lock":"xy"}'
```
- 只修 `flagged=true` 的行；`interval` 抄那一行的（每段一个 op）。复测：同一条 slide_report，该行 `drift_mm` < 1。

### 7.7 陷地/悬空（fix_ground）——例：左脚 449–450 帧陷地
```
<套件>/tools/agent ground_report '{"agent_id":"<ME>","side":"L","frame_range":[440,460]}'
<套件>/tools/agent fix_ground '{"agent_id":"<ME>","frame_range":[445,454],"side":"L","loc_path":"pose.bones[\"foot_ik.L\"].location","mode":"pen","rest_clearance":0.077}'
```
- 参数就是 ground_report 回的 `fix_ground_args` 那一项**去掉 why**（`rest_clearance` 已经是米）。脚底点是关节中心，穿厚底靴踩实时离地 7–8 cm 是正常的。
- **修后量**：ground_report 的 `frame_range` 用写入窗去掉两端 4 帧（例：写 [445,454] → 量 [449,450]），`pen_max_mm` ≤ 1。两端的过渡帧（脚正在落地/抬起）别算进去。
- `mode`：`pen` 往上推陷地帧，`lift` 往下拉悬空帧。没有 `snap`。fix_ground **不支持 dry_run，也不支持 reapply**——不满意就 `revert` 再写。

### 7.8 骨盆高度（solve_pelvis）——例：300–309 帧骨盆降 1 cm
```
<套件>/tools/agent solve_pelvis '{"agent_id":"<ME>","frame_range":[300,309],"pelvis_path":"pose.bones[\"torso_root\"].location","pelvis_dz":[-0.01,-0.01,-0.01,-0.01,-0.01,-0.01,-0.01,-0.01,-0.01,-0.01],"blend":2}'
<套件>/tools/agent effect_check '{"agent_id":"<ME>","op_id":"<op_id>"}'
```
- `pelvis_dz` 是**每帧**一个数（米，正 = 往上），个数 = 你传的 `frame_range`（也就是**外扩后的写入窗**）的帧数，含两端：
  [300,309] 是 10 个；用户说 1250–1270、写入窗 [1246,1274] 就是 29 个。`blend` 小一点（2）。`<op_id>` 换成写入回包的 `data.op_id`。不支持 dry_run，也不支持 reapply。
- 修前没有现成的读数：报"修前 0（未改）"，修后 = effect_check 的 `per_frame[].bones.torso_root.pos_mm`（应 ≈ 你给的 dz×1000）。

### 7.9 套模板（apply_exemplar）
```
<套件>/tools/agent apply_exemplar '{"agent_id":"<ME>","frame_range":[790,853],"ex_id":"<模板名>","loc_path":"pose.bones[\"foot_ik.R\"].location","quat_path":"pose.bones[\"foot_ik.R\"].rotation_quaternion","target_pos":[[0,0,0]],"target_quat":[[1,0,0,0]]}'
```
- 需要先登记过的模板 `ex_id`，这个文件里**没有**，而且 target_pos/target_quat 要逐帧数组。任务没明确给模板就**不要用**，报告。

### 7.10 复制/镜像（motion_copy）——例：左臂 630–680 镜像到右臂同一时间
**源窗和目标窗都按 §5 外扩 4 帧**：用户说 630–680 → `src_range:[626,684]`、`dst_start:626`（不外扩的话 630–633、677–680
落在渐入渐出里，没复制到位，实测差 55°）。
```
<套件>/tools/agent motion_copy '{"agent_id":"<ME>","chain":"arm.L","src_range":[626,684],"dst_start":626,"mirror":true,"dry_run":true}'
<套件>/tools/agent motion_copy '{"agent_id":"<ME>","chain":"arm.L","src_range":[626,684],"dst_start":626,"mirror":true}'
<套件>/tools/agent compare_motion '{"agent_id":"<ME>","op_id":"<op_id>"}'
```
- `chain`/`bones` 写的是**源**；镜像时写入的是另一侧（claim 目标侧：`arm.R` × [626,684]）。修前 = dry_run 回的
  `metrics.verify.err_inner_before_deg`。compare_motion 按 op 量的就是目标窗去掉两端 4 帧 = 用户的 630–680。
- 时间平移：`"dst_start":1426`（= 用户目标起点 1430 − 4）、不加 mirror；慢放：`"dst_range":[1000,1100]`。

### 7.11 预备（anticipation）——例：右臂 550–603 那一下挥臂
```
<套件>/tools/agent analyze_motion '{"agent_id":"<ME>","chain":"arm_nofingers.R","frame_range":[550,603],"main_bone":"upper_arm_fk.R","brief":true}'
<套件>/tools/agent anticipation '{"agent_id":"<ME>","chain":"arm_nofingers.R","frame_range":[550,603],"main_bone":"upper_arm_fk.R","amount":0.15,"lead":6,"delay":2,"blend":3}'
```
- **先找准是哪一下**。用户只说"第 N 帧（左右）出拳/挥手"时：
  1. analyze_motion 的 `frame_range` 取 **[N−12, N+25]**，`chain` = 用户说的那一侧（没说就两侧都跑），`main_bone` = `upper_arm_fk.<侧>`；
  2. 看回包 `data.main.peak_frame`：**必须在 N−8 … N+8 之间**。不在 = 窗口里有另一下更快的动作被挑中了 → 把窗口起点挪到那一下的
     `stop_frame` 之后（或缩成 [N−8, N+25]）重跑，直到 peak_frame 落在 N 附近；`peak_speed` 太小（< 2 °/帧）就换 `forearm_fk.<侧>` 再试一次；
  3. 用这次回包的 `data.suggest.anticipation.args` **原样**写（它钉好了 onset/stop 和写入窗）。
  实例：第 490 帧左手出拳 → [478,515]：onset 481、peak 489、stop 510 ✓；如果用 [440,520]，挑中的是 473 帧那一下更快的回收动作（错）。
- 复测：第一条原样再跑（不钉 onset）。`peak_speed` < 2 °/帧或幅度 < 5°：动作太小，报告后跳过。

### 7.12 跟随（follow_through）——例：右前臂 721 帧停下后甩一下
```
<套件>/tools/agent follow_through '{"agent_id":"<ME>","chain":"arm_nofingers.R","frame_range":[684,742],"main_bone":"forearm_fk.R","onset_frame":689,"stop_frame":721,"amount":0.12,"period":8,"decay":6,"cycles":2,"blend":3}'
<套件>/tools/agent analyze_motion '{"agent_id":"<ME>","chain":"arm_nofingers.R","frame_range":[684,742],"main_bone":"forearm_fk.R","onset_frame":689,"stop_frame":721,"baseline_op":"<op_id>","brief":true}'
```
- 复测要钉住修前的 `onset_frame`/`stop_frame` 并带 `baseline_op`，看 `data.vs_baseline`。修前写"0（未加）"。

### 7.13 过冲（overshoot）——同一个停止点和跟随二选一
```
<套件>/tools/agent overshoot '{"agent_id":"<ME>","chain":"arm_nofingers.R","frame_range":[684,745],"main_bone":"forearm_fk.R","stop_frame":721,"amount":0.08,"peak_after":2,"settle":6}'
```

### 7.14 骨链错时（overlap）——例：右臂 20–110 帧一节节带过去
overlap 的 `frame_range` **就写用户帧段、不外扩**（它自己按延迟自动留过渡：链越长过渡越宽）。
```
<套件>/tools/agent overlap '{"agent_id":"<ME>","chain":"arm.R","frame_range":[20,110],"delay":1.0,"dry_run":true}'
<套件>/tools/agent chain_lag '{"agent_id":"<ME>","chain":"arm.R","frame_range":[32,98]}'
<套件>/tools/agent overlap '{"agent_id":"<ME>","chain":"arm.R","frame_range":[20,110],"delay":1.0}'
```
- 第二条 chain_lag 的 `frame_range` = 第一条（dry_run）回包里的 `data.metrics.inner_frames`（这个例子是 [32,98]）；**修前、修后都用它**。
  只看 `reliable=true` 的级。
- 某个可靠级的增量不在 +delay ± 0.5 里（比如 +0.13）：**那一级就是"未达标"，别打 ✓**。再看写入回包 `metrics.bones.<骨>.lag_frames`
  是不是按深度递增（0,1,2,3…）——是 = 工具写对了、是 chain_lag 在这段动作上量不准（手、小指常见），报告里写
  "该级未达标（+0.13），lag_frames 正确，疑为测量限制"。腿是 IK：`leg.*` 写了看不见。

### 7.15 改节奏（time_warp）——例：左臂 440–530 以 1.5 倍速到达 478 帧
```
<套件>/tools/agent time_warp '{"agent_id":"<ME>","chain":"arm_nofingers.L","frame_range":[440,530],"speed":1.5,"pivot":478}'
```
- 验收看写入回包 `data.metrics.speed_into_pivot` ≈ 1.5、`pivot_time_old` = 478。

### 7.16 方向箭头（markers）——给掌心/脚底/膝/肘/脸/胸/骨盆建骨骼父级箭头
```
<套件>/tools/agent markers '{"agent_id":"<ME>","action":"create","parts":["knee","elbow"]}'
<套件>/tools/agent markers '{"agent_id":"<ME>","action":"check"}'
```
- 有合格的 `MCD_*` 箭头时 probe 以它为准（`evidence.*_source = marker`）。`check` 报 `error` 的箭头（没父级、绑错侧、顶点父级在另一只手、带关键帧）probe 不读，把 `problems` 和 `fix` 原文报告。
- 工人任务里一般不用（协调者/用户开工前建好）；不碰动画数据，不需要 claim。

### 7.17 改参数（reapply）——op_id 不变，删旧写新
```
<套件>/tools/agent reapply '{"agent_id":"<ME>","op_id":"<op_id>","overrides":{"strength":0.5}}'
```
- `overrides:{}` = 不改参数、按当前现场重算。可改：`strength` `blend` `frame_range` `width` `amount` `delay` `toward`……（就是原工具的参数名）。
- **支持 reapply 的**：hold_pose、clean_jitter、restore_accent（hf_reinject/refilter 除外）、swivel、motion_copy、anticipation、follow_through、
  overshoot、overlap、time_warp、foot_lock。**不支持**：fix_ground、solve_pelvis、apply_exemplar——不满意就 revert 再写。

### 7.18 力度（set_influence）——0.5 = 一半，1.5 = 超量
```
<套件>/tools/agent set_influence '{"agent_id":"<ME>","op_id":"<op_id>","value":0.5}'
```

### 7.19 撤销（revert）——只能撤自己的
```
<套件>/tools/agent revert '{"agent_id":"<ME>","op_id":"<op_id>"}'
```

### 7.20 A/B 对比（ab_toggle）——只拨你自己的修复；调一次静音、再调一次恢复
```
<套件>/tools/agent ab_toggle '{"agent_id":"<ME>"}'
<套件>/tools/agent ab_toggle '{"agent_id":"<ME>"}'
```
- 回包 `data.muted=true` = 现在是原样（A），`false` = 修复生效（B）。**最后一定是 false**。

## 8. 常见坑（都有 agent 踩过）

1. **左右**：L/R = 角色自己的左右。正面镜头里角色的左手在**画面右边**。拿不准就跑 `orient_report` / `conventions` 看 `lr`。
2. **"朝前" ≠ [0,-1,0]**：角色会转身（这份数据里第 1 帧躯干与世界 −Y 差 66°）。用 `"forward"`；给了世界向量时 warnings 会提醒。
3. **"朝镜头" = `"camera"`**（从部位指向镜头）。用户在视口里看、说"朝我/朝屏幕" → `"viewer"`。
4. **腿是 IK**：脚的位置/朝向改 `foot_ik.<侧>`，膝朝向用 `swivel`。`thigh_fk/shin_fk/foot_fk` 写了看不见（会被拒）；快照工具里的 `left_knee` 等腿部角色读的也是看不见的 FK 骨。
5. **快照 vs 实时**：`describe/get_series/get_joint_angles/snapshot/validate/list_intervals/get_overview` 读的是**最初烘焙的原始动作**，修完不变——别拿它们复测。复测只用：`probe_anatomy` `orient_report` `analyze_motion` `compare_motion` `chain_lag` `slide_report` `ground_report` `effect_check`。`conventions` 和 `list_timeline_markers` 属**场景类**（读场景本身，不是姿态），随时可读。
6. **err_inner_deg，不是 err_max_deg**：两端 taper 帧本来就没修到位。probe 用**用户帧段**量，别用外扩后的写入窗。
7. **单位**：位置米，`slide_report`/`ground_report` 毫米；`rest_clearance` 米。
8. **dry_run**：hold_pose、clean_jitter、restore_accent 和全部新工具（swivel、motion_copy、预备/跟随/过冲/重叠/time_warp、foot_lock）支持；fix_ground、solve_pelvis、apply_exemplar 不支持（会报错，不会偷偷写）。回包里没有 `dry_run:true` 就说明真写了。
9. **别叠**：同一骨同一段已有同类修复（写入 warnings 会说"同骨同帧已有同类修复"）→ reapply 那条或 revert 你的，别叠第二层。
   fix_ground / solve_pelvis / apply_exemplar 不能 reapply：revert 再写。
10. **拼错参数会直接报错**并提示正确名，照改即可。
11. **膝/肘的误差是"绕连线还差多少度"**（`err_metric:"swivel"`）：只看人能看出来的那个转角；目标几乎沿着 髋→踝/肩→腕 连线的帧量不了（会被跳过并计数）。

## 9. 报告（唯一格式）

```
<工具> @[写入窗 A,B] <骨/部位>：修前 X → 修后 Y（<指标名>，<单位>，在用户帧段 a–b 上量）；op=<op_id> save=ok release=ok
遗留：<无 / 没做的、低置信度、超出 scope 的、warnings 原文>
```
没写入也要报：第一行写 `<工具> @[A,B] <部位>：未写入（<原因>）`，把量到的数字写在遗留里。
