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

AGENT_TRACK_PREFIX = "mcd_agent"     # legacy shared committed track
PREVIEW_TRACK = "AGENT_PREVIEW"      # legacy shared preview track
BASE_TRACK = "mcd_base"              # pushed-down base action lives here
OPLOG_NAME = "agent_ops.json"

# Every track the agent layer owns.  Per-op tracks are named after their strip
# ("agent_hold_505_570"); the two legacy shared names are migrated away but
# still recognised so an old .blend keeps working.  mcd_base is NOT included -
# it is the baseline, never part of A/B or per-fix control.
AGENT_TRACK_PREFIXES = ("agent_", PREVIEW_TRACK, AGENT_TRACK_PREFIX)


def is_agent_track_name(name: Any) -> bool:
    return str(name).startswith(AGENT_TRACK_PREFIXES)


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
                base_strip = tr.strips[0]
                # 老文件修复：strip 起点曾被 max(1,f0) 钳过而 action_frame_start
                # 没同步 → 基底滞后 (frame_start-afs) 帧求值，大角度 delta 直接
                # 炸出波浪残差。强制 afs=frame_start → sampled_t == f 恒等。
                if abs(float(base_strip.action_frame_start)
                       - float(base_strip.frame_start)) > 1e-4:
                    base_strip.action_frame_end += (
                        float(base_strip.frame_start)
                        - float(base_strip.action_frame_start))
                    base_strip.action_frame_start = \
                        float(base_strip.frame_start)
                return base_strip.action
        return None
    # NOTE: Blender 4.x exposes no nla_tracks.move(), so ordering relies on
    # creation order - nla_tracks.new() lands on TOP of the stack (evaluated
    # last), i.e. the track created LATEST wins.  We create the base track
    # first and agent tracks after it; _create order in _write_strip keeps
    # preview above base.  Verified by effect_check().
    track = anim.nla_tracks.new()
    track.name = BASE_TRACK
    f0, f1 = action.frame_range
    # 关键：action_frame_start 必须等于 frame_start——strip 把
    # [frame_start,frame_end] 映射到 [afs,afe]，sampled_t = afs+f-frame_start，
    # afs==frame_start 时恒等；错位则整条基底偏帧求值（曾经的 1 帧滞后 bug）。
    fs = max(1, int(f0))
    strip = track.strips.new("base", fs, action)
    strip.blend_type = "REPLACE"
    strip.extrapolation = "HOLD"
    strip.action_frame_start = float(fs)
    strip.action_frame_end = float(fs) + (float(f1) - float(f0))
    anim.action = None
    return action


def ensure_agent_track(armature: Any, track_name: str | None = None):
    """Fetch a named track (creating it on top of the stack if missing).

    Only used for explicit/legacy names - per-op writes go through
    ``_write_strip`` which always makes a fresh track so two fixes can share a
    frame range (strips may not overlap inside one track)."""
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

    Each write gets its OWN track named after the strip: two fixes on the same
    frames then stack instead of colliding ("no space to accommodate"), and
    every fix can be muted / re-tuned on its own.  ``track_name`` forces reuse
    of an existing track (legacy layout, migration).
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

    anim = armature.animation_data or armature.animation_data_create()
    track = None
    if track_name:
        for tr in anim.nla_tracks:
            if tr.name == track_name:
                track = tr
                break
    if track is None:
        track = anim.nla_tracks.new()      # new() lands on top = wins
        track.name = track_name or name
    strip = track.strips.new(name, int(frame_start), action)
    strip.blend_type = "COMBINE"
    strip.use_auto_blend = True
    strip.extrapolation = "NOTHING"
    if not track_name:
        track.name = strip.name    # mirror the uniquified strip name (.001 on clash)
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


# ---- plugin hooks -----------------------------------------------------------
# agent_bridge sets CURRENT_OWNER (the calling agent_id) around a write tool so
# every op written in that call carries an "owner" - revert/reapply by another
# agent is then refused.  None (GUI / legacy callers) = no owner key at all, so
# old logs and old callers see byte-identical ops.
CURRENT_OWNER: str | None = None
# Tools living in plugin modules (agent_motion / agent_copy / ...) register
# their re-solve function here:  fn(armature, base_action, *, params,
# frame_range, status, scene, track_name) -> op dict (NOT recorded).
REAPPLY_HANDLERS: dict = {}


def _new_op(tool: str, params: Mapping[str, Any], frames,
            strip_name: str, status: str, metrics: Mapping | None,
            track: str | None = None) -> dict:
    op = {
        "id": f"{tool}_{int(time.time() * 1000) % 10**9}",
        "tool": tool,
        "params": dict(params),
        "frames": [int(frames[0]), int(frames[1])],
        "strip": strip_name,
        "track": track,
        "status": status,
        "metrics": dict(metrics or {}),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if CURRENT_OWNER:
        op["owner"] = str(CURRENT_OWNER)
    return op


def _record(data_dir, op) -> dict:
    ops = _load_oplog(data_dir)
    # op id is the primary key (commit / revert / per-fix strength address it),
    # and _new_op's millisecond stamp can repeat when two writes land in the
    # same tick - so uniquify against the log here, not in the generator.
    existing = {o.get("id") for o in ops}
    if op.get("id") in existing:
        n = 2
        while f"{op['id']}_{n}" in existing:
            n += 1
        op["id"] = f"{op['id']}_{n}"
    ops.append(op)
    _save_oplog(data_dir, ops)
    return op


def list_ops(data_dir: str | Path) -> list:
    return _load_oplog(data_dir)


def get_op(data_dir: str | Path, op_id: str) -> dict | None:
    for op in _load_oplog(data_dir):
        if op.get("id") == op_id:
            return op
    return None


def base_action_of(armature: Any) -> Any | None:
    """基底动作：active action，或已压进 mcd_base strip 的那个。"""
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None
    if anim.action is not None:
        return anim.action
    for tr in anim.nla_tracks:
        if tr.name == BASE_TRACK and tr.strips:
            return tr.strips[0].action
    return None


# 每种写工具暴露给参数面板的可调项：kind = float/int/choice/object/range。
# 面板只画这里列的 key；bones/values 这类结构参数不给用户调。
TUNABLE_PARAMS = {
    "hold_pose": [
        {"key": "mode", "kind": "choice",
         "options": ["replace", "clamp", "outlier"]},
        {"key": "threshold_deg", "kind": "float", "min": 0.5, "max": 60.0,
         "when": {"mode": ["clamp", "outlier"]}},
        {"key": "strength", "kind": "float", "min": 0.0, "max": 2.0},
        {"key": "blend", "kind": "int", "min": 0, "max": 40},
        {"key": "dir_object", "kind": "object",
         "when": {"target": ["world_dir"]}},
        {"key": "dir_mode", "kind": "choice", "options": ["arrow", "aim"],
         "when": {"target": ["world_dir"], "dir_object": True}},
        {"key": "frame_range", "kind": "range"},
    ],
    "clean_jitter": [
        {"key": "strength", "kind": "float", "min": 0.0, "max": 2.0},
        {"key": "width", "kind": "int", "min": 1, "max": 15},
        {"key": "blend", "kind": "int", "min": 0, "max": 40},
        {"key": "frame_range", "kind": "range"},
    ],
    "restore_accent": [
        {"key": "strength", "kind": "float", "min": 0.0, "max": 1.0},
        {"key": "impact_frame", "kind": "int", "min": 0, "max": 100000},
        {"key": "blend", "kind": "int", "min": 0, "max": 40},
        {"key": "frame_range", "kind": "range"},
    ],
}


def _reapply_kwargs(tool: str, params: Mapping[str, Any],
                    frame_range, status: str) -> dict:
    """op params → 各工具的求解 kwargs。"""
    if tool == "hold_pose":
        return dict(
            bones=list(params.get("bones") or []),
            frame_range=frame_range,
            target=params.get("target", "values"),
            values=params.get("values"),
            ref_frame=params.get("ref_frame"),
            world_dir=params.get("world_dir"),
            world_axis=params.get("world_axis", "Y"),
            secondary_axis=params.get("secondary_axis"),
            dir_object=params.get("dir_object"),
            dir_mode=params.get("dir_mode", "arrow"),
            flip_guard_deg=float(params.get("flip_guard_deg", 150.0)),
            mode=params.get("mode", "replace"),
            threshold_deg=float(params.get("threshold_deg", 8.0)),
            strength=float(params.get("strength", 1.0)),
            blend=int(params.get("blend", 4)),
            op_mode=status,
        )
    if tool == "clean_jitter":
        return dict(
            paths=[tuple(p) for p in params.get("paths", [])],
            frame_range=frame_range,
            strength=float(params.get("strength", 1.0)),
            width=int(params.get("width", 5)),
            blend=int(params.get("blend", 4)),
            mode=status,
        )
    if tool == "restore_accent":
        if params.get("method") in ("hf_reinject", "refilter"):
            raise RuntimeError(
                f"{params.get('method')} 依赖 raw_values（不存 op log），"
                "该 op 不支持参数重写，请 revert 后重做")
        return dict(
            data_path=params["path"], index=params.get("index"),
            frame_range=frame_range, method=params.get("method"),
            strength=float(params.get("strength", 0.5)),
            impact_frame=params.get("impact_frame"),
            retime_speed=float(params.get("retime_speed", 1.5)),
            retime_split=float(params.get("retime_split", 0.35)),
            blend=int(params.get("blend", 4)),
            op_mode=status,
        )
    raise RuntimeError(f"{tool} 不支持参数重写")


def reapply(data_dir: str | Path, armature: Any, op_id: str, *,
            scene: Any | None = None, base_action: Any | None = None,
            **overrides) -> dict:
    """同轨重写：用更新后的参数重新解算，删掉旧 strip，在同一 track 写新的。

    修复条目的参数控件走这里：滑块防抖 250ms 后调本函数——任何时刻场景里
    只有一条 strip，op_id 不变，params/metrics 更新进 log。
    """
    ops = _load_oplog(data_dir)
    op = next((o for o in ops if o.get("id") == op_id), None)
    if op is None:
        raise RuntimeError(f"op 不存在：{op_id}")
    tool = op.get("tool")
    plugin = REAPPLY_HANDLERS.get(tool)
    if tool not in TUNABLE_PARAMS and plugin is None:
        raise RuntimeError(f"{tool} 不支持参数重写")
    params = dict(op.get("params") or {})
    params.update(overrides)
    frame_range = params.get("frame_range") or op.get("frames")
    base_action = base_action or base_action_of(armature)
    if base_action is None:
        raise RuntimeError("找不到基底动作（active action / mcd_base）")

    kwargs = (None if plugin is not None
              else _reapply_kwargs(tool, params, frame_range, op.get("status")))
    old_track_name = op.get("track")
    old_strip_name = op.get("strip")

    # 同轨不允许时间重叠：先把旧 strip 挪出时间窗，新 strip 写成功后删旧的；
    # 写失败挪回——不会两头丢。
    anim = armature.animation_data
    track = None
    if anim is not None and old_track_name:
        for tr in anim.nla_tracks:
            if tr.name == old_track_name:
                track = tr
                break
    old_strip = (track.strips.get(old_strip_name)
                 if track is not None and old_strip_name else None)
    _SHIFT = 100000
    if old_strip is not None:
        old_strip.frame_start += _SHIFT
        old_strip.frame_end += _SHIFT
    res = None
    try:
        if plugin is not None:
            res = plugin(armature, base_action, params=params,
                         frame_range=frame_range, status=op.get("status"),
                         scene=scene, track_name=old_track_name)
        elif tool == "hold_pose":
            res = hold_pose(armature, base_action, scene=scene, data_dir=None,
                            record=False, track_name=old_track_name, **kwargs)
        elif tool == "clean_jitter":
            res = clean_jitter(armature, base_action, data_dir=None,
                               track_name=old_track_name, **kwargs)
        elif tool == "restore_accent":
            res = restore_accent(armature, base_action, data_dir=None,
                                 track_name=old_track_name, **kwargs)
    except Exception:
        if old_strip is not None:
            old_strip.frame_start -= _SHIFT
            old_strip.frame_end -= _SHIFT
        raise
    if track is not None:
        if old_strip is not None:
            track.strips.remove(old_strip)
        # 新 strip 让回原 strip 名，保证 op.strip / 列表显示稳定
        if res is not None:
            new_strip = None
            for s in track.strips:
                if s.name == res.get("strip"):
                    new_strip = s
                    break
            if new_strip is not None and old_strip_name \
                    and new_strip.name != old_strip_name:
                try:
                    new_strip.name = old_strip_name
                    res["strip"] = new_strip.name
                except Exception:
                    pass
    op["params"] = params
    op["params"]["frame_range"] = [int(frame_range[0]), int(frame_range[1])]
    op["frames"] = [int(frame_range[0]), int(frame_range[1])]
    if res is not None:
        op["strip"] = res.get("strip", op["strip"])
        op["metrics"] = res.get("metrics", {})
    op["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_oplog(data_dir, ops)
    return op


def _find_strip(armature: Any, strip_name: str):
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None, None
    for track in anim.nla_tracks:
        for strip in track.strips:
            if strip.name == strip_name:
                return track, strip
    return None, None


def find_op_strip(armature: Any, op: Mapping[str, Any]):
    """Locate the (track, strip) a log entry points at.

    Ops with a ``track`` field (per-op-track era) match that track EXACTLY - a
    miss means the strip is gone, not "fall through to name search": the same
    strip name can exist on another armature, and the fall-through let
    source-side ops steal the RIG's strip.  Legacy ops (no track) may only
    claim strips on the legacy shared tracks, for the same reason - a
    same-named strip on a per-op track belongs to a newer op."""
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None, None
    tname = op.get("track")
    sname = op.get("strip")
    if tname:
        for tr in anim.nla_tracks:
            if tr.name != tname:
                continue
            for s in tr.strips:
                if not sname or s.name == sname:
                    return tr, s
        return None, None
    if sname:
        for tr in anim.nla_tracks:
            if not (tr.name.startswith(PREVIEW_TRACK)
                    or tr.name.startswith(AGENT_TRACK_PREFIX)):
                continue
            for s in tr.strips:
                if s.name == sname:
                    return tr, s
    return None, None


def delete_op_strip(armature: Any, op: Mapping[str, Any]) -> bool:
    """Remove an op's strip + its now-empty track + its private action."""
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return False
    track, strip = find_op_strip(armature, op)
    if strip is None:
        return False
    act = strip.action
    track.strips.remove(strip)
    if act is not None and act.users == 0:
        bpy.data.actions.remove(act)
    if len(track.strips) == 0:
        anim.nla_tracks.remove(track)
    return True


def revert(armature: Any, data_dir: str | Path, op_id: str) -> dict:
    ops = _load_oplog(data_dir)
    for op in ops:
        if op["id"] == op_id:
            delete_op_strip(armature, op)
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


# ---------------------------------------------------------------------------
# legacy layout migration + reconciliation

def migrate_legacy_tracks(armature: Any, data_dir: str | Path | None = None) -> dict:
    """Give every strip on a legacy shared track its own per-op track.

    Idempotent: after the first run there are no legacy tracks left, so a
    second call is a no-op.  Updates the op log's ``track`` field so panel
    lookups stay exact.

    Every structural NLA edit (new/remove track or strip) invalidates earlier
    RNA pointers - hence three phases: snapshot by NAME, build the new track
    under a temp name, then drop the source and rename to the real name.  The
    strip is created before the source is deleted, so a mid-way failure never
    loses animation.
    """
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return {"moved": 0}

    # ---- phase 1: snapshot (names + settings only)
    snapshots = []
    for tr in anim.nla_tracks:
        if not (tr.name.startswith(PREVIEW_TRACK)
                or tr.name.startswith(AGENT_TRACK_PREFIX)):
            continue
        for s in tr.strips:
            snapshots.append({
                "src_track": tr.name,
                "name": s.name,
                "action": s.action.name if s.action else None,
                "frame_start": float(s.frame_start),
                "frame_end": float(s.frame_end),
                "action_start": float(s.action_frame_start),
                "action_end": float(s.action_frame_end),
                "blend_type": s.blend_type,
                "auto_blend": bool(s.use_auto_blend),
                "extrapolation": s.extrapolation,
                "influence": float(s.influence),
            })
    if not snapshots:
        return {"moved": 0}

    ops = _load_oplog(data_dir) if data_dir else []
    by_strip = {o.get("strip"): o for o in ops if o.get("strip")}
    moved = 0

    # ---- phase 2 + 3: build under a temp name, drop the source, rename back
    for spec in snapshots:
        action = bpy.data.actions.get(spec["action"]) if spec["action"] else None
        if action is None:
            continue
        temp_track = f"{spec['name']}__migrating"
        anim.nla_tracks.new().name = temp_track
        track = None
        for tr in anim.nla_tracks:
            if tr.name == temp_track:
                track = tr
                break
        if track is None:
            continue
        strip = track.strips.new(spec["name"], int(spec["frame_start"]), action)
        strip.blend_type = spec["blend_type"]
        strip.use_auto_blend = spec["auto_blend"]
        strip.extrapolation = spec["extrapolation"]
        strip.influence = spec["influence"]
        strip.action_frame_start = spec["action_start"]
        strip.action_frame_end = spec["action_end"]
        strip.frame_end = spec["frame_end"]

        src_track = None
        for tr in anim.nla_tracks:
            if tr.name != spec["src_track"]:
                continue
            src_track = tr
            for s in list(tr.strips):
                if s.action is action and s.name == spec["name"]:
                    tr.strips.remove(s)
                    break
        if src_track is not None and len(src_track.strips) == 0:
            anim.nla_tracks.remove(src_track)

        final_track = None
        for tr in anim.nla_tracks:          # pointers went stale - re-fetch
            if tr.name == temp_track:
                final_track = tr
                break
        if final_track is None:
            continue
        if final_track.strips:
            final_track.strips[0].name = spec["name"]
        final_track.name = spec["name"]
        moved += 1

        op = by_strip.get(spec["name"])
        if op is not None:
            op["track"] = final_track.name

    if data_dir and moved:
        _save_oplog(data_dir, ops)
    return {"moved": moved}


def _op_label(op: Mapping[str, Any]) -> str:
    """Human tag for the fix list: frames + tool + bone (多条同窗 op 的区分)."""
    p = op.get("params", {}) or {}
    tag = ""
    path = str(p.get("path") or "")
    if '"' in path:
        tag = path.split('"')[1]
        tag += "·位置" if path.endswith(".location") else "·旋转"
    elif p.get("bones"):
        bl = list(p["bones"])
        tag = str(bl[0]) + ("…" if len(bl) > 1 else "")
    fr = op.get("frames")
    head = f"{fr[0]}-{fr[1]}" if fr else ""
    return f"{head} {op.get('tool', '')} {tag}".rstrip()


def reconcile(armature: Any, data_dir: str | Path) -> list:
    """Op log vs. live NLA - the scene is the truth about what exists.

    Returns one row per fix: log entries that still have a live strip, entries
    whose strip vanished (status "lost"), and agent tracks nobody claims
    ("unregistered").  The panel renders exactly these rows.
    """
    ops = _load_oplog(data_dir)
    rows: list[dict] = []
    claimed: set[str] = set()
    for op in ops:
        if op.get("status") == "reverted":
            continue
        track, strip = find_op_strip(armature, op)
        row = {
            "op_id": op["id"],
            "tool": op.get("tool", ""),
            "status": op.get("status", ""),
            "frames": op.get("frames"),
            "label": _op_label(op),
            "strip": op.get("strip"),
            "track": track.name if track is not None else op.get("track"),
            "alive": strip is not None,
            "exponent": 1.0,
            "muted": False,
        }
        if strip is not None:
            act = strip.action
            row["exponent"] = float(act.get("applied_exp", 1.0)) if act else 1.0
            row["muted"] = bool(track.mute)
            claimed.add(strip.name)
        else:
            row["status"] = "lost"
        rows.append(row)

    anim = getattr(armature, "animation_data", None)
    for tr in (anim.nla_tracks if anim else ()):
        if not is_agent_track_name(tr.name):
            continue
        for s in tr.strips:
            if s.name in claimed:
                continue
            act = s.action
            rows.append({
                "op_id": "",
                "tool": "?",
                "status": "unregistered",
                "frames": [int(s.frame_start), int(s.frame_end)],
                "label": s.name,
                "strip": s.name,
                "track": tr.name,
                "alive": True,
                "exponent": float(act.get("applied_exp", 1.0)) if act else 1.0,
                "muted": bool(tr.mute),
            })
    return rows


def set_strip_exponent(strip: Any, exponent: float) -> dict:
    """力度旋钮：把 strip delta 写成 delta^exponent（>1 = 超量修正）。

    NLA strip.influence 硬上限是 1.0，拖过 1 没用；真正的"力度"是把 delta
    曲线的旋转角本身放大。轴角缩放保持方向、只加倍数。

    注意：applied_exp 记在 **action** 上——NLA strip 不支持自定义属性
    （连 .get() 都抛 TypeError），action 是 ID 没有这个限制。
    """
    from .pkl_hand import aa_to_quat, quat_to_aa

    action = strip.action
    if action is None:
        return {"touched": 0}

    # 收集每骨的 4 条四元数曲线
    by_bone: dict[str, dict[int, Any]] = {}
    for fc in action.fcurves:
        if fc.data_path.endswith(".rotation_quaternion"):
            by_bone.setdefault(fc.data_path, {})[fc.array_index] = fc

    touched = 0
    e_prev = float(action.get("applied_exp", 1.0)) or 1.0
    for path, curves in by_bone.items():
        if len(curves) != 4:
            continue
        n = len(curves[0].keyframe_points)
        for i in range(n):
            frame = curves[0].keyframe_points[i].co[0]
            q = np.array([curves[c].keyframe_points[i].co[1] for c in range(4)])
            unit_aa = quat_to_aa(q.reshape(1, 4))[0] / e_prev
            new_q = aa_to_quat((unit_aa * exponent).reshape(1, 3))[0]
            for c in range(4):
                kp = curves[c].keyframe_points[i]
                kp.co = (frame, float(new_q[c]))
        for fc in curves.values():
            fc.update()      # 重算贝塞尔手柄，保持原插值类型
        touched += 1

    action["applied_exp"] = float(exponent)
    strip.influence = 1.0    # 力度烘进曲线，influence 不再当旋钮
    return {"touched": touched, "exponent": float(exponent)}


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
    index: int | None,
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
    """Force-feel methods on a delta strip.

    Channel handling (力量感必须整骨同步改时间，不能单分量)：
    - rotation_quaternion：四个分量同窗同参数重塑 → 归一化 → 写**真四元数
      delta**（conj(cur) ⊗ new）。COMBINE 对四元数是乘法，按分量差写标量
      会得到方向错误的旋转——旧实现就是这么错的，脊柱类骨头从没正确生效过。
    - location：三个轴一条 op 里同步重塑（同一速度增益曲线），时间保持一致。
    - 其他通道：单 (path, index)，行为同旧版。
    """
    from . import accent

    start, end = int(frame_range[0]), int(frame_range[1])
    path = str(data_path)
    k = (impact_frame if impact_frame is not None
         else (start + end) // 2) - start

    def _reshape(values, raw_c=None):
        values = np.asarray(values, dtype=np.float64)
        if method == "ease_reshape":
            return accent.ease_reshape(values, k, pre=len(values) // 3,
                                       post=len(values) // 3,
                                       strength=strength, blend=blend)
        if method == "retime":
            return accent.retime(values, attack_speed=retime_speed,
                                 split=retime_split, blend=blend)
        if method == "hf_reinject":
            if raw_c is None:
                raise RuntimeError("hf_reinject 需要 raw_values")
            return accent.hf_reinject(values, raw_c[:len(values)],
                                      strength=strength, blend=blend)
        if method == "refilter":
            if raw_c is None:
                raise RuntimeError("refilter 需要 raw_values")
            return accent.refilter(values, raw_c[:len(values)],
                                   strength=strength, blend=blend)
        raise RuntimeError(f"未知方式 {method}，可用 {accent.METHODS}")

    name = f"agent_accent_{method}_{start}_{end}"

    if path.endswith(".rotation_quaternion"):
        comps = [agent_bake.sample_fcurve_values(base_action, path, i,
                                                 start, end)
                 for i in range(4)]
        if any(c is None for c in comps):
            raise RuntimeError(f"通道不存在：{path}")
        cur = np.stack(comps, axis=1)              # (T,4) wxyz
        cur /= np.linalg.norm(cur, axis=1, keepdims=True)
        for i in range(1, len(cur)):               # 防 fcurve 符号翻转
            if float(cur[i] @ cur[i - 1]) < 0:
                cur[i] = -cur[i]
        raw4 = None if raw_values is None else np.asarray(raw_values)
        new = cur.copy()
        for c in range(4):
            raw_c = None if raw4 is None else raw4[:, c]
            new[:, c] = _reshape(cur[:, c], raw_c)
        new /= np.linalg.norm(new, axis=1, keepdims=True)
        dq = agent_fx.delta_quat(new, cur)
        _track, strip = _write_strip(armature, name, start, quats={path: dq},
                                     blend=blend, track_name=track_name)
        ang = np.degrees(2 * np.arccos(np.clip(
            np.abs(np.sum(cur * new, axis=1)), 0.0, 1.0)))
        metrics = {"max_pose_shift_deg": round(float(ang.max()), 1),
                   "impact_frame": int(k + start)}
    elif path.endswith(".location"):
        comps = [agent_bake.sample_fcurve_values(base_action, path, i,
                                                 start, end)
                 for i in range(3)]
        if any(c is None for c in comps):
            raise RuntimeError(f"通道不存在：{path}")
        cur = np.stack(comps, axis=1)              # (T,3)
        raw3 = None if raw_values is None else np.asarray(raw_values)
        new = cur.copy()
        for c in range(3):
            raw_c = None if raw3 is None else raw3[:, c]
            new[:, c] = _reshape(cur[:, c], raw_c)
        _track, strip = _write_strip(
            armature, name, start,
            scalars={(path, i): new[:, i] - cur[:, i] for i in range(3)},
            blend=blend, track_name=track_name)
        shift = np.linalg.norm(new - cur, axis=1)
        metrics = {"max_shift_m": round(float(shift.max()), 4),
                   "impact_frame": int(k + start)}
    else:
        cur = agent_bake.sample_fcurve_values(base_action, path,
                                              int(index), start, end)
        if cur is None:
            raise RuntimeError(f"通道不存在：{path}[{index}]")
        new = _reshape(cur, raw_values)
        _track, strip = _write_strip(
            armature, name, start,
            scalars={(path, int(index)): new - cur},
            blend=blend, track_name=track_name)
        metrics = accent.accent_metrics(cur, new, raw_values)

    op = _new_op("restore_accent",
                 {"path": path, "index": index, "method": method,
                  "strength": strength, "impact_frame": impact_frame,
                  "retime_speed": retime_speed, "retime_split": retime_split,
                  "blend": blend, "frame_range": [start, end]},
                 (start, end), strip.name, op_mode, metrics,
                 track=_track.name)
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
                  "width": width, "blend": blend,
                  "frame_range": [start, end]},
                 (start, end), strip.name, mode,
                 {"channel_count": len(scalars)},
                 track=_track.name)
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
                 {"max_sole_shift": float(np.abs(desired_sole - sole_h).max())},
                 track=_track.name)
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
                 {"max_dz": float(np.abs(dz).max())},
                 track=_track.name)
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


_AXIS_VECTORS = {
    "X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0),
    "-X": (-1.0, 0.0, 0.0), "-Y": (0.0, -1.0, 0.0), "-Z": (0.0, 0.0, -1.0),
}


def _axis_vec(axis: Any):
    """world_axis/secondary_axis 参数：'X'/'-Z' 字符串或任意局部向量三元组。"""
    from mathutils import Vector
    if axis is None:
        return None
    if isinstance(axis, str):
        key = axis.strip().upper()
        if key not in _AXIS_VECTORS:
            raise RuntimeError(f"未知轴 {axis!r}：用 X/Y/Z（可带负号）、三元组"
                               "或 'probe:<part>.<side>'")
        return Vector(_AXIS_VECTORS[key])
    v = Vector(axis)
    if v.length < 1e-6:
        raise RuntimeError("轴向量长度为零")
    return v.normalized()


def _probe_axis_fn(axis: Any):
    """'probe:<part>[.<side>]' → 逐帧世界方向函数；否则 None。

    解剖方向相对控制骨随帧变（手指有自己的动画，实测局部轴散布 71°）——
    均值轴对齐每帧都留几十度残差。probe 轴让求解器逐帧现推。"""
    if not (isinstance(axis, str) and axis.startswith("probe:")):
        return None
    spec = axis[6:].strip()
    part, _, side = spec.rpartition(".")
    from . import agent_anatomy
    return agent_anatomy.frame_probe_fn(part, side.upper() or None)


def _target_fn(scene: Any, armature: Any, pb: Any,
               world_dir: Any, dir_object: str | None,
               dir_mode: str):
    """返回 callable()->Vector，逐帧求目标方向。

    - world_dir 给固定向量：常量目标
    - dir_object + mode='arrow'：空物体（single-arrow 约定）局部 +Z 轴
    - dir_object + mode='aim'：骨头发射到物体位置
    空物体可 k 动画 → 方向随帧变，本就逐帧解算所以免费支持。
    """
    from mathutils import Vector

    if dir_object:
        obj = bpy.data.objects.get(str(dir_object))
        if obj is None:
            raise RuntimeError(f"方向物体不存在：{dir_object}")
        if dir_mode == "aim":
            def fn():
                d = (obj.matrix_world.translation
                     - (armature.matrix_world @ pb.head))
                return d.normalized() if d.length > 1e-6 else Vector((0, 0, 1))
        else:                                # arrow：+Z 轴即箭头指向
            def fn():
                return (obj.matrix_world.to_quaternion()
                        @ Vector((0.0, 0.0, 1.0))).normalized()
        return fn
    if world_dir is None:
        raise RuntimeError("world_dir 需要向量或 dir_object")
    const = Vector(world_dir).normalized()

    def fn():
        return Vector(const)
    return fn


def _desired_world_dir(
    scene: Any,
    armature: Any,
    bone: str,
    frames: Sequence[int],
    dir_vec: np.ndarray | None,
    axis: Any = "Y",
    secondary_axis: Any = None,
    dir_object: str | None = None,
    dir_mode: str = "arrow",
    flip_guard_deg: float = 150.0,
) -> tuple[np.ndarray, dict]:
    """Per-frame basis quat so the bone's world `axis` points along the target.

    axis/secondary_axis: "X"/"-Z" 或任意局部向量三元组（probe_anatomy 给的
    就是后者）。无次轴 = 最小旋转（旧行为）；给次轴 = 双轴解算：主轴转到
    target，次轴保持"当前指向在 ⊥target 平面上的投影"——扭转被显式钉住，
    180° 翻转成为绕次轴的干净滚转，不再有 rotation_difference 在近 180°
    时乱选轴把肢体翻过去的病态。

    无次轴路径加翻转护栏：所需旋转 > flip_guard_deg 的帧不转（近 180° 的
    最小旋转轴是任意的，硬转几乎必错——历史上"手翻进手里"就是这么来的），
    计入 metrics.skipped_flip_frames。

    返回 (wxyz 基四元数 (T,4), per-bone metrics)。
    """
    from mathutils import Matrix, Vector

    from .animation import preserve_scene_frame, set_scene_frame

    pb = armature.pose.bones[bone]
    target = _target_fn(scene, armature, pb, dir_vec, dir_object, dir_mode)
    lp_fn = _probe_axis_fn(axis)
    ls_fn = _probe_axis_fn(secondary_axis)
    lp_static = None if lp_fn else _axis_vec(axis).normalized()
    ls_static = None if ls_fn else _axis_vec(secondary_axis)
    dual = ls_static is not None or ls_fn is not None
    if dual and lp_static is not None:
        # 静态+静态：局部正交架只建一次（probe 轴逐帧重建，见循环内）
        ls_o = ls_static - lp_static * ls_static.dot(lp_static)
        if ls_o.length < 1e-4:
            raise RuntimeError("secondary_axis 与主轴平行，退化成单轴")
        Lr_static = Matrix((lp_static, ls_o.normalized(),
                            lp_static.cross(ls_o.normalized())))
    else:
        Lr_static = None

    out = np.zeros((len(frames), 4))
    mets = {"align_max_deg": 0.0, "align_mean_deg": 0.0,
            "flipped_frames": 0, "skipped_flip_frames": 0,
            "secondary_keep_deg": 0.0, "probe_fallback_frames": 0}
    angles = []
    lp_prev = None
    ls_prev = None
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
            cur_rot = cur_world.to_quaternion()
            t = target().normalized()
            # ---- 逐帧轴解析（probe:* 现推，静态沿用）----
            if lp_fn is not None:
                w = lp_fn(armature, scene)
                if w is None or w.length < 1e-6:
                    if lp_prev is None:
                        raise RuntimeError(
                            f"probe 轴 {axis!r} 在第 {f} 帧推不出方向")
                    lp = lp_prev
                    mets["probe_fallback_frames"] += 1
                else:
                    lp = (cur_rot.inverted() @ w).normalized()
                    lp_prev = lp
            else:
                lp = lp_static
            cur_P = cur_rot @ lp
            dot = max(-1.0, min(1.0, float(cur_P.normalized() @ t)))
            ang = float(np.degrees(np.arccos(dot)))
            angles.append(ang)
            if not dual:
                if ang > float(flip_guard_deg):
                    # 近180°最小旋转病态：保持原样，记 skipped
                    desired_pose = pb.matrix.copy()
                    mets["skipped_flip_frames"] += 1
                else:
                    align = cur_P.rotation_difference(t)
                    desired_world = \
                        align.to_matrix().to_4x4() @ cur_world
                    desired_pose = arm_inv @ desired_world
            else:
                if ls_fn is not None:
                    w2 = ls_fn(armature, scene)
                    if w2 is None or w2.length < 1e-6:
                        if ls_prev is None:
                            raise RuntimeError(
                                f"probe 次轴 {secondary_axis!r} 在第 {f}"
                                " 帧推不出方向")
                        ls = ls_prev
                        mets["probe_fallback_frames"] += 1
                    else:
                        ls = (cur_rot.inverted() @ w2).normalized()
                        ls_prev = ls
                else:
                    ls = ls_static
                ls_o = ls - lp * ls.dot(lp)
                if ls_o.length < 1e-4:
                    raise RuntimeError(
                        f"第 {f} 帧次轴与主轴平行，双轴解算退化")
                ls_o.normalize()
                cur_S = cur_rot @ ls_o
                s_des = cur_S - t * cur_S.dot(t)
                if s_des.length < 1e-4:      # 次轴恰好 ∥ 目标：任取 ⊥ 轴
                    tmp = t.cross(Vector((0.0, 0.0, 1.0)))
                    if tmp.length < 1e-3:
                        tmp = t.cross(Vector((0.0, 1.0, 0.0)))
                    s_des = tmp
                s_des.normalize()
                mets["secondary_keep_deg"] = max(
                    mets["secondary_keep_deg"],
                    float(np.degrees(np.arccos(max(-1.0, min(
                        1.0, float(cur_S.normalized() @ s_des)))))))
                Lr = Matrix((lp, ls_o, lp.cross(ls_o)))
                W = Matrix((t, s_des, t.cross(s_des)))
                R = W.transposed() @ Lr      # 世界旋转：L架→W架
                desired_world = R.to_4x4()
                desired_world.translation = cur_world.translation
                desired_pose = arm_inv @ desired_world
            if parent is not None:
                basis = (rel_rest.inverted()
                         @ pb.parent.matrix.inverted() @ desired_pose)
            else:
                basis = pb.bone.matrix_local.inverted() @ desired_pose
            q = basis.to_quaternion()
            out[i] = (q.w, q.x, q.y, q.z)
    if angles:
        mets["align_max_deg"] = round(max(angles), 1)
        mets["align_mean_deg"] = round(float(np.mean(angles)), 1)
        # 需要 >guard 旋转的帧数（双轴路径信息项：发生了大翻转但非病态）
        mets["flipped_frames"] = int(sum(
            1 for a in angles if a > float(flip_guard_deg)))
    # sign continuity
    for i in range(1, len(out)):
        if float(np.dot(out[i - 1], out[i])) < 0.0:
            out[i] = -out[i]
    return out, mets


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
    world_axis: Any = "Y",
    secondary_axis: Any = None,
    dir_object: str | None = None,
    dir_mode: str = "arrow",
    flip_guard_deg: float = 150.0,
    scene: Any | None = None,
    mode: str = "replace",
    threshold_deg: float = 8.0,
    strength: float = 1.0,
    blend: int = 4,
    op_mode: str = "preview",
    data_dir: str | Path | None = None,
    track_name: str | None = None,
    strip_name: str | None = None,
    record: bool = True,
) -> dict:
    """通用姿态保持：让若干骨骼在帧段内保持某个姿态（delta strip 实现）。

    target: "values"   - values={bone: wxyz}，默认 identity（伸直/回零位）
            "from_frame" - ref_frame 帧号或 "auto"（区间内摆动角最小的一帧）
            "world_dir"  - 每帧反算局部旋转，令骨的 world_axis 指向目标
    world_axis / secondary_axis: "X"/"-Z" 或任意骨局部向量三元组——
        语义修复用 probe_anatomy 返回的 local_axis/secondary_axis，不猜轴。
        给 secondary_axis 即双轴解算（主轴对目标、次轴保持当前指向投影），
        掌心 180° 翻转成为绕次轴的干净滚转。
    dir_object/dir_mode: 目标方向可绑空物体——"arrow"=空物体 +Z 轴（平行于
        箭头），"aim"=骨→物体位置（指向它）。空物体 k 动画即逐帧目标。
    mode:   "replace"  - 整段强制设成目标
            "clamp"    - 只把偏离目标 > threshold_deg 的帧压回阈值，保留小抖动
            "outlier"  - 超阈帧判为坏帧，用前后好帧 slerp 补
    strength 落在 strip.influence 上（NLA 属性里可拖滑块实时调）。
    record=False 时返回未入 log 的 op dict（reapply 用）。
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
    dir_metrics: dict[str, dict] = {}
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
            if scene is None or (world_dir is None and not dir_object):
                raise RuntimeError("world_dir 需要 scene 与向量或 dir_object")
            desired, dmets = _desired_world_dir(
                scene, armature, bone, frames,
                np.asarray(world_dir, dtype=np.float64)
                if world_dir is not None else None,
                axis=world_axis, secondary_axis=secondary_axis,
                dir_object=dir_object, dir_mode=dir_mode,
                flip_guard_deg=flip_guard_deg)
            dir_metrics[bone] = dmets
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
        if bone in dir_metrics:
            metrics["bones"][bone].update(dir_metrics[bone])
        metrics["fixed_frames"] += int((err > threshold_deg).sum())
        quats[path] = agent_fx.delta_quat(final, cur)
        # scale the correction by strength via angle scaling
        if float(strength) < 1.0:
            from .pkl_hand import aa_to_quat, quat_to_aa
            quats[path] = aa_to_quat(
                quat_to_aa(quats[path]) * float(strength))

    name = strip_name or f"agent_hold_{start}_{end}"
    _track, strip = _write_strip(
        armature, name, start, quats=quats, blend=blend,
        track_name=track_name)
    strip.influence = float(strength)
    op = _new_op(
        "hold_pose",
        # params 必须覆盖全部求解输入（reapply 靠它重算）
        {"bones": list(bones), "target": target,
         "values": {k: list(v) for k, v in (values or {}).items()},
         "ref_frame": ref_frame if target == "from_frame" else None,
         "world_dir": list(world_dir) if world_dir is not None else None,
         "world_axis": (list(world_axis)
                        if not isinstance(world_axis, str) else world_axis),
         "secondary_axis": (
             list(secondary_axis)
             if secondary_axis is not None
             and not isinstance(secondary_axis, str) else secondary_axis),
         "dir_object": dir_object, "dir_mode": dir_mode,
         "flip_guard_deg": flip_guard_deg,
         "mode": mode, "threshold_deg": threshold_deg,
         "strength": strength, "blend": blend,
         "frame_range": [start, end]},
        (start, end), strip.name, op_mode, metrics,
        track=_track.name)
    if data_dir and record:
        return _record(data_dir, op)
    return op


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
                 {"max_pos_shift": float(np.abs(desired["pos"] - np.asarray(target_pos)).max())},
                 track=_track.name)
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
