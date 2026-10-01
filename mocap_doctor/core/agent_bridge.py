"""In-process tool server for LLM co-editing inside the GUI Blender session.

Architecture (per the plan):
- a background thread runs a tiny JSON-lines socket server on 127.0.0.1
- bpy may ONLY be touched on the main thread: requests go into a queue, and a
  ``bpy.app.timers`` pump drains it every TIMER_INTERVAL seconds
- preview writes land on the dedicated ``AGENT_PREVIEW`` Combine NLA track,
  viewport is redrawn immediately, playback range jumps to the op's frames
- a data version counter bumps on every depsgraph change, so a tool call can
  carry ``expect_version`` and get "scene changed" instead of clobbering the
  user's fresh hand edits
- commit does ``undo_push`` so Ctrl+Z covers agent work too

Client protocol: one JSON object per line, both directions.
    {"id": 1, "tool": "describe", "args": {"target": "contact.L:0"}}
    {"id": 1, "ok": true, "version": 12, "result": {...}}
"""

from __future__ import annotations

import json
import queue
import socket
import socketserver
import threading
import traceback
from typing import Any, Mapping, Sequence

import bpy
import numpy as np

from . import agent_bake, agent_fx, agent_io, agent_ops, agent_query

HOST = "127.0.0.1"
PORT = 6211
TIMER_INTERVAL = 0.07
PREVIEW_TRACK = "AGENT_PREVIEW"
COMMIT_TRACK = "mcd_agent"

_running = False
_requests: "queue.Queue" = queue.Queue()
_DATA_VERSION = 0
_STORE = None           # cached DataStore
_STORE_KEY = None
_LAST_TOOL = ""
_STATUS = {"clients": 0, "last_tool": "", "last_error": ""}


# ---------------------------------------------------------------------------
# context / store

def _settings(scene=None):
    scene = scene or bpy.context.scene
    return scene, scene.mocap_doctor


def _source_armature(settings):
    arm = getattr(settings, "source_armature", None)
    if arm is not None and getattr(arm, "type", "") == "ARMATURE":
        return arm
    return None


def get_store(force: bool = False):
    """Build (or reuse) the query store over the current source armature."""
    global _STORE, _STORE_KEY
    scene, settings = _settings()
    armature = _source_armature(settings)
    if armature is None:
        raise RuntimeError("没有识别到源骨架（settings.source_armature 为空）")
    key = (armature.name, scene.frame_start, scene.frame_end, _DATA_VERSION)
    if force or _STORE is None or _STORE_KEY != key:
        _STORE = agent_io.build_store_for_scene(
            scene, armature, settings,
            data_dir=settings.data_directory or None,
            use_cache=True, tag="gui",
        )
        _STORE_KEY = key
    return _STORE


def data_version() -> int:
    return _DATA_VERSION


def _bump_version(scene=None, _d=None):
    global _DATA_VERSION
    _DATA_VERSION += 1


def _redraw():
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
    except Exception:
        pass


def _focus_preview(scene, frame_range):
    try:
        agent_ops.set_preview(scene, frame_range)
        scene.frame_set(int(frame_range[0]))
    except Exception:
        pass
    try:
        with bpy.context.temp_override():
            bpy.ops.screen.animation_play()
    except Exception:
        pass  # playback start is a nicety, never a failure


def _base_action(armature):
    """The baseline action - active action, or the mcd_base strip's action once
    it has been pushed onto NLA (active action sits ABOVE tracks and REPLACEd
    our deltas, so the first write pushes it down)."""
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None
    if anim.action is not None:
        return anim.action
    for track in anim.nla_tracks:
        if track.name == agent_ops.BASE_TRACK and track.strips:
            return track.strips[0].action
    return None


def _track_by_name(armature, name):
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        return None
    for track in anim.nla_tracks:
        if track.name.startswith(name):
            return track
    return None


# ---------------------------------------------------------------------------
# tool registry

def _check_version(args):
    expect = args.pop("expect_version", None)
    if expect is not None and int(expect) != _DATA_VERSION:
        raise agent_query.AgentQueryError(
            f"场景已变（期望 v{expect}，当前 v{_DATA_VERSION}）",
            code="E_STALE", fix="重新调用读工具拿新数据")


def _op_envelope(op: dict, tool: str) -> dict:
    """Write-tool result → unified envelope fields."""
    frames = op.get("frames", [0, 0])
    return {
        "summary": f"{tool} {op.get('status','preview')}："
                   f"{frames[0]}-{frames[1]} 帧",
        "data": {
            "op_id": op.get("id"),
            "status": op.get("status"),
            "params_echo": op.get("params"),
            "frames": frames,
            "touched": op.get("params", {}).get("bones")
                       or op.get("params", {}).get("paths")
                       or op.get("params", {}).get("loc_path"),
            "metrics": op.get("metrics"),
            "preview": {"track": op.get("strip"),
                        "playback_range": frames},
        },
        "warnings": [],
        "truncated": False,
        "hint": "看视口 A/B 后 commit(op_id) 或 revert(op_id)",
    }


def _tool_ping(_ctx, **_):
    return {"summary": f"服务运行中 · 数据 v{_DATA_VERSION}",
            "data": {"ok": True, "version": _DATA_VERSION,
                     "running": _running,
                     "tools": sorted(TOOLS)},
            "warnings": [], "truncated": False, "hint": ""}


def _tool_overview(_ctx, force_refresh=False, **_):
    store = get_store(force=bool(force_refresh))
    env = agent_query.get_overview(store)
    # expose the bake spec so "missing finger signals" is one glance away
    env["data"]["bones"] = dict(getattr(store, "spec", {}).get("bones", {}))
    env["data"]["bake_missing"] = list(getattr(store, "bake_missing", []))
    env["data"]["data_dir"] = str(_ctx.get("data_dir") or "")
    return env


def _tool_list_intervals(_ctx, kind=None, frame_range=None, tag=None, **_):
    return agent_query.list_intervals(
        get_store(), kind=kind, frame_range=frame_range, tag=tag)


def _tool_describe(_ctx, target=None, channels=None, context=15,
                   frame_range=None, **_):
    if target is None and frame_range is not None:
        target = list(frame_range)
    return agent_query.describe(get_store(), target,
                                channels=channels, context=int(context))


def _tool_get_series(_ctx, channels, frame_range, max_points=60,
                     agg="mean", **_):
    return agent_query.get_series(get_store(), channels, frame_range,
                                  max_points=max_points, agg=agg)


def _tool_find_events(_ctx, cond, frame_range=None, **_):
    return agent_query.find_events(get_store(), cond, frame_range)


def _tool_compare(_ctx, channel, a, b, **_):
    return agent_query.compare(get_store(), channel, a, b)


def _tool_snapshot(_ctx, frame, roles=None, **_):
    return agent_query.snapshot(get_store(), frame, roles)


def _tool_eval(_ctx, expr, **_):
    """Evaluate a Python expression in the live scene; returns repr() ≤ 4000 chars.

    Debugging/inspection escape hatch - single expressions only, result must be
    repr-able. This socket is localhost-only by design.
    """
    # env must be globals so list-comprehension scopes can see bpy/scene/pb
    env = {
        "__builtins__": None,   # replaced below
        "bpy": bpy,
        "scene": _ctx["scene"],
        "armature": _ctx["armature"],
        "data": bpy.data,
    }
    try:
        armature = _ctx["armature"]
        if armature is not None:
            env["pb"] = armature.pose.bones
    except Exception:
        pass
    import builtins as _bi
    safe_builtins = {k: getattr(_bi, k) for k in (
        "len", "list", "dict", "tuple", "set", "sorted", "str", "repr",
        "round", "float", "int", "bool", "min", "max", "sum", "any",
        "all", "enumerate", "zip", "range", "getattr", "hasattr", "isinstance",
        "type", "abs", "iter",
    ) if hasattr(_bi, k)}
    env["__builtins__"] = safe_builtins
    result = eval(str(expr), env, env)  # noqa: S307
    text = repr(result)
    truncated = len(text) > 4000
    return {"summary": text[:120],
            "data": {"expr": str(expr), "result": text[:4000]},
            "warnings": [], "truncated": truncated,
            "hint": "结果被截断到 4000 字符" if truncated else ""}


def _tool_get_joint_angles(_ctx, bones, frame_range, max_points=60, **_):
    return agent_query.get_joint_angles(
        get_store(), bones, frame_range, max_points=max_points)


def _tool_effect_check(ctx, track_name=PREVIEW_TRACK, bones=None,
                       frames=None, **_):
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到源骨架")
    if bones is None or frames is None:
        # 从 op log 最新一条 preview 里找参数
        ops = agent_ops.list_ops(ctx["data_dir"])
        last = next((o for o in reversed(ops)
                     if o.get("status") == "preview"), None)
        if last is None:
            raise RuntimeError("op log 里没有 preview，传 bones/frames")
        bones = bones or last.get("params", {}).get("bones") \
            or [last.get("params", {}).get("bone")]
        fr = last.get("frames")
        frames = frames or [fr[0], (fr[0] + fr[1]) // 2, fr[1]]
    res = agent_ops.effect_check(ctx["scene"], armature,
                                 track_name=track_name,
                                 bones=list(bones), frames=list(frames))
    return {"summary": f"{track_name}: {res['verdict']}",
            "data": res, "warnings": [], "truncated": False, "hint": ""}


def _tool_hold_pose(ctx, bones, frame_range, target="values",
                    values=None, ref_frame=None, world_dir=None,
                    mode="replace", threshold_deg=8.0, strength=1.0,
                    blend=4, op_mode="preview", **_):
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到源骨架")
    op = agent_ops.hold_pose(
        armature, _base_action(armature), list(bones), frame_range,
        target=target, values=values, ref_frame=ref_frame,
        world_dir=world_dir, scene=ctx["scene"],
        mode=mode, threshold_deg=float(threshold_deg),
        strength=float(strength), blend=int(blend), op_mode=op_mode,
        data_dir=ctx["data_dir"], track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_bake_range(_ctx, frame_range, roles=None, point_ids=None, **_):
    """Return world pos/quat arrays for roles/points over a range - the LLM
    feeds these into apply_exemplar / pelvis math."""
    store = get_store()
    a, b = int(frame_range[0]), int(frame_range[1])
    mask = (store.frames >= a) & (store.frames <= b)
    out = {"frames": [int(f) for f in store.frames[mask]]}
    for role in (roles or list(store.positions)):
        if role in store.positions:
            out[f"pos::{role}"] = np.asarray(store.positions[role])[mask].tolist()
    return out


def _write_common(ctx, armature, frame_range):
    _redraw()
    _focus_preview(ctx["scene"], frame_range)


def _tool_clean_jitter(ctx, frame_range, bone=None, paths=None,
                       strength=1.0, width=5, blend=4, mode="preview", **_):
    armature = ctx["armature"]
    if paths is None and bone:
        paths = (
            [(agent_ops.bone_path(bone, "location"), i) for i in range(3)]
            + [(agent_ops.bone_path(bone, "rotation_quaternion"), i)
               for i in range(4)]
        )
    if not paths:
        raise RuntimeError("clean_jitter 需要 bone 或 paths")
    op = agent_ops.clean_jitter(
        armature, _base_action(armature),
        [tuple(p) for p in paths], frame_range,
        strength=float(strength), width=int(width), blend=int(blend),
        mode=mode, data_dir=ctx["data_dir"], track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_fix_ground(ctx, frame_range, side, loc_path,
                     mode="lift", pin_xy=False, blend=4,
                     op_mode="preview", **_):
    armature = ctx["armature"]
    store = get_store()
    sole = store.signals.get(f"foot.{side}.sole_h")
    if sole is None:
        raise RuntimeError(f"信号库没有 foot.{side}.sole_h")
    a, b = int(frame_range[0]), int(frame_range[1])
    mask = (store.frames >= a) & (store.frames <= b)
    op = agent_ops.fix_ground(
        armature, _base_action(armature), loc_path, sole[mask],
        floor_z=store.floor_z, mode=mode, pin_xy=bool(pin_xy),
        frame_range=frame_range, blend=int(blend), op_mode=op_mode,
        data_dir=ctx["data_dir"], track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_restore_accent(ctx, frame_range, data_path, index, method,
                         strength=0.5, impact_frame=None,
                         retime_speed=1.5, retime_split=0.35,
                         raw_action=None, blend=4, op_mode="preview", **_):
    armature = ctx["armature"]
    raw_values = None
    if raw_action:
        raw_act = bpy.data.actions.get(raw_action)
        if raw_act is None:
            raise RuntimeError(f"参考动作 {raw_action} 不存在")
        raw_values = agent_bake.sample_fcurve_values(
            raw_act, data_path, int(index),
            int(frame_range[0]), int(frame_range[1]))
    op = agent_ops.restore_accent(
        armature, _base_action(armature), data_path, int(index),
        frame_range, method, strength=float(strength),
        raw_values=raw_values, impact_frame=impact_frame,
        retime_speed=retime_speed, retime_split=retime_split,
        blend=int(blend), op_mode=op_mode,
        data_dir=ctx["data_dir"], track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_solve_pelvis(ctx, frame_range, pelvis_path, pelvis_dz,
                       blend=4, op_mode="preview", **_):
    armature = ctx["armature"]
    op = agent_ops.solve_pelvis(
        armature, _base_action(armature), pelvis_path,
        list(pelvis_dz), frame_range=frame_range, blend=int(blend),
        op_mode=op_mode, data_dir=ctx["data_dir"],
        track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_apply_exemplar(ctx, frame_range, ex_id, loc_path, quat_path,
                         target_pos, target_quat, anchor_yaw_deg=0.0,
                         yaw_scale=1.0, mirror=False, blend=4,
                         op_mode="preview", **_):
    armature = ctx["armature"]
    ex = agent_ops.load_exemplar(ctx["data_dir"], ex_id)
    op = agent_ops.apply_exemplar(
        armature, ex, target_pos, target_quat, float(anchor_yaw_deg),
        loc_path, quat_path, frame_range=frame_range,
        yaw_scale=float(yaw_scale), mirror=bool(mirror), blend=int(blend),
        op_mode=op_mode, data_dir=ctx["data_dir"], track_name=PREVIEW_TRACK)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_validate(ctx, frame_range=None, **_):
    store = get_store()
    return agent_ops.validate(store.signals, store.frames, frame_range,
                              floor_z=store.floor_z)


def _tool_list_ops(ctx, **_):
    return {"ops": agent_ops.list_ops(ctx["data_dir"])}


def _tool_commit(ctx, op_id, **_):
    """Mark committed and move the strip from AGENT_PREVIEW to mcd_agent."""
    armature = ctx["armature"]
    track, strip = agent_ops._find_strip(armature,
                                         _op_strip(ctx, op_id))
    if strip is not None and track is not None and \
            track.name.startswith(PREVIEW_TRACK):
        # recreate on the committed track with the same action
        commit_track = _track_by_name(armature, COMMIT_TRACK)
        if commit_track is None:
            anim = armature.animation_data
            commit_track = anim.nla_tracks.new()
            commit_track.name = COMMIT_TRACK
        new_strip = commit_track.strips.new(
            strip.name.replace("preview", "agent"),
            int(strip.frame_start), strip.action)
        new_strip.blend_type = "COMBINE"
        new_strip.use_auto_blend = True
        track.strips.remove(strip)
    op = agent_ops.commit(ctx["data_dir"], op_id)
    try:
        bpy.ops.ed.undo_push()
    except Exception:
        pass
    _redraw()
    return op


def _op_strip(ctx, op_id):
    for op in agent_ops.list_ops(ctx["data_dir"]):
        if op["id"] == op_id:
            return op["strip"]
    raise RuntimeError(f"op {op_id} 不在记录里")


def _tool_revert(ctx, op_id, **_):
    op = agent_ops.revert(ctx["armature"], ctx["data_dir"], op_id)
    _redraw()
    return op


def _tool_ab_toggle(ctx, **_):
    armature = ctx["armature"]
    track = _track_by_name(armature, PREVIEW_TRACK)
    if track is None:
        return {"muted": None, "note": "没有预览轨"}
    track.mute = not track.mute
    _redraw()
    return {"muted": bool(track.mute)}


def _tool_set_preview(ctx, frame_range, **_):
    agent_ops.set_preview(ctx["scene"], frame_range)
    _redraw()
    return {"preview_range": [int(frame_range[0]), int(frame_range[1])]}


TOOLS = {
    "ping": _tool_ping,
    "get_overview": _tool_overview,
    "list_intervals": _tool_list_intervals,
    "describe": _tool_describe,
    "get_series": _tool_get_series,
    "find_events": _tool_find_events,
    "compare": _tool_compare,
    "snapshot": _tool_snapshot,
    "get_joint_angles": _tool_get_joint_angles,
    "eval_bpy": _tool_eval,
    "bake_range": _tool_bake_range,
    "clean_jitter": _tool_clean_jitter,
    "hold_pose": _tool_hold_pose,
    "effect_check": _tool_effect_check,
    "fix_ground": _tool_fix_ground,
    "restore_accent": _tool_restore_accent,
    "solve_pelvis": _tool_solve_pelvis,
    "apply_exemplar": _tool_apply_exemplar,
    "validate": _tool_validate,
    "list_ops": _tool_list_ops,
    "commit": _tool_commit,
    "revert": _tool_revert,
    "ab_toggle": _tool_ab_toggle,
    "set_preview": _tool_set_preview,
}


def _ctx():
    scene, settings = _settings()
    return {
        "scene": scene,
        "settings": settings,
        "armature": _source_armature(settings),
        "data_dir": settings.data_directory or ".",
    }


def _dispatch(request: Mapping[str, Any]) -> dict:
    global _LAST_TOOL
    name = str(request.get("tool", ""))
    args = dict(request.get("args") or {})
    try:
        _check_version(args)
        tool = TOOLS.get(name)
        if tool is None:
            raise agent_query.AgentQueryError(
                f"未知工具 {name!r}", code="E_UNKNOWN",
                fix=f"可用：{', '.join(sorted(TOOLS))}")
        _LAST_TOOL = name
        _STATUS["last_tool"] = name
        result = tool(_ctx(), **args)
        # op dicts (from agent_ops) get the op envelope; _env-shaped dicts
        # pass through; anything else lands under data verbatim
        if isinstance(result, dict) and "summary" in result:
            payload = result
        elif isinstance(result, dict) and ("strip" in result
                                           or "op" in result
                                           or "id" in result):
            payload = _op_envelope(result, name)
        else:
            payload = {"summary": f"{name} 完成", "data": result,
                       "warnings": [], "truncated": False, "hint": ""}
        return {"ok": True, "tool": name, "version": _DATA_VERSION,
                **payload}
    except agent_query.AgentQueryError as exc:
        _STATUS["last_error"] = f"{name}: {exc}"
        return {"ok": False, "tool": name, "version": _DATA_VERSION,
                "summary": "", "data": None, "warnings": [],
                "truncated": False, "hint": "",
                "error": {"code": exc.code, "message": str(exc),
                          "fix": exc.fix}}
    except Exception as exc:  # noqa: BLE001 - relay everything
        _STATUS["last_error"] = f"{name}: {exc}"
        msg = repr(exc)
        code = "E_SCOPE" if "越界" in msg else "E_TOOL"
        return {"ok": False, "tool": name, "version": _DATA_VERSION,
                "summary": "", "data": None, "warnings": [],
                "truncated": False, "hint": "",
                "error": {"code": code, "message": msg,
                          "fix": "message 看不懂就翻 trace 定位行号"},
                "trace": traceback.format_exc(limit=4)}


# ---------------------------------------------------------------------------
# server + main-thread pump

def _pump():
    """Runs on the main thread via bpy.app.timers; drains the request queue."""
    while True:
        try:
            sock_file, request = _requests.get_nowait()
        except queue.Empty:
            break
        response = _dispatch(request)
        response["id"] = request.get("id")
        try:
            sock_file.write(
                (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
            sock_file.flush()
        except OSError:
            pass
    return TIMER_INTERVAL if _running else None


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        _STATUS["clients"] += 1
        try:
            for line in self.rfile:
                try:
                    request = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                _requests.put((self.wfile, request))
        finally:
            _STATUS["clients"] -= 1


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


_server = None


def start_server(port: int = PORT) -> dict:
    _STATUS["last_error"] = ""
    global _running, _server
    if _running:
        return {"running": True, "port": _server.server_address[1]}
    _server = _Server((HOST, int(port)), _Handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    _running = True
    if not bpy.app.timers.is_registered(_pump):
        bpy.app.timers.register(_pump, first_interval=TIMER_INTERVAL)
    if _bump_version not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_bump_version)
    return {"running": True, "port": _server.server_address[1]}


def stop_server() -> dict:
    global _running, _server
    _running = False
    if _server is not None:
        _server.shutdown()
        _server.server_close()
        _server = None
    if bpy.app.timers.is_registered(_pump):
        bpy.app.timers.unregister(_pump)
    if _bump_version in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_bump_version)
    return {"running": False}


def is_running() -> bool:
    return _running


def status() -> dict:
    return {"running": _running, "version": _DATA_VERSION,
            "clients": _STATUS["clients"], "last_tool": _STATUS["last_tool"],
            "last_error": _STATUS["last_error"],
            "port": _server.server_address[1] if _server else PORT}
