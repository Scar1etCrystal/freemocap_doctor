# 验收者提示词（收尾：只跑测试、对账、出报告；不写 op、不改代码）

> 你只读、只跑测试：**不许**改任何源码/文档、不许 commit/push、不许写 op、不许 deploy、不许起服务。
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
- 服务**没在跑**时 server-status 会打出一段 Python traceback（`socket.create_connection` … 连接被拒），
  最后一行是 `lock owner: free`——这是正常的"没在跑"。在跑（第一行是 `{"ok": true`）→ 停下，报告给协调者，
  不要自己停服务。
- `status --short` 有 `mocap_doctor/` 下的改动、或没出现 `SYNC_OK` → 现场没冻结/没部署：停下报告，不要自己 deploy。
- 记下 HEAD 的 commit 号（报告里写"验收对象"）。

## 2. e2e（11 套）

```bash
for t in e2e_anatomy e2e_perfix e2e_accent e2e_fixlist_timer e2e_concurrency e2e_bugfixes e2e_motion_copy e2e_principles e2e_overlap e2e_foot_lock e2e_ground; do echo "## $t"; bash /home/sb/remote_kit_1.7.1/tools/mcd.sh e2e /home/sb/remote_kit_1.7.1/tests/$t.py | grep -E "^====? |^=== [0-9]|^\[FAIL\]|rc=|falling back"; done
```
套件的结论行有两种写法（`==== N/N PASS ====` 和 `=== N/N passed ===`），都算。

## 3. 纯 Python 单测（13 个文件，不需要 Blender）

```bash
for f in /home/sb/freemocap_doctor/tests/test_*.py; do printf '%s: ' "$(basename $f)"; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sb/freemocap_doctor python3 "$f" 2>&1 | tail -1; done
```
每行结尾应是 `OK` / `==== 0 FAIL ====` / `PASS …`。

## 4. 基准：结果必须与原版逐位一致（速度只是附带）

每条基准 15–60 秒，Bash 的 timeout 给 600000 毫秒。
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
| e2e | anatomy 17/17 · perfix 17/17 · accent 8/8 · fixlist_timer 7/7 · concurrency 38/38 · bugfixes 32/32 · motion_copy 38/38 · principles 35/35 · overlap 39/39 · foot_lock 15/15 · ground 20/20（共 266），每套 rc=0，没有 `falling back` |
| 单测 | 13 个文件全过 |
| agent 层 golden | `GOLDEN DIFF: 405 differences (numeric 400, max |Δ|=7.550e+01)` 且 `GOLDEN DIFF SECTIONS: ['clean_jitter', 'effect_check']`——只允许这两节、这个数（两个有意的 bug 修复）；`INFO tools added=[…16 个…] removed=[]` 正常 |
| 向导 | `STEPS ALL SAME`（8 步关键帧 + 物体摘要与原版相同；source_check/source_floor 两版都报"源骨架没有活动 Action"，正常） |
| 导出链 | `STEPS ALL SAME`（mmd_bake / export_prep 关键帧摘要 + 导出 .vmd 字节哈希与原版相同） |

速度只在报告里附上（机器负载会让它浮动 ±10%）；**输出摘要不同 = FAIL**，哪怕更快。

## 5. 文档与提交（只读）

- `git -C /home/sb/freemocap_doctor log --oneline 190e354..HEAD | wc -l` = 本轮提交数（190e354 = v1.7.1 的 save 工具提交）；
  `git -C /home/sb/freemocap_doctor log --oneline 190e354..HEAD` 里任务1–4、修复、文档都要有。
- 工具清单：`python3 -c "import json; print(sorted(json.load(open('/home/sb/remote_kit_1.7.1/logs/bench_verify.json'))['golden']['ping']['tools']))"`
  → 逐个 `grep -c '<工具名>' /home/sb/freemocap_doctor/docs/工具手册_agent.md`；表格行或小节标题都算有，0 次 = 缺口。

## 报告格式

```
== 验收报告 ==
验收对象：<HEAD commit>   现场：SYNC_OK / git 干净（或写明哪里不对）
e2e:  anatomy 17/17 ✓ perfix 17/17 ✓ … ground 20/20 ✓（共 X/266）  falling back: 无
单测: 13/13 文件通过
golden: 405 处，DIFF SECTIONS = [clean_jitter, effect_check] ✓   tools +16/−0
向导: STEPS ALL SAME ✓（tilt 23.5→4.2 s …）   导出链: STEPS ALL SAME ✓（export_prep 13.9→10.8 s）
提交: <n>（190e354..HEAD）   文档缺口: <n>（列名字）
结论: PASS / FAIL（哪一项、失败行原文）
```
