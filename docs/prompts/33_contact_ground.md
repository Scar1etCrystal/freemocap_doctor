# 剧本 33：脚滑 / 穿地 / 悬空（slide_report · foot_lock · validate · fix_ground）

> 配合 `tools_io.md`。腿是 **IK 模式**：唯一有效的腿部控制骨是 `foot_ik.L` / `foot_ik.R`。
> `thigh_fk/shin_fk/foot_fk` 有关键帧但**改了看不见**。
> 路径占位符 `<套件>` = 套件根目录（任务块给全路径，原样替换）。

## A. 脚滑（最常见）

1. **体检**：
   ```
   <套件>/tools/agent slide_report '{"agent_id":"<ME>","side":"R","threshold_mm":10}'
   ```
   `data.rows` 按漂移从大到小排；每行有 `interval`（如 `contact.R:17`）、`frames`、
   `drift_mm`（foot_ik 头部的世界水平漂移，**毫米**，相对该段接触里最静止的一帧）、`flagged`、
   `foot_lock_args`。只处理 `flagged=true` 的行。注意 `frame_range` 只是筛选：返回的是**与之相交的
   整段**接触，drift 按整段算。
2. `claim bones=["foot_ik.R"] frames=[a−4, b+4]`：interval 模式的**实际写入窗 = 接触段两侧各扩
   blend 帧**（默认 blend=4）。写入窗超出你的 scope（比如接触段跨了 scope 边界）→ **不写**，
   在报告"遗留"里列出该段的 interval、drift_mm 和需要的写入窗。拿不准就先 `"dry_run":true`
   看返回的 `frames`。
3. **踩实**：
   ```
   <套件>/tools/agent foot_lock '{"agent_id":"<ME>","interval":"contact.R:17","lock":"xy","expect_version":<v>}'
   ```
   - `lock="xy"`（默认）：只钉水平位置，**保留高度**——脚跟抬起、脚尖滚动不受影响。首选。
   - `"xy+rot"`：再钉住脚的朝向（脚在地上拧来拧去时用）。
   - `"pos"` / `"pos+rot"`：连高度一起钉死（整只脚完全平放不动的段落才用）。
4. **复测**：`slide_report side=R frame_range=[a,b]` → 该行 `drift_mm` 应 < 1。
5. 一个 interval 一个 op。做完 `list_ops` → `save` → `release`。

## B. 下沉（穿地）/ 悬空（ground_report · fix_ground）

先知道一件事：工具量的"脚底"是**关节中心**（踝 / 前掌 / 脚尖骨的头尾取最低），不是鞋底。穿厚底鞋的
模型踩实时这些点也离地好几厘米（fixture：左 77 mm、右 81.5 mm）。所以 `ground_report` 会先从全片的
contact 标注**标定每只脚"正常着地"的高度** `contact_height_mm`，再按相对值判断：
`rel = 当前高度 − 着地高度`，rel 负 = 比平时踩地还低（下沉/穿地），接触期整段 rel 正 = 悬空。

1. **体检（实时，修前）**：
   ```
   <套件>/tools/agent ground_report '{"agent_id":"<ME>","side":"R","frame_range":[A,B]}'
   ```
   看 `data.sides.R`：`contact_height_mm`、`pen_frames`（rel < −10 mm 的帧段）、`pen_max_mm`、
   `contacts[]`（`floating:true` = 这段接触整段比平时高 > 10 mm）、`fix_ground_args`（现成参数）。
   修前数字：下沉记 `pen_max_mm`；悬空记那段 contact 的 `rel_max_mm`（验收也看它；`rel_min_mm` 一并写上）。
   想知道鞋子本身有没有陷进地面：加 `"mesh":true`，看 `data.mesh.<side>`（靴底网格最低点 − 地面，mm）。如果 warnings 说
   "接触期靴底网格整体比地面低 X mm"——那是全局偏移，**别用 fix_ground 逐段修**，报告给协调者。
2. `claim bones=["foot_ik.R"] frames=<fix_ground_args 的 frame_range>`。
3. **写入**：把 `fix_ground_args` 里的一项**去掉 `why`** 原样传（`rest_clearance` 已经是**米**，别换算）：
   ```
   <套件>/tools/agent fix_ground '{"agent_id":"<ME>","frame_range":[a,b],"side":"R",
     "loc_path":"pose.bones[\"foot_ik.R\"].location","mode":"pen","rest_clearance":0.0815,"expect_version":<v>}'
   ```
   | mode | 做什么 | 用在 |
   |---|---|---|
   | `pen` | 低于 地面+rest_clearance 的帧**往上推**到这个高度，其余不动 | 下沉/穿地 |
   | `lift` | 高于 地面+rest_clearance 的帧**往下拉**到这个高度，其余不动 | 接触期悬空 |
   | `float` | 整段钉在 地面+rest_clearance（脚跟/脚尖滚动也被抹平） | 很少用 |
   **没有 `snap`**（旧手册写错了）。**不传 rest_clearance = 0**：在穿鞋的模型上 `lift` 会把整段脚按进地里
   几厘米——所以一律用 ground_report 给的参数。
4. **复测**：同第 1 步，`frame_range` 用写入窗去掉两端 blend（fix_ground 的 blend 默认 4，返回里不回显：[a+4, b−4]）→ 下沉：`pen_max_mm ≤ 1`；
   悬空：那段 contact 的 `rel_max_mm ≤ 1`。`effect_check` 只答"动没动"。
5. ⚠ `fix_ground` 按**快照**（最初烘焙的原始动作）里的脚底高度计算。ground_report 的 warnings 出现
   "快照…与当前姿态差 > 1 mm" = 这只脚这段已经被修过（foot_lock 的 pos/xy+rot、别人的 fix_ground）——
   fix_ground 会按旧高度算错：**不写**，报告给协调者。——**你自己写完 fix_ground 之后**复测时出现这条警告是正常的
   （快照里还是修前的高度），只是别在同一段再叠一次 fix_ground。`validate` / `describe` 的穿地·悬空提示现在也按同一个标定的着地高度判断，但读的是**快照**（修完不变）——
   找问题段可以用，修后复测只用 ground_report。

## C. 顺序

同一只脚、同一段：先 foot_lock（`lock:"xy"`，水平），再 fix_ground（高度）。xy 锁不改高度，快照仍然有效；
用了 `pos*`/`xy+rot` 之后快照就过时了（见 B-5），反过来先 fix_ground 再 `pos*` 又会把抬高的结果钉回去。

## 报告
```
foot_lock @[790,853] foot_ik.R（contact.R:17 [794,849]，lock=xy）：修前 35.1 → 修后 0.0 mm（slide_report drift_mm）；op=<id> claim=<id> save=ok；看 794–849 帧
```
