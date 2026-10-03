# 验收者提示词（收尾：只跑测试、对账、出报告；不写 op、不改代码）

> 你只读、只跑测试：**不许**改任何源码/文档、不许 commit/push、不许写 op、不许 deploy、不许起服务
> （mcd.sh 往 `logs/` 写的 .log/.json 是正常的）。
> 所有 Blender 运行都经过 `mcd.sh`（排队、查内存，同一时刻只有 1 个 Blender）——命令**一条一条**跑，
> 不要并行两个 mcd.sh。下面的命令照抄：全是绝对路径、没有 shell 变量。某一步失败就记下失败行原文，
> 继续做后面的步骤，最后统一下结论。
>
> 前提（协调者负责，你只核对）：代码已由协调者 deploy；验收期间 clone / 套件被冻结（没人改、没人 deploy）。

## 1. 现场核对（只读）

```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-status
git -C /home/sb/freemocap_doctor status --short
git -C /home/sb/freemocap_doctor log --oneline -1
diff -rq /home/sb/freemocap_doctor/mocap_doctor /home/sb/remote_kit_1.7.1/sandbox/extensions/user_default/mocap_doctor -x __pycache__ && echo SYNC_OK
```
- 判据：第一行**不是** `{"ok": true` 且最后一行以 `lock owner: free` 开头 = 服务没在跑（中间那段被截断的 Python
  traceback 是正常的）。第一行是 `{"ok": true` = 在跑 → 停下，报告给协调者，不要自己停服务。
- `status --short` 有 `mocap_doctor/` 下的改动、或没出现 `SYNC_OK` → 现场没冻结/没部署：停下报告，不要自己 deploy。
- 记下 HEAD 的 commit 号（报告里写"验收对象"）。

## 2. e2e（11 套）

```bash
for t in e2e_anatomy e2e_perfix e2e_accent e2e_fixlist_timer e2e_concurrency e2e_bugfixes e2e_motion_copy e2e_principles e2e_overlap e2e_foot_lock e2e_ground; do echo "## $t"; bash /home/sb/remote_kit_1.7.1/tools/mcd.sh e2e /home/sb/remote_kit_1.7.1/tests/$t.py | grep -E "^====? |^=== [0-9]|^\[FAIL\]|rc=|falling back"; done
```
11 套合计约 75 秒（单套 2–14 s）：**前台一条 Bash 跑完**即可，不用后台/轮询。套件的结论行有两种写法
（`==== N/N PASS ====` 和 `=== N/N passed ===`），都算。

## 3. 纯 Python 单测（13 个文件，不需要 Blender）

```bash
for f in /home/sb/freemocap_doctor/tests/test_*.py; do o=/home/sb/remote_kit_1.7.1/logs/ut_$(basename $f).out; printf '%s: ' "$(basename $f)"; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sb/freemocap_doctor python3 "$f" > $o 2>&1; echo "rc=$? $(tail -1 $o) fails=$(grep -c -E 'FAIL|Traceback|Error' $o)"; done
```
每行应是 `rc=0`、`fails=0`。末行是 `==== 0 FAIL ====` 的文件（test_agent_claims、test_agent_pose_math）fails=1 也对——
那一行本身含 FAIL。

## 4. 基准：结果必须与原版逐位一致（速度只是附带）

耗时：bench_baseline ~13 s、bench_wizard ~72 s、bench_export ~44 s；六条命令可以用 `;` 串成一个 Bash 调用（顺序执行，
timeout 给 600000 毫秒）。bench_wizard 的控制台只打出 source_check/source_floor 两行 EXC 和几行
"Error: 源骨架 没有活动 Action"（正常），其余步骤看后面的 compare 脚本。
```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh run /home/sb/remote_kit_1.7.1/tests/bench_baseline.py -- --label verify
python3 /home/sb/remote_kit_1.7.1/tests/bench_compare.py /home/sb/remote_kit_1.7.1/logs/bench_orig1.json /home/sb/remote_kit_1.7.1/logs/bench_verify.json | grep -E "^INFO|^GOLDEN|socket|probe|world_dir"
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh run /home/sb/remote_kit_1.7.1/tests/bench_wizard.py -- --label verify --reps 2
python3 /home/sb/remote_kit_1.7.1/tests/bench_steps_compare.py /home/sb/remote_kit_1.7.1/logs/wizbench_all_orig.json /home/sb/remote_kit_1.7.1/logs/wizbench_verify.json
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh run /home/sb/remote_kit_1.7.1/tests/bench_export.py -- --label verify --reps 2
python3 /home/sb/remote_kit_1.7.1/tests/bench_steps_compare.py /home/sb/remote_kit_1.7.1/logs/expbench_orig.json /home/sb/remote_kit_1.7.1/logs/expbench_verify.json
```
（`*_orig*.json` 是用原始 1.7.1 代码跑出的基线，已在 `logs/` 里。）

## 基线（2026-10-03 终版）

| 项 | 应得 |
|---|---|
| e2e | anatomy 17/17 · perfix 17/17 · accent 8/8 · fixlist_timer 7/7 · concurrency 45/45 · bugfixes 38/38 · motion_copy 42/42 · principles 38/38 · overlap 42/42 · foot_lock 15/15 · ground 25/25（共 294），每套 rc=0，没有 `falling back` |
| 单测 | 13 个文件全过 |
| agent 层 golden | `GOLDEN DIFF: 414 differences (numeric 400, max |Δ|=7.550e+01)` 且 `GOLDEN DIFF SECTIONS: ['clean_jitter', 'describe', 'effect_check', 'probe_palm', 'probe_palm_75', 'probe_sole', 'validate']`——只允许这些节、这个数（四个有意修复：去抖四元数、effect_check 取样、厚底靴的假"悬空"、probe 的 hold_pose_args 改成逐帧 probe 轴写法）；`INFO tools added=[…16 个…] removed=[]` 正常 |
| 向导 | `STEPS ALL SAME`（8 步关键帧 + 物体摘要与原版相同；source_check/source_floor 两版都报"源骨架没有活动 Action"，正常） |
| 导出链 | `STEPS ALL SAME`（mmd_bake / export_prep 关键帧摘要 + 导出 .vmd 字节哈希与原版相同） |

速度只在报告里附上（机器负载会让它浮动 ±10%；导出步骤比原版慢约 0.3–0.4 s 是正常的：原版导出完存盘直接报错跳过了，
现在真的存了盘）；**输出摘要不同 = FAIL**，哪怕更快。

## 5. 文档与提交（只读）

- `git -C /home/sb/freemocap_doctor log --oneline 190e354..HEAD | wc -l` = 本轮提交数（190e354 = v1.7.1 的 save 工具提交；
  只记录，不判 PASS/FAIL）；
  `git -C /home/sb/freemocap_doctor log --oneline 190e354..HEAD` 里任务1–4、修复、文档都要有。
- 工具清单对照（一条命令；`-w` 整词匹配，免得 save/claim 这类通用词被无关行凑数）：
  ```bash
  python3 -c "import json; print('\n'.join(sorted(json.load(open('/home/sb/remote_kit_1.7.1/logs/bench_verify.json'))['golden']['ping']['tools'])))" | while read -r n; do printf '%-18s %s\n' "$n" "$(grep -cw -- "$n" /home/sb/freemocap_doctor/docs/工具手册_agent.md)"; done
  ```
  0 次 = 缺口。只命中 1 次的再看一眼是哪一行（表格行或小节标题 = 有条目；只在正文里顺带提到 = 缺口）：
  `grep -nw -- '<工具名>' /home/sb/freemocap_doctor/docs/工具手册_agent.md`（几个工具共用一张表格行也算有）。

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
