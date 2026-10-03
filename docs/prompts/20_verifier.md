# 验收者提示词（收尾：只跑测试、对账、出报告；不写 op、不改代码）

> 你只读、只跑测试：**不许**改任何源码/文档、不许 commit/push、不许写 op。所有 Blender 运行都经过
> `mcd.sh`（它排队、查内存，同一时刻只有 1 个 Blender）。下面的命令照抄——全是绝对路径、没有 shell 变量。
> 每一步把结论行抄进报告；某一步失败就记下失败行，继续做后面的步骤，最后统一下结论。

## 1. 服务

```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-status
```
服务在跑（`ok: true`）→ 先问协调者"可以停吗（都 save 了吗）"，得到同意再
`bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-stop`。e2e 和基准都要用唯一的 Blender 名额。

## 2. 部署 + e2e（10 套）

```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh deploy
for t in e2e_anatomy e2e_perfix e2e_accent e2e_fixlist_timer e2e_concurrency e2e_bugfixes e2e_motion_copy e2e_principles e2e_overlap e2e_foot_lock; do bash /home/sb/remote_kit_1.7.1/tools/mcd.sh e2e /home/sb/remote_kit_1.7.1/tests/$t.py | grep -E "^====? |^=== [0-9]|^\[FAIL\]|rc=|falling back"; done
```

## 3. 纯 Python 单测（13 个文件，不需要 Blender）

```bash
for f in /home/sb/freemocap_doctor/tests/test_*.py; do printf '%s: ' "$(basename $f)"; PYTHONPATH=/home/sb/freemocap_doctor python3 "$f" 2>&1 | tail -1; done
```
每行结尾应是 `OK` / `==== 0 FAIL ====` / `PASS …`。

## 4. 基准：结果必须与原版逐位一致（速度只是附带）

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
| e2e | anatomy 17/17 · perfix 17/17 · accent 8/8 · fixlist_timer 7/7 · concurrency 38/38 · bugfixes 32/32 · motion_copy 38/38 · principles 35/35 · overlap 39/39 · foot_lock 15/15（共 246），日志里没有 `falling back to` |
| 单测 | 13 个文件全过 |
| agent 层 golden | `GOLDEN DIFF SECTIONS: ['clean_jitter', 'effect_check']`——只允许这两节（两个有意的 bug 修复）；`INFO tools added=[…15 个…] removed=[]` 正常 |
| 向导 | `STEPS ALL SAME`（8 步关键帧 + 物体摘要与原版相同；source_check/source_floor 两版都报"源骨架没有活动 Action"，正常） |
| 导出链 | `STEPS ALL SAME`（mmd_bake / export_prep 关键帧摘要 + 导出 .vmd 字节哈希与原版相同） |

速度只在报告里附上（机器负载会让它浮动 ±10%）；**输出摘要不同 = FAIL**，哪怕更快。

## 5. 对账与文档（可选，协调者要求时做）

- 工作文件对账：`bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-start <工作文件.blend>` →
  `/home/sb/remote_kit_1.7.1/tools/agent list_ops '{"agent_id":"verifier","compact":true}'` → `fixes` 里没有
  `alive:false` 的行（= 日志里有、场景里丢了）→ `server-stop`。
- `git -C /home/sb/freemocap_doctor log --oneline | head -40`：每个任务号（任务1–4、修复、文档）都有 commit。
- `docs/工具手册_agent.md` 里每个工具都有一行（与 ping 的 `data.tools` 对照）。

## 报告格式

```
== 验收报告 ==
e2e:  anatomy 17/17 ✓ perfix 17/17 ✓ … foot_lock 15/15 ✓（共 X/246）  falling back: 无
单测: 13/13 文件通过
golden: DIFF SECTIONS = [clean_jitter, effect_check] ✓   tools +15/−0
向导: STEPS ALL SAME ✓（tilt 23.5→4.2 s …）   导出链: STEPS ALL SAME ✓（export_prep 13.9→10.8 s）
对账: ops=<n> alive=false=<n>   commits=<n>   文档缺口=<n>（做了才写）
结论: PASS / FAIL（哪一项、失败行原文）
```
