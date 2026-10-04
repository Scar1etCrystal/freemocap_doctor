"""标记箭头（markers）：把"用户看到的方向"和"agent 算的方向"钉成同一支箭头。

用户的流程：拿到一个模型，先给掌心、脚底、膝、肘绑好空物体箭头，之后下指令、看结果都
以这些箭头为准。难点是"箭头怎么绑才一直跟着网格"：
  - 掌心/脚底这类部位的网格相对带动它的骨是刚性的（掌心皮肤法线在手骨局部坐标里 150 帧
    散布 ≤1.5°），所以**骨骼父级**就是正确绑法——一帧对准，全程有效。本工具替用户做这步：
    建 SINGLE_ARROW 空物体 MCD_<part>.<side>，父级绑到真正带动网格的骨（MMD 骨架的
    手首/足首，没有时用 RIG 的 DEF 骨），初值 = 网格标定 / 骨几何算出的方向。用户在视口里
    过一眼，不对就直接旋转箭头；probe / hold_pose 读到这支箭头就以它为准
    （evidence.palm_source = "marker"）。
  - 膝/肘"朝向"是两段骨夹角的凸出方向，相对任一段都随弯曲角转（半角），不能刚性绑；
    用 bake：按帧把 agent 算出的方向 K 到一支箭头上（只用来看，不读回）。
  - Child Of + 顶点组 不行：只跟平均顶点法线，绕法线的滚转不受控（实测漂 8–35°）。

动作：create（默认）/ bake / list / remove。不碰 RIG 动画数据，不需要 claim。
"""
from __future__ import annotations

from typing import Any

import bpy
from mathutils import Matrix, Vector

from . import agent_anatomy as A
from . import agent_pose as P
from .animation import preserve_scene_frame, set_scene_frame

# 绑定骨：优先 MMD 骨架（真正带动网格的骨），其次 RIG 的 DEF 骨
_BIND_BONES = {"palm": ("手首.{s}", "DEF-hand.{s}"),
               "sole": ("足首.{s}", "DEF-foot.{s}")}
# bake 的锚点（箭头放哪）：part -> 取点函数
_SIDED = ("palm", "back_of_hand", "finger_dir", "knuckle", "hand_axis",
          "sole", "instep", "toe", "knee_front", "elbow_front")
_ACTIONS = ("create", "bake", "list", "remove")


def _settings(ctx):
    return getattr(ctx["scene"], "mocap_doctor", None)


def _bind_target(ctx, armature, part, side):
    """(父级骨架, 骨名)：MMD 骨架上的 手首/足首，没有就 RIG 的 DEF 骨。"""
    mmd_name, def_name = _BIND_BONES[part]
    mmd = getattr(_settings(ctx), "mmd_armature", None)
    if mmd is not None and mmd.pose.bones.get(mmd_name.format(s=side)) is not None:
        return mmd, mmd_name.format(s=side)
    if armature.pose.bones.get(def_name.format(s=side)) is not None:
        return armature, def_name.format(s=side)
    raise RuntimeError(f"找不到可绑定的骨：{mmd_name.format(s=side)}（MMD 骨架）或 "
                       f"{def_name.format(s=side)}（RIG）")


def _pw(armature, bone, end="head"):
    pb = armature.pose.bones.get(bone)
    if pb is None:
        return None
    return armature.matrix_world @ (pb.head if end == "head" else pb.tail)


def _anchor(armature, part, side):
    """箭头的位置（世界）：掌心皮肤中心 / 脚底三点中心 / 关节点 / 指根中心 / 骨盆。"""
    if part in ("palm", "back_of_hand", "hand_axis", "knuckle", "finger_dir"):
        cal = A.palm_calibration(armature, side)
        pb = armature.pose.bones.get(f"hand_fk.{side}")
        if cal and cal.get("centre_local") is not None and pb is not None:
            return (armature.matrix_world @ pb.matrix) @ cal["centre_local"]
        roots = [_pw(armature, f"{A._FINGER_STEMS[f]}.01.{side}") for f in A._PALM_FINGERS]
        roots = [r for r in roots if r is not None]
        wrist = _pw(armature, f"hand_fk.{side}")
        if roots and wrist is not None:
            return (wrist + sum(roots, Vector()) / len(roots)) * 0.5
        return wrist
    if part in ("sole", "instep", "toe"):
        pts = [_pw(armature, f"DEF-foot.{side}", "head"), _pw(armature, f"DEF-foot.{side}", "tail"),
               _pw(armature, f"DEF-toe.{side}", "tail")]
        pts = [q for q in pts if q is not None]
        return sum(pts, Vector()) / len(pts) if pts else None
    if part == "knee_front":
        return _pw(armature, f"thigh_fk.{side}", "tail")
    if part == "elbow_front":
        return _pw(armature, f"upper_arm_fk.{side}", "tail")
    if part == "body_forward":
        return _pw(armature, "torso_root") or Vector((0.0, 0.0, 0.0))
    return None


def _get_or_make(name, length):
    obj = bpy.data.objects.get(name)
    created = obj is None
    if created:
        obj = bpy.data.objects.new(name, None)
    if obj.type != "EMPTY":
        raise RuntimeError(f"{name} 已存在但不是空物体，换个名字或先删掉它")
    if obj.name not in bpy.context.scene.collection.objects and not obj.users_collection:
        bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = "SINGLE_ARROW"
    obj.empty_display_size = float(length)
    return obj, created


def _aim_matrix(anchor: Vector, direction: Vector) -> Matrix:
    m = direction.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    m.translation = anchor
    return m


def _world_dir_now(scene, armature, part, side):
    fn = A.frame_probe_fn(part, side)
    return fn(armature, scene)


def _create(ctx, parts, sides, length, overwrite, frame):
    scene, armature = ctx["scene"], ctx["armature"]
    rows, warnings = [], []
    with preserve_scene_frame(scene):
        set_scene_frame(scene, frame)
        for part in parts:
            if part not in A.MARKER_PARTS:
                raise RuntimeError(f"create 只支持刚性部位 {A.MARKER_PARTS}（膝/肘请用 action=bake）；收到 {part!r}")
            for side in sides:
                name = A.marker_name(part, side)
                existing = bpy.data.objects.get(name)
                if existing is not None and not overwrite:
                    mk, why = A.bound_marker(part, side)
                    rows.append({"name": name, "part": part, "side": side, "status": "kept",
                                 "bound": mk is not None, "why": why})
                    if mk is None:
                        warnings.append(f"{name} 已存在但{ '没有骨骼父级' if why == 'unbound' else why }，"
                                        f"没动它；要重建加 overwrite=true")
                    continue
                with A.ignore_markers():
                    res = A.probe(scene, armature, part=part, side=side, frame_range=[frame, frame])
                d = Vector(res["world_dir"])
                anchor = _anchor(armature, part, side)
                if anchor is None:
                    raise RuntimeError(f"{part}.{side} 找不到锚点骨")
                par, bone = _bind_target(ctx, armature, part, side)
                obj, created = _get_or_make(name, length)
                obj.parent = par
                obj.parent_type = "BONE"
                obj.parent_bone = bone
                obj.matrix_parent_inverse = Matrix.Identity(4)
                obj["mcd_marker"] = "bound"
                obj["mcd_part"], obj["mcd_side"] = part, side
                bpy.context.view_layer.update()
                obj.matrix_world = _aim_matrix(anchor, d)
                bpy.context.view_layer.update()
                got = A.marker_dir(obj)
                err = A._angle_deg(got, d)
                src = res.get("evidence", {}).get(f"{part}_source")
                rows.append({"name": name, "part": part, "side": side,
                             "status": "created" if created else "updated",
                             "parent": par.name, "bone": bone, "source": src,
                             "world_dir": [round(v, 4) for v in got],
                             "place_err_deg": round(err, 2)})
                if err > 0.5:
                    warnings.append(f"{name} 放置后读回方向偏 {err:.1f}°（父级矩阵异常？）")
                if part == "palm" and src == "fingers":
                    warnings.append(f"{name} 的初值来自手指几何（没有网格标定：{res.get('evidence', {}).get('mesh_calibration')}），"
                                    "可信度低——请在视口里把它转到垂直于掌心")
    return rows, warnings


def _bake(ctx, part, side, frame_range, length):
    scene, armature = ctx["scene"], ctx["armature"]
    if frame_range is None:
        raise RuntimeError("bake 需要 frame_range=[A,B]")
    if part in _SIDED and side not in ("L", "R"):
        raise RuntimeError(f"{part} 需要 side='L'/'R'")
    a, b = int(frame_range[0]), int(frame_range[1])
    name = A.marker_name(part, side) if side else f"{A.MARKER_PREFIX}{part}"
    if bpy.data.objects.get(name) is not None and bpy.data.objects[name].get("mcd_marker") == "bound":
        raise RuntimeError(f"{name} 是绑定标记（骨骼父级），不往上烘焙；要看逐帧方向就先 remove 它")
    obj, created = _get_or_make(name, length)
    obj.parent = None
    obj.rotation_mode = "QUATERNION"
    obj["mcd_marker"] = "baked"
    obj["mcd_part"], obj["mcd_side"] = part, side or ""
    obj["mcd_baked_range"] = [a, b]
    if obj.animation_data and obj.animation_data.action:
        obj.animation_data_clear()
    fallback = 0
    prev = None
    with preserve_scene_frame(scene):
        for f in range(a, b + 1):
            set_scene_frame(scene, f)
            d = _world_dir_now(scene, armature, part, side)
            if d is None or d.length < 1e-6:
                if prev is None:
                    continue
                d = prev
                fallback += 1
            prev = d
            anchor = _anchor(armature, part, side) or Vector((0.0, 0.0, 0.0))
            m = _aim_matrix(anchor, d)
            obj.location = m.translation
            obj.rotation_quaternion = m.to_quaternion()
            obj.keyframe_insert("location", frame=f)
            obj.keyframe_insert("rotation_quaternion", frame=f)
    if prev is None:
        raise RuntimeError(f"{part}.{side} 在 {a}–{b} 推不出方向")
    return {"name": name, "part": part, "side": side, "status": "created" if created else "rebaked",
            "frame_range": [a, b], "fallback_frames": fallback,
            "note": "烘焙箭头只用来看，probe 不读回；姿态改了（修复后）要重新 bake"}


def _list(ctx, frame_range):
    scene, armature = ctx["scene"], ctx["armature"]
    rows = []
    frames = None
    if frame_range is not None:
        a, b = int(frame_range[0]), int(frame_range[1])
        n = min(9, b - a + 1)
        frames = sorted({int(round(a + i * (b - a) / max(1, n - 1))) for i in range(n)})
    for obj in bpy.data.objects:
        if not obj.name.startswith(A.MARKER_PREFIX) or obj.type != "EMPTY":
            continue
        kind = obj.get("mcd_marker") or "unknown"
        part, side = obj.get("mcd_part"), obj.get("mcd_side") or None
        row = {"name": obj.name, "kind": kind, "part": part, "side": side,
               "parent": obj.parent.name if obj.parent else None,
               "bone": obj.parent_bone if obj.parent_type == "BONE" else None}
        if kind == "bound" and part in A.MARKER_PARTS and side:
            mk, why = A.bound_marker(part, side)
            row["valid"] = mk is not None
            if mk is None:
                row["why"] = why
            if frames and mk is not None:
                worst = 0.0
                with preserve_scene_frame(scene):
                    for f in frames:
                        set_scene_frame(scene, f)
                        with A.ignore_markers():
                            g = _world_dir_now(scene, armature, part, side)
                        if g is not None:
                            worst = max(worst, A._angle_deg(A.marker_dir(mk), g))
                row["vs_geometry_max_deg"] = round(worst, 1)
                row["frames"] = frames
        rows.append(row)
    return rows


def _remove(parts, sides, all_markers):
    gone = []
    if all_markers:
        names = [o.name for o in bpy.data.objects if o.name.startswith(A.MARKER_PREFIX) and o.type == "EMPTY"]
    else:
        names = [A.marker_name(p, s) for p in parts for s in sides]
    for n in names:
        obj = bpy.data.objects.get(n)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
            gone.append(n)
    return gone


def _tool_markers(ctx, action="create", parts=None, sides=None, part=None, side=None,
                  frame_range=None, length=0.15, overwrite=False, frame=None, all=False,
                  **unknown):
    P.reject_unknown_args("markers", _tool_markers, unknown)
    action = str(action).lower()
    if action not in _ACTIONS:
        raise RuntimeError(f"未知 action {action!r}，可用：{_ACTIONS}")
    if ctx["armature"] is None:
        raise RuntimeError("没有识别到 RIG 骨架")
    scene = ctx["scene"]
    parts = [str(p).lower() for p in (parts or ([part] if part else list(A.MARKER_PARTS)))]
    sides = [str(s).upper() for s in (sides or ([side] if side else ["L", "R"]))]
    if action == "create":
        f = int(frame) if frame is not None else int(scene.frame_current)
        rows, warnings = _create(ctx, parts, sides, float(length), bool(overwrite), f)
        made = [r["name"] for r in rows if r["status"] != "kept"]
        return {"summary": f"markers: {len(made)} 支已绑（{', '.join(made) or '无'}），{len(rows) - len(made)} 支保留",
                "data": {"markers": rows, "frame": f}, "warnings": warnings, "truncated": False,
                "hint": "在视口里检查：箭头应从掌心/脚底垂直指出。不对就直接旋转箭头（它跟着骨，一帧对准全程有效）；"
                        "之后 probe_anatomy 的 evidence.palm_source/sole_source 会是 marker"}
    if action == "bake":
        if len(parts) != 1:
            raise RuntimeError("bake 一次一个 part（膝/肘/手指等逐帧方向）")
        res = _bake(ctx, parts[0], (sides[0] if (side or sides) else None) if parts[0] in _SIDED else None,
                    frame_range, float(length))
        return {"summary": f"bake {res['name']} @{res['frame_range']}（{res['status']}，fallback {res['fallback_frames']} 帧）",
                "data": res, "warnings": [], "truncated": False,
                "hint": "播放这段看箭头；修复后要重新 bake"}
    if action == "list":
        rows = _list(ctx, frame_range)
        bad = [r["name"] for r in rows if r.get("valid") is False]
        return {"summary": f"{len(rows)} 支标记" + (f"，{len(bad)} 支无效：{bad}" if bad else ""),
                "data": {"markers": rows}, "warnings": [f"{n} 没有骨骼父级，probe 会忽略它" for n in bad],
                "truncated": False, "hint": "vs_geometry_max_deg = 标记与网格/骨几何估计的最大夹角（给了 frame_range 才算）"}
    gone = _remove(parts, sides, bool(all))
    return {"summary": f"removed {gone}", "data": {"removed": gone}, "warnings": [],
            "truncated": False, "hint": ""}


TOOLS = {"markers": _tool_markers}
