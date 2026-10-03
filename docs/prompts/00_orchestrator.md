# 协调者提示词（主会话：拆任务 → 派 3–5 个 socket agent → 收数字 → 终审）

## 0. 开工前

```bash
K=/home/sb/remote_kit_1.7.1
bash $K/tools/mcd.sh status                     # 内存、Blender 锁
bash $K/tools/mcd.sh server-start <工作文件.blend>  # 起 headless 服务（占用唯一的 Blender 名额）
/home/sb/remote_kit_1.7.1/tools/agent ping '{}'  # 工具表里要有 claim / plan_scopes / 你要用的工具
```
- 机器只有 ~8GB：**同时只能有 1 个 Blender**。服务开着时不能跑 e2e（mcd.sh 会排队等）。
- 先 `list_ops` 看文件里已有的修复（别让 agent 在用户已有修复上乱叠）。

## 1. 拆任务（每条 = 一个剧本 + 一个 scope）

用户反馈协议：**帧段 + 部位 + 问题 → 想要的样子**。每条映射成：

| 问题 | 剧本 | scope 写法 |
|---|---|---|
| 朝向 | 30 | `bones:[owner]`（先 probe 拿 owner）× 帧段 |
| 抖 | 31 | 骨 × 帧段 |
| 打击感 | 32 | 骨 × 帧段 |
| 脚滑/穿地 | 33 | `foot_ik.L/R` × 接触段±blend |
| 复制/镜像 | 34 | **目标**骨 × **目标**窗 |
| 预备/跟随/过冲 | 35 | 链 × 帧段 |
| 重叠/改节奏 | 36 | 链 × 帧段 |

帧段两端要留 `blend`（默认 3–4）帧余量：有效区是 `[A+blend, B−blend]`。

## 2. 派单前体检（让 agent 天然避开同一段关键帧）

```bash
/home/sb/remote_kit_1.7.1/tools/agent plan_scopes '{"tasks":[
  {"name":"左臂预备","chain":"arm_nofingers.L","frames":[550,603]},
  {"name":"右脚脚滑","bones":["right_foot"],"frames":[790,853]},
  {"name":"脊柱去抖","chain":"spine_head","frames":[500,620]}]}'
```
- `data.waves`：建议批次。**同一批内并行派**（≤5 个），下一批等上一批 release。
- 规则：同骨 + 帧重叠 = hard，必须不同批；父子骨（脊柱 vs 手臂、前臂 vs 手）= related，
  父骨的任务先做（父骨一动，子骨的世界朝向就变，子骨任务要基于新姿态）。
- `vs_claims` 非空 = 现有租约挡路（上一批没 release / 有人还在干）。

## 3. 每个 agent 的提示词 = 三段拼起来

1. `tools_io.md` 全文（通用协议 + 单位 + 工具表）
2. 对应剧本全文（30–36）
3. 任务块：
```
模型：sonnet
你的 agent_id：<短名，如 armL-anti>
任务：<一句话：帧段 + 部位 + 问题 → 想要的样子>
scope：<骨/链> × [A,B]。只许写这里。先 claim。
验收：<剧本里的指标 + 目标值>
完成后：list_ops（owner=你，compact）自查 → save（允许：它是协议的一部分）→ release →
按 tools_io §8 的格式报告；不许改任何源码/文档文件、不启动 Blender
```

## 4. 收单检查（每份报告都过一遍）

- 有修前/修后**数字**，且数字来自实时类读工具（probe_anatomy / analyze_motion / compare_motion /
  chain_lag / slide_report）。"应该没问题" = 没做完。
- `list_claims` 里该 agent 已 release；`list_ops` 里它的 op 都是 `preview`、`alive=true`、owner 正确。
- 报告里说"层级相关"的，安排对应子骨任务的 agent 复测。
- 最后协调者自己 `save` 一次，`list_ops` 对账：`fixes` 里没有 `lost` / `unregistered`。

## 5. 收尾

**等所有 agent 的报告都到了**（不是只看它 release 了——有的 agent release 后还会再复测一次）
再 `bash $K/tools/mcd.sh server-stop`（之前先 save！）→ 需要回归时跑 `20_verifier.md`。
