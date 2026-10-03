"""任务1 e2e：多 agent 并发安全（claim/release + owner + scope 版本）。

全部走 agent_bridge._dispatch（真实入口），最后用真 socket 起 4 个线程模拟
4 个 agent 同时写。期望 ==== N/N PASS ====。
"""
import os
import socket
import sys
import threading
import time
import json

import addon_utils
import bpy

addon_utils.enable("bl_ext.user_default.mocap_doctor")
from bl_ext.user_default.mocap_doctor.core import agent_bridge, agent_ops  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), str(detail)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}", flush=True)


scene = bpy.context.scene
settings = scene.mocap_doctor
rig = settings.mmr_rig or next(o for o in scene.objects if o.type == "ARMATURE"
                               and o.name.startswith("RIG-"))
settings.mmr_rig = rig
data_dir = os.path.join(os.path.dirname(bpy.data.filepath), "e2e_concurrency_data")
os.makedirs(data_dir, exist_ok=True)
settings.data_directory = data_dir
oplog = os.path.join(data_dir, "agent_ops.json")
if os.path.exists(oplog):
    os.remove(oplog)
agent_bridge._LEASES.clear()


def call(tool, **args):
    return agent_bridge._dispatch({"tool": tool, "args": args})


def err(r):
    return (r.get("error") or {}).get("code")


HP = dict(target="values", blend=2)

# ---- claims -----------------------------------------------------------------
r = call("claim", agent_id="a1", bones=["left_hand"], frames=[100, 150])
check("1 claim granted", r["ok"] and r["data"]["granted"], r["summary"])
r = call("claim", agent_id="a2", bones=["left_hand"], frames=[140, 200])
check("2 overlapping claim denied", r["ok"] and not r["data"]["granted"]
      and r["data"]["conflicts"][0]["agent_id"] == "a1"
      and r["data"]["conflicts"][0]["frames"] == [140, 150], r["summary"])
r = call("claim", agent_id="a2", bones=["left_hand"], frames=[151, 200])
check("3 adjacent claim granted", r["data"]["granted"], r["summary"])
r = call("claim", agent_id="a3", bones=["left_forearm"], frames=[100, 150])
check("4 parent bone: granted + related warning",
      r["data"]["granted"] and r["data"]["related"] and r["warnings"], r["warnings"])
r = call("claim", agent_id="a4", bones=["left_forearm"], frames=[100, 150], strict=True)
check("5 strict denies hierarchy overlap", not r["data"]["granted"], r["summary"])
r = call("claim", agent_id="a4", bones=["head"], frames=[1, 50], check_only=True)
check("5b check_only does not take lease", r["data"]["granted"]
      and not any(c["agent_id"] == "a4" for c in call("list_claims")["data"]["claims"]))
r = call("claim", bones=["head"], frames=[1, 50])
check("5c claim without agent_id refused", not r["ok"], (r.get("error") or {}).get("fix"))

# ---- write enforcement ------------------------------------------------------
r = call("hold_pose", agent_id="a2", bones=["left_hand"], frame_range=[120, 130], **HP)
check("6 write into other's claim → E_CLAIMED", err(r) == "E_CLAIMED",
      (r.get("error") or {}).get("message"))
r = call("hold_pose", bones=["left_hand"], frame_range=[120, 130], **HP)
check("7 anonymous write into claim → E_CLAIMED", err(r) == "E_CLAIMED")
r = call("hold_pose", agent_id="a1", bones=["left_hand"], frame_range=[120, 130], **HP)
op_a1 = (r.get("data") or {}).get("op_id")
check("8 owner writes inside own claim", r["ok"] and op_a1, r["summary"])
op = agent_ops.get_op(data_dir, op_a1)
check("8b op.owner = a1", op and op.get("owner") == "a1", op and op.get("owner"))
rows = call("list_ops")["data"]["fixes"]
check("8c list_ops shows owner", any(x.get("op_id") == op_a1 and x.get("owner") == "a1"
                                     for x in rows))

# ---- ownership --------------------------------------------------------------
r = call("reapply", agent_id="a2", op_id=op_a1, overrides={"blend": 3})
check("9 reapply someone else's op → E_OWNER", err(r) == "E_OWNER",
      (r.get("error") or {}).get("message"))
r = call("revert", agent_id="a2", op_id=op_a1)
check("9b revert someone else's op → E_OWNER", err(r) == "E_OWNER")
r = call("set_influence", agent_id="a2", op_id=op_a1, value=1.2)
check("9c set_influence someone else's op → E_OWNER", err(r) == "E_OWNER")
r = call("reapply", agent_id="a1", op_id=op_a1, overrides={"blend": 3})
check("9d owner may reapply", r["ok"], r["summary"])

# ---- scoped expect_version ----------------------------------------------------
v_a1 = r["version"]
r = call("hold_pose", agent_id="a5", bones=["right_hand"], frame_range=[400, 420], **HP)
check("10 a5 writes elsewhere (auto-claim)", r["ok"] and any("自动认领" in w for w in r["warnings"]),
      r["warnings"])
v_after = r["version"]
r = call("hold_pose", agent_id="a1", bones=["left_hand"], frame_range=[131, 140],
         expect_version=v_a1, **HP)
check("11 unrelated change does not stale a1", r["ok"] and v_after > v_a1
      and any("已放行" in w for w in r["warnings"]), f"v{v_a1}→v{v_after} {r.get('warnings')}")
v_a1 = r["version"]
r = call("claim", agent_id="a3", bones=["spine3"], frames=[100, 150])
r = call("hold_pose", agent_id="a3", bones=["spine3"], frame_range=[110, 140], **HP)
check("12 a3 writes ancestor (spine3)", r["ok"], r["summary"])
r = call("hold_pose", agent_id="a1", bones=["left_hand"], frame_range=[121, 125],
         expect_version=v_a1, **HP)
check("12b ancestor change → E_STALE for a1", err(r) == "E_STALE",
      (r.get("error") or {}).get("message", "")[:160])
r = call("describe", target=[100, 120], expect_version=0)
check("12c read tool stays strict", err(r) == "E_STALE")

# ---- reads don't bump -------------------------------------------------------
v0 = call("ping")["version"]
call("probe_anatomy", part="palm", side="L", frame_range=[150, 170], toward=[0, -1, 0])
call("effect_check", op_id=op_a1)
v1 = call("ping")["version"]
check("13 read tools (frame_set inside) don't bump version", v0 == v1, f"v{v0}→v{v1}")

# ---- TTL + release ------------------------------------------------------------
r = call("claim", agent_id="a6", bones=["head"], frames=[1, 10], ttl_s=1)
time.sleep(1.3)
r2 = call("claim", agent_id="a7", bones=["head"], frames=[1, 10])
check("14 lease expires (TTL)", r["data"]["granted"] and r2["data"]["granted"], r2["summary"])
r = call("release", agent_id="a1")
check("15 release all", r["ok"] and r["data"]["released"], r["data"]["released"])
r = call("claim", agent_id="a2", bones=["left_hand"], frames=[100, 150])
check("15b freed scope claimable", r["data"]["granted"], r["summary"])

# ---- per-agent A/B ------------------------------------------------------------
r = call("ab_toggle", agent_id="a5")
tracks = r["data"].get("tracks") or []
own = {o["track"] for o in agent_ops.list_ops(data_dir) if o.get("owner") == "a5"}
check("16 ab_toggle(agent_id) only touches own tracks",
      r["ok"] and tracks and set(tracks) <= own, tracks)
call("ab_toggle", agent_id="a5")
r = call("ab_toggle", agent_id="nobody")
check("16b global ab_toggle refused while others hold claims",
      err(call("ab_toggle")) == "E_CLAIMED")

# ---- real socket: 4 agents in parallel ----------------------------------------
agent_bridge._LEASES.clear()
PORT = 6297
agent_bridge.start_server(PORT)
plan = {"w1": ("left_hand", 600), "w2": ("right_hand", 600),
        "w3": ("head", 700), "w4": ("spine2", 800)}
results = {k: [] for k in plan}
errors = []


def sock_call(tool, args):
    with socket.create_connection(("127.0.0.1", PORT), timeout=60) as s:
        s.sendall((json.dumps({"id": 1, "tool": tool, "args": args}) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.split(b"\n", 1)[0])


def worker(name, bone, base):
    try:
        r = sock_call("claim", {"agent_id": name, "bones": [bone], "frames": [base, base + 60]})
        results[name].append(("claim", r["ok"] and r["data"]["granted"], r["version"]))
        v = r["version"]
        for k in range(3):
            a = base + k * 20
            r = sock_call("hold_pose", {"agent_id": name, "bones": [bone],
                                        "frame_range": [a, a + 15], "target": "values",
                                        "blend": 2, "expect_version": v})
            results[name].append(("write", r["ok"], (r.get("error") or {}).get("code")))
            v = r["version"]
        r = sock_call("release", {"agent_id": name})
        results[name].append(("release", r["ok"], None))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{name}: {exc!r}")


threads = [threading.Thread(target=worker, args=(n, b, base), daemon=True)
           for n, (b, base) in plan.items()]
# contention: two agents race for the same scope
race = []


def racer(name):
    try:
        race.append(sock_call("claim", {"agent_id": name, "bones": ["neck"],
                                         "frames": [900, 950]})["data"]["granted"])
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{name}: {exc!r}")


threads += [threading.Thread(target=racer, args=(n,), daemon=True) for n in ("r1", "r2")]
for t in threads:
    t.start()
deadline = time.time() + 120
while any(t.is_alive() for t in threads) and time.time() < deadline:
    agent_bridge._pump()
    time.sleep(0.01)
agent_bridge.stop_server()
writes = [x for v in results.values() for x in v if x[0] == "write"]
check("17 4 agents × 3 writes over socket, all ok (no false E_STALE)",
      not errors and len(writes) == 12 and all(w[1] for w in writes),
      f"errors={errors} writes={[(w[1], w[2]) for w in writes]}")
check("18 race: exactly one of two same-scope claims granted",
      sorted(race) == [False, True], race)
ops = agent_ops.list_ops(data_dir)
owned = [o for o in ops if o.get("owner") in plan]
check("19 every socket op recorded with its owner",
      len(owned) == 12 and all(o["status"] == "preview" for o in owned),
      f"{len(owned)} owned")
rows = agent_ops.reconcile(rig, data_dir)
bad = [r for r in rows if r["status"] in ("lost", "unregistered")]
check("20 reconcile: no lost/unregistered strips", not bad, bad[:3])

fails = [r for r in RESULTS if not r[1]]
print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS ====")
for n, _o, d in fails:
    print(f"FAIL {n}: {d}")
sys.exit(1 if fails else 0)
