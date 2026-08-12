# 文件丢失事故记录 — 2026-08-12（更正）

## 已确认事实

1. `F:\mocap_ai_doctor` 不是链接；当前目录的 NTFS File ID 为
   `0000000000000000001200000000938d`。
2. NTFS USN Journal 记录显示，`2026-08-11 15:23:31`，以下项目内容发生了连续的
   `File delete | Close`：
   - `blends`、`configs`、`reports`、`scripts` 目录；
   - 顶层的 `ai动捕修复2.md`、`run_analyze_source.sh`；
   - 这些目录中的大量 Blend、VMD、JSON、Python 脚本等文件。
3. 上述顶层对象的 `Parent file ID` 均为当前工作目录的 File ID
   `0000000000000000001200000000938d`。因此可以确认：这不是 F 盘根目录的普遍清理，
   而是一次针对 `F:\mocap_ai_doctor` 内容的递归删除；工作目录本身没有被删除。
4. 保存的 Blender 日志首行确实是：

   ```text
   tempdir_session_create: Could not generate a temp file name for
   'F:\\blender_a05432', falling back to 'F:\\'
   ```

   这证明当次 Blender 测试的临时目录隔离失败，Blender 回退到了 F 盘根目录。这是
   严重的测试配置错误。
5. 当前的
   `F:\mocap_ai_doctor\blends\teto_clean_floor_v1_footlock_xy_mocap_doctor_work.blend`
   是用户在事故后手动放入的，不能作为“由系统恢复”的证据，也不能用来推断删除来源。

## 尚未证实的事项

- USN Journal 不记录发起删除的进程、命令行或用户，因此目前不能仅凭 USN 指认
  Blender、Codex、某个子代理或其他程序为删除发起者。
- Blender 的临时目录回退与这次针对 `mocap_ai_doctor` 的递归删除在时间上接近，且构成
  高风险配置错误；但现有证据不足以证明它就是本次删除的直接原因。此前把两者直接说成
  已确认因果关系的结论已撤回。
- PowerShell 历史中目前只看到一个定义 `Remove-Item -Recurse -Force` 的函数，未看到
  在该时刻明确执行整个工作目录删除的命令；这不能排除其他进程或脚本的行为。

## 当前处理状态

- 未对 H 盘旧备份执行恢复、覆盖或合并。
- 未删除任何 USN、Blender、测试或会话日志。
- 后续若要运行 Blender，必须先在工作目录内创建并验证专用临时目录，同时设置
  `TEMP`、`TMP`、`TMPDIR`、`BLENDER_USER_CONFIG`、`BLENDER_USER_SCRIPTS`、
  `BLENDER_USER_DATAFILES`，并确认日志没有 `falling back to`；输入文件必须是测试副本。
- 在没有新的进程审计证据前，任何责任归因都应写成“未证实”，不得猜测。
