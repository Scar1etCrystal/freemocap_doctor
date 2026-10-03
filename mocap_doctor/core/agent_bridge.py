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
import time
import traceback
from typing import Any, Mapping, Sequence

import bpy
import numpy as np

from . import (agent_anatomy, agent_bake, agent_fx, agent_io, agent_ops,
             agent_query)

HOST = "127.0.0.1"
PORT = 6211
TIMER_INTERVAL = 0.07
WATCHDOG_INTERVAL = 2.0   # how often we check the pump is still ticking
PREVIEW_TRACK = agent_ops.PREVIEW_TRACK   # legacy shared preview track
COMMIT_TRACK = agent_ops.AGENT_TRACK_PREFIX


def agent_track_prefixes():
    """Names that mark a track as ours.  Per-op tracks are named after their
    strip ("agent_hold_505_570"); the legacy shared names stay recognised so an
    old .blend keeps working.  mcd_base is excluded - it is the baseline."""
    return agent_ops.AGENT_TRACK_PREFIXES


_running = False
_requests: "queue.Queue" = queue.Queue()
_DATA_VERSION = 0
_LAST_BUMP = 0.0
_STORE = None           # cached DataStore
_STORE_KEY = None
_LAST_TOOL = ""
_LAST_PUMP = 0.0          # wall-clock of last successful _pump tick
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


def _rig_armature(settings, scene=None):
    """The MMR control rig is what the agent layer operates on: Teto 自身没有
    action（全靠约束跟 RIG），源骨架 f_avg 与 Teto 间是烘焙链路——修源骨架
    下游看不到，修 RIG 立刻反映到最终模型。"""
    rig = getattr(settings, "mmr_rig", None)
    if rig is not None and getattr(rig, "type", "") == "ARMATURE":
        return rig
    scene = scene or bpy.context.scene
    for ob in scene.objects:
        if ob.type == "ARMATURE" and ob.name.startswith("RIG-"):
            return ob
    return None


def _resolve_bones(armature, names):
    """bones 参数既可以是字面骨名也可以是角色名（finger_l_index1 等）。"""
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    spec = agent_io.rig_bake_spec(armature)
    role_map = spec["bones"]
    out = []
    unknown = []
    for n in names:
        if n in role_map:
            out.append(role_map[n])
        elif n in armature.data.bones:
            out.append(n)
        else:
            unknown.append(n)
    if unknown:
        raise agent_query.AgentQueryError(
            f"RIG 骨架上没有这些骨：{unknown}",
            code="E_UNKNOWN",
            fix=f"可用角色名：{sorted(role_map)}")
    return out


def get_store(force: bool = False):
    """Build (or reuse) the query store over the current RIG armature."""
    global _STORE, _STORE_KEY
    scene, settings = _settings()
    armature = _rig_armature(settings, scene)
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架（settings.mmr_rig 为空，"
                           "且场景里没有 RIG-* 骨架）")
    key = (armature.name, scene.frame_start, scene.frame_end, _DATA_VERSION)
    if force or _STORE is None or _STORE_KEY != key:
        _STORE = agent_io.build_store_for_scene(
            scene, armature, settings,
            spec=agent_io.rig_bake_spec(armature),
            data_dir=settings.data_directory or None,
            use_cache=True, tag="rig",
        )
        _STORE_KEY = key
    return _STORE


def data_version() -> int:
    return _DATA_VERSION


def _bump_version(scene=None, _d=None):
    """depsgraph_update_post fires on EVERY depsgraph event - frame scrub,
    influence drag, cursor blink.  Throttle so the version still means
    'something changed' instead of 'wall clock moved'."""
    global _DATA_VERSION, _LAST_BUMP
    now = time.monotonic()
    if now - _LAST_BUMP < 0.3:
        return
    _LAST_BUMP = now
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
        "armature": _ctx["armature"],      # RIG 控制架
        "source": _ctx["source_armature"], # f_avg 源骨架
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


def _tool_effect_check(ctx, track_name=None, op_id=None, bones=None,
                       frames=None, **_):
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    op = None
    if op_id:
        op = _op_by_id(ctx, op_id)
        track, strip = agent_ops.find_op_strip(armature, op)
        if track is None:
            raise RuntimeError(f"{op_id} 的轨找不到了（可能已被撤销/删除）")
        track_name = track.name
    if bones is None or frames is None:
        if op is None:
            ops = agent_ops.list_ops(ctx["data_dir"])
            op = next((o for o in reversed(ops)
                       if o.get("status") in ("preview", "committed")), None)
        if op is None:
            raise RuntimeError("op log 里没有修复记录，传 bones/frames")
        bones = bones or op.get("params", {}).get("bones") \
            or [op.get("params", {}).get("bone")]
        fr = op.get("frames")
        frames = frames or [fr[0], (fr[0] + fr[1]) // 2, fr[1]]
    if track_name is None:
        # 没指定就查所有 agent 轨（A/B 语义：全部修复一起 mute）
        armature_anim = getattr(armature, "animation_data", None)
        names = [t.name for t in (armature_anim.nla_tracks if armature_anim else ())
                 if agent_ops.is_agent_track_name(t.name)]
        if not names:
            raise RuntimeError("RIG 上没有 agent 轨")
        merged = None
        for nm in names:
            res = agent_ops.effect_check(ctx["scene"], armature,
                                         track_name=nm,
                                         bones=list(bones), frames=list(frames))
            if merged is None:
                merged = res
                merged["tracks"] = [nm]
            else:
                merged["tracks"].append(nm)
                for a, b in zip(merged["per_frame"], res["per_frame"]):
                    for bone, cell in b["bones"].items():
                        cur = a["bones"].get(bone)
                        if cur is None or cell["pos_mm"] > cur["pos_mm"] \
                                or cell["rot_deg"] > cur["rot_deg"]:
                            a["bones"][bone] = cell
                    a["moved"] = a["moved"] or b["moved"]
        hits = sum(1 for r in merged["per_frame"] if r["moved"])
        merged["verdict"] = f"{hits}/{len(merged['per_frame'])} 帧有变化"
        merged["pass"] = hits == len(merged["per_frame"])
        merged["track"] = "all"
        res = merged
        label = f"全部 agent 轨({len(names)})"
    else:
        res = agent_ops.effect_check(ctx["scene"], armature,
                                     track_name=track_name,
                                     bones=list(bones), frames=list(frames))
        label = track_name
    return {"summary": f"{label}: {res['verdict']}",
            "data": res, "warnings": [], "truncated": False, "hint": ""}


def _tool_hold_pose(ctx, bones, frame_range, target="values",
                    values=None, ref_frame=None, world_dir=None,
                    world_axis="Y", secondary_axis=None,
                    dir_object=None, dir_mode="arrow",
                    flip_guard_deg=150.0,
                    mode="replace", threshold_deg=8.0, strength=1.0,
                    blend=4, op_mode="preview", track_name=None, **_):
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    op = agent_ops.hold_pose(
        armature, _base_action(armature),
        _resolve_bones(armature, list(bones)), frame_range,
        target=target, values=values, ref_frame=ref_frame,
        world_dir=world_dir, world_axis=world_axis,
        secondary_axis=secondary_axis,
        dir_object=dir_object, dir_mode=dir_mode,
        flip_guard_deg=float(flip_guard_deg),
        scene=ctx["scene"],
        mode=mode, threshold_deg=float(threshold_deg),
        strength=float(strength), blend=int(blend), op_mode=op_mode,
        data_dir=ctx["data_dir"], track_name=track_name)
    _write_common(ctx, armature, frame_range)
    return op


def _tool_probe_anatomy(ctx, part, side=None, bone=None, finger=None,
                        frame_range=None, toward=None, max_frames=9, **_):
    """语义解剖探头：从几何推世界方向 + owner 骨局部向量 + 置信度。"""
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    res = agent_anatomy.probe(
        ctx["scene"], armature, part=part, side=side, bone=bone,
        finger=finger, frame_range=frame_range, toward=toward,
        max_frames=int(max_frames))
    conf = res.get("confidence")
    summary = (f"{part}{'.' + side if side else ''}: "
               f"world={res.get('world_dir')} conf={conf}"
               + (f" err={res['err_max_deg']}°"
                  if res.get("err_max_deg") is not None else ""))
    warnings = []
    if conf is not None and conf < 0.5:
        warnings.append(f"低置信度({conf})：{res.get('evidence')}")
        if res.get("alternatives"):
            warnings.append("符号歧义：alternatives 给出两个候选方向")
    return {"summary": summary, "data": res, "warnings": warnings,
            "truncated": False, "hint": ""}


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
    _bump_ops_rev(ctx)
    _redraw()
    _focus_preview(ctx["scene"], frame_range)


def _tool_clean_jitter(ctx, frame_range, bone=None, paths=None,
                       strength=1.0, width=5, blend=4, mode="preview", **_):
    armature = ctx["armature"]
    if paths is None and bone:
        bone = _resolve_bones(armature, [bone])[0]
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
        mode=mode, data_dir=ctx["data_dir"])
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
        data_dir=ctx["data_dir"])
    _write_common(ctx, armature, frame_range)
    return op


def _tool_restore_accent(ctx, frame_range, data_path, index=None, method="ease_reshape",
                         strength=0.5, impact_frame=None,
                         retime_speed=1.5, retime_split=0.35,
                         raw_action=None, blend=4, op_mode="preview", **_):
    """data_path 指到 .rotation_quaternion / .location 时四分量/三轴整体
    重塑（index 忽略）；其他通道才需要 index 选分量。"""
    armature = ctx["armature"]
    raw_values = None
    if raw_action:
        raw_act = bpy.data.actions.get(raw_action)
        if raw_act is None:
            raise RuntimeError(f"参考动作 {raw_action} 不存在")
        raw_values = agent_bake.sample_fcurve_values(
            raw_act, data_path, int(index) if index is not None else 0,
            int(frame_range[0]), int(frame_range[1]))
    op = agent_ops.restore_accent(
        armature, _base_action(armature), data_path,
        int(index) if index is not None else None,
        frame_range, method, strength=float(strength),
        raw_values=raw_values, impact_frame=impact_frame,
        retime_speed=retime_speed, retime_split=retime_split,
        blend=int(blend), op_mode=op_mode,
        data_dir=ctx["data_dir"])
    _write_common(ctx, armature, frame_range)
    return op


def _tool_solve_pelvis(ctx, frame_range, pelvis_path, pelvis_dz,
                       blend=4, op_mode="preview", **_):
    armature = ctx["armature"]
    op = agent_ops.solve_pelvis(
        armature, _base_action(armature), pelvis_path,
        list(pelvis_dz), frame_range=frame_range, blend=int(blend),
        op_mode=op_mode, data_dir=ctx["data_dir"])
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
        op_mode=op_mode, data_dir=ctx["data_dir"])
    _write_common(ctx, armature, frame_range)
    return op


def _tool_validate(ctx, frame_range=None, **_):
    store = get_store()
    return agent_ops.validate(store.signals, store.frames, frame_range,
                              floor_z=store.floor_z)


def _tool_list_ops(ctx, **_):
    """Op log enriched with live state (track / exponent / mute) so an agent can
    see exactly what is on the rig without guessing."""
    armature = ctx["armature"]
    rows = agent_ops.reconcile(armature, ctx["data_dir"])
    return {"ops": agent_ops.list_ops(ctx["data_dir"]), "fixes": rows}


def _tool_commit(ctx, op_id, **_):
    """Mark committed.  With per-op tracks the strip no longer moves: track is
    identity, status is intent, and a committed fix stays adjustable."""
    op = agent_ops.commit(ctx["data_dir"], op_id)
    _bump_ops_rev(ctx)
    try:
        bpy.ops.ed.undo_push()
    except Exception:
        pass
    _redraw()
    return op


def _op_by_id(ctx, op_id):
    for op in agent_ops.list_ops(ctx["data_dir"]):
        if op["id"] == op_id:
            return op
    raise RuntimeError(f"op {op_id} 不在记录里")


def _op_strip(ctx, op_id):
    return _op_by_id(ctx, op_id).get("strip", "")


def _bump_ops_rev(ctx):
    """Tell the panel its fix list is stale (write/commit/revert happened)."""
    try:
        ctx["settings"].agent_ops_rev = int(ctx["settings"].agent_ops_rev) + 1
    except Exception:
        pass


def _tool_revert(ctx, op_id, **_):
    op = agent_ops.revert(ctx["armature"], ctx["data_dir"], op_id)
    _bump_ops_rev(ctx)
    _redraw()
    return op


def _tool_reapply(ctx, op_id, overrides=None, **_):
    """用新参数重写某条 op 的 strip（同轨删旧写新，op_id 不变）。

    overrides 是 params 的局部覆盖，如 {"threshold_deg": 6, "blend": 8}、
    {"dir_object": "mcd_dir", "dir_mode": "arrow"}、{"frame_range": [a,b]}。"""
    armature = ctx["armature"]
    if armature is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    op = agent_ops.reapply(ctx["data_dir"], armature, str(op_id),
                           scene=ctx["scene"], **dict(overrides or {}))
    _bump_ops_rev(ctx)
    _sync_params_list(ctx["settings"], ctx["data_dir"])
    _redraw()
    return {"summary": f"已重写 {op['id']}（{op.get('tool')}）",
            "data": op, "warnings": [], "truncated": False, "hint": ""}


def _tool_ab_toggle(ctx, **_):
    """A/B 对比：mute/unmute 所有 agent 轨（每条修复各自一轨），
    mcd_base 保持原样。"""
    armature = ctx["armature"]
    anim = getattr(armature, "animation_data", None)
    agent_tracks = [t for t in (anim.nla_tracks if anim else ())
                    if agent_ops.is_agent_track_name(t.name)]
    if not agent_tracks:
        return {"muted": None, "note": "没有 agent 轨"}
    # 以"是否有未静音轨"决定方向：有一个还响着 → 全部静音
    new_state = any(not t.mute for t in agent_tracks)
    for t in agent_tracks:
        t.mute = new_state
    _redraw()
    return {"muted": new_state,
            "tracks": [t.name for t in agent_tracks]}


def _tool_set_preview(ctx, frame_range, **_):
    agent_ops.set_preview(ctx["scene"], frame_range)
    _redraw()
    return {"preview_range": [int(frame_range[0]), int(frame_range[1])]}


def _tool_set_influence(ctx, value, op_id=None, track_name=None, **_):
    """力度旋钮：按 op 把该修复的 delta 曲线重写成 delta^value。

    op_id 是首选寻址（每条修复一条轨）；track_name 是回退（找该轨上全部
    strip），后者只留给迁移前的旧布局。"""
    armature = ctx["armature"]
    anim = getattr(armature, "animation_data", None)
    if anim is None:
        raise RuntimeError("RIG 没有动画数据")
    if op_id:
        op = _op_by_id(ctx, op_id)
        track, strip = agent_ops.find_op_strip(armature, op)
        if strip is None:
            raise RuntimeError(f"{op_id} 的 strip 找不到了（可能已被撤销/删除）")
        res = agent_ops.set_strip_exponent(strip, float(value))
        _redraw()
        return {"op_id": op_id, "strip": strip.name,
                "track": track.name if track else None,
                "exponent": float(value), "touched": res.get("touched", 0)}
    tracks = [t for t in anim.nla_tracks
              if t.name.startswith(track_name or PREVIEW_TRACK)]
    if not tracks:
        raise RuntimeError(f"没有轨 {track_name or PREVIEW_TRACK}")
    touched = 0
    for t in tracks:
        for s in t.strips:
            agent_ops.set_strip_exponent(s, float(value))
            touched += 1
    _redraw()
    return {"influence": float(value), "strips": touched,
            "tracks": [t.name for t in tracks]}


TOOLS = {
    "ping": _tool_ping,
    "get_overview": _tool_overview,
    "list_intervals": _tool_list_intervals,
    "describe": _tool_describe,
    "get_series": _tool_get_series,
    "find_events": _tool_find_events,
    "compare": _tool_compare,
    "snapshot": _tool_snapshot,
    "probe_anatomy": _tool_probe_anatomy,
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
    "reapply": _tool_reapply,
    "ab_toggle": _tool_ab_toggle,
    "set_preview": _tool_set_preview,
    "set_influence": _tool_set_influence,
}


def _ctx():
    scene, settings = _settings()
    return {
        "scene": scene,
        "settings": settings,
        "armature": _rig_armature(settings, scene),
        "source_armature": _source_armature(settings),
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
    """Runs on the main thread via bpy.app.timers; drains the request queue.

    Bare ``except Exception`` everywhere: a raised exception in a timer
    callback silently unregisters it (that's the "server died" bug) - every
    failure path must return the interval so the pump keeps ticking.
    """
    global _LAST_PUMP
    _LAST_PUMP = time.time()
    try:
        while True:
            try:
                sock_file, request = _requests.get_nowait()
            except queue.Empty:
                break
            try:
                response = _dispatch(request)
                response["id"] = request.get("id")
                sock_file.write(
                    (json.dumps(response, ensure_ascii=False)
                     + "\n").encode("utf-8"))
                sock_file.flush()
            except Exception as exc:  # noqa: BLE001
                _STATUS["last_error"] = f"pump: {exc!r}"
    except Exception as exc:  # noqa: BLE001 - never propagate out of a timer
        _STATUS["last_error"] = f"pump-loop: {exc!r}"
    return TIMER_INTERVAL if _running else None


def _watchdog():
    """If the pump timer vanished while the server is running, re-register it.
    Also stamps _LAST_PUMP so stale-pump diagnostics are visible in status()."""
    if _running and not bpy.app.timers.is_registered(_pump):
        _STATUS["last_error"] = "pump 掉线，watchdog 重启"
        try:
            bpy.app.timers.register(_pump, first_interval=TIMER_INTERVAL)
        except Exception as exc:  # noqa: BLE001
            _STATUS["last_error"] = f"watchdog 失败: {exc!r}"
    return WATCHDOG_INTERVAL if _running else None


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
    if not bpy.app.timers.is_registered(_watchdog):
        bpy.app.timers.register(_watchdog, first_interval=WATCHDOG_INTERVAL)
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
    if bpy.app.timers.is_registered(_watchdog):
        bpy.app.timers.unregister(_watchdog)
    if _bump_version in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_bump_version)
    return {"running": False}


def is_running() -> bool:
    return _running


def ensure_layout(settings=None, scene=None) -> dict:
    """One-shot housekeeping: migrate the legacy shared tracks to per-op
    tracks (idempotent) and keep the fix list in sync.

    MUST NOT be called from panel draw - renaming NLA tracks writes ID data,
    which is forbidden in the draw context ("Writing to ID classes in this
    context is not allowed").  The fixlist timer calls this instead."""
    scene = scene or bpy.context.scene
    settings = settings or scene.mocap_doctor
    rig = _rig_armature(settings, scene)
    if rig is None:
        return {"migrated": 0, "rows": 0, "rig": None}
    mig = agent_ops.migrate_legacy_tracks(rig, settings.data_directory or None)
    if mig.get("moved"):
        _bump_ops_rev_from(settings)
    rows = sync_fixes_list(settings, scene)
    _sync_params_list(settings)
    return {"migrated": mig.get("moved", 0), "rows": rows, "rig": rig.name}


FIXLIST_INTERVAL = 1.0
_LAST_FIXLIST = 0.0          # wall-clock of last _fixlist_tick

# ---- 参数控件防抖重写 + 方向空物体监视 ------------------------------------
# 修复条目的参数控件（properties.MD_PG_AgentParam）不直接调 reapply：
# 滑块拖动一帧一个 update，逐个写会堆 strip/卡死。这里统一排队，静默
# PARAM_DEBOUNCE 秒后一次性同轨重写（删旧写新同名，op_id 不变）。
# dir_object 绑定的空物体被拖动/k动画时同理排队刷新（key="__refresh__"）。
PARAM_TICK = 0.2
PARAM_DEBOUNCE = 0.25
_PARAM_PENDING: dict = {}      # (op_id, key) -> value
_PARAM_LAST_EDIT = 0.0
_EMPTY_WATCH: dict = {}        # op_id -> 方向物体 matrix 签名


def schedule_param_apply(op_id, key, value):
    """参数控件/监视器的唯一入口：排队 + 记时间戳 + 拉起计时器。"""
    global _PARAM_LAST_EDIT
    _PARAM_PENDING[(str(op_id), str(key))] = value
    _PARAM_LAST_EDIT = time.time()
    try:
        if not bpy.app.timers.is_registered(_param_tick):
            bpy.app.timers.register(_param_tick, first_interval=PARAM_TICK)
    except Exception:
        pass


def _param_tick():
    """防抖排水 + dir_object 空物体变换监视。"""
    global _PARAM_LAST_EDIT
    try:
        scene = bpy.context.scene
        settings = getattr(scene, "mocap_doctor", None)
        if settings is None or not getattr(settings, "initialized", False):
            return PARAM_TICK
        data_dir = settings.data_directory or "."
        rig = _rig_armature(settings, scene)
        if rig is None:
            return PARAM_TICK
        # 方向物体监视：绑定的空物体矩阵变了 → 排队重写（无 overrides，
        # reapply 用 op params 里的 dir_object 重新逐帧取方向）
        try:
            ops = agent_ops.list_ops(data_dir)
        except Exception:
            ops = []
        live = set()
        for op in ops:
            if op.get("status") not in ("preview", "committed"):
                continue
            dob = (op.get("params") or {}).get("dir_object")
            if not dob:
                continue
            live.add(op.get("id"))
            obj = bpy.data.objects.get(str(dob))
            if obj is None:
                continue
            mw = obj.matrix_world
            sig = (tuple(round(v, 5) for v in mw.translation)
                   + tuple(round(v, 5) for v in mw.to_quaternion()))
            prev = _EMPTY_WATCH.get(op.get("id"))
            _EMPTY_WATCH[op["id"]] = sig
            if prev is not None and prev != sig:
                schedule_param_apply(op["id"], "__refresh__", True)
        for dead in set(_EMPTY_WATCH) - live:
            _EMPTY_WATCH.pop(dead, None)
        # 静默期满 → 排水重写
        if _PARAM_PENDING \
                and time.time() - _PARAM_LAST_EDIT >= PARAM_DEBOUNCE:
            pending = dict(_PARAM_PENDING)
            _PARAM_PENDING.clear()
            applied = False
            for (op_id, key), value in pending.items():
                try:
                    overrides = {} if key == "__refresh__" else {key: value}
                    agent_ops.reapply(data_dir, rig, op_id,
                                      scene=scene, **overrides)
                    applied = True
                except Exception as exc:
                    _STATUS["last_error"] = f"参数 {key}: {exc!r}"
            if applied:
                _bump_ops_rev_from(settings)
                _sync_params_list(settings, data_dir)
                _redraw()
    except Exception as exc:  # noqa: BLE001 - a timer must never die
        _STATUS["last_error"] = f"paramtick: {exc!r}"
    return PARAM_TICK


def _sync_params_list(settings, data_dir=None):
    """把每个 op 的可调参数镜像进 settings.agent_params（面板只读这里）。

    key = "op_id::param"；pending 中的项跳过（不覆盖用户正在拖的值）。"""
    from .. import properties as _props

    data_dir = data_dir or settings.data_directory or "."
    try:
        ops = agent_ops.list_ops(data_dir)
    except Exception:
        return
    want = {}
    for op in ops:
        specs = agent_ops.TUNABLE_PARAMS.get(op.get("tool"))
        if not specs or not op.get("id"):
            continue
        params = op.get("params") or {}
        for spec in specs:
            when = spec.get("when")      # 条件暴露：{"param": 允许值|True}
            if when and not all(
                    (params.get(wk) in wv
                     if isinstance(wv, list)
                     else (bool(params.get(wk)) if wv is True
                          else params.get(wk) == wv))
                    for wk, wv in when.items()):
                continue
            k = spec["key"]
            v = params.get(k)
            if k == "frame_range" and v is None:
                v = op.get("frames")
            want[f"{op['id']}::{k}"] = (op["id"], spec, v)
    coll = settings.agent_params
    existing = {it.pkey: it for it in coll}
    for i in range(len(coll) - 1, -1, -1):
        if coll[i].pkey not in want:
            coll.remove(i)
    for pkey, (op_id, spec, v) in want.items():
        it = existing.get(pkey)
        if it is None:
            it = coll.add()
            it.pkey = pkey
        if (op_id, spec["key"]) in _PARAM_PENDING:
            continue                     # 用户正在拖，别覆盖
        _props.sync_param_item(it, op_id, spec, v)


def _fixlist_tick():
    """Auto-sync the panel's fix list outside the draw context.

    Draw may only read; every mutation (NLA migration, collection rebuild)
    happens here.  Stale = op log revision moved ahead of the list, or the
    list is empty while the rig exists (fresh file)."""
    global _LAST_FIXLIST
    _LAST_FIXLIST = time.time()
    try:
        scene = bpy.context.scene
        if scene is None:
            return FIXLIST_INTERVAL
        settings = getattr(scene, "mocap_doctor", None)
        if settings is None or not settings.initialized:
            return FIXLIST_INTERVAL
        stale = (int(settings.agent_fixes_rev) != int(settings.agent_ops_rev)
                 or (len(settings.agent_fixes) == 0
                     and _rig_armature(settings, scene) is not None))
        if stale:
            ensure_layout(settings, scene)
    except Exception as exc:  # noqa: BLE001 - a timer must never die
        _STATUS["last_error"] = f"fixlist: {exc!r}"
    return FIXLIST_INTERVAL


def _on_file_loaded(*_args):
    """A file load can outlive the startup registration - re-arm the timer."""
    _PARAM_PENDING.clear()
    _EMPTY_WATCH.clear()       # 新文件里旧签名无意义
    try:
        start_fixlist_timer()
    except Exception:
        pass


def start_fixlist_timer():
    # timer first: if the handler append below fails (odd context), the timer
    # itself is already armed
    if not bpy.app.timers.is_registered(_fixlist_tick):
        bpy.app.timers.register(_fixlist_tick, first_interval=FIXLIST_INTERVAL)
    if not bpy.app.timers.is_registered(_param_tick):
        bpy.app.timers.register(_param_tick, first_interval=PARAM_TICK)
    if _on_file_loaded not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_file_loaded)


def stop_fixlist_timer():
    if bpy.app.timers.is_registered(_fixlist_tick):
        bpy.app.timers.unregister(_fixlist_tick)
    if bpy.app.timers.is_registered(_param_tick):
        bpy.app.timers.unregister(_param_tick)
    if _on_file_loaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_loaded)


def _bump_ops_rev_from(settings):
    try:
        settings.agent_ops_rev = int(settings.agent_ops_rev) + 1
    except Exception:
        pass


def sync_fixes_list(settings, scene=None) -> int:
    """Rebuild the panel's fix list from op log + live NLA state.

    Values already shown are preserved by op_id, so a rebuild never fights the
    slider the user is dragging (drags do not touch agent_ops_rev)."""
    scene = scene or bpy.context.scene
    rig = _rig_armature(settings, scene)
    if rig is None:
        return 0
    from .. import properties as _props
    rows = agent_ops.reconcile(rig, settings.data_directory or ".")
    coll = settings.agent_fixes
    keep = {item.op_id: (item.exponent, item.muted, item.selected)
            for item in coll}
    active_id = (coll[settings.agent_fix_index].op_id
                 if 0 <= settings.agent_fix_index < len(coll) else "")
    coll.clear()
    for row in rows:
        item = coll.add()
        item.op_id = row["op_id"] or ""
        item.label = (row.get("label")
                      or (f"{row['frames'][0]}-{row['frames'][1]} {row['tool']}"
                          if row.get("frames")
                          else f"{row['tool']} {row['strip']}"))
        item.strip = row.get("strip") or ""
        item.track = row.get("track") or ""
        item.status = row.get("status") or ""
        item.alive = bool(row.get("alive"))
        item.frames = f"{row['frames'][0]}-{row['frames'][1]}" if row.get("frames") else ""
        prev = keep.get(item.op_id)
        if prev is not None and not row.get("alive"):
            item.exponent, item.muted = prev[0], prev[1]   # 丢失行：保住调过的值
        else:
            item.exponent = float(row.get("exponent", 1.0) or 1.0)
            item.muted = bool(row.get("muted"))
        item.selected = bool(prev[2]) if prev is not None else False
    settings.agent_fixes_rev = int(settings.agent_ops_rev)
    if active_id:
        for i, item in enumerate(coll):
            if item.op_id == active_id:
                _props.set_quietly(settings, "agent_fix_index", i)
                break
    if settings.agent_fix_index >= len(coll):
        _props.set_quietly(settings, "agent_fix_index", max(0, len(coll) - 1))
    return len(coll)


def fixes_snapshot(settings, scene=None) -> list:
    """Read-only rows for the panel (no rebuild)."""
    scene = scene or bpy.context.scene
    rig = _rig_armature(settings, scene)
    if rig is None:
        return []
    return agent_ops.reconcile(rig, settings.data_directory or ".")


def status() -> dict:
    pump_age = round(time.time() - _LAST_PUMP, 1) if _LAST_PUMP else None
    fixlist_age = round(time.time() - _LAST_FIXLIST, 1) if _LAST_FIXLIST else None
    return {"running": _running, "version": _DATA_VERSION,
            "clients": _STATUS["clients"], "last_tool": _STATUS["last_tool"],
            "last_error": _STATUS["last_error"],
            "pump_age_s": pump_age,
            "pump_registered": bpy.app.timers.is_registered(_pump),
            "fixlist_registered": bpy.app.timers.is_registered(_fixlist_tick),
            "fixlist_age_s": fixlist_age,
            "port": _server.server_address[1] if _server else PORT}
