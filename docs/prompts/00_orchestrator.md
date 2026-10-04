# 协调者提示词（主会话：拆任务 → 派 3–5 个 socket agent → 收数字 → 终审）

## 0. 开工前

```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh status                     # 内存、Blender 锁
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-start <工作文件.blend>  # 起 headless 服务（占用唯一的 Blender 名额）
/home/sb/remote_kit_1.7.1/tools/agent ping '{"agent_id":"coord"}'  # 工具表里要有 claim / plan_scopes / 你要用的工具
```
- 机器只有 ~8GB：**同时只能有 1 个 Blender**。服务开着时不能跑 e2e（mcd.sh 会排队等）。
- 先 `list_ops` 看文件里已有的修复（别让 agent 在用户已有修复上乱叠）。
- `conventions '{"agent_id":"coord","frame":<用户提到的帧>}'`：角色这一帧面朝哪、镜头/视口在角色哪一侧（画面左右是否镜像）、
  哪条腿/胳膊是 IK、帧号怎么对应视频。把用户的"朝前/左/朝镜头"翻成方向词（`forward` `char_left` `camera` …）再写进任务块。
- 朝向类任务（掌心/脚底/膝/肘/脸/胸/骨盆）开工前 `markers '{"agent_id":"coord","action":"check"}'`：有用户绑的箭头就以它为准
  （check 会把场景里用户自己的 SINGLE_ARROW 也体检一遍：绑错侧、顶点父级在另一只手、没父级、带关键帧都报 error + fix；
  status=ok 的用户箭头 `action:"adopt"` 收编）；没有就 `action:"create"`（默认 palm/sole/knee/elbow）建好，告诉用户在视口里
  过一眼。膝/肘的标记是刚性的（绑小腿/前臂，直腿也有定义）；想看当帧凸出角平分线才用 `bake`（`MCD_bake_*`）。
- 用户只给了模糊说法（"左手那一下"、"膝盖别内扣"）：`orient_report` 把现状翻成人话、对着用户的话核对一遍再派单；
  能看图就 `render_view` 渲一张给自己/用户看。

## 1. 拆任务（每条 = 一个剧本 + 一个 scope）

用户反馈协议：**帧段 + 部位 + 问题 → 想要的样子**。每条映射成：

| 问题 | 剧本 | scope 写法 |
|---|---|---|
| 朝向 | 30 | `bones:[owner]`（先 probe 拿 owner）× 帧段；**膝/肘** = swivel 的控制骨（IK 腿 `thigh_ik.L`，FK 臂 `upper_arm_fk.L`+`hand_fk.L`） |
| 抖 | 31 | 骨 × 帧段 |
| 打击感 | 32 | 骨 × 帧段 |
| 脚滑/穿地 | 33 | `foot_ik.L/R` × 接触段±blend |
| 复制/镜像 | 34 | **目标**骨 × **目标**窗（镜像时是另一侧：源 arm.L → scope 写 arm.R）+ `reads` = 源骨 × 源窗。注意 motion_copy 调用里的 `chain` 是**源** |
| 预备/跟随/过冲 | 35 | 链 × 帧段 |
| 重叠/改节奏 | 36 | 链 × 帧段 |

**用户给的帧段 = 要生效的区域**。写入窗 = 两端各外扩 `blend`（默认 4）帧：`[A−4, B+4]`，scope 也写外扩后的窗；
复测/验收都在用户帧段上量（复制类：源窗和目标窗同样外扩，副本才能整段到位——2026-10-04 Haiku 第一轮照着没外扩的例子
复制，用户帧段两端 4 帧差 55°）。
**"第 N 帧那一下"类任务**：任务块里写清楚是哪一侧、哪一下（先用 analyze_motion [N−12, N+25] 确认 peak_frame ≈ N，把 onset/stop
写进任务块）——窗口里有更快的另一下动作时 analyze_motion 会挑那一下（Haiku 第一轮就加到了前一下回收动作上）。

## 2. 派单前体检（让 agent 天然避开同一段关键帧）

```bash
/home/sb/remote_kit_1.7.1/tools/agent plan_scopes '{"agent_id":"coord","tasks":[
  {"name":"左臂预备","chain":"arm_nofingers.L","frames":[550,603]},
  {"name":"右脚脚滑","bones":["right_foot"],"frames":[790,853]},
  {"name":"脊柱去抖","chain":"spine_head","frames":[500,620]},
  {"name":"复制手势","chain":"arm.L","frames":[1430,1480],"reads":{"chain":"arm.L","frames":[630,680]}}]}'
```
- **复制类任务要写 `reads`**（源窗）：别的任务改到这段源，`plan_scopes` 会报 `kind:"read"` 并把改源的任务排在前面
  （否则复制的是改之前的旧姿态）。时间平移/重叠/变速只读自己的窗口，不用写。
- `data.waves`：建议批次。**同一批内并行派**（≤5 个），下一批等上一批 release。
- 规则：同骨 + 帧重叠 = hard，必须不同批；父子骨（脊柱 vs 手臂、前臂 vs 手）= related，
  父骨的任务先做（父骨一动，子骨的世界朝向就变，子骨任务要基于新姿态）。
- `vs_claims` 非空 = 现有租约挡路（上一批没 release / 有人还在干）。

## 3. 每个 agent 的提示词 = 四段拼起来（tools_io + 剧本 + 11_socket_worker + 任务块）

1. `tools_io.md` 全文（通用协议 + 单位 + 工具表）
2. 对应剧本全文（30–36）
3. 任务块：
```
模型：sonnet
你的 agent_id：<短名，如 armL-anti>
任务：<一句话：帧段 + 部位 + 问题 → 想要的样子>
scope：<骨/链> × [A,B]。只许写这里。写之前 claim（读、dry_run 不用）。
（预备/跟随/过冲写明 main_bone；朝向写明 toward 目标向量；复制写明源窗与目标窗）
验收：<剧本里的指标 + 目标值>
完成后：list_ops（owner=你，compact）自查 → save（允许：它是协议的一部分）→ release →
按 tools_io §8 的格式报告；不许改任何源码/文档文件、不启动 Blender
```

## 4. 收单检查（每份报告都过一遍）

- 有修前/修后**数字**，且数字来自实时类读工具（probe_anatomy / analyze_motion / compare_motion /
  chain_lag / slide_report / ground_report）。"应该没问题" = 没做完。
- `list_claims` 里该 agent 已 release；`list_ops` 里它的 op 都是 `preview`、`alive=true`、owner 正确。
- 报告里说"层级相关"的，安排对应子骨任务的 agent 复测。改了**父骨**（上臂、脊柱）的任务即使没有租约冲突，也要看一眼
  这段帧上子骨（前臂、手、手指、头）已有的**朝向类**修复——父骨一动它们的世界朝向就变了，需要的话 reapply。
- 你自己串行执行任务时也一样：每个任务做完就 save（save 很快），别攒到最后。
- 每批结束后 `list_ops {"agent_id":"coord","live":true,"compact":true}` 扫一眼：带 `stale` 的复制行 = 源被后来的修复改了，
  让它的 owner（或你自己）`reapply {op_id, overrides:{}}`。
- 你（coord）`revert`/`reapply` 了别人的 op（`force:true`）之后**立刻 `release`**：对 op 的写操作会按 op 的骨×帧**自动认领**
  15 分钟，下一个来修这段的 agent 会被你挡住（2026-10-04 第二轮：撤掉一条失败的复制后没 release，重派的 Haiku 正确地停手了）。
- 最后协调者自己 `save` 一次，`list_ops` 对账：`fixes` 里没有 `lost` / `unregistered`。

## 5. 收尾

**等所有 agent 的报告都到了**（不是只看它 release 了——有的 agent release 后还会再复测一次）
再 `bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-stop`（之前先 save！）→ 需要回归时跑 `20_verifier.md`。

派验收者之前：**协调者自己** `mcd.sh deploy`（subagent 跑 deploy 会被自动模式权限当成"生产部署"拦下），
`git status` 干净或改动已提交；之后**冻结**——验收期间不改 clone、不 deploy、不起服务、不跑别的 Blender，
否则验收测的不是你以为的那份代码（2026-10-03 第四轮就踩了：协调者中途改代码并重新部署）。
