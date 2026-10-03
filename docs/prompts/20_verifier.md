# 验收者提示词（收尾：只跑测试、对账、出报告；不写 op、不改代码）

```bash
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh server-stop          # e2e 要用唯一的 Blender 名额（停之前确认已 save）
for t in e2e_anatomy e2e_perfix e2e_accent e2e_concurrency e2e_bugfixes \
         e2e_motion_copy e2e_principles e2e_overlap e2e_foot_lock; do
  bash /home/sb/remote_kit_1.7.1/tools/mcd.sh e2e /home/sb/remote_kit_1.7.1/tests/$t.py | grep -E "^====? |^=== [0-9]|^\[FAIL\]"
done
python3 /home/sb/freemocap_doctor/tests/test_agent_claims.py | tail -1
python3 /home/sb/freemocap_doctor/tests/test_data_dir.py
python3 /home/sb/freemocap_doctor/tests/test_agent_pose_math.py | tail -1
bash /home/sb/remote_kit_1.7.1/tools/mcd.sh run /home/sb/remote_kit_1.7.1/tests/bench_baseline.py -- --label final
python3 /home/sb/remote_kit_1.7.1/tests/bench_compare.py /home/sb/remote_kit_1.7.1/logs/bench_before.json /home/sb/remote_kit_1.7.1/logs/bench_final.json
```

基线（2026-10-03 终版）：anatomy 17/17 · perfix 17/17 · accent 8/8 · concurrency 38/38 · bugfixes 32/32 ·
motion_copy 38/38 · principles 35/35 · overlap 39/39 · foot_lock 15/15；纯 Python：test_agent_claims、
test_data_dir、test_agent_pose_math（`python3 /home/sb/freemocap_doctor/tests/test_agent_pose_math.py`）全过。

## 验收清单

1. 全部 e2e 全绿（数字和上面一致或更多）。
2. 基准：`GOLDEN` 只允许 `clean_jitter`、`effect_check` 两节有差异（2026-10-03 的两个修复改了
   它们的输出，见 CHANGES 文档）；其余必须 IDENTICAL。速度表附在报告里。
3. 工作文件对账：`server-start <工作文件>` → `list_ops` → `fixes` 里无 `lost`/`unregistered`。
4. `git log --oneline`：每个任务号都有 commit。
5. 工具手册 `docs/工具手册_agent.md` 里每个工具都有一行档。

## 报告格式

```
== 验收报告 ==
e2e:  anatomy 17/17 ✓ perfix 17/17 ✓ accent 8/8 ✓ concurrency X/X … overlap X/X foot_lock X/X
基准: <表>   golden: IDENTICAL（除 clean_jitter/effect_check）
对账: ops=<n> 孤儿=<n>   commits=<n>   文档缺口=<n>
结论: PASS / FAIL（哪一项，归谁）
```
