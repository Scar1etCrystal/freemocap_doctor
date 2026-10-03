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


TOOLS = {"foot_lock": _tool_foot_lock, "slide_report": _tool_slide_report}
WRITE_SCOPES = {"foot_lock": _scope_foot_lock}
TUNABLE = {"foot_lock": [
    {"key": "lock", "kind": "choice", "options": list(LOCK_MODES)},
    {"key": "strength", "kind": "float", "min": 0.0, "max": 1.0},
    {"key": "blend", "kind": "int", "min": 0, "max": 40},
    {"key": "frame_range", "kind": "range"},
]}
REAPPLY = {"foot_lock": _reapply_foot_lock}
