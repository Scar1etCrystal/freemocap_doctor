"""语义解剖探头：从实时场景几何推导解剖学方向，替代"猜局部轴"。

为什么需要这一层：修复意图是语义的（"手心朝前"），而执行器吃的是骨骼局部
轴。以前哪根局部轴对应掌心、符号是正还是负全靠猜，验证又用同一个假设
自证——两次掌心修复失败都是这个模式。本模块从几何事实推导：

- 掌心：优先用**目标网格**标定（见 palm_calibration：掌心皮肤相对 hand_fk 刚性，
  量一次得到固定局部向量，逐帧只需转一下）；没有网格时退回手指几何——四指指根连线
  × 手指指向 定掌平面，各指末节弯曲向量定号（手指一弯这个平面就跟着转，实测与可见
  掌心差中位数 45°，所以只是兜底；evidence.palm_source 标明用的是哪种）。
- 脚底：脚跟/前掌/脚尖三点定平面，小腿在脚背侧定号（空中同样成立）。
- 膝/肘前：大小两段骨的夹角方向即关节凸出方向。
- 身体前方：脚尖水平投影为主，肩线×竖直轴、相机方向交叉验证。
- 每个返回值附带 owner 骨上的**精确局部向量**（喂给 hold_pose.world_axis）
  与次轴（喂给 secondary_axis 双轴解算），以及数值证据和跨帧一致性。

所有方向都在世界空间推导，再反算成控制骨局部向量——骨架约定（Rigify
轴向、左右手镜像）完全不用关心。
"""

from __future__ import annotations

import contextlib
from typing import Any, Mapping, Sequence

import bpy
import numpy as np
from mathutils import Vector

from .animation import preserve_scene_frame, set_scene_frame

# MMR 手指控制骨名（与 agent_io._RIG_FINGER_STEMS 保持一致，本模块独立副本
# 以免探头被 io 层结构绑死）
_FINGER_STEMS = {"index": "f_index", "middle": "f_middle",
                 "ring": "f_ring", "pinky": "f_pinky", "thumb": "thumb"}
_PALM_FINGERS = ("index", "middle", "ring", "pinky")   # 拇指另行处理

_EPS = 1e-6


def _pw(armature: Any, bone: str, end: str = "head") -> Vector | None:
    """世界空间的 pose 骨端点（评估后姿态，包含所有 NLA strip）。"""
    pb = armature.pose.bones.get(bone)
    if pb is None:
        return None
    return armature.matrix_world @ (pb.head if end == "head" else pb.tail)


def _norm(v: Vector) -> Vector | None:
    return v.normalized() if v.length > _EPS else None


def _angle_deg(a: Vector, b: Vector) -> float:
    d = max(-1.0, min(1.0, float(a.normalized() @ b.normalized())))
    return float(np.degrees(np.arccos(d)))


def _local_of(armature: Any, bone: str, world_dir: Vector) -> Vector | None:
    """world_dir 在指定骨上的当前局部表达（喂给 world_axis/secondary_axis）。"""
    pb = armature.pose.bones.get(bone)
    if pb is None:
        return None
    rot = (armature.matrix_world @ pb.matrix).to_quaternion()
    return rot.inverted() @ world_dir


def _sample_frames(scene: Any, frame_range: Sequence[int] | None,
                   max_n: int) -> list[int]:
    if frame_range:
        a = int(frame_range[0])
        b = int(frame_range[1]) if len(frame_range) > 1 else a
        if b <= a:
            return [a]
        n = max(2, min(int(max_n), b - a + 1))
        return sorted({int(round(a + i * (b - a) / (n - 1)))
                       for i in range(n)})
    return [int(scene.frame_current)]


# ---------------------------------------------------------------------------
# 掌心网格标定：让 agent 读到的"掌心"= 用户在视口里看到的掌心网格
#
# 旧法（手指几何）把"手指指向"当掌平面的一条边，手指一弯它就倒向掌心侧，掌平面跟着
# 转：arue 式重音テト 1499 帧实测，与可见掌心网格法线的夹角中位数 45°、最大 168°，
# 手指伸直时还会定错号（置信度 ≥0.5 的帧里 13% 符号相反）。而掌心皮肤本身相对
# hand_fk 是刚性的（权重 94% 在 手首，法线在骨局部坐标里 150 帧散布 ≤1.5°），所以
# 掌心 = hand_fk 上一个固定局部向量，从目标网格量一次就够：
#   1) 手骨几何定掌平面：指根连线 × (腕→指根中心)，符号取拇指根所在侧（拇指根在
#      手掌侧，实测离手中面 12.8 mm；再与手指弯曲定号交叉验证，不一致只做标记）；
#   2) 在手骨坐标系里框出手掌皮肤：腕→指根 25%–95%、横向 ±0.6 指根跨度、掌侧
#      0–40 mm（这件衣服的袖口在 60 mm 外；手背皮肤在另一侧），顶点权重须主要落在
#      本侧 手首/手指/手捩 组（排除贴近的另一只手臂）；
#   3) 取其中朝掌侧的面，面积加权求法线，反算到 hand_fk 局部并缓存。
# 没有目标网格 / 不是 MMD 命名（无 手首.L/R 顶点组）→ 退回手指几何，
# evidence.palm_source = "fingers"（bridge 会给 warning）。

_MESH_HAND_GROUP = "手首.{s}"
_MESH_FINGER_GROUPS = tuple(f"{a}{b}" for a in ("親指", "人指", "中指", "薬指", "小指")
                            for b in ("０", "１", "２", "３", "先"))
_MESH_TWIST_GROUPS = ("手捩", "手捩1", "手捩2", "手捩3")
_PALM_BOX = {"t_min": 0.25, "t_max": 0.95, "lat": 0.6, "h_max": 0.04}
_PALM_CAL: dict[tuple, dict | None] = {}


def _target_mesh(scene: Any = None) -> Any | None:
    """向导里设的目标模型网格（settings.target_mesh），不是 MESH 时返回 None。"""
    scene = scene if scene is not None else getattr(bpy.context, "scene", None)
    settings = getattr(scene, "mocap_doctor", None)
    obj = getattr(settings, "target_mesh", None)
    return obj if obj is not None and getattr(obj, "type", "") == "MESH" else None


def reset_palm_calibration() -> None:
    _PALM_CAL.clear()


def _mesh_group_weights(mesh: Any, groups: Mapping[str, Sequence[str]]) -> dict[str, np.ndarray]:
    """{key: (V,) 顶点在该组名单上的权重之和}，一遍扫完所有顶点（MMD 权重已归一）。"""
    by_name = {g.name: g.index for g in mesh.vertex_groups}
    ids = {k: {by_name[n] for n in names if n in by_name} for k, names in groups.items()}
    n = len(mesh.data.vertices)
    out = {k: np.zeros(n) for k in groups}
    lookup = {gi: k for k, s in ids.items() for gi in s}
    if not lookup:
        return out
    for v in mesh.data.vertices:
        for ge in v.groups:
            k = lookup.get(ge.group)
            if k is not None:
                out[k][v.index] += ge.weight
    return out


def _evaluated_mesh_arrays(mesh: Any):
    """评估后网格（含骨架变形）的世界空间数组：顶点、面法线、面积、面→顶点索引。"""
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    try:
        nv, nf = len(m.vertices), len(m.polygons)
        co = np.empty(nv * 3, dtype=np.float32)
        m.vertices.foreach_get("co", co)
        pn = np.empty(nf * 3, dtype=np.float32)
        m.polygons.foreach_get("normal", pn)
        pa = np.empty(nf, dtype=np.float32)
        m.polygons.foreach_get("area", pa)
        ls = np.empty(nf, dtype=np.int64)
        m.polygons.foreach_get("loop_start", ls)
        lt = np.empty(nf, dtype=np.int64)
        m.polygons.foreach_get("loop_total", lt)
        lv = np.empty(len(m.loops), dtype=np.int64)
        m.loops.foreach_get("vertex_index", lv)
    finally:
        ev.to_mesh_clear()
    mat = np.asarray(ev.matrix_world, dtype=np.float64)
    rot = mat[:3, :3]
    co = co.reshape(nv, 3).astype(np.float64) @ rot.T + mat[:3, 3]
    pn = pn.reshape(nf, 3).astype(np.float64) @ np.linalg.inv(rot)      # 法线用逆转置
    pn /= np.linalg.norm(pn, axis=1, keepdims=True) + 1e-12
    return co, pn, pa.astype(np.float64), ls, lt, lv


def _calibrate_palm(armature: Any, side: str, mesh: Any) -> dict | None:
    """当前帧量一次：掌心皮肤法线在 hand_fk 局部的表达。失败返回 {"reason": ...}。"""
    pb = armature.pose.bones
    need = [f"hand_fk.{side}", f"thumb.01.{side}"] + \
        [f"{_FINGER_STEMS[f]}.01.{side}" for f in _PALM_FINGERS]
    if any(pb.get(n) is None for n in need):
        return {"reason": "missing_hand_bones"}
    mw = armature.matrix_world

    def head(n):
        return np.asarray(mw @ pb[n].head, dtype=np.float64)
    wrist = head(f"hand_fk.{side}")
    roots = [head(f"{_FINGER_STEMS[f]}.01.{side}") for f in _PALM_FINGERS]
    kc = np.mean(roots, axis=0)
    axis, lat = kc - wrist, roots[3] - roots[0]
    hand_len, span = float(np.linalg.norm(axis)), float(np.linalg.norm(lat))
    if hand_len < 1e-4 or span < 1e-4:
        return {"reason": "degenerate_hand"}
    axis, lat = axis / hand_len, lat / span
    n0 = np.cross(lat, axis)
    if np.linalg.norm(n0) < _EPS:
        return {"reason": "degenerate_hand"}
    n0 /= np.linalg.norm(n0)
    d_thumb = float((head(f"thumb.01.{side}") - 0.5 * (wrist + kc)) @ n0)
    if abs(d_thumb) < 0.003:                       # 拇指根几乎在手中面上：定不了号
        return {"reason": "thumb_on_midplane", "thumb_mm": round(d_thumb * 1000, 1)}
    n_geo = n0 if d_thumb > 0 else -n0

    co, pn, pa, ls, lt, lv = _evaluated_mesh_arrays(mesh)
    if len(co) != len(mesh.data.vertices):
        return {"reason": "mesh_topology_changed"}
    w = _mesh_group_weights(mesh, {
        "hand": [_MESH_HAND_GROUP.format(s=side)],
        "fingers": [f"{g}.{side}" for g in _MESH_FINGER_GROUPS],
        "twist": [f"{g}.{side}" for g in _MESH_TWIST_GROUPS]})
    if not w["hand"].any():
        return {"reason": "no_hand_vertex_group"}
    rel = co - wrist
    t, h = rel @ axis, rel @ n_geo
    l = rel @ lat - float((kc - wrist) @ lat)
    box = _PALM_BOX
    verts = ((w["hand"] + w["fingers"] + w["twist"]) > 0.9) & (w["fingers"] < 0.6) \
        & (t > box["t_min"] * hand_len) & (t < box["t_max"] * hand_len) \
        & (np.abs(l) < box["lat"] * span) & (h > 0.0) & (h < box["h_max"])
    if int(verts.sum()) < 6:
        return {"reason": "too_few_palm_vertices", "n": int(verts.sum())}
    face_all = np.minimum.reduceat(verts[lv].astype(np.int8), ls) == 1   # 面的顶点全部入选
    faces = face_all & (pn @ n_geo > 0.5)
    if int(faces.sum()) < 4:
        return {"reason": "too_few_palm_faces", "n": int(faces.sum())}
    n = (pn[faces] * pa[faces, None]).sum(axis=0)
    if np.linalg.norm(n) < _EPS:
        return {"reason": "degenerate_palm_patch"}
    n /= np.linalg.norm(n)
    fingers = _hand_frame_fingers(armature, side)
    conflict = bool(fingers and fingers["confidence"] >= 0.5
                    and float(np.asarray(fingers["palm"]) @ n) < 0)
    hand_mat = mw @ pb[f"hand_fk.{side}"].matrix
    rot = hand_mat.to_quaternion()
    local = (rot.inverted() @ Vector(n.tolist())).normalized()
    fc = np.add.reduceat(co[lv], ls, axis=0) / lt[:, None]          # 面中心
    centre = (fc[faces] * pa[faces, None]).sum(axis=0) / pa[faces].sum()
    centre_local = hand_mat.inverted() @ Vector(centre.tolist())
    return {"local": local, "centre_local": centre_local,
            "faces": int(faces.sum()), "verts": int(verts.sum()),
            "thumb_mm": round(d_thumb * 1000, 1),
            "geo_vs_mesh_deg": round(_angle_deg(Vector(n_geo.tolist()), Vector(n.tolist())), 1),
            "frame": int(getattr(bpy.context.scene, "frame_current", 0)),
            "sign_conflict": conflict, "mesh": mesh.name}


def palm_calibration(armature: Any, side: str, scene: Any = None) -> dict | None:
    """缓存的掌心标定（键：网格名 + 骨架名 + 侧 + 顶点数）；没有目标网格 → None。"""
    mesh = _target_mesh(scene)
    if mesh is None:
        return None
    key = (mesh.name, armature.name, side, len(mesh.data.vertices))
    if key not in _PALM_CAL:
        try:
            _PALM_CAL[key] = _calibrate_palm(armature, side, mesh)
        except Exception as exc:  # noqa: BLE001 - 标定只是增强，失败退回手指几何
            _PALM_CAL[key] = {"reason": f"error: {exc}"}
    return _PALM_CAL[key]


# ---------------------------------------------------------------------------
# 标记箭头（markers）：用户/工具绑在骨上的 SINGLE_ARROW 空物体 MCD_<part>.<side>，+Z = 方向。
# 有它就以它为准（palm_source / sole_source = "marker"）——用户看到的、agent 算的是同一支箭头。
# 只认骨骼父级的（刚性跟随）；没父级的箭头是静止的世界方向，当定义必错，忽略并提醒。
# 烘焙出来的（mcd_marker="baked"，逐帧 K 帧的显示用箭头）不读回。

MARKER_PREFIX = "MCD_"
MARKER_PARTS = ("palm", "sole")
_IGNORE_MARKERS = [False]


@contextlib.contextmanager
def ignore_markers():
    """临时不读标记（markers 工具重建标记、list 对比几何估计时用）。"""
    prev = _IGNORE_MARKERS[0]
    _IGNORE_MARKERS[0] = True
    try:
        yield
    finally:
        _IGNORE_MARKERS[0] = prev


def marker_name(part: str, side: str) -> str:
    return f"{MARKER_PREFIX}{part}.{side}"


def bound_marker(part: str, side: str) -> tuple[Any | None, str | None]:
    """(合格的标记物体, None) / (None, 原因)；原因 None = 根本没有这支标记。"""
    if _IGNORE_MARKERS[0]:
        return None, "ignored"
    obj = bpy.data.objects.get(marker_name(part, side))
    if obj is None:
        return None, None
    if obj.get("mcd_marker") == "baked":
        return None, "baked"
    par = getattr(obj, "parent", None)
    if (par is None or getattr(par, "type", "") != "ARMATURE"
            or obj.parent_type != "BONE" or not obj.parent_bone):
        return None, "unbound"
    return obj, None


def marker_dir(obj: Any) -> Vector:
    return (obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, 1.0))).normalized()


# ---------------------------------------------------------------------------
# 逐帧几何推导（每帧一个 dict，聚合在 probe() 里做）

def _hand_frame(armature: Any, side: str) -> dict | None:
    """掌心/手背/手指方向。掌心优先用网格标定（刚性局部向量），否则手指几何。"""
    d = _hand_frame_fingers(armature, side)
    if d is None:
        return None
    ev = d["evidence"]
    cal = palm_calibration(armature, side)
    pb = armature.pose.bones.get(f"hand_fk.{side}")
    mesh_palm = None
    if cal and cal.get("local") is not None and pb is not None:
        rot = (armature.matrix_world @ pb.matrix).to_quaternion()
        mesh_palm = (rot @ cal["local"]).normalized()
        ev["finger_palm_vs_mesh_deg"] = round(_angle_deg(d["palm"], mesh_palm), 1)
    mk, why = bound_marker("palm", side)
    if mk is not None:
        palm = marker_dir(mk)
        ev.update({"palm_source": "marker", "marker": mk.name,
                   "marker_bone": f"{mk.parent.name}/{mk.parent_bone}",
                   "sign_ambiguous": False})
        if mesh_palm is not None:
            ev["marker_vs_mesh_deg"] = round(_angle_deg(palm, mesh_palm), 1)
        d["palm"], d["back"] = palm, -palm
        d["confidence"], d["alternatives"] = 1.0, []
        return d
    if why == "unbound":
        ev["marker_ignored"] = marker_name("palm", side)
    if mesh_palm is not None:
        d["palm"], d["back"] = mesh_palm, -mesh_palm
        d["confidence"] = 0.6 if cal.get("sign_conflict") else 1.0
        d["alternatives"] = []
        ev.update({"palm_source": "mesh", "mesh_faces": cal["faces"],
                   "thumb_side_mm": cal["thumb_mm"], "sign_ambiguous": False})
        if cal.get("sign_conflict"):
            ev["sign_conflict"] = True
        return d
    ev["palm_source"] = "fingers"
    if cal and cal.get("reason"):
        ev["mesh_calibration"] = cal["reason"]
    return d


def _hand_frame_fingers(armature: Any, side: str) -> dict | None:
    """手指几何版：手指弯曲向量只能指向掌心侧 → 定号，无需分左右（网格标定的兜底）。"""
    seg = {}   # finger -> (root, j1, j2, tip) 世界点
    for finger, stem in _FINGER_STEMS.items():
        b1 = armature.pose.bones.get(f"{stem}.01.{side}")
        b2 = armature.pose.bones.get(f"{stem}.02.{side}")
        b3 = armature.pose.bones.get(f"{stem}.03.{side}")
        if b1 is None or b2 is None or b3 is None:
            continue
        seg[finger] = (
            armature.matrix_world @ b1.head,
            armature.matrix_world @ b1.tail,
            armature.matrix_world @ b2.tail,
            armature.matrix_world @ b3.tail,
        )
    avail = [f for f in _PALM_FINGERS if f in seg]
    if len(avail) < 2 or "index" not in seg or "pinky" not in seg:
        return None

    finger_dirs = [_norm(seg[f][3] - seg[f][0]) for f in avail]
    finger_dirs = [d for d in finger_dirs if d is not None]
    if not finger_dirs:
        return None
    finger_dir = _norm(sum(finger_dirs, Vector((0.0, 0.0, 0.0)))) 
    knuckle = _norm(seg["pinky"][0] - seg["index"][0])
    if finger_dir is None or knuckle is None:
        return None
    # 腕→指根中心：相对 hand_fk 刚性，与掌心法线近乎垂直（实测 7°）。掌心修复的次轴用它：
    # finger_dir 在手攥紧时会倒向掌心法线（拳头上只差 24°），双轴解算的滚转就没了依据。
    wrist = _pw(armature, f"hand_fk.{side}", "head")
    roots_c = sum((seg[f][0] for f in avail), Vector((0.0, 0.0, 0.0))) / len(avail)
    hand_axis = _norm(roots_c - wrist) if wrist is not None else None
    if hand_axis is None:
        hand_axis = finger_dir
    n0 = knuckle.cross(finger_dir)
    if n0.length < _EPS:
        return None                        # 指根连线 ∥ 手指方向，病态
    n0.normalize()

    # 弯曲向量：末节指向 − 根节指向；手指铰链只能向掌心侧弯 → 指向掌心。
    # 拇指同样只朝掌心侧收拢，权重减半（它的弯平面斜一些）。
    curl = Vector((0.0, 0.0, 0.0))
    for f in avail:
        s_first = _norm(seg[f][1] - seg[f][0])
        s_last = _norm(seg[f][3] - seg[f][2])
        if s_first is not None and s_last is not None:
            curl += s_last - s_first
    thumb_curl = Vector((0.0, 0.0, 0.0))
    if "thumb" in seg:
        t_first = _norm(seg["thumb"][1] - seg["thumb"][0])
        t_last = _norm(seg["thumb"][3] - seg["thumb"][2])
        if t_first is not None and t_last is not None:
            thumb_curl = t_last - t_first
    curl_all = curl + 0.5 * thumb_curl
    # 只要垂直于手指方向的分量参与定号
    curl_perp = curl_all - finger_dir * curl_all.dot(finger_dir)
    curl_mag = curl_perp.length
    palm = Vector(n0)
    if curl_mag > 0.03:
        if palm.dot(curl_perp) < 0:
            palm = -palm
        ambiguous = False
    else:
        ambiguous = True                   # 手指全直 → 符号两边都可能

    confidence = min(1.0, curl_mag / (0.30 * max(1, len(avail))))
    if ambiguous:
        confidence = min(confidence, 0.3)
    return {
        "palm": palm, "back": -palm, "finger_dir": finger_dir,
        "knuckle": knuckle, "hand_axis": hand_axis,
        "evidence": {
            "curl_mag": round(float(curl_mag), 3),
            "fingers_used": len(avail),
            "thumb_used": "thumb" in seg,
            "sign_ambiguous": ambiguous,
        },
        "confidence": confidence,
        "alternatives": [[*(-n0)], [*n0]] if ambiguous else [],
    }


def _foot_frame(armature: Any, side: str) -> dict | None:
    """脚底法线/脚尖方向。三点定平面，小腿在脚背侧定号——空中也成立。"""
    heel = _pw(armature, f"DEF-foot.{side}", "head")
    ball = _pw(armature, f"DEF-foot.{side}", "tail")
    toe = _pw(armature, f"DEF-toe.{side}", "tail")
    knee = _pw(armature, f"shin_fk.{side}", "head")
    if heel is None or ball is None or toe is None or knee is None:
        return None
    n0 = (ball - heel).cross(toe - ball)
    if n0.length < _EPS:
        return None
    n0.normalize()
    leg = _norm(heel - knee)               # 从膝指向踝 ≈ 小腿向下
    sole = Vector(n0)
    sign_evidence = None
    if leg is not None:
        d = sole.dot(leg)                  # 脚底背离小腿 → 法线与小腿同向为正
        if abs(d) > 0.05:
            if d < 0:
                sole = -sole
            sign_evidence = abs(d)
    toe_dir = _norm(toe - heel)
    if toe_dir is None:
        return None
    confidence = 0.9 if sign_evidence else 0.4
    out = {
        "sole": sole, "instep": -sole, "toe": toe_dir,
        "evidence": {"leg_sign": (round(sign_evidence, 3)
                                 if sign_evidence else None),
                     "sole_source": "bones"},
        "confidence": confidence,
        "alternatives": [] if sign_evidence else [[*(-n0)], [*n0]],
    }
    mk, why = bound_marker("sole", side)
    if mk is not None:
        msole = marker_dir(mk)
        out["evidence"].update({"sole_source": "marker", "marker": mk.name,
                                "marker_bone": f"{mk.parent.name}/{mk.parent_bone}",
                                "marker_vs_bones_deg": round(_angle_deg(msole, sole), 1)})
        out["sole"], out["instep"] = msole, -msole
        out["confidence"], out["alternatives"] = 1.0, []
    elif why == "unbound":
        out["evidence"]["marker_ignored"] = marker_name("sole", side)
    return out


def _finger_frame(armature: Any, side: str, finger: str) -> dict | None:
    """单根手指的指向（修手指用）：owner = 该指 01 节骨。"""
    stem = _FINGER_STEMS.get(str(finger).lower())
    if stem is None:
        raise RuntimeError(
            f"未知手指 {finger!r}，可用：{sorted(_FINGER_STEMS)}")
    b1 = armature.pose.bones.get(f"{stem}.01.{side}")
    b3 = armature.pose.bones.get(f"{stem}.03.{side}")
    if b1 is None or b3 is None:
        return None
    root = armature.matrix_world @ b1.head
    tip = armature.matrix_world @ b3.tail
    d = _norm(tip - root)
    if d is None:
        return None
    return {"finger_dir": d, "_owner": f"{stem}.01.{side}",
            "confidence": 1.0, "evidence": {"finger": finger},
            "alternatives": []}


def _joint_frame(armature: Any, side: str, kind: str) -> dict | None:
    """膝/肘前：两段骨夹角的凸出方向。kind='knee'|'elbow'。"""
    if kind == "knee":
        p0 = _pw(armature, f"thigh_fk.{side}", "head")
        p1 = _pw(armature, f"thigh_fk.{side}", "tail")
        p2 = _pw(armature, f"shin_fk.{side}", "tail")
        owner = f"thigh_fk.{side}"
    else:
        p0 = _pw(armature, f"upper_arm_fk.{side}", "head")
        p1 = _pw(armature, f"upper_arm_fk.{side}", "tail")
        p2 = _pw(armature, f"forearm_fk.{side}", "tail")
        owner = f"upper_arm_fk.{side}"
    if p0 is None or p1 is None or p2 is None:
        return None
    s1, s2 = _norm(p1 - p0), _norm(p2 - p1)
    if s1 is None or s2 is None:
        return None
    bend = s1 - s2                          # |bend| = 2·sin(弯角/2)
    if bend.length < 0.02:
        return {"front": Vector(s1), "confidence": 0.0,
                "evidence": {"bend": 0.0},
                "alternatives": [], "owner": owner, "s1": s1}
    front = bend.normalized()
    confidence = min(1.0, bend.length / 0.5)
    return {"front": front, "confidence": confidence,
            "evidence": {"bend": round(float(bend.length), 3)},
            "alternatives": [], "owner": owner, "s1": s1}


def _body_forward(armature: Any, scene: Any) -> dict | None:
    """身体前方：脚尖水平投影为主；肩线×竖直轴、相机方向做交叉证据。"""
    up = Vector((0, 0, 1))
    feet = []
    for side in ("L", "R"):
        heel = _pw(armature, f"DEF-foot.{side}", "head")
        toe = _pw(armature, f"DEF-toe.{side}", "tail")
        if heel is None or toe is None:
            continue
        d = toe - heel
        d.z = 0.0
        d = _norm(d)
        if d is not None:
            feet.append(d)
    evidence = {}
    fwd = None
    if feet:
        fwd = _norm(sum(feet, Vector((0.0, 0.0, 0.0))))
        evidence["feet_count"] = len(feet)
        if len(feet) == 2:
            evidence["feet_spread_deg"] = round(_angle_deg(feet[0], feet[1]), 1)
    # 肩线交叉：角色右肩−左肩 = 右手侧；up × (R−L) = 前方（朝向 −Y、左肩 +X 时）
    sl = _pw(armature, "shoulder.L", "head")
    sr = _pw(armature, "shoulder.R", "head")
    fwd_sh = None
    if sl is not None and sr is not None:
        s_vec = _norm(sr - sl)
        if s_vec is not None:
            fwd_sh = _norm(up.cross(s_vec))
            if fwd_sh is not None:
                evidence["shoulder_fwd"] = [round(v, 3) for v in fwd_sh]
    cam = getattr(scene, "camera", None)
    fwd_cam = None
    if cam is not None:
        f = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        f.z = 0.0
        fwd_cam = _norm(f)
        if fwd_cam is not None:
            evidence["camera_fwd"] = [round(v, 3) for v in fwd_cam]
    if fwd is None:
        fwd = fwd_sh or fwd_cam
    if fwd is None:
        return None
    # 脚尖与肩线矛盾（例如转身瞬间）→ 降置信度
    conf = 0.9
    if fwd_sh is not None:
        disagree = _angle_deg(fwd, fwd_sh)
        evidence["toe_vs_shoulder_deg"] = round(disagree, 1)
        if disagree > 60:
            conf = 0.4
    if len(feet) == 2 and evidence.get("feet_spread_deg", 0) > 60:
        conf = min(conf, 0.5)
    return {"forward": fwd, "confidence": conf, "evidence": evidence,
            "alternatives": []}


# ---------------------------------------------------------------------------
# 聚合与对外入口

def _aggregate(frames_data: list[dict], key: str) -> dict:
    """跨帧聚合一个方向：均值向量 + 最大散布角。"""
    dirs = [d[key] for d in frames_data if d.get(key) is not None]
    if not dirs:
        return {}
    mean = _norm(sum(dirs, Vector((0.0, 0.0, 0.0))))
    spread = max(_angle_deg(mean, d) for d in dirs)
    return {"world_dir": [round(v, 4) for v in mean],
            "spread_deg": round(spread, 1), "n": len(dirs)}


def _resolve_toward(scene: Any, armature: Any, toward: Any,
                    owner_head: Vector | None) -> tuple[Vector | None, str]:
    """把 toward 解析成世界向量：数字三元组 / 方向词 / 空物体名。"""
    if toward is None:
        return None, ""
    if isinstance(toward, str):
        w = toward.strip()
        low = w.lower()
        if low in ("up", "+z"):
            return Vector((0, 0, 1)), "up"
        if low in ("down", "-z"):
            return Vector((0, 0, -1)), "down"
        if low == "forward":
            res = _body_forward(armature, scene)
            if res:
                return res["forward"], "forward(body)"
            return Vector((0, -1, 0)), "forward(-Y fallback)"
        if low == "camera":
            cam = getattr(scene, "camera", None)
            if cam is not None:
                f = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
                f.z = 0.0
                return _norm(f), "camera"
            return None, "camera(无相机)"
        obj = bpy.data.objects.get(w)
        if obj is not None:
            if obj.empty_display_type == "SINGLE_ARROW":
                return (obj.matrix_world.to_quaternion()
                        @ Vector((0, 0, 1))), f"object:{w}(arrow +Z)"
            if owner_head is not None:
                return _norm(obj.matrix_world.translation - owner_head), \
                    f"object:{w}(aim)"
            return _norm(obj.matrix_world.translation), f"object:{w}(pos)"
        return None, f"无法解析方向 {w!r}"
    try:
        v = Vector(toward)
        return _norm(v), "vec"
    except Exception:
        return None, f"无法解析方向 {toward!r}"


_PARTS = ("palm", "back_of_hand", "finger_dir", "knuckle", "hand_axis",
          "sole", "instep", "toe",
          "knee_front", "elbow_front", "body_forward", "bone_axis")


def probe(scene: Any, armature: Any, *, part: str, side: str | None = None,
          bone: str | None = None, finger: str | None = None,
          frame_range: Sequence[int] | None = None, toward: Any = None,
          max_frames: int = 9) -> dict:
    """解剖探头入口。返回世界方向、owner 骨局部向量、置信度、证据。

    part:
      palm / back_of_hand / finger_dir / knuckle / hand_axis   —— 需 side（hand_axis = 腕→指根，刚性）
      sole / instep / toe                          —— 需 side
      knee_front / elbow_front                     —— 需 side
      body_forward                                 —— 全身
      bone_axis                                    —— 需 bone（任意骨六根主轴）
      finger（finger_dir + finger 名）              —— 单根手指指向
    toward 可选：解析目标方向并附 err_deg（修后复测就是同一调用加 toward）。

    任务2：原版对同一组采样帧扫 4 遍（取方向 / 局部主轴 / 次轴 / toward 误差），
    每遍都 frame_set。每帧求值是确定的，所以这里一遍扫帧里把 4 样都算掉
    （≈4× 少 frame_set），输出与 _probe_slow 逐位相同（bench golden 校验）。
    唯一不能合并的情形——owner 骨在采样帧间变化——回落到 _probe_slow。
    """
    part = str(part).strip().lower()
    if part not in _PARTS and part != "finger":
        raise RuntimeError(f"未知 part {part!r}，可用：{_PARTS} + finger")
    part_in = part
    if part == "finger":
        part = "finger_dir"
    side_n = (side or "").upper() or None
    frames = _sample_frames(scene, frame_range, max_frames)
    key_map = {"palm": "palm", "back_of_hand": "back",
               "finger_dir": "finger_dir", "knuckle": "knuckle", "hand_axis": "hand_axis",
               "sole": "sole", "instep": "instep", "toe": "toe",
               "knee_front": "front", "elbow_front": "front",
               "body_forward": "forward"}
    key = None if part == "bone_axis" else key_map[part]
    sec_key = {"palm": "hand_axis", "back_of_hand": "hand_axis", "hand_axis": "palm",
               "sole": "toe", "instep": "toe",
               "knee_front": "s1", "elbow_front": "s1"}.get(part)

    frames_data = []
    owner = None
    extra = []          # per frame: (owner_used, local_key, local_sec, t2|exc)
    with preserve_scene_frame(scene):
        for f in frames:
            set_scene_frame(scene, f)
            if part in ("palm", "back_of_hand", "finger_dir", "knuckle", "hand_axis"):
                if side_n not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                if part == "finger_dir" and finger:
                    d = _finger_frame(armature, side_n, finger)
                else:
                    d = _hand_frame(armature, side_n)
                if d is not None and "_owner" not in d:
                    d["_owner"] = f"hand_fk.{side_n}"
            elif part in ("sole", "instep", "toe"):
                if side_n not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                d = _foot_frame(armature, side_n)
                if d is not None:
                    d["_owner"] = f"foot_ik.{side_n}"
            elif part in ("knee_front", "elbow_front"):
                if side_n not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                kind = "knee" if part == "knee_front" else "elbow"
                d = _joint_frame(armature, side_n, kind)
                if d is not None and d.get("owner"):
                    d["_owner"] = d["owner"]
            elif part == "body_forward":
                d = _body_forward(armature, scene)
            elif part == "bone_axis":
                if not bone:
                    raise RuntimeError("bone_axis 需要 bone=<骨名>")
                pb = armature.pose.bones.get(bone)
                if pb is None:
                    raise RuntimeError(f"骨不存在：{bone}")
                rot = (armature.matrix_world @ pb.matrix).to_quaternion()
                d = {"_axes": {k: rot @ Vector(v)
                               for k, v in _AXIS_SET.items()},
                     "_owner": bone}
            if d:
                frames_data.append((f, d))
                if d.get("_owner"):
                    owner = d["_owner"]
                # 同一帧顺手算后三遍要的量（用"到目前为止的 owner"，事后核对）
                lk = ls = t2 = None
                if owner and key:
                    if d.get(key) is not None:
                        lk = _local_of(armature, owner, d[key])
                    if sec_key and d.get(sec_key) is not None:
                        ls = _local_of(armature, owner, d[sec_key])
                if toward is not None and key and d.get(key) is not None:
                    try:
                        t2, _ = _resolve_toward(
                            scene, armature, toward,
                            _pw(armature, owner, "head") if owner else None)
                    except Exception as exc:  # noqa: BLE001 - replayed below
                        t2 = exc
                extra.append((owner, lk, ls, t2))

    if not frames_data:
        raise RuntimeError(f"{part} 所需骨骼在场景里不存在（side={side_n}）")
    if any(e[0] != owner for e in extra):
        return _probe_slow(scene, armature, part=part_in, side=side,
                           bone=bone, finger=finger, frame_range=frame_range,
                           toward=toward, max_frames=max_frames)

    out: dict[str, Any] = {"part": part, "side": side_n,
                           "frames_sampled": frames,
                           "owner_bone": owner}

    if part == "bone_axis":
        last = frames_data[-1][1]["_axes"]
        out["axes"] = {k: [round(x, 4) for x in v] for k, v in last.items()}
        out["confidence"] = 1.0
    else:
        agg = _aggregate([d for _, d in frames_data], key)
        if not agg:
            raise RuntimeError(f"{part} 在所采帧上推不出方向")
        out.update(agg)
        confs = [d.get("confidence", 0.0) for _, d in frames_data]
        out["confidence"] = round(min(confs), 2)
        out["evidence"] = dict(frames_data[0][1].get("evidence", {}))
        if out["spread_deg"] > 45:
            out["evidence"]["spread_note"] = \
                "方向随帧变化大，修复会逐帧对齐，属正常"
        alts = [d.get("alternatives") for _, d in frames_data
                if d.get("alternatives")]
        if alts:
            out["alternatives"] = alts[0]

    if owner and key:
        locals_ = [e[1] for (_f, d), e in zip(frames_data, extra)
                   if d.get(key) is not None and e[1] is not None]
        if locals_:
            lm = _norm(sum(locals_, Vector((0.0, 0.0, 0.0))))
            out["local_axis"] = [round(v, 4) for v in lm]
            out["local_spread_deg"] = round(
                max(_angle_deg(lm, v) for v in locals_), 1)
            if sec_key:
                secs = [e[2] for (_f, d), e in zip(frames_data, extra)
                        if d.get(sec_key) is not None and e[2] is not None]
                if secs:
                    sm = _norm(sum(secs, Vector((0.0, 0.0, 0.0))))
                    out["secondary_axis"] = [round(v, 4) for v in sm]
                    out["secondary_name"] = sec_key
            out["hold_pose_args"] = _hold_pose_args(part, side_n, owner, out, finger)

    if toward is not None and key:
        head_pos = _pw(armature, owner, "head") if owner else None
        tv, how = _resolve_toward(scene, armature, toward, head_pos)
        out["toward_resolved"] = [round(v, 4) for v in tv] if tv else None
        out["toward_how"] = how
        if tv is not None:
            errs = []
            for (_f, d), e in zip(frames_data, extra):
                if d.get(key) is None:
                    continue
                if isinstance(e[3], Exception):
                    raise e[3]
                if e[3] is not None:
                    errs.append(_angle_deg(d[key], e[3]))
            if errs:
                out["err_max_deg"] = round(max(errs), 1)
                out["err_mean_deg"] = round(float(np.mean(errs)), 1)
                frames_ok = [f for f, d in frames_data
                             if d.get(key) is not None]
                out["err_per_frame"] = [
                    [int(f), round(e, 1)]
                    for f, e in zip(frames_ok, errs)]
                inner = out["err_per_frame"][1:-1] \
                    if len(out["err_per_frame"]) >= 5 \
                    else out["err_per_frame"]
                if inner:
                    out["err_inner_deg"] = round(
                        max(e for _, e in inner), 1)
    return out


def _probe_slow(scene: Any, armature: Any, *, part: str, side: str | None = None,
          bone: str | None = None, finger: str | None = None,
          frame_range: Sequence[int] | None = None, toward: Any = None,
          max_frames: int = 9) -> dict:
    """原版（多遍扫帧）实现：owner 在采样帧间不一致时的兜底，也是逐位对照基准。

    解剖探头入口。返回世界方向、owner 骨局部向量、置信度、证据。

    part:
      palm / back_of_hand / finger_dir / knuckle / hand_axis   —— 需 side（hand_axis = 腕→指根，刚性）
      sole / instep / toe                          —— 需 side
      knee_front / elbow_front                     —— 需 side
      body_forward                                 —— 全身
      bone_axis                                    —— 需 bone（任意骨六根主轴）
      finger（finger_dir + finger 名）              —— 单根手指指向
    toward 可选：解析目标方向并附 err_deg（修后复测就是同一调用加 toward）。
    """
    part = str(part).strip().lower()
    if part not in _PARTS and part != "finger":
        raise RuntimeError(f"未知 part {part!r}，可用：{_PARTS} + finger")
    if part == "finger":
        part = "finger_dir"
    side = (side or "").upper() or None
    frames = _sample_frames(scene, frame_range, max_frames)

    frames_data = []
    owner = None
    with preserve_scene_frame(scene):
        for f in frames:
            set_scene_frame(scene, f)
            if part in ("palm", "back_of_hand", "finger_dir", "knuckle", "hand_axis"):
                if side not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                if part == "finger_dir" and finger:
                    d = _finger_frame(armature, side, finger)
                else:
                    d = _hand_frame(armature, side)
                if d is not None and "_owner" not in d:
                    d["_owner"] = f"hand_fk.{side}"
            elif part in ("sole", "instep", "toe"):
                if side not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                d = _foot_frame(armature, side)
                if d is not None:
                    d["_owner"] = f"foot_ik.{side}"
            elif part in ("knee_front", "elbow_front"):
                if side not in ("L", "R"):
                    raise RuntimeError(f"{part} 需要 side='L'/'R'")
                kind = "knee" if part == "knee_front" else "elbow"
                d = _joint_frame(armature, side, kind)
                if d is not None and d.get("owner"):
                    d["_owner"] = d["owner"]
            elif part == "body_forward":
                d = _body_forward(armature, scene)
            elif part == "bone_axis":
                if not bone:
                    raise RuntimeError("bone_axis 需要 bone=<骨名>")
                pb = armature.pose.bones.get(bone)
                if pb is None:
                    raise RuntimeError(f"骨不存在：{bone}")
                rot = (armature.matrix_world @ pb.matrix).to_quaternion()
                d = {"_axes": {k: rot @ Vector(v)
                               for k, v in _AXIS_SET.items()},
                     "_owner": bone}
            if d:
                frames_data.append((f, d))
                if d.get("_owner"):
                    owner = d["_owner"]

    if not frames_data:
        raise RuntimeError(f"{part} 所需骨骼在场景里不存在（side={side}）")

    out: dict[str, Any] = {"part": part, "side": side,
                           "frames_sampled": frames,
                           "owner_bone": owner}

    if part == "bone_axis":
        last = frames_data[-1][1]["_axes"]
        out["axes"] = {k: [round(x, 4) for x in v] for k, v in last.items()}
        out["confidence"] = 1.0
        key = None
    else:
        key_map = {"palm": "palm", "back_of_hand": "back",
                   "finger_dir": "finger_dir", "knuckle": "knuckle", "hand_axis": "hand_axis",
                   "sole": "sole", "instep": "instep", "toe": "toe",
                   "knee_front": "front", "elbow_front": "front",
                   "body_forward": "forward"}
        key = key_map[part]
        agg = _aggregate([d for _, d in frames_data], key)
        if not agg:
            raise RuntimeError(f"{part} 在所采帧上推不出方向")
        out.update(agg)
        confs = [d.get("confidence", 0.0) for _, d in frames_data]
        out["confidence"] = round(min(confs), 2)
        out["evidence"] = dict(frames_data[0][1].get("evidence", {}))
        # spread 只报告不扣分：方向随帧变化≠推导不可信（手在动很正常）
        if out["spread_deg"] > 45:
            out["evidence"]["spread_note"] = \
                "方向随帧变化大，修复会逐帧对齐，属正常"
        alts = [d.get("alternatives") for _, d in frames_data
                if d.get("alternatives")]
        if alts:
            out["alternatives"] = alts[0]

    # owner 骨局部向量：逐帧算，取均值；附散布（解剖相对控制骨是否稳）
    if owner and key:
        locals_ = []
        with preserve_scene_frame(scene):
            for f, d in frames_data:
                if d.get(key) is None:
                    continue
                set_scene_frame(scene, f)
                lv = _local_of(armature, owner, d[key])
                if lv is not None:
                    locals_.append(lv)
        if locals_:
            lm = _norm(sum(locals_, Vector((0.0, 0.0, 0.0))))
            out["local_axis"] = [round(v, 4) for v in lm]
            out["local_spread_deg"] = round(
                max(_angle_deg(lm, v) for v in locals_), 1)
            # 次轴：手的 sec=手指方向；脚 sec=脚尖；膝肘 sec=上段骨方向
            sec_key = {"palm": "hand_axis", "back_of_hand": "hand_axis", "hand_axis": "palm",
                       "sole": "toe", "instep": "toe",
                       "knee_front": "s1", "elbow_front": "s1"}.get(part)
            if sec_key:
                secs = []
                with preserve_scene_frame(scene):
                    for f, d in frames_data:
                        if d.get(sec_key) is None:
                            continue
                        set_scene_frame(scene, f)
                        lv = _local_of(armature, owner, d[sec_key])
                        if lv is not None:
                            secs.append(lv)
                if secs:
                    sm = _norm(sum(secs, Vector((0.0, 0.0, 0.0))))
                    out["secondary_axis"] = [round(v, 4) for v in sm]
                    out["secondary_name"] = sec_key
            out["hold_pose_args"] = _hold_pose_args(part, side, owner, out, finger)

    # toward：解析目标 + 误差角（修后复测同一调用）
    if toward is not None and key:
        head_pos = _pw(armature, owner, "head") if owner else None
        tv, how = _resolve_toward(scene, armature, toward, head_pos)
        out["toward_resolved"] = [round(v, 4) for v in tv] if tv else None
        out["toward_how"] = how
        if tv is not None:
            errs = []
            with preserve_scene_frame(scene):
                for f, d in frames_data:
                    if d.get(key) is None:
                        continue
                    set_scene_frame(scene, f)
                    # toward=aim 时方向随帧变
                    t2, _ = _resolve_toward(
                        scene, armature, toward,
                        _pw(armature, owner, "head") if owner else None)
                    if t2 is not None:
                        errs.append(_angle_deg(d[key], t2))
            if errs:
                out["err_max_deg"] = round(max(errs), 1)
                out["err_mean_deg"] = round(float(np.mean(errs)), 1)
                frames_ok = [f for f, d in frames_data
                             if d.get(key) is not None]
                out["err_per_frame"] = [
                    [int(f), round(e, 1)]
                    for f, e in zip(frames_ok, errs)]
                # 中段误差：strip 两端有 taper，边缘帧保留原姿态是设计行为，
                # 复测报告应以中段为准（>=5 个采样点时掐头去尾）
                inner = out["err_per_frame"][1:-1] \
                    if len(out["err_per_frame"]) >= 5 \
                    else out["err_per_frame"]
                if inner:
                    out["err_inner_deg"] = round(
                        max(e for _, e in inner), 1)
    return out


_AXIS_SET = {"+X": (1, 0, 0), "-X": (-1, 0, 0),
             "+Y": (0, 1, 0), "-Y": (0, -1, 0),
             "+Z": (0, 0, 1), "-Z": (0, 0, -1)}

_FRAME_KEYS = {"palm": "palm", "back_of_hand": "back",
               "finger_dir": "finger_dir", "knuckle": "knuckle", "hand_axis": "hand_axis",
               "sole": "sole", "instep": "instep", "toe": "toe",
               "knee_front": "front", "elbow_front": "front",
               "body_forward": "forward"}


# probe 返回的 hold_pose_args = 推荐写法（与剧本 30 的表一致）：逐帧 probe 主轴 + 次轴
# 掌心/手背的次轴是 hand_axis（腕→指根，刚性、⊥掌心）而不是 finger_dir：手攥紧时 finger_dir
# 倒向掌心法线，双轴解算的滚转失去依据（2026-10-04 掌心网格标定后发现）。
_HOLD_AXES = {"palm": ("palm", "hand_axis"), "back_of_hand": ("back_of_hand", "hand_axis"),
              "finger_dir": ("finger_dir", "palm"), "knuckle": ("knuckle", "palm"),
              "hand_axis": ("hand_axis", "palm"),
              "sole": ("sole", "toe"), "instep": ("instep", "toe"), "toe": ("toe", "sole"),
              "knee_front": ("knee_front", None), "elbow_front": ("elbow_front", None)}


def _hold_pose_args(part, side, owner, out, finger=None) -> dict:
    """"可直接展开给 hold_pose"的参数必须是推荐写法：逐帧 "probe:<part>.<side>" 轴。

    以前给的是全段平均的固定局部轴——解剖方向相对控制骨随帧变（手指实测散布 ~70°），
    均值轴对齐后每帧留几十度残差；照抄返回值的弱模型会踩这个坑（sonnet 第三轮指出）。
    单根手指（finger=）/ bone_axis / body_forward 没有对应的 probe 轴，仍给均值轴。"""
    spec = _HOLD_AXES.get(part) if (side in ("L", "R") and not finger) else None
    if spec is None:
        args = {"bones": [owner], "world_axis": out["local_axis"]}
        if out.get("secondary_axis"):
            args["secondary_axis"] = out["secondary_axis"]
        return args
    main, sec = spec
    args = {"bones": [owner], "world_axis": f"probe:{main}.{side}"}
    if sec:
        args["secondary_axis"] = f"probe:{sec}.{side}"
    elif out.get("secondary_axis"):
        args["secondary_axis"] = out["secondary_axis"]       # 膝/肘：次轴用探出的局部向量
    return args


def frame_probe_fn(part: str, side: str | None = None):
    """逐帧解剖方向函数：set_scene_frame 之后调，返回该帧的世界 Vector。

    hold_pose 的 "probe:<part>.<side>" 轴走这里——解剖方向相对控制骨随帧
    变化（手指有自己的动画），均值轴会留几十度残差，必须逐帧现推。
    """
    part = str(part).strip().lower()
    if part not in _FRAME_KEYS:
        raise RuntimeError(
            f"probe 轴不支持 {part!r}，可用：{sorted(_FRAME_KEYS)}")
    key = _FRAME_KEYS[part]
    side = (side or "").upper() or None

    def fn(armature: Any, scene: Any) -> Vector | None:
        if part in ("palm", "back_of_hand", "finger_dir", "knuckle", "hand_axis"):
            d = _hand_frame(armature, side)
        elif part in ("sole", "instep", "toe"):
            d = _foot_frame(armature, side)
        elif part == "knee_front":
            d = _joint_frame(armature, side, "knee")
        elif part == "elbow_front":
            d = _joint_frame(armature, side, "elbow")
        else:
            d = _body_forward(armature, scene)
        return d.get(key) if d else None
    return fn
