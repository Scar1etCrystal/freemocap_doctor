# 用户偏好丢失事故记录 — 2026-08-13

## 已确认事实

1. `C:\Users\George\AppData\Roaming\Blender Foundation\Blender\4.3\config\userpref.blend`
   于 `2026-08-13 10:54` 被重写（mtime、大小 176,580 字节）。用隔离会话读取其内容确认：
   文件内容为**出厂默认偏好**，仅启用了 `bl_ext.user_default.mocap_doctor`。
   用户 4.3 的原偏好（启用的插件清单、主题、键位等）随这次覆盖丢失。
2. 同一时间 `...\4.3\extensions\user_default\mocap_doctor` 被更新为 0.1.16
   （manifest version 0.1.16，目录 mtime 10:54）。原计划的隔离安装目录
   `e2e_vmd_016_20260813\ext_install` 保持为空——隔离没有生效。
3. 10:54 执行的是 0.1.16 的"隔离安装注册测试"命令
   `--command extension install-file --repo user_default --enable`。该命令把
   `MCD_TEST_BASE` 与 `TEMP/TMP/TMPDIR/BLENDER_USER_CONFIG/BLENDER_USER_SCRIPTS/
   BLENDER_USER_DATAFILES` 放在**同一条 export 语句**里。bash 在同一 export 中先展开
   所有单词再赋值，`$MCD_TEST_BASE` 展开时为空，于是 `BLENDER_USER_CONFIG/SCRIPTS/
   DATAFILES` 变成了 `/config`、`/ext_install`、`/datafiles` 这类无效路径，Blender
   静默回落到真实 AppData；回落的告警日志被命令末尾的 `tail -3` 截掉，未被发现。
4. 复现验证（2026-08-13 11:16–11:18，全部在隔离目录内进行）：
   - `--command extension build`（env 正确隔离）**不写** userpref.blend，隔离 config
     目录保持为空。
   - `--command extension install-file`（env 正确隔离、因目标仓库枚举报错而安装失败）
     在退出时**仍写** userpref.blend（176,404 字节）到 `BLENDER_USER_CONFIG` 指向的
     目录。即：该命令退出必写偏好文件；env 正确时写入隔离目录，env 失效时写入真实
     AppData。
   - 普通 `-b --factory-startup` 脚本会话不写 userpref.blend（隔离 config 目录始终为空）。
5. 结论：真实 `userpref.blend` 的 10:54 覆盖来自 install-file 命令的退出写偏好，
   根因是第 3 条的 export 链式赋值 + `tail -3` 截断告警。`extension build` /
   `extension validate` 两个未隔离运行经复现验证不会写偏好文件。
6. 用户 4.3 偏好没有备份：config 目录中无 `userpref.blend@`；4.2 版本的偏好文件
   （6 月 21 日）与 4.3 不兼容，且以其作为会话偏好加载会连带加载真实 blender_org
   插件并在启动阶段崩溃，不能用于恢复。
7. 幸存内容：全部插件文件（`4.3\extensions\` 各仓库与 `4.3\scripts\addons\`）、
   `recent-files.txt`（09:30）、`bookmarks.txt`（09:30）、`startup.blend`。
   用户 09:30 的正常 GUI 会话记录（recent-files.txt 时间戳）证明 09:30 时偏好完好。

## 尚未证实的事项

- 未能从会话转录文件中提取 10:54 命令的完整原文（转录解析未成功），"单条 export
  链导致 env 失效"这一机制由空 ext_install 目录 + AppData 实际安装 + 复现实验共同
  推断，尚未直接核对命令文本。
- build / validate 两个无 env 运行在 10:52–10:53 是否写过 config 目录无法分辨
  （10:54 的覆盖已由 install-file 完全解释，此点不影响结论）。

## 当前处理状态

- 未对 AppData 做任何恢复或修改。真实 userpref.blend 自 10:54 起未被再次写入
  （md5 `2af4ecea15840ce7f0639ebf9f6611c2` 复查一致，mtime 仍为 10:54）。
- 测试残留：`F:\blender.crash.txt`（读取 4.2 偏好实验产生的崩溃日志）已删除；
  `repro_*` 目录位于 gitignored 测试区 `.blender_test_tmp\e2e_vmd_016_20260813\`。
- mocap_doctor 0.1.16 已装在真实 user_default 仓库并处于启用状态——这是用户需要
  测试的版本，但本次安装未经过用户确认。

## 后续安全规则（并入运行协议）

1. env 变量一律**逐条 export**、使用绝对路径；禁止在同一条 export 中引用尚未赋值的变量。
2. 每次 Blender 运行后检查**完整日志**（不得用 tail 截断）中的 `falling back to`。
3. `extension install-file` 及任何带 `--enable` 的命令退出时必写偏好文件，
   必须且只能与有效的 `BLENDER_USER_CONFIG` 隔离配套使用。
4. `extension build` / `validate` 虽经验证不写偏好，也一律带完整 env 隔离运行。
