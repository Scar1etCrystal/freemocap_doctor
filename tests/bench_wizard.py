"""Timing + output digest of the wizard's auto-fix steps (向导自动修复步骤).

    bash tools/mcd.sh run tests/bench_wizard.py -- --label before [--reps 1]

The shipped fixture is at step 9 with every step committed, and the
pre-step checkpoints live on the user's machine - so the steps refuse to
re-run.  In THIS throwaway process only, the "already committed" guard is
relaxed and each step runs on a freshly reloaded fixture (identical input).
Nothing is saved; the project data dir points at a scratch folder (steps
write 181 MB checkpoints) that is wiped afterwards.

Output digest per step = sha1 over every action's keyframes (foreach_get
co / interpolation) + every object's matrix_world - two runs of the same code
must match exactly; an optimisation must keep them identical.
"""
import hashlib
import json
import os
import shutil
import statistics
import sys
import time

import addon_utils
import bpy
import numpy as np

addon_utils.enable("bl_ext.user_default.mocap_doctor")
from bl_ext.user_default.mocap_doctor import operators as OPS  # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LABEL = ARGV[ARGV.index("--label") + 1] if "--label" in ARGV else "run"
REPS = int(ARGV[ARGV.index("--reps") + 1]) if "--reps" in ARGV else 1
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = bpy.data.filepath
SCRATCH = os.path.join(KIT, "sandbox", "tmp", "bench_wizard_data")
STEPS = ["source_check", "source_floor", "contacts", "global_correction", "tilt",
         "ground_feet", "target_floor", "foot_lock"]

OPS._require_restore_before_rerun = lambda scene, step_id: None   # throwaway only


def digest():
    h = hashlib.sha1()
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        h.update(act.name.encode())
        for fc in act.fcurves:
            n = len(fc.keyframe_points)
            co = np.zeros(2 * n, dtype=np.float32)
            fc.keyframe_points.foreach_get("co", co)
            h.update(f"{fc.data_path}[{fc.array_index}]:{n}".encode())
            h.update(co.tobytes())
    for ob in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        h.update(ob.name.encode())
        h.update(np.asarray(ob.matrix_world, dtype=np.float32).tobytes())
    return h.hexdigest()[:16]


res = {}
for step in STEPS:
    times, outs = [], []
    for _ in range(REPS):
        bpy.ops.wm.open_mainfile(filepath=FIX)
        shutil.rmtree(SCRATCH, ignore_errors=True)
        os.makedirs(SCRATCH, exist_ok=True)
        st = bpy.context.scene.mocap_doctor
        st.data_directory = SCRATCH
        t0 = time.perf_counter()
        try:
            r = bpy.ops.mocap_doctor.run_step(step_id=step)
            msg = st.status_message
        except Exception as exc:  # noqa: BLE001
            r, msg = f"EXC {exc!r}"[:160], ""
        times.append(time.perf_counter() - t0)
        outs.append((str(r), msg[:100], digest()))
    res[step] = {"median_s": statistics.median(times), "runs": len(times),
                 "result": outs[0][0], "msg": outs[0][1], "digest": outs[0][2],
                 "deterministic": len({o[2] for o in outs}) == 1}
    print(f"WIZBENCH {step:18s} {res[step]['median_s'] * 1000:9.1f} ms  {outs[0][0]}  "
          f"digest={outs[0][2]}  {outs[0][1]!r}", flush=True)
shutil.rmtree(SCRATCH, ignore_errors=True)
out = os.path.join(KIT, "logs", f"wizbench_{LABEL}.json")
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"WIZBENCH written {out}")
