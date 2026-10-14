# 回滚 / 恢复脚本（会话 session-2c3a0cb5）

## 0. 摘要（compaction）路由已改为 DeepSeek-V41-Flash + max

2026-10-06 11:44 写入 `C:\Users\George\.dsh\profiles\desktop\cordis.patch.yml`（profile patch 层）：

```yaml
- id: preset-standard          # 按 Loader 行 id 覆盖随附的 standard preset 声明
  name: '@deepseek-ai/dsh-agent-preset'
  config:
    id: standard
    order: 1
    plugins:
      ...                      # 与随附声明逐行相同（32 行，含嵌套 group）
      - id: compaction-basic
        name: '@deepseek-ai/dsh-compaction-basic'
        config:
          summarizationProvider: deepseek-official
          summarizationModel: deepseek-flash
      ...
- id: llm-deepseek             # 该路由的默认思考强度（摘要调用不带 effort，取的就是它）
  name: '@deepseek-ai/dsh-llm-deepseek-api-key'
  config:
    reasoningEffort: max
```

- 随附声明原件在 `app.asar` 内：`@deepseek-ai/dsh-web-app/presets/standard.patch.yml`
  （已导出到 `asar_extract/presets_standard.patch.yml` 供比对）
- 覆盖合法性依据：app 自带 skill `editing-cordis-compositions` 的 “Change a shipped preset” 一节
- 生成脚本 `build_patch.py`（生成 `patch_addition.yml`）、校验脚本 `verify_patch.mjs`
  （逐行比对 32 个插件行，只允许 compaction-basic 多出这两项；并校验整份 patch 的 YAML）
- 备份：`backup\cordis.patch.yml.before-summary-route-<时间戳>`
- 生效条件：**重启 DSH**（patch 层在启动时合成）
- 回退：把备份覆盖回 `C:\Users\George\.dsh\profiles\desktop\cordis.patch.yml`（或删掉文件末尾这两段）
- 验证：拿一个可丢弃的会话跑 `/compact`，在它的 session 日志里看 `compaction/summary`：
  `provider` 应为 `deepseek-official`、`model` 应为 `deepseek-flash`
  （用 `rollback.py <日志> 0` 可打印日志里的记录类型分布）

## 背景

`session-2c3a0cb5-3175-4358-a29a-34ccc991b9da`（工作区 `F:\mocap_ai_doctor`，标题「阅读 HANDOFF.md 准备接手工作」）
在 2026-10-06 01:26 执行了一次 `/compact`：

- `compaction/summary`（seq 11428）把 seq **[9696, 11413]** 的 593 个表层节点（约 424,522 tokens）
  替换成了一小段摘要；
- 但该摘要实际是失败的：摘要模型（`gpt2 / gpt-6.1-sol`，maxTokens 65536）把输出预算花在推理上，
  最终只写出 ~150 tokens 正文（`rawOutput` 里全是 reasoning），**没有**触发 maxTokens 截断错误，
  因此 `compaction/end` 记成了成功。结果会话上下文从 437,636 tokens 掉到 13,268 tokens。

## 已做的回滚

- 备份（原始日志、原始投影缓存）：`F:\mocap_ai_doctor\.session_recover\backup\`
- 回滚后的日志（可直接覆盖使用）：`backup\restored-session.v4.jsonl.zstd`
- 回滚点：**seq 11423（turn 168 的 `turn/end`）**，即 `/compact` 之前最后一刻
  - 丢弃的记录：`model/selection ×2`、`command/run`、`compaction/start`、`compaction/summary`、
    替换用的 `user/message`、`compaction/end`、`command/done`（共 8 条）
  - 回滚后：11424 条记录（seq 0..11423），表层节点 **596**（回滚前只有 4）
- 投影缓存 `storages\session_projcache\sessions\session-2c3a0cb5-*.json` 已移走（缓存会按日志重建）

## 重新应用（万一被宿主进程覆写 / 追加污染）

先**完全退出 DSH**，再执行：

```powershell
pwsh -File F:\mocap_ai_doctor\.session_recover\restore-rollback.ps1
```

## 撤销回滚（恢复成 compact 之后的原样）

```powershell
pwsh -File F:\mocap_ai_doctor\.session_recover\restore-rollback.ps1 -Undo
```

## 验证回滚结果

```powershell
& "C:\Users\George\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" `
  F:\mocap_ai_doctor\.session_recover\rollback.py `
  "C:\Users\George\.dsh\sessions\--F-mocap_ai_doctor--\session-2c3a0cb5-3175-4358-a29a-34ccc991b9da\session.v4.jsonl.zstd" 11423
```

期望输出：`records : 11424 (last seq 11423 turn/end)`、`surface CURRENT : 596 nodes`。

## 注意

- 回滚后**必须重启 DSH** 再打开该会话；否则宿主内存里仍是 compact 之后的旧状态，
  在该状态下继续对话会以 seq 11432 追加，和磁盘上的 seq 11423 之间出现断号 → 日志损坏。
- 原日志格式未变（仅裁掉尾部 8 条记录），只是重新分帧写回（首帧仍然只有 header 行）。
