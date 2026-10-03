# Agent 协作层实现会话记录（1.6.0，2026-10-01）

> 项目内 memory 文件。HANDOFF.md 只保留基线交接，不写会话细节（用户要求）。

## 架构

- **服务**：`core/agent_bridge.py` — bg 线程 `ThreadingTCPServer`（127.0.0.1:6211）收 JSON-lines `{"id","tool","args"}` → `_requests` 队列 → `bpy.app.timers` `_pump()`（0.07s）主线程执行。bpy 永不离开主线程。`depsgraph_update_post` bump `_DATA_VERSION`，工具可传 `expect_version` → E_STALE。
- **客户端**：`tools/agent_client.py`（一次性 CLI）+ `tools/agent_mcp.py`（stdio MCP 代理，MCP 协议进不了 Blender 进程，只能桥接）。
- **UI**：N 面板「Agent 协作」框（server 开关/端口/客户端数/last_tool/last_error + A/B 对比键）。
- **写工具 = delta strip**：`_write_strip` 生成新 Action 装 delta 曲线，挂 `AGENT_PREVIEW` 轨 COMBINE；commit=挪 `mcd_agent` 轨+记 log；revert=删 strip。`strip.influence` 可拖。

## 统一信封

`{ok, tool, version, summary, data, warnings, truncated, hint, error:{code,message,fix}}`。错误码 E_STALE/E_SCOPE/E_UNKNOWN(近似建议)/E_RANGE/E_TOOL(带 trace)。写工具走 `_op_envelope`（op_id/metrics/preview.track/frames）；判断条件是 dict 含 `strip`/`id`，裸 dict 落 `data`——**不要靠"含 summary 键"判断**（踩过）。

## 踩过的坑（按发现顺序，都验证过）

1. **`load_bake` 键名错**：写了 `bake["point"]` 但初始化键是 `point_pos` → 缓存命中必崩。（subagent 逮的）
2. **`_mask` 只吃元组**：`scene_intervals` 产 dict 项 `{id,start,end}`，`item[0]`→KeyError:0。修成兼容两种。
3. **`basis` 不落盘**：npz 缓存只存 quat/pos/point——缓存一命中，finger.* 聚合信号和 get_joint_angles 全静默丢失。修 `basis::` 键往返 + 发现缺键返回 None 强制重烘。"手指不在烘焙集"假象的根源。
4. **NLA 栈顺序**：活动 action 在栈顶 REPLACE，盖掉所有下层 COMBINE delta → `ensure_base_on_nla` 把 base action 压成 `mcd_base` 轨的 REPLACE strip、`anim.action=None`。**Blender 4.x `nla_tracks.move()` 不存在**，顺序只能靠创建顺序（new() 落栈顶=最后求值=最强）。
5. **四元数 Combine 是右乘**：`result = lower ⊗ strip^influence`（nla_combine_quaternion）。delta 必须 `conj(base) ⊗ desired`（`agent_fx.delta_quat`），`desired ⊗ conj(base)` 的左乘方向会反向弯。
6. **`eval_bpy` 作用域**：env 要当 globals 传（`eval(expr, env, env)`），comprehension 只看得见 globals；safe_builtins 用 `import builtins` 取，别用 `__builtins__`（模块语境下是 dict 会落空，表现是"有的 builtin 有有的没有"）。
7. **服务卡死**：Blender 主线程被占时 timer 泵饿死 → socket 超时无响应。面板重启服务恢复；自愈/心跳**未做**。
8. **A/B 键失效**：`commit` 会把 strip 从 `AGENT_PREVIEW` 挪到 `mcd_agent`，而 ab_toggle/UI 按钮只 mute preview 轨 → 空轨静音无效果。修成 mute **所有 agent 轨**（preview + mcd_agent + mcd_agent* 前缀），mcd_base 除外；方向取"还有一个响着就全静音"。
8. **UTF-8**：agent_client/agent_mcp 开头 `sys.stdout.reconfigure(encoding="utf-8")`，否则 pwsh 里中文 GBK 乱码。

## hold_pose 语义（1499 实测）

- `target=values`（默认 identity=回零位伸直，**不猜骨骼轴向，最稳**）
- `target=from_frame`（`ref_frame="auto"` 自动挑区间内摆动角最小帧=最标准帧）
- `target=world_dir`（每帧反算让骨轴指向世界向量——**骨 Y 轴方向语义容易猜错**，那次错了手指反向弯）
- `mode=replace|clamp(超阈值压回)|outlier(坏帧用前后好帧 slerp)`；`strength`→`strip.influence`；scope ≤24 骨。
- 验收：左食指 505-570 伸直（values+replace），`hold_pose_870415531` committed。effect_check 实测 537 帧指尖位移 40mm/旋转 132°。

## 工具清单（22）

读：get_overview/list_intervals/describe/get_series/find_events/compare/snapshot/get_joint_angles/validate/bake_range
写：clean_jitter/fix_ground/solve_pelvis/restore_accent/hold_pose/apply_exemplar
管理：list_ops/revert/commit/set_preview/ab_toggle/effect_check/eval_bpy/ping

## 手指信号

`finger.{L,R}.{index,middle,ring,pinky,thumb}.{curl,flex1-3,up_err,azimuth}` —— swing-twist 分解（`agent_fx.swing_twist_deg`，注意 wxyz 里骨轴 Y 是**列 2** 不是列 1）。curl=三节摆动角和，伸直≈0°。

## 2026-10-01 深夜：架构定案——agent 改到 RIG 骨架修

**用户确认的事实**：f_avg 源 → RIG → Teto 是烘焙链路，源骨架上的修复 Teto 看不见。arue Teto 骨架**自己没有 action**（115 个约束全是 COPY_TRANSFORMS ← RIG），真正的"Teto 骨架"= `RIG-*` MMR 控制架（有烘焙 action，503 内部约束）。

**RIG 骨架现状**（1499 工作文件实测）：
- 有 action 的控制骨：`f_index.01-03.L/R`、`f_middle/f_ring/f_pinky.01-03.*`、`thumb.01-03.*`（拇指不带 f_ 前缀）、`foot_ik.L/R`、`hand_fk.L/R`、`forearm_fk.*`、`upper_arm_fk.*`、`spine_fk/.001/.003`、`neck`、`head`、`shoulder.L/R`、`thigh_fk.*`、`shin_fk.*`、`torso_root`、`thigh_ik_target.*`
- DEF- 形变骨（`DEF-foot.*`、`DEF-toe.*`、`DEF-f_index.*`…）在 data.bones 里但没有 fcurve（约束驱动）

**决策（grilling 定案）**：
1. agent 层全部搬到 RIG——`_rig_armature()`（`settings.mmr_rig` 优先、否则扫 `RIG-*`）；`get_store`/`effect_check`/`ab_toggle` 目标全换
2. **只留 RIG spec**（`agent_io.rig_bake_spec`，角色名不变、骨名换成 MMR 控制名）；源 spec 函数留着当废案不删
3. 骨名解析 `_resolve_bones`：字面骨名 + 角色名（`finger_l_index1`→`f_index.01.L`）都认
4. **向导防护**：`mmd_bake` 步检查到 RIG 上有 agent 轨就报错"先 commit/revert"（保证 base strip 指向的 action 不会被中途换掉）
5. Teto 导出不用动——RIG 的修改自动随 COPY_TRANSFORMS 进形变层
6. 向导 13 步不变（还是跑在源骨架上）
7. **自愈**：`_pump` 全 try/except + `_watchdog` 2s 检查重注册 + `status().pump_age_s/pump_registered`；`unregister()` 先 `stop_server()`（tbbmalloc 退出崩溃嫌疑）
8. **A/B 修复**：mute 所有 agent 轨（preview+committed），`mcd_base` 除外

**bake**：RIG 骨架会重新 bake 一遍（`tag="rig"`，与 gui 缓存分开，不互相污染）。

---

## 2026-10-02：每条修复独立力度（per-fix strength）落地

方案见 `docs/方案_每修复力度调节.md`。五条决策（列表+单滑块 / 每条一轨 / committed 可调 / 删全局滑块 / 行内静音）全部实现并验证。

### 关键实现事实（踩过的坑，别再犯）

1. **面板 draw 禁止写 ID**：在 `draw()` 里调迁移/建轨 → `Writing to ID classes in this context is not allowed: ... error setting NlaTrack.name`。所有重建/迁移改由 **fixlist 定时器**（1s）执行；draw 只读，失步时显示"列表同步中…"并顺手拉起定时器（注册定时器不是 ID 写）。另加 `load_post` 重新挂表 + 常驻「刷新」按钮（操作符上下文）三重兜底。
2. **NLA 结构改动会让已有 RNA 指针失效**（`ReferenceError: StructRNA of type NlaStrip has been removed`）——迁移必须"先快照（只存名字+参数）→ 建新轨 → 删源 → 改名"，且每步后按名字重新取指针。测试里读已删对象同理。
3. **NLA strip 不支持自定义属性**（连 `.get()` 都抛 `TypeError: this type doesn't support IDProperties`）——力度指数存 **action** 的 `applied_exp`。
4. **strip.influence 硬上限 1.0**，拖不过 1；"力度"= 把 delta 曲线的旋转角按指数重写（轴角缩放，方向不变），influence 恒 1。
5. **op id 会撞号**：`_new_op` 用毫秒时间戳，同 tick 两次写入重号——`_record` 里对照 log 去重（`_2` 后缀）。
6. **strip 名跨骨架会重名**：`find_op_strip` 不能"找不到轨就按名兜底"，否则源骨架废案 op 会抢 RIG 的同名 strip（撤销会误删活修复）。规则：有 `track` 字段就严格按轨找（找不到=丢失，不兜底）；旧条目（无 track）只能在旧式共享轨（AGENT_PREVIEW/mcd_agent*）上认领。
7. **行内控件只对活行有意义**：丢失行（strip 已不在场景）的静音眼睛点了没反应（回调找不到轨→静默返回），观感是"死按钮"。已删掉行内眼睛，力度/静音移到底部作用于选中行，且 `item.alive=False` 时整行控件置灰。
8. **committed ≠ 搬轨**：commit 只改 log 状态，strip 留在自己轨上（仍可调力度/静音）。revert = 删 strip + action + 空轨。

### 验证

- `tests/`：81 单测全绿
- `.blender_test_tmp/e2e_perfix.py`：17/17（重叠双写、每条一轨、力度 1.6→1.60x / 0.4→0.40x、单条静音隔离、迁移幂等、丢失/未登记对账、存盘重开力度保留）
- `.blender_test_tmp/e2e_perfix_ui.py`：15/15（面板回调链：滑块写 action、眼睛写轨、重建读回真值、提交/静音/刷新/撤销按钮、alive 标记）
- `.blender_test_tmp/e2e_fixlist_timer.py`：7/7（定时器迁移旧布局、二次 tick 稳定、rev 变化跟上、启停正常）

### 顺带修的

- `mmd_bake` 不再被 agent 轨卡死：放行 agent 轨（它们的修正会被 visual keying 烘进 MMD），范围检查改读 `mcd_base` 的 action；只拦陌生轨。
- 面板错误行改为**服务未运行时也显示**（fixlist 定时器的异常以前被藏住）。

---

## 2026-10-02 下午：restore_accent 四元数修复（力量感开工前提）

**旧 bug**：`restore_accent` 对 `rotation_quaternion` 通道按**分量差**写标量 delta——但 NLA COMBINE 对四元数是**乘法**（`结果 = 底层 ⊗ strip`），分量差写进去得到方向错误的旋转。脊柱/四肢这类纯旋转骨的力量感**从来没正确生效过**。

**修法**：quaternion 通道 = 四分量同窗同参数重塑 → 归一化 → `delta_quat(new, cur)`（真四元数 delta）；location 通道 = 三轴一条 op 同步重塑（同一速度增益曲线，时间一致）；其他通道维持单分量。bridge 的 `index` 变可选（quaternion/location 路径忽略）。

**顺带**：bridge 五个写工具（hold_pose/clean_jitter/fix_ground/solve_pelvis/apply_exemplar）还在硬传 `track_name=PREVIEW_TRACK`——socket 调用会挤回共享轨，全部改默认 per-op 轨。

**验证**（`e2e_accent.py`，扫描出的高运动窗 853-872）：8/8——delta 全为单位四元数、边缘连续 0.000°、发力帧位移与 metric 吻合、**到达角速度 1.94→5.31°/f**（剖面从减速进姿势变为加速撞进发力帧）、location 三轴一条 strip。

**测试教训**：验证"变脆"必须选高运动窗口 + 断言**到达帧的瞬间速度**（不是窗口峰值——静止段或窗外快动作会淹没信号，连续两轮栽在这）。

**力量感工作流**（用户已确认）：用户在时间轴打标记（M 键）→ 描述每处想要的方向 → 我读标记（eval_bpy 读 `scene.timeline_markers`）→ 查信号（pelvis.acc/jerk、rot_speed、hf_loss）→ restore_accent 写预览 → 用户 A/B + 每条力度滑块微调。用户明确：源数据已被滤过一次，高频找不回来（hf_reinject 不可用），走 ease_reshape。首单：下腰分两下起身，标记 F22/F39 为每下终点，各来一发"变脆"。

**遗留**：①已 commit 的源骨架食指修复留着当废案（源码侧的 strip 还在，Teto 无视它）；②服务卡死自愈已做待实测；③面板参数 UI/计划列表/spawn_subagent 等没做；④骨架选择参数 `armature="rig"` 没做——用户选了"只改 RIG 修"所以没留双轨。
