"""agent_contact.py — 触地工具：slide_report（脚滑体检，读）+ foot_lock（踩实，写）。

动捕最常见的毛病是"脚在地上滑"。向导的 foot_lock 步骤在源骨架上做过 XY 锁，
但重定向到 RIG 之后 foot_ik 仍会漂（fixture 实测：右脚 190–214 帧接触期
水平漂 27.8 mm）。这里在 agent 层补两件工具：

- ``slide_report``（输入/输出工具，只读）：按向导标注的 contact.L/R 区间，逐段
  量 foot_ik 世界水平漂移（mm），超阈值的段给出可直接用的 foot_lock 参数。
  修后再调一次就是复测。
- ``foot_lock``（写）：在帧段内把 foot_ik 钉在参考帧的世界位置上。
  lock="xy"（默认）只钉水平位置、保留高度曲线——脚跟抬起/脚尖滚动不受影响；
  "xy+rot" 再钉朝向；"pos" 钉三维位置；"pos+rot" 整只脚完全冻结。

约定：腿是 IK 模式（Rigify thigh_parent["IK_FK"]=0），foot_ik.{L,R} 是唯一有效
的腿部控制骨；FK 腿上调用会直接报错。世界目标 → 局部 basis 用父骨（MCH-foot_ik
.parent.*，带 ARMATURE 约束）的**求值后**矩阵换算：basis = rel_rest⁻¹·P⁻¹·D。
只写 frame_range 以内；用 interval="contact.R:7" 时窗口自动向两侧各扩 blend 帧，
让整段接触期都处在 taper 之外（真正钉住）。
"""

from __future__ import annotations

import numpy as np

from . import agent_io, agent_ops, agent_pose as P
from .ranges import frames_to_ranges

LOCK_MODES = ("xy", "xy+rot", "pos", "pos+rot")


def _foot(side: str) -> str:
    s = str(side or "").upper()
    if s not in ("L", "R"):
        raise RuntimeError(f"side 必须是 'L' 或 'R'，收到 {side!r}")
    return s


def _check_ik(armature, side: str):
    pb = armature.pose.bones.get(f"thigh_parent.{side}")
    if pb is not None and "IK_FK" in pb.keys() and float(pb["IK_FK"]) > 0.5:
        raise RuntimeError(
            f"{side} 腿当前是 FK 模式（thigh_parent.{side}[IK_FK]={float(pb['IK_FK'])}），"
            "foot_lock 只对 IK 腿有效；FK 腿请用 hold_pose 处理 thigh/shin/foot_fk")
    if armature.pose.bones.get(f"foot_ik.{side}") is None:
        raise RuntimeError(f"骨架上没有 foot_ik.{side}")


def _rest_rel(armature, bone: str) -> np.ndarray:
    db = armature.data.bones[bone]
    ml = np.asarray(db.matrix_local, dtype=np.float64)
    if db.parent is None:
        return ml
    return np.linalg.inv(np.asarray(db.parent.matrix_local, dtype=np.float64)) @ ml


def _ref_index(pos: np.ndarray, ref, frames, blend: int) -> int:
    n = len(pos)
    if ref in (None, "auto"):
        lo, hi = (blend, n - blend) if n - 2 * blend >= 3 else (0, n)
        sp = np.zeros(n)
        sp[1:] = np.linalg.norm(np.diff(pos[:, :2], axis=0), axis=1)
        sp[0] = sp[1] if n > 1 else 0.0
        seg = P.smooth(sp, 3)[lo:hi]
        return lo + int(np.argmin(seg))
    if ref == "first":
        return min(blend, n - 1)
    if ref == "last":
        return max(0, n - 1 - blend)
    if ref == "mid":
        return n // 2
    f = int(ref)
    if f not in frames:
        raise RuntimeError(f"ref={f} 不在帧段 {frames[0]}–{frames[-1]} 内")
    return frames.index(f)


def _resolve_interval(scene, interval: str, blend: int):
    """'contact.R:7' → (side, [a-blend, b+blend] clamped, (a, b))."""
    try:
        kind, idx = str(interval).rsplit(":", 1)
        rows = agent_io.scene_intervals(scene).get(kind)
        row = rows[int(idx)]
    except Exception:
        raise RuntimeError(
            f"interval {interval!r} 无效：写成 'contact.L:<序号>'，序号见 slide_report "
            "或 list_intervals kind=contact.L")
    side = kind.split(".")[-1].upper()
    a, b = int(row["start"]), int(row["end"])
    lo = max(int(scene.frame_start), a - int(blend))
    hi = min(int(scene.frame_end), b + int(blend))
    return side, [lo, hi], (a, b)


# ---------------------------------------------------------------------------
# slide_report (read)

def slide_report(scene, armature, *, side=None, frame_range=None,
                 threshold_mm: float = 10.0, min_len: int = 4,
                 max_rows: int = 60) -> dict:
    sides = [_foot(side)] if side else ["L", "R"]
    ivs = agent_io.scene_intervals(scene)
    rows = []
    for s in sides:
        _check_ik(armature, s)
        bone = f"foot_ik.{s}"
        segs = []
        for i, it in enumerate(ivs.get(f"contact.{s}", [])):
            a, b = int(it["start"]), int(it["end"])
            if frame_range is not None and (b < int(frame_range[0])
                                            or a > int(frame_range[1])):
                continue
            if b - a + 1 < int(min_len):
                continue
            segs.append((i, a, b))
        if not segs:
            continue
        frames = sorted({f for _i, a, b in segs for f in range(a, b + 1)})
        smp = P.sample_visible(scene, armature, [bone], frames, world=True)
        pos_all = smp["mat"][bone][:, :3, 3]
        at = {f: k for k, f in enumerate(frames)}
        for i, a, b in segs:
            pos = pos_all[[at[f] for f in range(a, b + 1)]]
            fr = list(range(a, b + 1))
            r = _ref_index(pos, "auto", fr, 0)
            d_ref = np.linalg.norm(pos[:, :2] - pos[r, :2], axis=1) * 1000
            d_med = np.linalg.norm(pos[:, :2] - np.median(pos[:, :2], axis=0),
                                   axis=1) * 1000
            drift = float(d_ref.max())
            rows.append({
                "interval": f"contact.{s}:{i}", "side": s, "frames": [a, b],
                "length": b - a + 1,
                "drift_mm": round(drift, 1),
                "drift_from_median_mm": round(float(d_med.max()), 1),
                "z_range_mm": round(float(np.ptp(pos[:, 2]) * 1000), 1),
                "ref_frame": fr[r],
                "flagged": drift > float(threshold_mm),
                "foot_lock_args": {"interval": f"contact.{s}:{i}", "lock": "xy"},
            })
    rows.sort(key=lambda r: -r["drift_mm"])
    flagged = [r for r in rows if r["flagged"]]
    return {"threshold_mm": float(threshold_mm), "intervals": len(rows),
            "flagged": len(flagged),
            "worst": rows[0] if rows else None,
            "rows": rows[:int(max_rows)],
            "truncated": len(rows) > int(max_rows),
            "units": "mm（foot_ik 头部世界水平漂移，相对接触期最静止的一帧）"}


# ---------------------------------------------------------------------------
# ground_report (read) - live sole height, same three points as the snapshot

# 与信号库快照（agent_io.rig_bake_spec 的 foot_points）同一组脚底点：
# DEF-foot 头（踝）/ 尾（前掌）+ DEF-toe 尾（脚尖），取三者最低 = 脚底高度。
_SOLE_POINTS = (("DEF-foot.{s}", "head"), ("DEF-foot.{s}", "tail"), ("DEF-toe.{s}", "tail"))


def sole_heights(scene, armature, sides, frames) -> dict:
    """{side: (T,3) world Z of heel/ball/toe} for the CURRENT visible pose.

    Computed exactly like the snapshot bake (``armature.matrix_world @ head/tail``),
    so frames nobody has touched read identically to ``foot.<s>.sole_h``."""
    names = {s: [(n.format(s=s), w) for n, w in _SOLE_POINTS] for s in sides}
    for s in sides:
        for n, _w in names[s]:
            if armature.pose.bones.get(n) is None:
                raise RuntimeError(f"骨架上没有 {n}（脚底高度用它的头/尾）")

    def extra(arm, _scene):
        world = arm.matrix_world
        row = {}
        for s in sides:
            zs = []
            for n, w in names[s]:
                pb = arm.pose.bones[n]
                zs.append(float((world @ (pb.head if w == "head" else pb.tail)).z))
            row[s] = zs
        return row

    smp = P.sample_visible(scene, armature, [names[sides[0]][0][0]], frames,
                           extra_fn=extra)
    return {s: np.asarray([e[s] for e in smp["extra"]], dtype=np.float64)
            for s in sides}


def contact_heights(signals, frames, floor_z, scene) -> dict:
    """每只脚"正常着地"时脚底点离地面的高度（米），从快照（原始动作）标定。

    脚底点是关节中心（踝/前掌/脚尖骨的头尾），不是鞋底：穿厚底鞋的模型着地时它们
    离地好几厘米（fixture：左 77 mm、右 81.5 mm）。取全片每段 contact 标注里脚底点
    最低值的中位数 = 这只脚踩实时的高度。少于 3 段标注 → 不标定（按 0 算）。"""
    ivs = agent_io.scene_intervals(scene)
    fr = np.asarray(frames)
    out = {}
    for s in ("L", "R"):
        sh = signals.get(f"foot.{s}.sole_h")
        if sh is None:
            continue
        sh = np.asarray(sh, dtype=np.float64)
        mins = []
        for it in ivs.get(f"contact.{s}", []):
            m = (fr >= int(it["start"])) & (fr <= int(it["end"]))
            if m.any():
                mins.append(float(sh[m].min()) - float(floor_z))
        if len(mins) >= 3:
            arr = np.asarray(mins) * 1000.0
            out[s] = {"height_m": float(np.median(arr)) / 1000.0, "contacts": len(mins),
                      "p10_mm": round(float(np.percentile(arr, 10)), 1),
                      "p90_mm": round(float(np.percentile(arr, 90)), 1)}
    return out


def ground_report(scene, armature, *, frame_range, floor_z, side=None,
                  threshold_mm: float = 10.0, blend: int = 4, snapshot=None,
                  contact_height=None, detail: bool = False) -> dict:
    """Live penetration / floating check - the before/after check for fix_ground.

    clearance = 脚底点最低值 − floor_z（mm）。判定相对"这只脚正常着地的高度"
    contact_height（见 contact_heights）：
      rel = clearance − contact_height；rel < −threshold = 下沉/穿地（pen_frames）；
      接触段整段 rel > +threshold = 悬空（contacts[].floating）。
    fix_ground_args：穿地 → mode=pen、悬空 → mode=lift，rest_clearance 已填好（米），
    两侧各留 blend。snapshot：{side: 快照 sole_h} → snapshot_diff_max_mm。"""
    sides = [_foot(side)] if side else ["L", "R"]
    a, b, frames = P.strip_window(frame_range)
    lo_clip, hi_clip = int(scene.frame_start), int(scene.frame_end)
    heights = sole_heights(scene, armature, sides, frames)
    ivs = agent_io.scene_intervals(scene)
    thr = float(threshold_mm)
    contact_height = contact_height or {}
    out = {"frame_range": [a, b], "floor_z": float(floor_z), "threshold_mm": thr,
           "units": "mm。clearance = 脚底点（关节中心）最低值 − 地面；rel = clearance − "
                    "contact_height（这只脚正常着地时的 clearance）；rel 负 = 下沉/穿地",
           "sides": {}}
    for s in sides:
        cal = contact_height.get(s)
        ref_m = float(cal["height_m"]) if cal else 0.0
        ref_mm = ref_m * 1000.0
        sole = heights[s].min(axis=1)
        clr = (sole - float(floor_z)) * 1000.0
        rel = clr - ref_mm
        i_min = int(np.argmin(clr))
        pen_frames = [f for f, r in zip(frames, rel) if r < -thr]
        pen_ranges = frames_to_ranges(pen_frames) if pen_frames else []
        loc_path = f'pose.bones["foot_ik.{s}"].location'
        contacts, suggest = [], []
        for lo, hi in pen_ranges:
            suggest.append({"frame_range": [max(lo_clip, lo - int(blend)),
                                            min(hi_clip, hi + int(blend))],
                            "side": s, "loc_path": loc_path, "mode": "pen",
                            "rest_clearance": round(ref_m, 4),
                            "why": f"{lo}–{hi} 比正常着地低 > {thr:g} mm（下沉/穿地）"})
        for k, it in enumerate(ivs.get(f"contact.{s}", [])):
            ca, cb = int(it["start"]), int(it["end"])
            idx = [i for i, f in enumerate(frames) if ca <= f <= cb]
            if not idx:
                continue
            r_c = rel[idx]
            row = {"interval": f"contact.{s}:{k}", "frames": [ca, cb],
                   "measured": [frames[idx[0]], frames[idx[-1]]],
                   "rel_min_mm": round(float(r_c.min()), 1),
                   "rel_max_mm": round(float(r_c.max()), 1),
                   "floating": bool(r_c.min() > thr),
                   "sunk": bool(r_c.min() < -thr)}
            contacts.append(row)
            if row["floating"]:
                suggest.append({"frame_range": [max(lo_clip, ca - int(blend)),
                                                min(hi_clip, cb + int(blend))],
                                "side": s, "loc_path": loc_path, "mode": "lift",
                                "rest_clearance": round(ref_m, 4),
                                "why": f"{row['interval']} 接触期比正常着地高 "
                                       f"{row['rel_min_mm']} mm（悬空）"})
        res = {"contact_height_mm": round(ref_mm, 1),
               "calibration": cal or {"contacts": 0, "note": "没有足够的 contact 标注，按 0 算"},
               "clearance_min_mm": round(float(clr[i_min]), 1),
               "clearance_min_frame": frames[i_min],
               "rel_min_mm": round(float(rel[i_min]), 1),
               "pen_max_mm": round(max(0.0, -float(rel[i_min])), 1),
               "pen_frames": [[int(lo), int(hi)] for lo, hi in pen_ranges],
               "contacts": contacts, "fix_ground_args": suggest}
        if snapshot is not None and snapshot.get(s) is not None:
            snap = np.asarray(snapshot[s], dtype=np.float64)
            if len(snap) == len(sole):
                res["snapshot_diff_max_mm"] = round(float(np.abs(sole - snap).max() * 1000.0), 2)
        if detail:
            res["rel_mm"] = [round(float(v), 1) for v in rel]
        out["sides"][s] = res
    return out


# ---------------------------------------------------------------------------
# foot_lock (write)

def foot_lock(scene, armature, *, side, frame_range, ref="auto", lock="xy",
              strength=1.0, blend=4, op_mode="preview", data_dir=None,
              track_name=None, dry_run=False, record=True, interval=None):
    side = _foot(side)
    if lock not in LOCK_MODES:
        raise RuntimeError(f"lock 只能是 {LOCK_MODES}，收到 {lock!r}")
    _check_ik(armature, side)
    bone = f"foot_ik.{side}"
    pb = armature.pose.bones[bone]
    a, b, frames = P.strip_window(frame_range)
    parent = pb.parent.name if pb.parent is not None else None
    smp = P.sample_visible(scene, armature,
                           [bone] + ([parent] if parent else []), frames,
                           world=True)
    M = smp["mat"][bone]
    pos = M[:, :3, 3]
    r = _ref_index(pos, ref, frames, int(blend))
    D = M.copy()
    if lock == "pos+rot":
        D[:] = M[r]
    elif lock == "pos":
        D[:, :3, 3] = M[r, :3, 3]
    elif lock == "xy":
        D[:, :2, 3] = M[r, :2, 3]
    else:                                   # xy+rot
        D[:, :3, :3] = M[r, :3, :3]
        D[:, :2, 3] = M[r, :2, 3]
    rel = _rest_rel(armature, bone)
    rel_inv = np.linalg.inv(rel)
    if parent:
        Pm = smp["mat"][parent]
        Bm = np.array([rel_inv @ np.linalg.inv(Pm[t]) @ D[t]
                       for t in range(len(frames))])
    else:
        Bm = np.array([rel_inv @ D[t] for t in range(len(frames))])
    des_loc = {bone: Bm[:, :3, 3]}
    des_quat = None
    if lock in ("pos+rot", "xy+rot"):
        R = Bm[:, :3, :3]
        R = R / np.linalg.norm(R, axis=1, keepdims=True)      # strip scale
        des_quat = {bone: P.quat_continuous(P.mat_to_quat(R))}
    scalars, quats, info = P.pose_deltas(armature, smp, desired_quat=des_quat,
                                         desired_loc=des_loc,
                                         strength=strength)
    inner = slice(int(blend), len(frames) - int(blend)) \
        if len(frames) > 2 * int(blend) else slice(None)
    drift = np.linalg.norm(pos[:, :2] - pos[r, :2], axis=1)[inner] * 1000
    metrics = {"bone": bone, "ref_frame": frames[r], "lock": lock,
               "drift_before_mm": round(float(drift.max()), 1) if len(drift) else 0.0,
               "z_range_before_mm": round(float(np.ptp(pos[inner, 2]) * 1000), 1)
               if len(drift) else 0.0,
               "bones": info,
               "note": "复测：slide_report 同段 drift_mm 应 ≈0（内段）；"
                       "两端各 blend 帧是过渡区"}
    params = {"side": side, "frame_range": [a, b], "ref": ref, "lock": lock,
              "strength": strength, "blend": blend, "interval": interval}
    if dry_run:
        return {"dry_run": True, "params": params, "metrics": metrics,
                "frames": [a, b]}
    track, strip = P.write_pose(armature, f"agent_footlock_{side}_{a}_{b}", a,
                                scalars, quats, blend=blend,
                                track_name=track_name)
    op = agent_ops._new_op("foot_lock", params, (a, b), strip.name, op_mode,
                           metrics, track=track.name)
    return agent_ops._record(data_dir, op) if (data_dir and record) else op


# ---------------------------------------------------------------------------
# bridge plumbing

def _foot_args(ctx, args):
    args = dict(args)
    blend = int(args.get("blend", 4))
    if args.get("interval"):
        side, fr, _ab = _resolve_interval(ctx["scene"], args["interval"], blend)
        if args.get("side") and _foot(args["side"]) != side:
            raise RuntimeError(f"interval 是 {side} 脚，side 却给了 {args['side']}")
        args["side"] = side
        args.setdefault("frame_range", fr)
        if args.get("frame_range") is None:
            args["frame_range"] = fr
    if args.get("frame_range") is None:
        raise RuntimeError("foot_lock 需要 frame_range 或 interval（如 'contact.R:7'）")
    if not args.get("side"):
        raise RuntimeError("foot_lock 需要 side='L'/'R'（或用 interval）")
    return args


def _tool_foot_lock(ctx, **args):
    args = _foot_args(ctx, args)
    op = foot_lock(ctx["scene"], ctx["armature"], data_dir=ctx["data_dir"], **args)
    if not op.get("dry_run"):
        ctx["after_write"](op["frames"])
    return op


def _tool_slide_report(ctx, side=None, frame_range=None, threshold_mm=10.0,
                       min_len=4, max_rows=60, **_):
    res = slide_report(ctx["scene"], ctx["armature"], side=side,
                       frame_range=frame_range, threshold_mm=threshold_mm,
                       min_len=min_len, max_rows=max_rows)
    w = res.get("worst")
    summary = (f"{res['intervals']} 段接触，{res['flagged']} 段漂移 > {threshold_mm} mm"
               + (f"；最差 {w['interval']} {w['frames']} 漂 {w['drift_mm']} mm" if w else ""))
    return {"summary": summary, "data": res, "warnings": [],
            "truncated": bool(res.get("truncated")), "hint":
            "flagged 段直接把 foot_lock_args 展开给 foot_lock；修后再调 slide_report 复测"}


def _tool_ground_report(ctx, frame_range=None, side=None, threshold_mm=10.0,
                        blend=4, detail=False, **_):
    if frame_range is None:
        raise RuntimeError("ground_report 需要 frame_range=[A,B]")
    from . import agent_bridge          # 运行期取信号库（避免插件载入时循环引用）
    store = agent_bridge.get_store()
    a, b = int(frame_range[0]), int(frame_range[1])
    snapshot = {}
    mask = (store.frames >= a) & (store.frames <= b)
    for s in (["L", "R"] if not side else [_foot(side)]):
        sh = store.signals.get(f"foot.{s}.sole_h")
        if sh is not None and int(mask.sum()) == b - a + 1:
            snapshot[s] = np.asarray(sh)[mask]
    cal = contact_heights(store.signals, store.frames, store.floor_z, ctx["scene"])
    res = ground_report(ctx["scene"], ctx["armature"], frame_range=frame_range,
                        floor_z=store.floor_z, side=side, threshold_mm=threshold_mm,
                        blend=blend, snapshot=snapshot, contact_height=cal,
                        detail=bool(detail))
    parts = []
    for s, r in res["sides"].items():
        parts.append(f"{s}: 着地高度 {r['contact_height_mm']} mm，最低处 rel {r['rel_min_mm']} mm"
                     f" @ {r['clearance_min_frame']}，下沉段 {len(r['pen_frames'])}，悬空接触段 "
                     f"{sum(1 for c in r['contacts'] if c['floating'])}")
    stale = [s for s, r in res["sides"].items() if r.get("snapshot_diff_max_mm", 0) > 1.0]
    warnings = ([f"{'/'.join(stale)} 脚的快照（fix_ground 用的 sole_h）与当前姿态差 > 1 mm："
                 "这段已经被修过，fix_ground 会按旧高度算"] if stale else [])
    return {"summary": "；".join(parts), "data": res, "warnings": warnings,
            "truncated": False,
            "hint": "fix_ground_args 去掉 why 后原样传给 fix_ground（rest_clearance 已是米）；修后同参数再调 ground_report 复测"}


def _scope_foot_lock(ctx, args):
    if args.get("dry_run"):
        return []
    a2 = _foot_args(ctx, args)
    return [([f"foot_ik.{_foot(a2['side'])}"],
             (int(a2["frame_range"][0]), int(a2["frame_range"][1])))]


def _reapply_foot_lock(armature, base_action, *, params, frame_range, status,
                       scene, track_name):
    p = dict(params)
    p["frame_range"] = frame_range
    return foot_lock(scene, armature, op_mode=status, data_dir=None,
                     track_name=track_name, record=False, **p)


TOOLS = {"foot_lock": _tool_foot_lock, "slide_report": _tool_slide_report,
         "ground_report": _tool_ground_report}
WRITE_SCOPES = {"foot_lock": _scope_foot_lock}
TUNABLE = {"foot_lock": [
    {"key": "lock", "kind": "choice", "options": list(LOCK_MODES)},
    {"key": "strength", "kind": "float", "min": 0.0, "max": 1.0},
    {"key": "blend", "kind": "int", "min": 0, "max": 40},
    {"key": "frame_range", "kind": "range"},
]}
REAPPLY = {"foot_lock": _reapply_foot_lock}
