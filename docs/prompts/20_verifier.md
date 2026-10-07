# 验收者提示词（收尾：只跑测试、对账、出报告；不写 op、不改代码）

> 你只读、只跑测试：**不许**改任何源码/文档、不许 commit/push、不许写 op、不许 deploy、不许起服务
> （mcd.sh 往 `logs/` 写的 .log/.json 是正常的）。
> 所有 Blender 运行都经过 `mcd.sh`（排队、查内存，同一时刻只有 1 个 Blender）——命令**一条一条**跑，
> 不要并行两个 mcd.sh。下面的命令先把 `<套件>` 换成套件根目录、`<仓库>` 换成代码仓库 clone
> （派单者给全路径，每条命令里原样替换；循环里的 `$t`/`$f` 是循环自己的）。某一步失败就记下失败行原文，
> 继续做后面的步骤，最后统一下结论。
>
> 前提（协调者负责，你只核对）：代码已由协调者 deploy；验收期间 clone / 套件被冻结（没人改、没人 deploy）。

## 1. 现场核对（只读）

```bash
bash <套件>/tools/mcd.sh server-status
git -C <仓库> status --short
git -C <仓库> log --oneline -1
diff -rq <仓库>/mocap_doctor <套件>/sandbox/extensions/user_default/mocap_doctor -x __pycache__ && echo SYNC_OK
```
- 判据：第一行**不是** `{"ok": true` 且最后一行以 `lock owner: free` 开头 = 服务没在跑（中间那段被截断的 Python
  traceback 是正常的）。第一行是 `{"ok": true` = 在跑 → 停下，报告给协调者，不要自己停服务。
- `status --short` 有 `mocap_doctor/` 下的改动、或没出现 `SYNC_OK` → 现场没冻结/没部署：停下报告，不要自己 deploy。
- 记下 HEAD 的 commit 号（报告里写"验收对象"）。

## 2. e2e（18 套：16 套用默认 fixture，e2e_root_pivot / e2e_upper_body 用它们自己的 fixture）

```bash
for t in e2e_anatomy e2e_perfix e2e_accent e2e_fixlist_timer e2e_concurrency e2e_bugfixes e2e_motion_copy e2e_principles e2e_overlap e2e_foot_lock e2e_ground e2e_markers e2e_align e2e_quickstart e2e_review_agent e2e_review_wizard; do echo "## $t"; bash <套件>/tools/mcd.sh e2e <套件>/tests/$t.py | grep -E "^====? |^=== [0-9]|^\[FAIL\]|rc=|falling back"; done
echo "## e2e_root_pivot"; bash <套件>/tools/mcd.sh e2e <套件>/tests/e2e_root_pivot.py <套件>/sandbox/work/fixture_root_pivot.blend | grep -E "^====? |^\[FAIL\]|rc=|falling back"
echo "## e2e_upper_body"; bash <套件>/tools/mcd.sh e2e <套件>/tests/e2e_upper_body.py <套件>/sandbox/work/fixture_root_pivot.blend | grep -E "^====? |^\[FAIL\]|rc=|falling back"
```
18 套合计约 150 秒（单套 2–19 s）：**前台一条 Bash 跑完**即可（timeout 给 400000 毫秒），不用后台/轮询。套件的结论行有两种写法
（`==== N/N PASS ====` 和 `=== N/N passed ===`），都算。

## 3. 纯 Python 单测（16 个文件，不需要 Blender）

```bash
for f in <仓库>/tests/test_*.py; do o=<套件>/logs/ut_$(basename $f).out; printf '%s: ' "$(basename $f)"; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<仓库> python3 "$f" > $o 2>&1; echo "rc=$? $(tail -1 $o) fails=$(grep -c -E 'FAIL|Traceback|Error' $o)"; done
```
每行应是 `rc=0`、`fails=0`。末行是 `==== 0 FAIL ====` 的文件（test_agent_claims、test_agent_pose_math、
test_agent_mcp、test_project_paths）fails=1 也对——那一行本身含 FAIL。test_pkl_hand 有一条会调用本机 Blender 自带的
`python3.11`（只是解释器，numpy 1.26，不是 Blender，不占 Blender 锁）读一个 numpy 2 写的 pkl；找不到该解释器时打印 SKIP 并算通过。

## 4. 基准：结果必须与原版逐位一致（速度只是附带）

耗时：bench_baseline ~13 s、bench_wizard ~72 s、bench_export ~44 s；六条命令可以用 `;` 串成一个 Bash 调用（顺序执行，
timeout 给 600000 毫秒）。bench_wizard 的控制台只打出 source_check/source_floor 两行 EXC 和几行
"Error: 源骨架 没有活动 Action"（正常），其余步骤看后面的 compare 脚本。
```bash
bash <套件>/tools/mcd.sh run <套件>/tests/bench_baseline.py -- --label verify
python3 <套件>/tests/bench_compare.py <套件>/logs/bench_orig1.json <套件>/logs/bench_verify.json | grep -E "^INFO|^GOLDEN|socket|probe|world_dir"
bash <套件>/tools/mcd.sh run <套件>/tests/bench_wizard.py -- --label verify --reps 2
python3 <套件>/tests/bench_steps_compare.py <套件>/logs/wizbench_all_bugfix_ref.json <套件>/logs/wizbench_verify.json
bash <套件>/tools/mcd.sh run <套件>/tests/bench_export.py -- --label verify --reps 2
python3 <套件>/tests/bench_steps_compare.py <套件>/logs/expbench_orig.json <套件>/logs/expbench_verify.json
```
（`*_orig*.json` 是用原始 1.7.1 代码跑出的基线，已在 `logs/` 里。向导步骤从 2026-10-04 起对
`wizbench_all_bugfix_ref.json` 对账：它就是 `wizbench_all_orig.json`（耗时也是原版的，便于看提速），只有 foot_lock 一步换成了
dev/bugfix M1（鞋底向量按骨架空间判左右）之后的摘要 `289377ce7d2ad031`——对原版文件比会报 foot_lock DIFF，这是有意的。）

## 基线（2026-10-03 终版）

| 项 | 应得 |
|---|---|
| e2e | anatomy 21/21 · perfix 17/17 · accent 8/8 · fixlist_timer 7/7 · concurrency 45/45 · bugfixes 38/38 · motion_copy 42/42 · principles 38/38 · overlap 42/42 · foot_lock 15/15 · ground 25/25 · markers 25/25 · align 38/38 · quickstart 6/6 · review_agent 34/34 · review_wizard 12/12 · root_pivot 9/9 · upper_body 12/12（共 434；2026-10-04 晚：§15 upper_body，§16 markers +4（审查 M20）+ align + quickstart，§17 review_agent + review_wizard；之前 13 套 328 / 12 套 319 / 11 套 294），每套 rc=0，没有 `falling back`。root_pivot 与 upper_body 的 fixture `sandbox/work/fixture_root_pivot.blend` = 用户 0999_fsb_showretargetproblem.blend 的副本（2026-10-06：quickstart 5/5 → 6/6，新增 Q5 覆盖 `list_timeline_markers`，文档命令数 42 → 43） |
| 单测 | 16 个文件全过（2026-10-04 新增 test_upper_body_swing.py；dev/bugfix 新增 test_agent_mcp.py、test_project_paths.py；2026-10-06 test_agent_layer.py 加 TimelineMarkerTests 5 条，26 条全过） |
| agent 层 golden | `GOLDEN DIFF: 1593 differences (numeric 1551, max |Δ|=1.078e+02)` 且 `GOLDEN DIFF SECTIONS: ['clean_jitter', 'describe', 'effect_check', 'hold_pose', 'list_ops', 'probe_body', 'probe_palm', 'probe_palm_75', 'probe_sole', 'reapply', 'set_influence', 'validate']`——只允许这些节、这个数。§16 相对 1577/11 节多出的 16 处：`probe_body`（身体前方改为躯干朝向，13 处）+ `hold_pose.world_dir`/`world_dir2` 的 envelope 各多 1 条"你给的是世界向量…用 forward"提醒（基准在 150–224 帧写 [0,-1,0]，这段角色躯干偏 −X 41°）。五个有意修复：去抖四元数、effect_check 取样、厚底靴的假"悬空"、probe 的 hold_pose_args 改成逐帧 probe 轴写法，以及 2026-10-04 掌心改为网格标定 + 次轴 hand_axis（基准里的 hold_pose 掌心修复及其 reapply / set_influence / list_ops 行随之变）；`INFO tools added=[…21 个…] removed=[]` 正常（§16 新增 swivel / orient_report / conventions / render_view；2026-10-03 终版是 414 处 / 7 节 / 16 个工具）。**2026-10-06 再加 `list_timeline_markers`（读用户的 M 键标记），golden 里 tools added 应变成 22 个，diff 数字不变**——它只读场景，不碰动作数据 |
| 向导 | 对 `wizbench_all_bugfix_ref.json`：`STEPS ALL SAME`（7 步关键帧 + 物体摘要与原版相同，foot_lock 与 M1 之后的参考相同；source_check/source_floor 两版都报"源骨架没有活动 Action"，正常）。速度（2026-10-04 dev/bugfix）：tilt 0.9 s、target_floor 4.7 s、foot_lock 11.3 s |
| 导出链 | `STEPS ALL SAME`（mmd_bake / export_prep 关键帧摘要 + 导出 .vmd 字节哈希与原版相同） |

速度只在报告里附上（机器负载会让它浮动 ±10%；导出步骤比原版慢约 0.3–0.4 s 是正常的：原版导出完存盘直接报错跳过了，
现在真的存了盘）；**输出摘要不同 = FAIL**，哪怕更快。

## 5. 文档与提交（只读）

- `git -C <仓库> log --oneline 190e354..HEAD | wc -l` = 本轮提交数（190e354 = v1.7.1 的 save 工具提交；
  只记录，不判 PASS/FAIL；标题前缀 `[任务N]`/`[修复]`/`[文档]` 缺哪类也只是记录）；
  `git -C <仓库> log --oneline 190e354..HEAD` 里任务1–4、修复、文档都要有。
- 工具清单对照（一条命令；`-w` 整词匹配，免得 save/claim 这类通用词被无关行凑数）：
  ```bash
  python3 -c "import json; print('\n'.join(sorted(json.load(open('<套件>/logs/bench_verify.json'))['golden']['ping']['tools'])))" | while read -r n; do printf '%-18s %s\n' "$n" "$(grep -cw -- "$n" <仓库>/docs/工具手册_agent.md)"; done
  ```
  0 次 = 缺口。再确认每个工具都有**表格行或小节标题**（只在正文里顺带提到 = 缺口；几个工具共用一张表格行也算有）：
  ```bash
  python3 -c "import json,re; tools=sorted(json.load(open('<套件>/logs/bench_verify.json'))['golden']['ping']['tools']); L=open('<仓库>/docs/工具手册_agent.md',encoding='utf-8').read().splitlines(); print('NO-ENTRY', [n for n in tools if not any(re.match(r'^\|[^|]*\x60'+re.escape(n)+r'\x60',l) or (l.startswith('#') and n in l) for l in L)])"
  ```
  打印 `NO-ENTRY []` = 没有缺口。

## 报告格式

```
== 验收报告 ==
验收对象：<HEAD commit>   现场：SYNC_OK / git 干净（或写明哪里不对）
e2e:  anatomy 17/17 ✓ perfix 17/17 ✓ … ground 25/25 ✓（共 X/294）  falling back: 无
单测: 13/13 文件通过
golden: 414 处，DIFF SECTIONS = [clean_jitter, describe, effect_check, probe_palm, probe_palm_75, probe_sole, validate] ✓   tools +16/−0
向导: STEPS ALL SAME ✓（tilt 23.5→4.2 s …）   导出链: STEPS ALL SAME ✓（export_prep 13.9→10.8 s）
提交: <n>（190e354..HEAD）   文档缺口: <n>（列名字）
结论: PASS / FAIL（哪一项、失败行原文）
```
