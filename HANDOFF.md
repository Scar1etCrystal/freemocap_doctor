# MoCap Doctor 工作交接文档

> 生成于 2026-09-30，由 Claude Code 会话整理。给接手 agent 的目标：读完即可继续当前工作，不需要考古聊天记录。
> 本文件未纳入 git（含本机绝对路径），**不要提交**。

## 0. 阅读顺序

1. 本文档
2. 记忆文件（§6 清单）。**必读前三个**：`user-communication-prefs`、`mocap-doctor-ground-feet`、`mocap-doctor-project`
3. 源码关键文件（§7 代码地图）
4. 聊天记录（§9，仅在需要考古细节时）

---

## 1. 项目一句话

**MoCap Doctor**：Blender 4.3–4.5 扩展（`f:\mocap_ai_doctor\mocap_doctor\`），把 GVHMR 单目视频动捕 → MMD VMD 的后处理固化成 **16 步向导**，固定预设 30fps / arue 式重音テト ver 2.01 + MikuMikuRig + mmd_tools 导出。前端（GVHMR 捕捉 + ARP/MMR 重定向）由 PoseCapture_Pack 完成，本插件负责重定向**之后**的清理与导出。权威文档：`mocap_doctor/workflow.py`（步骤表）、`README.md`（用法与约束）、`PARAMETERS.md`（参数）。

环境事实：
- 无头测试 Blender：`D:\blender-3.2.1-windows-x64\blender.exe`（**实际是 4.5.14 LTS**）
- 仓库 `f:\mocap_ai_doctor`，**git 目录是 `.repo_git` 不是 `.git`**；远端 github.com/Scar1etCrystal/freemocap_doctor（main）；http.sslBackend 已设 schannel
- 最后一次推送：`f4c6da7`（1.0.0）。**其后所有改动（1.1.0→1.4.0）都未提交、未推送**，全在工作树和 `dist/` 的 zip 里

## 2. 版本与验收状态（最重要的上下文）

| 版本 | 内容 | 用户验收 |
|---|---|---|
| 1.0.0 | 基线（含贴地锁定的前身、对象名回退） | 已推送 |
| 1.1.0 / 1.1.1 | planted 区间贴地 + 容差/去毛刺护栏 | **被 1.2.0 整体取代**（方向错了，别参考） |
| 1.2.0 | 第 13 步「贴地锁定」改版：**腾空区间标注 + 非腾空帧无条件钉最低脚 + 腾空段物理弹道重建**（g=9.81，h=g·T²/8） | ✅ 用户："效果很好" |
| 1.3.0 | ①贴地移到 Mesh 穿地修复**之前**（第 11 步）；②地面高度默认全部归零（旧 0.0257 是拟合数）；③**踝-鞋底落差从模型绑定几何实测**（`model_sole_offset`，Teto=5.58cm）；④穿地修复参数重调（strength 1.0/smooth 0）——并**挖出 Blender 4.4+ 槽绑定 bug**（`ensure_action_slot`：新建 Action 赋给无动作对象时槽未绑定，曲线静默失效；穿地修复此前从未生效） | ✅ 用户："mesh 穿地生效了" |
| 1.4.0 | foot_lock 加「旋转锁」（X/Y 开 Z 关，锁段中位数）+「逐侧贴地」（双脚等高） | ❌ **用户否决**："大方向错了——锁的是控制、动的是 mesh"。**不要沿此方向继续**；这两个功能将在下一版被闭环方案替换删除 |

`dist/` 里有 0.1.12–1.4.0 全部 zip。用户 Blender 里装的版本以用户口述为准（他们自己装）。

## 3. 当前正在做的事：脚部稳定性 → 闭环方案（进行中）

**问题**：位置 XY 锁把脚踝钉到了 0.1mm，但用户看整个脚掌"还是在动"。

**已完成的归因（Phase 0 诊断，2026-09-30，在 1499 工作文件实测）**：
- 动的是**脚的世界旋转**：planted 段 [1,100] 内足首三轴旋转变化 L 13.6°/5.3°/18.9°、R 8.8°/8.4°/9.6°；foot_ik 自己被重定向写了旋转曲线（世界 swing L 23.3°/R 11.5°）——重定向就是给了 planted 段脚掌旋转
- `MCH-foot_ik.parent.L/R`（foot_ik 的父骨）世界旋转**全程 0.0°** → 锁 foot_ik 局部通道 == 锁世界，闭环无需父级补偿
- `つま先.L/R` 相对 `足首` 的局部位置/旋转**全程 0.0mm/0.0°**（刚性连接）→ 钉住足首即钉住整个脚掌含 toe 网格；**"双支点锁 toe_ik"的社区方案在这台 rig 上不需要**
- rig 上**没有任何 toe 控制曲线**（重定向没给 toe 控制动画权限）
- R 侧 |Δfoot_ik| 与 |Δ足首| 精确相等（11.5=11.5）→ 旋转传递角守恒（干净）
- ⚠️ 方法论教训：当时用的"传递失配"指标有数学缺陷（没扣两骨固定姿态偏移的共轭 + 四元数双覆盖翻转把 L 侧吹成 341°伪影）。**别复用那个公式**；正确残差 = `d_foot @ (C⁻¹ d_ik C)⁻¹`，C 为参考帧处两骨姿态偏移

**Phase 1 已实现并 e2e 通过（2026-10-01）——闭环世界空间稳定器 `stabilize_planted_feet`**：
1. 核心思想转变：从"锁控制器、假设传递干净"改为"**量 mesh 侧骨头的世界位姿，修正控制直到结果匹配**"（对传递路径缺陷免疫）
2. 每个 planted 段取锚帧（中位帧），抓 `足首.L/R` 的**完整世界矩阵**（位置+旋转）
3. 段内逐帧：读求值后足首世界矩阵 → 与锚比出 6DoF 误差 → 换算 foot_ik 的世界 Δ → 写入 foot_ik 通道 → **单轮写 + 一次复测**（见下"关键实现事实"）
4. **三轴全锁（含 yaw）**；真实碾转段靠**从 planted 删段豁免**（现有人工分工）
5. **已替换** 1.4.0 的 `lock_foot_ik_rotation` 和 `equalize_planted_feet_height`（代码删除、UI/properties 清理完）；`lock_foot_ik_xy` 位置锁**保留**（工作正常）
6. 不动 rig 绑定

**关键实现事实（e2e 里挖出来的，别再踩）**：
- **写入必须走解析 basis 路径**：`basis = (B_rest⁻¹·P_rest·P_pose⁻¹)·M_target`（父骨 `MCH-foot_ik.parent` 静态，K 一次算好，setup 时对照实数据自校验）。**不要**用 `pb.matrix=` setter + 每帧 `frame_set` 的写法——大 Action 上 2500 次会打爆 Blender 4.5 守护分配器（MEM_dupallocN/reallocN/freeN 刷屏后 tbbmalloc/VCRUNTIME 访问违例）
- **只能单轮写**：第二写 pass 正是崩溃现场；且物理上没必要——第一遍后旋转全收敛 0.00°、位置到可达极限
- **残余地板 = 腿够程饱和**：段首落地过渡帧（如 1499 的 109/1086）foot_ik 写到位但踝在 IK 延伸极限上不去（残余 72-104mm 恒定两轮）——报告 `verification:"unconverged"` + `unconverged_frames` 诚实列出，不硬推
- 同会话求值**是新鲜的**（写 fcurve→frame_set→读 evaluated 立刻反映新值），无需担心陈旧读

**e2e 数字（全新会话复测存盘文件）**：1499：60 段旋转全 0.00°、56/60 段位置 ≤0.4mm、4 段首饱和帧 72-104mm；未锁帧零误伤。0999：9 段，残余 1.53mm/0.00°

**Phase 1b 已实现并 e2e 通过（2026-10-01，同日追加）——骨盆修约 + 贴地锚**：
1. 动机：planted 段脚被骨盆带离地面（模型腿按比例偏长 → 同髋高下腿近伸直 0.9977、脚悬空 5-9cm）。用户给的方向 = opus5.5 方案（着地约束+腿长比解骨盆），落在插件内做 post-pass，不动前端不重跑推理
2. `_settle_pelvis_for_reach`：逐帧解 `|髋−踝|/腿长` 使模型比率 = 源骨架同帧比率（两节腿链里比率与膝角是几何恒等）→ 修正写进 **`torso_root`**（全身平移唯一携带者；torso/hips/root 均无 loc 曲线，torso_root 有 1500 键、父骨 root 静态）。planted 帧脚目标=贴地锚，双脚取**更低**解；摆动帧用当时踝位同式解；补缺插值→9帧低通→2mm死区→**±`pelvis_correction_max`（默认0.025）硬钳不警告**，报告计 capped_frames
3. **锚高度贴地化**：planted=接触 → 锚 Z 换成"锚旋转下足底贴地的踝高"= `floor − (R_anchor @ sole_dir_local).z`。`sole_contact_offsets()` 从网格最低点测出踝→足底的骨内向量——**踮脚/翻滚脚自动落在更高踝高**（1499 实测锚高 97-140mm，那批"浮空"段本来就是踮脚站立的真实高度，平放假设会制造伪饱和）
4. **仿射标定（替代基体公式假设）**：`pose_trans = M@loc + t` 对两种父子组合规则（default/parent_space）各算 (M,t)，采样帧实测投票选对的——torso_root 用默认式。foot_ik 校验路径顺手修了帧错位 bug（`pb.location` 之前在 preserve_scene_frame 恢复后才读，对比的是两帧不同数据）
5. e2e v3：1499 文件 unconverged 仅 10 帧（全是落地下降段 109-110/1086-1089 真饱和），599-651 等段脚实际落在踮脚高度；0999 残余 170→80mm。**cap 全段吃帽（1498/1499 帧）**——源比率系统性要求 30mm+ 下沉，25mm 只够贴地不够全恢复膝弯；要更弯需用户放宽阈值

**剩余**：用户目视验收（planted 段脚是否落地、踮脚段高度是否自然、全身 25mm 下沉幅度观感、跳跃未被压平）；cap 是否放宽（>30mm 可恢复更多膝弯但更明显的下蹲感）；通过后 bump 1.5.0 打 zip。**版本号仍 1.4.0 未改**；提交/推送由用户决定

**用户的明确原话**（约束方案）："就算脚部所有 IK 全程完全不动，胯部的正常活动也会带动脚的网格……我们一直在锁骨骼，动的却是 mesh。" 这是这次方向修正的出发点。

~~**现在卡在哪：等用户的三项人工观测结果**~~（已收到——①膝自然；②脚尖游移看不出；③微插地可接受但"胯动带动脚插更深"= 锁定应修的症状；④无拧腿；⑤[1,100] 无真实碾转）

## 4. 已否决/锁定决策（不要重试）

- **不要**用 planted 检测做贴地判定（数据分不出飘和跳）；**不要**容差质疑标注（用户原则：人工标注即事实，数据才是被告）
- **不要**自动弹道/概率融合/静止概率融 planted（实测无收益，已否决）
- **不要**回到"检测接触帧再修"的任何路线
- 倾斜扶正（tilt/global_correction 步骤）**保留**（用户拍板，倾向跳过不删）
- 「轻度旋转平滑」步骤已删除（GVHMR 自带滤波）；手指动作替换步骤已删除；**手部链（源诊断/标注/修复 3 步）1.6.0 已整个移出向导**——改成导入前 pkl 预检工具；`core/occlusion.py`（vitpose.pt 读取）随之删除，运动统计量在遮挡段上不可判别已实测
- 顿挫感 = 艺术效果，不自动还原；抬腿/跳跃高度 → 人工创作（数据里没有）
- 用户的认识论分工：**人只标视频里可观测的**（腾空、手部遮挡），**不标数据里看不见的**（接触）

## 5. 文件与路径地图

**测试文件（用户的，绝不可覆盖——e2e 一律拷贝到沙盒）**：
- 1499 take（**当前主测试文件**）：`F:\0001-1499_f_full_20260925_165539等2项文件\0001-1499_f_full_20260925_165539\Untitled_mocap_doctor_work.blend`
  - 最新实测状态（2026-09-30 探针）：schema 5、current_step 12（foot_lock）、步骤 project/source_floor/source_check/contacts/retarget/tilt/**ground_feet/target_floor/foot_lock** 全 ACCEPTED、未 bake（mmd_action=None）、57 条 MMR 约束活动
  - planted 已编辑：43/44 段，尾部 [1128,1484] 大改（9+7 手工段、23 处相对自动结果的删除）→ 跳跃删段就在这个文件里
- 0999 take（上一轮测试，弹道重建在此验收）：`F:\0001-1499_f_full_20260925_165539等2项文件\0001-0999_f_full_20260925_162525\mp_mocap_doctor_work.blend`（腾空 [12,19] 在沙盒副本标过；用户真实文件以打开读记录为准）
- `...0999...\mp_mocap_doctor_work_备份_1.2.0版.blend`：99MB 备份，用户可能要删
- PoseCapture Pack（可读）：`F:\gvhmr\pack2\PoseCapture_Pack`（**其父级目录是别的整合包，用户明令禁止查看**）；其 `blender_addon\foot_slide_fix.py`（K 空物体无条件钉地）和 `gvhmr_pose_capture.py` 的 `_apply_manual_foot_slide_jumps_to_z`（12754 行起：起跳/顶点/落地三点+手填顶点高度+**分段直线**，不是抛物线）是贴地方案的参照

**沙盒**：
- 隔离 e2e：`f:\mocap_ai_doctor\.blender_test_tmp\e2e_45_smoke\`（= BLENDER_USER_* 指向的隔离环境，`extensions/user_default/mocap_doctor` 是拷贝安装，**改完源码要重新 `cp -r` 同步**；`extensions/blender_org/mmd_tools` 必须存在否则报 No module named）
- 探针/测量脚本集合：`f:\mocap_ai_doctor\.blender_test_tmp\e2e_ground_feet_20260928\`（probe_p0.py = Phase 0 诊断、run_ground.py/run_full.py = 沙盒跑步骤、measure_v2.py/probe_lift.py 等 = 测量）

## 6. 记忆文件索引（Claude Code 的持久记忆，纯 Markdown，直接读）

目录：`C:\Users\George\.claude\projects\f--mocap-ai-doctor\memory\`

| 文件 | 内容一句话 |
|---|---|
| `MEMORY.md` | 索引 |
| `user-communication-prefs.md` | **必读**：中文、只报事实、不擅自开 subagent |
| `mocap-doctor-project.md` | 插件形态、16 步、版本、git 目录是 .repo_git |
| `mocap-doctor-ground-feet.md` | **必读**：贴地锁定的完整演化史（1.1.0 容差→1.2.0 弹道→1.3.0 落差/槽修复），含全部实测数字与坑 |
| `mocap-doctor-bake-leg-fk.md` | 三处 nla.bake 参数；导出前删六根腿 FK 保足 IK |
| `gvhmr-frontend-pivot.md` | 换 GVHMR 前端的决策与 A/B bmap 实测 |
| `gvhmr-foot-pivot-failure.md` | 脚掌原地内收外展识别不了；新方案先拿 0999 验 |
| `source-vertical-drift.md` | 源整体上飘；整平要移动骨架物体，别写骨骼通道 |
| `posecapture-pack-facts.md` | 一键包结构、脚滑修复、FK VMD 导出 |
| `mmr-receiver-vmd-qa.md` | VMD 回导验收流程；付与绑定误删事故；e2e 隔离协议 |
| `blender-headless-pitfalls.md` | headless 保存丢贴图、stale 状态静默 no-op、转义坑 |
| `blender-slotted-action-slot-binding.md` | 4.4+ 槽绑定 bug（穿地修复中招）；排查口诀 |
| `hand-occlusion-detection.md` | 手部故障要用可见性抓，运动统计量抓不到 |
| `hand-finger-lateral-bend.md` | PIP/DIP 侧弯待修，只能在 pkl 层修 |
| `mocap-doctor-history-archive.md` | 历史对话存档位置 |

## 7. 代码地图（`mocap_doctor/`）

- `workflow.py`：13 步表（顺序唯一来源）。1.6.0 起手部链移出向导：source_check(2) → source_floor(3) → contacts(4) → retarget(5) → … → foot_lock(10) → mmd_bake(11) → export_prep(12) → export(13)；手部坏段修复改在**导入前**的「源手部修复」预检区块（面板未建项目时显示，操作 merged pkl）
- `core/target.py`：`ground_feet_outside_airborne`（贴地+弹道核心，GRAVITY/BALLISTIC_MAX_FRAMES/MAX_CORRECTION 常量）、`model_sole_offset`（踝-鞋底落差实测）、`sole_contact_offsets`（踝→足底骨内向量，roll-aware 贴地高）、`lock_foot_ik_xy`（位置锁，**保留**）、`stabilize_planted_feet` + `_segment_lock_weights`（**Phase 1 闭环稳定**）+ `_settle_pelvis_for_reach`（**Phase 1b 骨盆修约**，PELVIS_CORRECTION_MAX/SMOOTH_FRAMES/DEADBAND、SOURCE_LEG_BONES f_avg_*/MODEL_LEG_BONES 足.ひざ.足首、DEFAULT_PELVIS_BONE=torso_root）、`_ballistic_z`/`_pin_corrections`/`_smooth_limit_grounded`（纯函数，有单测）
- `core/animation.py`：`ensure_action_slot`（4.4+ 槽绑定修复，在 `ensure_action` 和 `begin_action_preview` 调用）
- `annotation.py`：NLA 标注编辑器全套；HAND_L/R_AUTO+MANUAL 通道保留（预检手部标注复用，`hand_ranges` 只剩频道组键）；`set_hand_auto_hints`/`set_air_auto_ranges`（自动提示**非破坏性**：轨道非空不覆盖）；创建新区间后不选中任何 strip
- `core/pkl_hand.py`（**新增，纯 numpy 无 Blender**）：`find_take_pkls`/`detect_candidates`（腕/指旋转帧差+HF 残余，度地板 15/10/8° + 封顶 45°）/`repair_pkl`（hold/bridge/smooth 三策略写 `body_pose` 腕列 57:63 与 `*_hand_pose`，段外+其它字段逐字节断言不变）；手工段策略=`hand_pkl_strategy` prop（auto→自动段用建议策略/手标段 bridge）
- `operators.py`：`MD_OT_PklHandDetect`/`MD_OT_PklHandRepair`（预检按钮）、`enter_annotation_mode` 的 HAND 组不再需要项目；`_run_ground_feet`、`_run_foot_lock`、其余不变
- `project.py`：`SCHEMA_VERSION = 6`（5→6 迁移：current_step≥5 减 3、≤4 钳到 source_floor、删 source_analyze/hand_ranges/hand_repair 孤儿记录）；预览/检查点/回滚机制
- `presets.py`：DEFAULTS（地面相关已全零；target_floor_strength 1.0、smooth_radius 0、max_delta 0.01）、MMR_LEG_CONSTRAINTS 等固定名
- **`core/agent_*`（1.6.0 新增，"新方案.txt" 落地）**：`agent_bake.py` 逐帧世界姿态烘焙+npz 缓存（`bake_bone_samples`/`load_or` save，`BAKE_VERSION`）；`agent_signals.py` 命名信号注册表（foot.L/R.{toe,ball,heel}_h/pen/clearance/yaw/yaw_rate/pivot_idx/pivot_still、pelvis.h/speed/acc/jerk、`<bone>.rot_speed`、`hf_loss.<bone>`、contact/air/jitter 掩码——掩码来自 annotation 频道）；`agent_query.py` 声明式查询七件套（get_overview/list_intervals/describe/get_series/find_events/compare/snapshot，全 JSON 进出、difflib 纠错提示、长度硬上限）；`agent_io.py` 装配（`build_store_for_scene`：`source_bake_spec` 自动吃 GVHMR/FreeMoCap 前缀 + 追加 L_Hip/Knee/Spine* 等可选角色）；`accent.py` 力量感四法（hf_reinject/ease_reshape/retime/refilter，窗口 smoothstep 渐变、端点钉 0、`hf_reinject_quats` 四元数版、`accent_metrics` 峰值加速度比指标；`apply_scalar` 为直写变体）
- **`core/agent_fx.py` + `core/agent_ops.py`（输出端写工具，按新方案"NLA Combine 层"落地）**：所有写操作=在 `mcd_agent_*` 轨上挂 Combine strip，strip action 里存**增量**（标量 desired−base、四元数 desired⊗conj(base)），两端 taper 到 identity→源 Action 永不改、revert=删 strip。`agent_ops`：`clean_jitter`（零相位）、`fix_ground`(lift/pen/float+pin_xy)、`solve_pelvis`(吃 agent_fx.pelvis_height_corrections 的 dz)、`restore_accent`(四法走 strip)、样例迁移三件套 `register_exemplar`(pre/post bake 抽残差→锚点局部系→签名+npz 存 `agent_cache/../exemplars/`)/`find_matches`(DTW 签名打分)/`apply_exemplar`(时间缩放+按转角缩放+镜像+写 strip)、`interval_signatures`、`validate`(穿地/滑步/悬空/边界跳变)、op 管理 `list_ops/revert/commit/set_preview/locked_exclusions`（log=`data_dir/agent_ops.json`）。preview/commit 只差 op 状态（strip 都可见），违规拒绝 commit 由调用方把关
- **`core/agent_bridge.py`（GUI 协作桥，opus 架构落地）**：Blender 内 socket 服务器 127.0.0.1:6211（后台线程收 JSON-lines → `bpy.app.timers` 0.07s 泵到主线程执行，bpy 永不离主线程）；预览 strip 走 `AGENT_PREVIEW` Combine 轨、commit 时挪到 `mcd_agent` 轨；写完 view_layer.update+tag_redraw+预览范围跳转+自动播放；`depsgraph_update_post` 版本号防陈旧覆盖（工具可传 expect_version）；commit 带 undo_push。20 个工具全在 `TOOLS` 表。**传输层**：`tools/agent_client.py`（我们自己的直连 CLI，`python tools/agent_client.py describe '{...}'`）；`tools/agent_mcp.py`（stdio MCP 代理→socket，任何 MCP 宿主可配）——blender-mcp 同款分层
- 新 op：`mocap_doctor.agent_server_toggle`（启停服务）、`agent_ab_toggle`（预览轨静音 A/B）；ui.py 加了 "Agent 协作" 区块（状态/端口号/客户端数/A/B 键）
- 腾空标注语义（已写进 README/PARAMETERS）：标**两只脚都不在地面**的帧；入/出点**都含播放头所在帧**（触地帧不标）；单帧小跳=同帧按入再按出；对区间长度敏感（跳高∝T²）

## 8. 测试 / 构建 / e2e 协议

```bash
# 单测（55 项，纯 Python 无需 Blender）
cd f:/mocap_ai_doctor && python -m unittest discover -s tests

# 无头环境变量（每次都要 export 这一整块）
export BLENDER_USER_SCRIPTS="F:/mocap_ai_doctor/.blender_test_tmp/e2e_45_smoke/scripts"
export BLENDER_USER_CONFIG="F:/mocap_ai_doctor/.blender_test_tmp/e2e_45_smoke/config"
export BLENDER_USER_EXTENSIONS="F:/mocap_ai_doctor/.blender_test_tmp/e2e_45_smoke/extensions"
export TEMP="F:/mocap_ai_doctor/.blender_test_tmp/e2e_45_smoke/tmp"; export TMP="$TEMP"; export TMPDIR="$TEMP"

# 改完源码先同步沙盒再跑：
rm -rf .blender_test_tmp/e2e_45_smoke/extensions/user_default/mocap_doctor && cp -r mocap_doctor .blender_test_tmp/e2e_45_smoke/extensions/user_default/

# smoke（10 项；注意脚本实际在 toe_diag_20260924 下）
"D:/blender-3.2.1-windows-x64/blender.exe" -b --factory-startup --disable-autoexec --python .blender_test_tmp/toe_diag_20260924/smoke45.py -- .blender_test_tmp/e2e_45_smoke/smoke_X.json

# 构建
"D:/blender-3.2.1-windows-x64/blender.exe" --command extension build --source-dir mocap_doctor --output-filepath dist/mocap_doctor-X.Y.Z.zip
```

**e2e 铁律**（每条都踩过）：
1. **两段式**：一段跑 operator+accept+存盘，另一段**全新会话**测量（同会话读回曲线是陈旧的，会得出假故障）
2. 沙盒脚本**别硬编码路径**，从 argv 传（曾把 A 文件场景存进 B 的副本）
3. 直接改 `obj.location` 会被动画曲线覆盖，要验传递只能改曲线
4. Windows heredoc 写非 ASCII 脚本易炸，**用文件写盘再执行**；控制台中文输出乱码，用 `grep 标记 | python -c 解析` 模式
5. 用户文件只读打开探针可以；任何写操作必须在 `cp` 出的副本上，且 `data_directory/work_filepath` 重定向到沙盒

## 9. 协作协议（用户偏好，硬约束）

- **中文回复；只报事实，不安慰不铺垫**；坏消息直说
- **未经要求不开 subagent**
- 用户是 Blender 骨架新手但熟 MMD/MMR 操作；逐步讲解骨骼机制有效
- 现行分工：agent 负责骨级测量和实现，**网格观感/视频核对由用户自己看**（给出帧号+看什么+判什么）
- 用户可能中途改主意并给出新原则，以最新原话为准；重大方向变更先确认再动工
- 版本升级节奏：用户验收后再进下一个功能；构建 zip 但**不主动提交/推送**（用户明说）

## 10. 待办清单（按优先级）

1. **[当前]** 收用户三项观测 → 实现 Phase 1 闭环稳定器 → e2e（0999+1499 两文件）→ 版本 1.5.0
2. 提交/推送积压的 1.1.0→1.4.0（用户发话才做；先做 Phase 1 可能一起打包）
3. 朋友在跑 HaMeR 可见性补丁（`pack_patch_stage1/` 的 drop-in 文件，产出 hand_keypoint_conf）→ 数据到手后给 `core/occlusion.py` 加读取器，手部遮挡检测从 ViTPose 手腕置信度升级为 HaMeR 关键点置信度
4. 手指 PIP/DIP 轻微侧弯：只能在 pkl 层修（源数据问题），轴角度量有坑（轴角符号歧义），未动工
5. 0999 备份文件（99MB）待用户决定删否
6. README/PARAMETERS 已同步到 1.4.0；Phase 1 落地时要再改 foot_lock 一节

---

## 12. Agent 协作层 → 见 `agent_reports/SESSION_2026-10-01_agent_layer.md`

本文件不更新会话细节（用户要求 HANDOFF 只保留基线交接）。1.6.0 的 agent 协作层实现细节、踩坑记录、验收情况全部在项目内 `agent_reports/` 下。

## 11. 档案位置（考古用）

- 本次完整聊天记录（JSONL，很大，仅细节考古用）：`C:\Users\George\.claude\projects\f--mocap-ai-doctor\aa6d9bb2-bcdd-486a-a34f-fb7d122b87fb.jsonl`
- 1.2.0 时代的计划文件（**已被后续决策部分取代**，仅历史）：`C:\Users\George\.claude\plans\steady-cuddling-sonnet.md`
- 历史规划/事故对话存档：见 memory `mocap-doctor-history-archive.md` 指向的位置
- 各步骤 JSON 报告：各工作文件旁 `.mocap_doctor\<文件名>\reports\`（含 foot_lock 报告里的逐帧下拉量等）
