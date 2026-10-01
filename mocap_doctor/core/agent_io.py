"""Glue: live scene + annotation channels + bake cache → DataStore.

This is the only layer that knows about Blender objects, the fixed source
profiles, and the annotation channel constants.  Everything downstream
(signals, queries, accent methods) consumes plain dicts / numpy arrays.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .. import annotation
from ..presets import resolve_source_profile
from . import agent_bake, agent_query, agent_signals

# extra roles sampled when the rig carries them (SMPL names shown; the role
# list is what's stable for signal names, the suffix differs per frontend)
_EXTRA_ROLES = (
    ("left_hip", "L_Hip"),
    ("right_hip", "R_Hip"),
    ("left_knee", "L_Knee"),
    ("right_knee", "R_Knee"),
    ("spine1", "Spine1"),
    ("spine2", "Spine2"),
    ("spine3", "Spine3"),
    ("neck", "Neck"),
    ("head", "Head"),
)

# 手指三节指骨（SMPL 后缀 L_Index1..3 等），信号层聚合成 finger.L.index.*
_FINGERS = ("Index", "Middle", "Ring", "Pinky", "Thumb")
_FINGER_ROLES = tuple(
    (f"finger_{side.lower()}_{name.lower()}{i}", f"{side}_{name}{i}")
    for side in ("L", "R") for name in _FINGERS for i in (1, 2, 3)
)


def source_bake_spec(
    armature: Any,
    settings: Any,
) -> dict[str, Any]:
    """Resolve this source rig into a bake spec {bones, points} for agent_bake."""
    maps = resolve_source_profile(
        armature, getattr(settings, "source_profile", "AUTO")
    )
    if maps is None:
        raise RuntimeError("无法识别源骨架（既不是 FreeMoCap 也没有 GVHMR 前缀）")
    bones = dict(maps["bones"])
    prefix = maps.get("prefix")
    existing = {b.name for b in armature.data.bones}
    if prefix:
        for role, suffix in _EXTRA_ROLES + _FINGER_ROLES:
            name = f"{prefix}_{suffix}"
            if name in existing:
                bones[role] = name
    points = {}
    # foot_points per side: (heel-ish, ball-ish, toe-ish) in order
    labels = ("heel", "ball", "toe")
    for side in ("L", "R"):
        foot_pts = maps.get("foot_points", {}).get(side, ())
        for idx, (bone_name, point) in enumerate(foot_pts[:3]):
            points[f"foot.{side}.{labels[idx]}"] = (bone_name, point)
    # fingertip points for direction/up_err signals
    for side in ("L", "R"):
        for name in _FINGERS:
            for i in (1, 3):   # 指根(joint1 head) 与 指尖(joint3 tail)
                role = f"finger_{side.lower()}_{name.lower()}{i}"
                if role in bones:
                    label = "root" if i == 1 else "tip"
                    points[f"finger.{side}.{name.lower()}.{label}"] = (
                        bones[role], "head" if i == 1 else "tail")
    return {"bones": bones, "points": points, "maps": maps}


def scene_intervals(scene: Any) -> dict[str, list]:
    """Pull the wizard's reliable ranges into agent interval items."""

    def _items(channel):
        return [
            {"id": i, "start": a, "end": b}
            for i, (a, b) in enumerate(
                annotation.get_channel_ranges(scene, channel)
            )
        ]

    return {
        "contact.L": _items(annotation.CHANNEL_FOOT_L_EFFECTIVE),
        "contact.R": _items(annotation.CHANNEL_FOOT_R_EFFECTIVE),
        "air": _items(annotation.CHANNEL_AIR),
        "jitter.L": _items(annotation.CHANNEL_HAND_L_MANUAL),
        "jitter.R": _items(annotation.CHANNEL_HAND_R_MANUAL),
    }


def build_store_for_scene(
    scene: Any,
    armature: Any,
    settings: Any,
    *,
    data_dir: str | Path | None = None,
    use_cache: bool = True,
    tag: str = "",
    raw_quat: Mapping[str, Any] | None = None,
) -> agent_query.DataStore:
    """Bake (or load cached) the source rig and assemble the query store."""

    spec = source_bake_spec(armature, settings)
    start = int(getattr(settings, "mocap_frame_start", 0) or 0) or None
    end = int(getattr(settings, "mocap_frame_end", 0) or 0) or None

    bake = None
    path = None
    if data_dir and use_cache:
        path = agent_bake.bake_cache_path(
            data_dir, getattr(armature, "name", "armature"),
            start or scene.frame_start, end or scene.frame_end, tag=tag,
        )
        bake = agent_bake.load_bake(path)
    if bake is None:
        bake = agent_bake.bake_bone_samples(
            scene, armature, spec["bones"], spec["points"], start, end
        )
        if path is not None:
            agent_bake.save_bake(path, bake)

    floor_z = float(getattr(settings, "source_floor_z", 0.0) or 0.0)
    interval_masks = scene_intervals(scene)
    signals = agent_signals.compute_signals(
        bake, floor_z=floor_z, intervals=interval_masks, raw_quat=raw_quat
    )
    # query-side intervals = the same items (signal masks mirror them)
    store = agent_query.build_store(
        signals,
        bake["frames"],
        intervals=interval_masks,
        positions=bake["pos"],
        joint_basis=bake.get("basis"),
        bone_roles=dict(spec["bones"]),
        fps=float(scene.render.fps) / float(scene.render.fps_base or 1.0),
        floor_z=floor_z,
    )
    store.bake_missing = bake.get("missing_bones", [])
    store.bake = bake          # 写工具（apply_exemplar/world_dir）要原始矩阵
    store.spec = spec
    return store
