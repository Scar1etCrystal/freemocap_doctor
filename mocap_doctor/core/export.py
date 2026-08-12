"""Final MMD/VMD animation preparation without saving or exporting files."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .animation import (
    bone_path,
    cache_fcurve_values,
    clear_object_transform_animation,
    current_view_layer,
    ensure_action,
    ensure_fcurve,
    fcurves_for_bone,
    get_action,
    get_fcurve,
    keyframe_map,
    preserve_scene_frame,
    remove_fcurves_for_bone,
    resolve_frame_range,
    set_fcurve_value,
    set_scene_frame,
    update_action,
)


TETO_LEG_FK_BONES = (
    "足.L",
    "ひざ.L",
    "足首.L",
    "足.R",
    "ひざ.R",
    "足首.R",
)


def bake_global_correction_to_all_parent(
    scene: Any,
    armature: Any,
    correction: Any,
    *,
    action: Any | None = None,
    bone_name: str = "全ての親",
    frame_start: int | None = None,
    frame_end: int | None = None,
    reset_correction: bool = True,
) -> dict[str, Any]:
    """Bake the evaluated root world motion after removing the outer Empty."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"MMD root bone not found: {bone_name}")
    active_action = get_action(armature, required=False)
    if action is not None and active_action is not action:
        raise RuntimeError("the supplied Action is not active on the MMD armature")
    action = action or active_action or ensure_action(
        armature, "mocap_doctor_all_parent_baked"
    )

    root_world_matrices: dict[int, Any] = {}
    view_layer = current_view_layer()
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            root_world_matrices[frame] = (
                armature.matrix_world @ pose_bone.matrix
            ).copy()

    removed_correction_curves = 0
    if reset_correction:
        removed_correction_curves = clear_object_transform_animation(correction)

    # Convert the cached visual result into channels under the armature's new
    # (normally correction-free) world matrix.  Cache every result before
    # touching the old root curves so later frames cannot see partial writes.
    locations: dict[int, tuple[float, float, float]] = {}
    rotations: dict[int, tuple[float, float, float]] = {}
    compatible_euler = None
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            target_pose_matrix = (
                armature.matrix_world.inverted_safe() @ root_world_matrices[frame]
            )
            conversion = {}
            if pose_bone.parent is not None:
                conversion["parent_matrix"] = pose_bone.parent.matrix.copy()
                conversion["parent_matrix_local"] = pose_bone.parent.bone.matrix_local.copy()
            basis_matrix = pose_bone.bone.convert_local_to_pose(
                target_pose_matrix,
                pose_bone.bone.matrix_local,
                invert=True,
                **conversion,
            )
            location, rotation, _scale = basis_matrix.decompose()
            euler = (
                rotation.to_euler("XYZ")
                if compatible_euler is None
                else rotation.to_euler("XYZ", compatible_euler)
            )
            compatible_euler = euler.copy()
            locations[frame] = (
                float(location.x),
                float(location.y),
                float(location.z),
            )
            rotations[frame] = (
                float(euler.x),
                float(euler.y),
                float(euler.z),
            )

    pose_bone.rotation_mode = "XYZ"
    location_path = bone_path(bone_name, "location")
    rotation_path = bone_path(bone_name, "rotation_euler")
    # This is a dense visual bake.  Rebuild location as well as rotation
    # instead of trying to mutate the previously evaluated root curves in
    # place; old keys/modifiers must not survive and override the cached
    # combined world motion.
    conflicting_channel_paths = {
        location_path,
        rotation_path,
        bone_path(bone_name, "rotation_quaternion"),
        bone_path(bone_name, "rotation_axis_angle"),
    }
    for fcurve in list(action.fcurves):
        if fcurve.data_path in conflicting_channel_paths:
            action.fcurves.remove(fcurve)

    location_curves = [
        ensure_fcurve(action, location_path, axis, group=bone_name)
        for axis in range(3)
    ]
    rotation_curves = [
        ensure_fcurve(action, rotation_path, axis, group=bone_name)
        for axis in range(3)
    ]
    caches = [keyframe_map(curve) for curve in (*location_curves, *rotation_curves)]
    for frame in range(start, end + 1):
        for axis, curve in enumerate(location_curves):
            set_fcurve_value(
                curve,
                frame,
                locations[frame][axis],
                cache=caches[axis],
            )
        for axis, curve in enumerate(rotation_curves):
            set_fcurve_value(
                curve,
                frame,
                rotations[frame][axis],
                cache=caches[3 + axis],
            )
    update_action(action)
    return {
        "operation": "bake_global_correction_to_all_parent",
        "frame_range": [start, end],
        "armature": armature.name,
        "correction": correction.name,
        "bone": bone_name,
        "frames_keyed": end - start + 1,
        "values_written": (end - start + 1) * 6,
        "reset_correction": bool(reset_correction),
        "removed_correction_curves": removed_correction_curves,
    }


def remove_bone_animation_curves(
    action: Any,
    bone_names: Sequence[str],
) -> dict[str, Any]:
    """Remove every F-Curve belonging to each exact pose-bone name."""

    removed_by_bone: dict[str, int] = {}
    for bone_name in bone_names:
        removed_by_bone[str(bone_name)] = remove_fcurves_for_bone(
            action, str(bone_name)
        )
    return {
        "operation": "remove_bone_animation_curves",
        "bones": [str(name) for name in bone_names],
        "removed_by_bone": removed_by_bone,
        "removed_fcurve_count": sum(removed_by_bone.values()),
    }


def remove_teto_leg_fk_curves(
    action: Any,
    *,
    bone_names: Sequence[str] = TETO_LEG_FK_BONES,
) -> dict[str, Any]:
    """Delete all animation curves for the six FK leg bones."""

    result = remove_bone_animation_curves(action, bone_names)
    result["operation"] = "remove_teto_leg_fk_curves"
    return result


def summarize_bone_curves(
    action: Any,
    bone_names: Sequence[str],
) -> dict[str, Any]:
    """Return curve/key counts used by post-bake export validation."""

    bones: dict[str, dict[str, int]] = {}
    for bone_name in bone_names:
        curves = fcurves_for_bone(action, bone_name)
        bones[bone_name] = {
            "fcurve_count": len(curves),
            "keyframe_count": sum(len(curve.keyframe_points) for curve in curves),
        }
    return {
        "operation": "summarize_bone_curves",
        "bones": bones,
        "all_have_curves": bool(bones)
        and all(item["fcurve_count"] > 0 for item in bones.values()),
    }


def apply_vmd_floor_z_offset(
    scene: Any,
    armature: Any,
    *,
    action: Any | None = None,
    bone_name: str = "全ての親",
    z_offset: float = -0.0257,
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[str, Any]:
    """Add a constant Z offset to an MMD root bone over the scene window."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"MMD floor-offset bone not found: {bone_name}")
    active_action = get_action(armature, required=False)
    if action is not None and active_action is not action:
        raise RuntimeError("the supplied Action is not active on the MMD armature")
    action = action or active_action or ensure_action(armature, "mocap_doctor_floor_z")

    data_path = bone_path(bone_name, "location")
    z_curve = get_fcurve(action, data_path, 2)
    if z_curve is not None:
        original = cache_fcurve_values(z_curve, start, end)
    else:
        original: dict[int, float] = {}
        view_layer = current_view_layer()
        with preserve_scene_frame(scene, view_layer):
            for frame in range(start, end + 1):
                set_scene_frame(scene, frame, view_layer)
                original[frame] = float(pose_bone.location.z)
        z_curve = ensure_fcurve(action, data_path, 2, group=bone_name)

    cache = keyframe_map(z_curve)
    for frame in range(start, end + 1):
        set_fcurve_value(
            z_curve,
            frame,
            original[frame] + float(z_offset),
            cache=cache,
        )
    z_curve.update()
    return {
        "operation": "apply_vmd_floor_z_offset",
        "frame_range": [start, end],
        "bone": bone_name,
        "z_offset": float(z_offset),
        "frames_keyed": end - start + 1,
    }
