"""Agent write tools on a non-destructive NLA layer (Blender side).

Per the plan: corrections live on their own Combine-blend NLA strips - the
source action is never touched, each op is one strip, and reverting is simply
deleting it.  Strips store *deltas* (scalar: desired-base; rotation: rel-quat)
so Combine adds them / multiplies them onto whatever the base action holds -
including later hand edits.

mode="preview" writes the strip tagged "preview"; "commit" is just a status in
the op log - the strip is identical either way.  ``revert`` removes the strip;
every op also works on a copy so preview metrics are computed before writing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import bpy

from . import agent_bake, agent_fx
from .animation import bone_path

AGENT_TRACK_PREFIX = "mcd_agent"
BASE_TRACK = "mcd_base"          # pushed-down base action lives here
OPLOG_NAME = "agent_ops.json"


# ---------------------------------------------------------------------------
# strip plumbing

def ensure_base_on_nla(armature: Any):
    """Push the active action onto a bottom NLA strip.

    Blender evaluates: NLA tracks (bottom→top) then the ACTIVE action last with
    REPLACE - which silently overrides every Combine strip underneath.  So the
    base action must itself become a REPLACE strip at the bottom of the stack;
    then agent deltas on higher tracks actually reach the pose.
    """
    anim = armature.animation_data
    if anim is None:
        return None
    action = anim.action
    if action is None:
        for tr in anim.nla_tracks:            # already pushed down
            if tr.name == BASE_TRACK and tr.strips:
                return tr.strips[0].action
        return None
    # NOTE: Blender 4.x exposes no nla_tracks.move(), so ordering relies on
    # creation order - nla_tracks.new() lands on TOP of the stack (evaluated
    # last), i.e. the track created LATEST wins.  We create the base track
    # first and agent tracks after it; _create order in _write_strip keeps
    # preview above base.  Verified by effect_check().
    track = anim.nla_tracks.new()
    track.name = BASE_TRACK
    f0, f1 = action.frame_range
    strip = track.strips.new("base", max(1, int(f0)), action)
    strip.blend_type = "REPLACE"
    strip.extrapolation = "HOLD"
    strip.action_frame_start = float(f0)
    strip.action_frame_end = float(f1)
    anim.action = None
    return action


def ensure_agent_track(armature: Any, track_name: str | None = None):
    """Return the named agent track, creating it if needed.

    New tracks land on top of the NLA stack (evaluated last → wins)."""
    anim = armature.animation_data or armature.animation_data_create()
    wanted = track_name or AGENT_TRACK_PREFIX
    for tr in anim.nla_tracks:
        if tr.name == wanted:
            return tr
    track = anim.nla_tracks.new()
    track.name = wanted
    return track


def _write_strip(
    armature: Any,
    name: str,
    frame_start: int,
    scalars: Mapping[tuple, np.ndarray] | None = None,
    quats: Mapping[str, np.ndarray] | None = None,
    *,
    blend: int = 4,
    track_name: str | None = None,
) -> tuple[Any, Any]:
    """Build an action of tapered deltas and add it as a Combine strip.

    scalars: {(data_path, index): (T,) delta}
    quats:   {quat data_path: (T,4) delta quat}
    """
    scalars = scalars or {}
    quats = quats or {}
    if not scalars and not quats:
        raise RuntimeError("没有可写的通道")
    length = max(
        (len(v) for v in scalars.values()), default=0,
    )
    length = max(length, max((len(v) for v in quats.values()), default=0))

    ensure_base_on_nla(armature)     # base must be a strip or it masks deltas
    action = bpy.data.actions.new(f"{name}_delta")
    for (path, index), delta in scalars.items():
        agent_bake.write_fcurve_values(
            action, path, index, frame_start,
            agent_fx.taper_deltas(delta, blend), group=name,
        )
    for path, dq in quats.items():
        agent_bake.write_quat_values(
            action, path, frame_start,
            agent_fx.taper_quat_deltas(dq, blend), group=name,
        )

    track = ensure_agent_track(armature, track_name)
    strip = track.strips.new(name, int(frame_start), action)
    strip.blend_type = "COMBINE"
    strip.use_auto_blend = True
    strip.extrapolation = "NOTHING"
    return track, strip


# ---------------------------------------------------------------------------
# op log

def _oplog_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / "agent_ops.json"


def _load_oplog(data_dir: str | Path) -> list:
    path = _oplog_path(data_dir)
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_oplog(data_dir: str | Path, ops: Sequence[Mapping[str, Any]]) -> None:
    path = _oplog_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(ops), ensure_ascii=False, indent=1),
                    encoding="utf-8")


def _new_op(tool: str, params: Mapping[str, Any], frames,
            strip_name: str, status: str, metrics: Mapping | None) -> dict:
    return {
        "id": f"{tool}_{int(time.time() * 1000) % 10**9}",
        "tool": tool,
        "params": dict(params),
        "frames": [int(frames[0]), int(frames[1])],
        "strip": strip_name,
        "status": status,
        "metrics": dict(metrics or {}),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _record(data_dir, op) -> dict:
    ops = _load_oplog(data_dir)
    ops.append(op)
    _save_oplog(data_dir, ops)
    return op


def list_ops(data_dir: str | Path) -> list:
    return _load_oplog(data_dir)


def _find_strip(armature: Any, strip_name: str):
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None, None
    for track in anim.nla_tracks:
        for strip in track.strips:
            if strip.name == strip_name:
                return track, strip
    return None, None


def revert(armature: Any, data_dir: str | Path, op_id: str) -> dict:
    ops = _load_oplog(data_dir)
    for op in ops:
        if op["id"] == op_id:
            _track, strip = _find_strip(armature, op["strip"])
            if strip is not None:
                act = strip.action
                _track.strips.remove(strip)
                if act is not None:
                    bpy.data.actions.remove(act)
            op["status"] = "reverted"
            _save_oplog(data_dir, ops)
            return op
    raise RuntimeError(f"op {op_id} 不在记录里")


def commit(data_dir: str | Path, op_id: str) -> dict:
    ops = _load_oplog(data_dir)
    for op in ops:
        if op["id"] == op_id:
            op["status"] = "committed"
            _save_oplog(data_dir, ops)
            return op
    raise RuntimeError(f"op {op_id} 不在记录里")


def set_preview(scene: Any, frame_range: Sequence[int]) -> None:
    scene.use_preview_range = True
    scene.frame_preview_start = int(frame_range[0])
    scene.frame_preview_end = int(frame_range[1])


def locked_exclusions(data_dir: str | Path) -> list:
    """Ranges committed via apply_exemplar - the wizard must not auto-lock
    those frames again (they carry hand-authored content by design)."""
    out = []
    for op in _load_oplog(data_dir):
        if op.get("tool") == "apply_exemplar" and \
                op.get("status") in ("committed", "preview"):
            out.append(tuple(op["frames"]))
    return out


def effect_check(
    scene: Any,
    armature: Any,
    *,
    track_name: str,
    bones: Sequence[str],
    frames: Sequence[int],
) -> dict:
    """A/B 自检：mute→frame_set→读求值姿态，unmute→frame_set→再读。

    回答"这次写入真的改了求值结果吗"。对每个采样帧/骨骼给出指尖世界位移
    (mm) 和姿态旋转夹角 (deg)；verdict 是位移>1mm 或转角>0.5° 的帧占比。
    """
    from .animation import current_view_layer, preserve_scene_frame, \
        set_scene_frame

    anim = armature.animation_data
    track = None
    for tr in (anim.nla_tracks if anim else ()):
        if tr.name == track_name:
            track = tr
            break
    if track is None:
        raise RuntimeError(f"没有 NLA 轨 {track_name}")

    def _sample(frame):
        set_scene_frame(scene, int(frame))
        row = {}
        for bone in bones:
            pb = armature.pose.bones.get(bone)
            if pb is None:
                continue
            m = armature.matrix_world @ pb.matrix
            row[bone] = (m.translation.copy(), m.to_quaternion())
        return row

    per_frame = []
    hits = 0
    with preserve_scene_frame(scene):
        for f in frames:
            track.mute = True
            off = _sample(f)
            track.mute = False
            on = _sample(f)
            cells = {}
            for bone in off:
                (p0, q0), (p1, q1) = off[bone], on[bone]
                dist_mm = float((p1 - p0).length * 1000)
                ang = float(np.degrees(2 * np.arccos(
                    min(1.0, abs(float(q0.normalized().dot(q1.normalized())))))))
                cells[bone] = {"pos_mm": round(dist_mm, 1),
                               "rot_deg": round(ang, 1)}
            moved = any(c["pos_mm"] > 1.0 or c["rot_deg"] > 0.5
                        for c in cells.values())
            hits += int(moved)
            per_frame.append({"frame": int(f), "moved": moved,
                              "bones": cells})
    return {"track": track_name,
            "verdict": f"{hits}/{len(per_frame)} 帧有变化",
            "pass": hits == len(per_frame),
            "per_frame": per_frame}


def restore_accent(
    armature: Any,
    base_action: Any,
    data_path: str,
    index: int,
    frame_range: Sequence[int],
    method: str,
    *,
    strength: float = 0.5,
    raw_values: np.ndarray | None = None,
    impact_frame: int | None = None,
    retime_speed: float = 1.5,
    retime_split: float = 0.35,
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """Force-feel methods on a delta strip (same math as accent.apply_scalar)."""
    from . import accent

    start, end = int(frame_range[0]), int(frame_range[1])
    cur = agent_bake.sample_fcurve_values(base_action, data_path, index,
                                        start, end)
    if cur is None:
        raise RuntimeError(f"通道不存在：{data_path}[{index}]")
    n = len(cur)
    raw = None if raw_values is None else np.asarray(raw_values)[:n]
    method = str(method)
    if method == "hf_reinject":
        if raw is None:
            raise RuntimeError("hf_reinject 需要 raw_values")
        new = accent.hf_reinject(cur, raw, strength=strength, blend=blend)
    elif method == "ease_reshape":
        k = (impact_frame or (start + end) // 2) - start
        new = accent.ease_reshape(cur, k, pre=n // 3, post=n // 3,
                                 strength=strength, blend=blend)
    elif method == "retime":
        new = accent.retime(cur, attack_speed=retime_speed,
                            split=retime_split, blend=blend)
    elif method == "refilter":
        if raw is None:
            raise RuntimeError("refilter 需要 raw_values")
        new = accent.refilter(cur, raw, strength=strength, blend=blend)
    else:
        raise RuntimeError(f"未知方式 {method}，可用 {accent.METHODS}")

    name = f"agent_accent_{method}_{start}_{end}"
    _track, strip = _write_strip(
        armature, name, start, scalars={(data_path, index): new - cur},
        blend=blend, track_name=track_name)
    metrics = accent.accent_metrics(cur, new, raw)
    op = _new_op("restore_accent",
                 {"path": data_path, "index": index, "method": method,
                  "strength": strength},
                 (start, end), strip.name, op_mode, metrics)
    return _record(data_dir, op) if data_dir else op


# ---------------------------------------------------------------------------
# tools

def clean_jitter(
    armature: Any,
    base_action: Any,
    paths: Sequence[tuple],
    frame_range: Sequence[int],
    *,
    strength: float = 1.0,
    width: int = 5,
    blend: int = 4,
    mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """Zero-phase smooth each channel inside the window; write deltas."""
    start, end = int(frame_range[0]), int(frame_range[1])
    scalars = {}
    for path, index in paths:
        cur = agent_bake.sample_fcurve_values(base_action, path, index, start, end)
        if cur is None:
            continue
        new = agent_fx.clean_jitter_values(cur, strength=strength,
                                           width=width, blend=blend)
        scalars[(path, index)] = new - cur
    if not scalars:
        raise RuntimeError("没有任何通道在动作里")
    name = f"agent_jitter_{start}_{end}"
    _track, strip = _write_strip(armature, name, start, scalars=scalars,
                               blend=blend, track_name=track_name)
    op = _new_op("clean_jitter",
                 {"paths": [list(p) for p in paths], "strength": strength,
                  "width": width},
                 (start, end), strip.name, mode,
                 {"channel_count": len(scalars)})
    return _record(data_dir, op) if data_dir else op


def fix_ground(
    armature: Any,
    base_action: Any,
    loc_path: str,
    sole_h: np.ndarray,
    *,
    floor_z: float,
    rest_clearance: float = 0.0,
    mode: str = "lift",
    pin_xy: bool = False,
    frame_range: Sequence[int],
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """Fix sole height on an IK location channel; optionally pin XY."""
    start, end = int(frame_range[0]), int(frame_range[1])
    n = end - start + 1
    sole_h = np.asarray(sole_h, dtype=np.float64)[:n]
    desired_sole = agent_fx.ground_height_targets(
        sole_h, floor_z=floor_z, rest_clearance=rest_clearance,
        mode=mode, blend=blend)

    scalars = {}
    base_z = agent_bake.sample_fcurve_values(base_action, loc_path, 2, start, end)
    if base_z is None:
        raise RuntimeError(f"IK 位置 Z 通道不存在：{loc_path}")
    # sole and the IK root move together: same world-space delta
    scalars[(loc_path, 2)] = desired_sole - sole_h

    if pin_xy:
        for axis in (0, 1):
            base = agent_bake.sample_fcurve_values(base_action, loc_path, axis,
                                                   start, end)
            if base is None:
                continue
            pinned = np.full(len(base), float(np.median(base)))
            scalars[(loc_path, axis)] = pinned - base  # taper applied in strip
    name = f"agent_ground_{start}_{end}"
    _track, strip = _write_strip(armature, name, start, scalars=scalars,
                               blend=blend, track_name=track_name)
    op = _new_op("fix_ground",
                 {"loc_path": loc_path, "floor_z": floor_z, "mode": mode,
                  "pin_xy": pin_xy},
                 (start, end), strip.name, op_mode,
                 {"max_sole_shift": float(np.abs(desired_sole - sole_h).max())})
    return _record(data_dir, op) if data_dir else op


def solve_pelvis(
    armature: Any,
    base_action: Any,
    pelvis_path: str,
    pelvis_dz: np.ndarray,
    *,
    frame_range: Sequence[int],
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """Write precomputed pelvis-Z deltas (from agent_fx.pelvis_height_corrections)."""
    start, end = int(frame_range[0]), int(frame_range[1])
    dz = np.asarray(pelvis_dz, dtype=np.float64)
    if len(dz) != end - start + 1:
        raise RuntimeError("pelvis_dz 长度必须等于区间帧数")
    name = f"agent_pelvis_{start}_{end}"
    _track, strip = _write_strip(
        armature, name, start, scalars={(pelvis_path, 2): dz},
        blend=blend, track_name=track_name)
    op = _new_op("solve_pelvis",
                 {"pelvis_path": pelvis_path},
                 (start, end), strip.name, op_mode,
                 {"max_dz": float(np.abs(dz).max())})
    return _record(data_dir, op) if data_dir else op


def _basis_channel(action: Any, quat_path: str, start: int, end: int):
    """Sample rotation_quaternion fcurves → (T,4) wxyz; None if missing."""
    parts = [
        agent_bake.sample_fcurve_values(action, quat_path, i, start, end)
        for i in range(4)
    ]
    if any(p is None for p in parts):
        return None
    return np.stack(parts, axis=1)


def _geo_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Per-frame geodesic angle (deg) between two (T,4) quat series."""
    dot = np.abs(np.sum(a * b, axis=1))
    return np.degrees(2.0 * np.arccos(np.clip(dot, 0.0, 1.0)))


def _best_ref_frame(cur_by_bone: dict, start: int) -> int:
    """'auto' for from_frame: the range frame with the least total swing."""
    total = None
    for cur in cur_by_bone.values():
        swing = agent_fx.swing_twist_deg(cur)["swing_deg"]
        total = swing if total is None else total + swing
    return start + int(np.argmin(total))


def _desired_world_dir(
    scene: Any,
    armature: Any,
    bone: str,
    frames: Sequence[int],
    dir_vec: np.ndarray,
) -> np.ndarray:
    """Per-frame basis quat so the bone's world Y axis points along dir_vec.

    desired_pose = arm^-1 · align(cur_dir → dir_vec) · cur_world
    desired_basis = rel_rest^-1 · parent_pose^-1 · desired_pose
    """
    from mathutils import Matrix, Quaternion, Vector

    from .animation import preserve_scene_frame, set_scene_frame

    target = Vector(dir_vec).normalized()
    out = np.zeros((len(frames), 4))
    pb = armature.pose.bones[bone]
    parent = pb.parent
    if parent is not None:
        rel_rest = (parent.bone.matrix_local.inverted()
                    @ pb.bone.matrix_local)
    else:
        rel_rest = pb.bone.matrix_local.copy()
    arm_inv = armature.matrix_world.inverted()
    with preserve_scene_frame(scene):
        for i, f in enumerate(frames):
            set_scene_frame(scene, int(f))
            cur_world = armature.matrix_world @ pb.matrix
            cur_dir = (cur_world.to_quaternion() @ Vector((0.0, 1.0, 0.0)))
            align = cur_dir.rotation_difference(target).to_matrix().to_4x4()
            desired_world = align @ cur_world
            desired_pose = arm_inv @ desired_world
            if parent is not None:
                basis = (rel_rest.inverted()
                         @ pb.parent.matrix.inverted() @ desired_pose)
            else:
                basis = pb.bone.matrix_local.inverted() @ desired_pose
            q = basis.to_quaternion()
            out[i] = (q.w, q.x, q.y, q.z)
    # sign continuity
    for i in range(1, len(out)):
        if float(np.dot(out[i - 1], out[i])) < 0.0:
            out[i] = -out[i]
    return out


def hold_pose(
    armature: Any,
    base_action: Any,
    bones: Sequence[str],
    frame_range: Sequence[int],
    *,
    target: str = "values",
    values: Mapping[str, Sequence[float]] | None = None,
    ref_frame: int | str | None = None,
    world_dir: Sequence[float] | None = None,
    scene: Any | None = None,
    mode: str = "replace",
    threshold_deg: float = 8.0,
    strength: float = 1.0,
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """通用姿态保持：让若干骨骼在帧段内保持某个姿态（delta strip 实现）。

    target: "values"   - values={bone: wxyz}，默认 identity（伸直/回零位）
            "from_frame" - ref_frame 帧号或 "auto"（区间内摆动角最小的一帧）
            "world_dir"  - 每帧反算局部旋转，令骨轴指向 world_dir 向量
    mode:   "replace"  - 整段强制设成目标
            "clamp"    - 只把偏离目标 > threshold_deg 的帧压回阈值，保留小抖动
            "outlier"  - 超阈帧判为坏帧，用前后好帧 slerp 补
    strength 落在 strip.influence 上（NLA 属性里可拖滑块实时调）。
    """
    start, end = int(frame_range[0]), int(frame_range[1])
    n = end - start + 1
    if n < 2:
        raise RuntimeError("帧范围至少要 2 帧")
    if len(bones) > 24:
        raise RuntimeError(f"scope 越界：一次最多 24 根骨骼，给了 {len(bones)}")
    pose_names = set(armature.pose.bones.keys())
    missing = [b for b in bones if b not in pose_names]
    if missing:
        raise RuntimeError(f"scope 越界：骨骼不存在于该骨架 {missing}")

    frames = np.arange(start, end + 1)
    quats: dict[str, np.ndarray] = {}
    metrics = {"bones": {}, "fixed_frames": 0}
    values = values or {}

    cur_by_bone = {}
    for bone in bones:
        path = bone_path(bone, "rotation_quaternion")
        cur = _basis_channel(base_action, path, start, end)
        if cur is None:
            raise RuntimeError(f"{bone} 没有 rotation_quaternion 通道")
        cur_by_bone[bone] = cur

    if target == "from_frame" and ref_frame in (None, "auto"):
        ref_frame = _best_ref_frame(cur_by_bone, start)

    for bone in bones:
        cur = cur_by_bone[bone]
        path = bone_path(bone, "rotation_quaternion")
        # ---- desired basis per mode ----
        if target == "values":
            ref = np.asarray(values.get(bone, [1.0, 0.0, 0.0, 0.0]),
                             dtype=np.float64)
            if len(ref) != 4:
                raise RuntimeError(f"{bone} 的 values 需要 wxyz 四分量")
            ref = ref / np.linalg.norm(ref)
            desired = np.tile(ref, (n, 1))
        elif target == "from_frame":
            rf = int(ref_frame)
            ref = _basis_channel(base_action, path, rf, rf)
            if ref is None:
                raise RuntimeError(f"{bone} 在 {rf} 帧无数据")
            desired = np.tile(ref[0], (n, 1))
        elif target == "world_dir":
            if scene is None or world_dir is None:
                raise RuntimeError("world_dir 需要 scene 与 world_dir 向量")
            desired = _desired_world_dir(
                scene, armature, bone, frames,
                np.asarray(world_dir, dtype=np.float64))
        else:
            raise RuntimeError(f"未知 target：{target}")

        if np.dot(desired[0], cur[0]) < 0:
            desired = -desired
        err = _geo_deg(cur, desired)

        if mode == "replace":
            final = desired
        elif mode == "clamp":
            # keep small deviations; pull the rest down to the threshold
            final = cur.copy()
            hot = err > float(threshold_deg)
            for i in np.where(hot)[0]:
                t = 1.0 - float(threshold_deg) / err[i]
                final[i] = agent_fx.slerp_array(cur[i], desired[i], t)
        elif mode == "outlier":
            # bad frames (> thr) get bridged by slerp between good neighbors
            good = err <= float(threshold_deg)
            final = cur.copy()
            i = 0
            while i < n:
                if good[i]:
                    i += 1
                    continue
                j = i
                while j < n and not good[j]:
                    j += 1
                a = i - 1
                b = j
                if a < 0 and b >= n:
                    final[i:j] = desired[i:j]          # 全是坏帧 → 用目标
                elif a < 0:
                    final[i:j] = np.tile(cur[b], (j - i, 1))
                elif b >= n:
                    final[i:j] = np.tile(cur[a], (j - i, 1))
                else:
                    final[i:j] = agent_fx.slerp_series(cur[a], cur[b], j - i)
                i = j
        else:
            raise RuntimeError(f"未知 mode：{mode}")

        err_after = _geo_deg(final, desired)
        metrics["bones"][bone] = {
            "err_max_before_deg": round(float(err.max()), 1),
            "err_max_after_deg": round(float(err_after.max()), 1),
            "fixed_frames": int((err > threshold_deg).sum()),
        }
        metrics["fixed_frames"] += int((err > threshold_deg).sum())
        quats[path] = agent_fx.delta_quat(final, cur)
        # scale the correction by strength via angle scaling
        if float(strength) < 1.0:
            from .pkl_hand import aa_to_quat, quat_to_aa
            quats[path] = aa_to_quat(
                quat_to_aa(quats[path]) * float(strength))

    name = f"agent_hold_{start}_{end}"
    _track, strip = _write_strip(
        armature, name, start, quats=quats, blend=blend,
        track_name=track_name)
    strip.influence = float(strength)
    op = _new_op(
        "hold_pose",
        {"bones": list(bones), "target": target,
         "ref_frame": ref_frame if target == "from_frame" else None,
         "world_dir": list(world_dir) if world_dir is not None else None,
         "mode": mode, "threshold_deg": threshold_deg,
         "strength": strength, "blend": blend},
        (start, end), strip.name, op_mode, metrics)
    return _record(data_dir, op) if data_dir else op


# ---------------------------------------------------------------------------
# exemplar library

def exemplar_dir(data_dir: str | Path) -> Path:
    return Path(data_dir) / "exemplars"


def register_exemplar(
    pre_bake: Mapping[str, Any],
    post_bake: Mapping[str, Any],
    foot_role: str,
    point_id: str,
    tag: str,
    data_dir: str | Path,
) -> dict:
    """Compute residual (post − pre) in anchor-local frame; store as exemplar.

    pre_bake/post_bake: bake dicts over the SAME frame range; the user's edits
    live only in post.  residual = what their keying added.
    """
    frames = np.asarray(post_bake["frames"])
    start, end = int(frames[0]), int(frames[-1])
    base_pos = np.asarray(pre_bake["pos"][foot_role])
    base_quat = np.asarray(pre_bake["quat"][foot_role])
    cur_pos = np.asarray(post_bake["pos"][foot_role])
    cur_quat = np.asarray(post_bake["quat"][foot_role])
    anchor_yaw = agent_fx.quat_to_yaw_deg(base_quat[:1])[0]
    residual = agent_fx.extract_residual(
        base_pos, base_quat, cur_pos, cur_quat, base_pos[0], anchor_yaw)
    sig = agent_fx.exemplar_signature(cur_quat, cur_pos)
    side = "L" if ".L" in foot_role or foot_role.endswith("L") else "R"

    folder = exemplar_dir(data_dir)
    folder.mkdir(parents=True, exist_ok=True)
    ex_id = f"{tag}_{start}_{end}"
    path = folder / f"{ex_id}.npz"
    np.savez_compressed(
        path,
        d_pos=np.asarray(residual["d_pos"]),
        d_quat=np.asarray(residual["d_quat"]),
        sig_yaw_rate=np.asarray(sig["yaw_rate"]),
        meta=np.asarray([start, end, sig["duration"], sig["yaw_sweep"],
                         sig["speed_mean"], anchor_yaw]),
    )
    meta_path = folder / f"{ex_id}.json"
    meta_path.write_text(json.dumps({
        "id": ex_id, "tag": tag, "foot": foot_role, "side": side,
        "frames": [start, end], "signature": sig,
        "anchor_yaw_deg": residual["anchor_yaw_deg"],
        "mirror_of": None,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"id": ex_id, "path": str(path), "signature": sig}


def load_exemplar(data_dir: str | Path, ex_id: str) -> dict:
    folder = exemplar_dir(data_dir)
    with np.load(folder / f"{ex_id}.npz") as npz:
        meta = npz["meta"]
        return {
            "id": ex_id,
            "d_pos": npz["d_pos"],
            "d_quat": npz["d_quat"],
            "signature": {"duration": int(meta[2]), "yaw_rate":
                          npz["sig_yaw_rate"].tolist(),
                          "yaw_sweep": float(meta[3]),
                          "speed_mean": float(meta[4])},
            "anchor_yaw_deg": float(meta[5]),
        }


def interval_signatures(
    bake: Mapping[str, Any],
    ranges: Sequence[Sequence[int]],
    foot_role: str,
    point_id: str,
) -> list:
    """Compute exemplar signatures per frame range on a bake dict - feeds
    find_matches (e.g. one candidate per planted interval)."""
    frames = np.asarray(bake["frames"])
    quats = np.asarray(bake["quat"][foot_role])
    pos = np.asarray(bake["point_pos"][point_id])
    out = []
    for a, b in ranges:
        mask = (frames >= int(a)) & (frames <= int(b))
        idx = np.where(mask)[0]
        if len(idx) < 3:
            continue
        sig = agent_fx.exemplar_signature(quats[idx], pos[idx])
        sig["range"] = [int(a), int(b)]
        out.append(sig)
    return out


def find_matches(
    exemplar: Mapping[str, Any],
    candidate_sigs: Sequence[Mapping[str, Any]],
    *,
    top_k: int = 5,
    min_score: float = 0.3,
) -> list:
    """Score candidate signatures (e.g. per planted interval) by DTW+duration."""
    scored = [
        (agent_fx.match_signature(exemplar["signature"], cand), cand)
        for cand in candidate_sigs
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {"score": s, "candidate": c}
        for s, c in scored[: int(top_k)] if s >= float(min_score)
    ]


def apply_exemplar(
    armature: Any,
    exemplar: Mapping[str, Any],
    target_pos: np.ndarray,
    target_quat: np.ndarray,
    anchor_yaw_deg: float,
    loc_path: str,
    quat_path: str,
    *,
    frame_range: Sequence[int],
    yaw_scale: float = 1.0,
    mirror: bool = False,
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
) -> dict:
    """Apply a stored exemplar to a target window; writes one delta strip."""
    start, end = int(frame_range[0]), int(frame_range[1])
    desired = agent_fx.apply_residual(
        exemplar, target_pos, target_quat, anchor_yaw_deg,
        yaw_scale=yaw_scale, mirror=mirror, blend=blend)
    scalars = {}
    for axis in range(3):
        scalars[(loc_path, axis)] = desired["pos"][:, axis] - \
            np.asarray(target_pos)[:, axis]
    dq = agent_fx.delta_quat(desired["quat"], np.asarray(target_quat))
    name = f"agent_ex_{exemplar['id']}_{start}"
    _track, strip = _write_strip(
        armature, name, start, scalars=scalars, quats={quat_path: dq},
        blend=blend, track_name=track_name)
    op = _new_op("apply_exemplar",
                 {"exemplar": exemplar["id"], "yaw_scale": yaw_scale,
                  "mirror": mirror},
                 (start, end), strip.name, op_mode,
                 {"max_pos_shift": float(np.abs(desired["pos"] - np.asarray(target_pos)).max())})
    return _record(data_dir, op) if data_dir else op


# ---------------------------------------------------------------------------
# validation

def validate(
    signals: Mapping[str, np.ndarray],
    frames: np.ndarray,
    frame_range: Sequence[int] | None = None,
    *,
    floor_z: float = 0.0,
    pen_tol: float = 0.005,
    slide_tol: float = 0.02,
    boundary_jump_m: float = 0.05,
) -> dict:
    """Check the plan's violations on the signal store arrays.

    Returns {"violations": [...], "ok": bool}; callers decide commit/rollback.
    """
    frames = np.asarray(frames)
    lo, hi = (int(frames[0]), int(frames[-1])) if frame_range is None \
        else (int(frame_range[0]), int(frame_range[1]))
    win = (frames >= lo) & (frames <= hi)
    violations = []

    for side in ("L", "R"):
        pen = signals.get(f"foot.{side}.pen")
        contact = signals.get(f"contact.{side}")
        speed = signals.get(f"foot.{side}.speed_xy")
        if pen is not None and contact is not None:
            bad = np.where(win & (contact > 0.5) & (pen > pen_tol))[0]
            if len(bad):
                violations.append({"kind": "penetration", "side": side,
                                   "frames": [int(frames[i]) for i in bad]})
        if speed is not None and contact is not None:
            bad = np.where(win & (contact > 0.5) & (speed > slide_tol))[0]
            if len(bad):
                violations.append({"kind": "slip", "side": side,
                                   "frames": [int(frames[i]) for i in bad]})
        sole = signals.get(f"foot.{side}.sole_h")
        if sole is not None and contact is not None:
            bad = np.where(win & (contact > 0.5)
                           & (sole - floor_z > 0.02))[0]
            if len(bad):
                violations.append({"kind": "floating", "side": side,
                                   "frames": [int(frames[i]) for i in bad]})
    # boundary continuity: jump in any foot speed at the range edges
    for side in ("L", "R"):
        speed = signals.get(f"foot.{side}.speed_xy")
        if speed is None:
            continue
        for f in (lo, hi):
            i = int(np.searchsorted(frames, f))
            if 0 < i < len(speed) - 1 and abs(speed[i + 1] - speed[i]) > boundary_jump_m:
                violations.append({"kind": "boundary_jump", "side": side,
                                   "frame": int(f),
                                   "jump": round(float(abs(speed[i + 1] - speed[i])), 4)})
    return {"ok": not violations, "violations": violations,
            "frame_range": [lo, hi]}
