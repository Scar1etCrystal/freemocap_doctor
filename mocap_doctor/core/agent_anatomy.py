"""语义解剖探头：从实时场景几何推导解剖学方向，替代"猜局部轴"。

为什么需要这一层：修复意图是语义的（"手心朝前"），而执行器吃的是骨骼局部
轴。以前哪根局部轴对应掌心、符号是正还是负全靠猜，验证又用同一个假设
自证——两次掌心修复失败都是这个模式。本模块从几何事实推导：

- 掌心：四指指根连线 × 手指指向 定掌平面；手指只能朝掌心侧弯曲，用各指
  末节弯曲向量定号（左右手不用特判；手指完全伸直时定不了号 → 低置信度，
  由调用方走"两个候选"或"问用户摆箭头"路径）。
- 脚底：脚跟/前掌/脚尖三点定平面，小腿在脚背侧定号（空中同样成立）。
- 膝/肘前：大小两段骨的夹角方向即关节凸出方向。
- 身体前方：脚尖水平投影为主，肩线×竖直轴、相机方向交叉验证。
- 每个返回值附带 owner 骨上的**精确局部向量**（喂给 hold_pose.world_axis）
  与次轴（喂给 secondary_axis 双轴解算），以及数值证据和跨帧一致性。

所有方向都在世界空间推导，再反算成控制骨局部向量——骨架约定（Rigify
轴向、左右手镜像）完全不用关心。
"""

from __future__ import annotations

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
# 逐帧几何推导（每帧一个 dict，聚合在 probe() 里做）

def _hand_frame(armature: Any, side: str) -> dict | None:
    """掌心/手背/手指方向。手指弯曲向量只能指向掌心侧 → 定号，无需分左右。"""
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
        "knuckle": knuckle,
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
    return {
        "sole": sole, "instep": -sole, "toe": toe_dir,
        "evidence": {"leg_sign": (round(sign_evidence, 3)
                                 if sign_evidence else None)},
        "confidence": confidence,
        "alternatives": [] if sign_evidence else [[*(-n0)], [*n0]],
    }


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


_PARTS = ("palm", "back_of_hand", "finger_dir", "knuckle",
          "sole", "instep", "toe",
          "knee_front", "elbow_front", "body_forward", "bone_axis")


def probe(scene: Any, armature: Any, *, part: str, side: str | None = None,
          bone: str | None = None, finger: str | None = None,
          frame_range: Sequence[int] | None = None, toward: Any = None,
          max_frames: int = 9) -> dict:
    """解剖探头入口。返回世界方向、owner 骨局部向量、置信度、证据。

    part:
      palm / back_of_hand / finger_dir / knuckle   —— 需 side
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
            if part in ("palm", "back_of_hand", "finger_dir", "knuckle"):
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
                   "finger_dir": "finger_dir", "knuckle": "knuckle",
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
            sec_key = {"palm": "finger_dir", "back_of_hand": "finger_dir",
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
            out["hold_pose_args"] = {"bones": [owner],
                                     "world_axis": out["local_axis"]}
            if out.get("secondary_axis"):
                out["hold_pose_args"]["secondary_axis"] = out["secondary_axis"]

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
               "finger_dir": "finger_dir", "knuckle": "knuckle",
               "sole": "sole", "instep": "instep", "toe": "toe",
               "knee_front": "front", "elbow_front": "front",
               "body_forward": "forward"}


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
        if part in ("palm", "back_of_hand", "finger_dir", "knuckle"):
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
