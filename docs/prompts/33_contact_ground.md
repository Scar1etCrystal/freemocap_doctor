# 剧本 33：脚滑 / 穿地 / 悬空（slide_report · foot_lock · validate · fix_ground）

> 配合 `tools_io.md`。腿是 **IK 模式**：唯一有效的腿部控制骨是 `foot_ik.L` / `foot_ik.R`。
> `thigh_fk/shin_fk/foot_fk` 有关键帧但**改了看不见**。

## A. 脚滑（最常见）

1. **体检**：
   ```
   $C slide_report '{"agent_id":"'$ME'","side":"R","threshold_mm":10}' --pretty
   ```
   `data.rows` 按漂移从大到小排；每行有 `interval`（如 `contact.R:17`）、`frames`、
   `drift_mm`（水平漂移，**毫米**）、`flagged`、`foot_lock_args`。只处理 `flagged=true` 的行，
   且只处理任务分给你的帧段。
2. `claim bones=["foot_ik.R"] frames=[a−blend, b+blend]`（interval 模式会向两侧各扩 blend 帧写入）。
3. **踩实**：
   ```
   $C foot_lock '{"agent_id":"'$ME'","interval":"contact.R:17","lock":"xy","expect_version":<v>}' --pretty
   ```
   - `lock="xy"`（默认）：只钉水平位置，**保留高度**——脚跟抬起、脚尖滚动不受影响。首选。
   - `"xy+rot"`：再钉住脚的朝向（脚在地上拧来拧去时用）。
   - `"pos"` / `"pos+rot"`：连高度一起钉死（整只脚完全平放不动的段落才用）。
4. **复测**：`slide_report side=R frame_range=[a,b]` → 该行 `drift_mm` 应 < 1。
5. 一个 interval 一个 op。做完 `list_ops` → `save` → `release`。

## B. 穿地 / 悬空

1. `validate '{"frame_range":[A,B]}'` → 看哪些帧 `foot.*.pen > 0`（穿地，米）或悬空。
2. `fix_ground '{"frame_range":[A,B],"side":"L","loc_path":"pose.bones[\"foot_ik.L\"].location","mode":"lift"}'`
   - `lift`：只把穿地的帧抬到地面；`snap`：整段贴地。
3. ⚠ `validate`/`fix_ground` 用的是**最初烘焙的快照**里的脚底高度（修完不会刷新）。
   修后复测用 `effect_check op_id=<id>` 看是否动了，或 `slide_report` 看 `z_range_mm`。

## C. 顺序

同一只脚、同一段：先 foot_lock（水平），再 fix_ground（高度）。反过来做 foot_lock 的
`pos*` 模式会把抬高的结果钉回去。

## 报告
```
脚滑 foot_ik.R contact.R:17 [794,849]：漂移 35.1 → 0.0 mm（lock=xy）；op=<id>；看 790–853 帧
```
