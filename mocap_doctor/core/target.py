"""Validated repairs for the arue Teto model and its MMR control rig."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
import statistics
from typing import Any

try:
    import bpy  # type: ignore
    from mathutils import Euler  # type: ignore
except ImportError:  # pragma: no cover - module is executed inside Blender.
    bpy = None
    Euler = None

from .animation import (
    EPSILON,
    bone_path,
    cache_fcurve_values,
    current_view_layer,
    ensure_action,
    ensure_fcurve,
    get_action,
    get_fcurve,
    get_pose_quaternion,
    insert_pose_rotation_key,
    keyframe_map,
    limit_frame_delta,
    pose_bone_world_location,
    preserve_scene_frame,
    resolve_frame_range,
    set_fcurve_value,
    set_linear_for_paths,
    set_pose_quaternion,
    set_scene_frame,
    smooth_frame_values,
    update_action,
)
from .ranges import normalize_ranges


DEFAULT_FOOT_IK = {"L": "foot_ik.L", "R": "foot_ik.R"}
DEFAULT_EXCLUDED_MESH_KEYWORDS = (
    "ground",
    "plane",
    "video",
    "VID",
    "rigid",
    "Rigid",
    "joints",
    "Joint",
    "Camera",
    "Light",
)


def ensure_global_correction_empty(
    name: str = "teto_global_correction",
    *,
    collection: Any | None = None,
) -> Any:
    """Find or create the outer correction Empty; no file is saved."""

    if bpy is None:
        raise RuntimeError("global correction must run inside Blender")
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return existing
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.25
    (collection or bpy.context.collection).objects.link(empty)
    return empty


def _parent_keep_world(child: Any, parent: Any) -> None:
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = world


def apply_global_correction(
    model_root: Any,
    rig: Any,
    correction: Any,
    *,
    rotation_degrees: Sequence[float] = (-4.2, 3.7, 0.0),
) -> dict[str, Any]:
    """Parent Teto and MMR under one Empty, then apply the tested correction."""

    if len(rotation_degrees) != 3:
        raise ValueError("rotation_degrees must contain X, Y, and Z")
    children = (model_root, rig)
    world_matrices = {child.name: child.matrix_world.copy() for child in children}

    # Establish a neutral parent while preserving each child's current world pose.
    correction.location = (0.0, 0.0, 0.0)
    correction.rotation_euler = (0.0, 0.0, 0.0)
    correction.scale = (1.0, 1.0, 1.0)
    for child in children:
        if child.parent != correction:
            _parent_keep_world(child, correction)
        child.matrix_world = world_matrices[child.name]

    radians = tuple(math.radians(float(value)) for value in rotation_degrees)
    correction.rotation_mode = "XYZ"
    correction.rotation_euler = radians
    return {
        "operation": "apply_teto_global_correction",
        "model_root": model_root.name,
        "rig": rig.name,
        "correction": correction.name,
        "rotation_degrees": [float(value) for value in rotation_degrees],
    }


def _lerp_angle(current: float, target: float, strength: float) -> float:
    difference = (target - current + math.pi) % (2.0 * math.pi) - math.pi
    return current + difference * strength


def damp_foot_ik_tilt(
    scene: Any,
    rig: Any,
    action: Any,
    *,
    foot_bones: Sequence[str] = ("foot_ik.L", "foot_ik.R"),
    frame_start: int | None = None,
    frame_end: int | None = None,
    reference_frame: int | None = None,
    strength: float = 0.65,
    damp_axes: Sequence[bool] = (True, True, False),
) -> dict[str, Any]:
    """Dampen foot pitch/roll toward a reference while preserving yaw."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    reference = start if reference_frame is None else int(reference_frame)
    if not start <= reference <= end:
        raise ValueError(f"reference frame {reference} is outside {start}-{end}")
    strength = float(strength)
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be between 0 and 1")
    if len(damp_axes) != 3:
        raise ValueError("damp_axes must contain X, Y, and Z flags")
    if get_action(rig) is not action:
        raise RuntimeError("the supplied Action is not active on the MMR rig")
    if Euler is None:
        raise RuntimeError("foot IK tilt repair must run inside Blender")

    valid = [bone for bone in foot_bones if rig.pose.bones.get(bone) is not None]
    missing = [bone for bone in foot_bones if bone not in valid]
    if not valid:
        raise RuntimeError("no target foot IK bones were found")

    samples: dict[str, dict[int, tuple[float, float, float]]] = {
        bone: {} for bone in valid
    }
    view_layer = current_view_layer()
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            for bone_name in valid:
                euler = get_pose_quaternion(
                    rig.pose.bones[bone_name]
                ).to_euler("XYZ")
                samples[bone_name][frame] = (
                    float(euler.x),
                    float(euler.y),
                    float(euler.z),
                )

        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            for bone_name in valid:
                current = samples[bone_name][frame]
                target = samples[bone_name][reference]
                values = tuple(
                    _lerp_angle(current[index], target[index], strength)
                    if bool(damp_axes[index])
                    else current[index]
                    for index in range(3)
                )
                pose_bone = rig.pose.bones[bone_name]
                set_pose_quaternion(
                    pose_bone,
                    Euler(values, "XYZ").to_quaternion(),
                )
                insert_pose_rotation_key(pose_bone, frame)

    for bone_name in valid:
        set_linear_for_paths(
            action,
            (
                bone_path(bone_name, "rotation_quaternion"),
                bone_path(bone_name, "rotation_euler"),
                bone_path(bone_name, "rotation_axis_angle"),
            ),
        )
    return {
        "operation": "damp_teto_foot_ik_tilt",
        "frame_range": [start, end],
        "reference_frame": reference,
        "strength": strength,
        "damp_axes": [bool(value) for value in damp_axes],
        "changed_bones": valid,
        "missing_bones": missing,
        "frames_keyed": (end - start + 1) * len(valid),
    }


def _has_excluded_keyword(obj: Any, keywords: Sequence[str]) -> bool:
    current = obj
    while current is not None:
        if any(keyword in current.name for keyword in keywords):
            return True
        current = current.parent
    return False


def collect_target_meshes(
    model_root: Any,
    *,
    visible_only: bool = True,
    excluded_keywords: Sequence[str] = DEFAULT_EXCLUDED_MESH_KEYWORDS,
) -> list[Any]:
    objects = [model_root, *list(model_root.children_recursive)]
    return [
        obj
        for obj in objects
        if obj.type == "MESH"
        and (not visible_only or obj.visible_get())
        and not _has_excluded_keyword(obj, excluded_keywords)
        and obj.data is not None
        and len(obj.data.vertices) > 0
    ]


def _evaluated_mesh_min_z(
    obj: Any,
    depsgraph: Any,
    vertex_sample_step: int,
) -> float | None:
    evaluated = obj.evaluated_get(depsgraph)
    mesh = None
    try:
        mesh = evaluated.to_mesh()
        if mesh is None or not mesh.vertices:
            return None
        matrix = evaluated.matrix_world
        minimum: float | None = None
        for index in range(0, len(mesh.vertices), max(1, int(vertex_sample_step))):
            z = float((matrix @ mesh.vertices[index].co).z)
            minimum = z if minimum is None else min(minimum, z)
        return minimum
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()


def repair_mesh_floor_lift_v3_safe(
    scene: Any,
    model_root: Any,
    correction: Any,
    *,
    action: Any | None = None,
    frame_start: int | None = None,
    frame_end: int | None = None,
    floor_z: float = 0.0257,
    target_clearance: float = 0.0015,
    tolerance: float = 0.004,
    max_lift_per_frame: float = 0.035,
    strength: float = 0.55,
    smooth_radius: int = 3,
    max_delta_per_frame: float = 0.0045,
    visible_only: bool = True,
    vertex_sample_step: int = 2,
    reset_existing_z_curve: bool = True,
    excluded_keywords: Sequence[str] = DEFAULT_EXCLUDED_MESH_KEYWORDS,
    worst_sample_limit: int = 100,
) -> dict[str, Any]:
    """Scan evaluated Teto meshes and add a non-accumulating correction Z."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    meshes = collect_target_meshes(
        model_root,
        visible_only=visible_only,
        excluded_keywords=excluded_keywords,
    )
    if not meshes:
        raise RuntimeError("no target meshes were found under the Teto root")

    existing_action = get_action(correction, required=False)
    if action is not None and existing_action is not action:
        raise RuntimeError("the supplied correction Action is not active")
    action = action or existing_action
    existing_curve = get_fcurve(action, "location", 2) if action else None

    view_layer = current_view_layer()
    original_z: dict[int, float] = {}
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            original_z[frame] = float(correction.location.z)

    removed_curves = 0
    if reset_existing_z_curve and existing_curve is not None:
        action.fcurves.remove(existing_curve)
        existing_curve = None
        removed_curves = 1

    depsgraph = (
        bpy.context.evaluated_depsgraph_get() if bpy is not None else None
    )
    if depsgraph is None:
        raise RuntimeError("mesh floor repair must run inside Blender")

    minimum_by_frame: dict[int, float | None] = {}
    mesh_by_frame: dict[int, str | None] = {}
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            # When a stale Z curve was removed, explicitly restore that frame's
            # cached clean baseline before evaluating the mesh.
            correction.location.z = original_z[frame]
            if view_layer is not None:
                view_layer.update()
            minimum: float | None = None
            minimum_mesh: str | None = None
            for mesh in meshes:
                value = _evaluated_mesh_min_z(
                    mesh,
                    depsgraph,
                    vertex_sample_step,
                )
                if value is not None and (minimum is None or value < minimum):
                    minimum = value
                    minimum_mesh = mesh.name
            minimum_by_frame[frame] = minimum
            mesh_by_frame[frame] = minimum_mesh

    target_z = float(floor_z) + float(target_clearance)
    raw: dict[int, float] = {}
    worst: list[dict[str, Any]] = []
    for frame in range(start, end + 1):
        minimum = minimum_by_frame[frame]
        if minimum is None:
            raw[frame] = 0.0
            continue
        penetration = target_z - minimum
        if penetration > float(tolerance):
            lift = min(penetration, float(max_lift_per_frame)) * float(strength)
            raw[frame] = lift
            worst.append(
                {
                    "frame": frame,
                    "min_z": round(minimum, 6),
                    "penetration": round(penetration, 6),
                    "raw_lift": round(lift, 6),
                    "mesh": mesh_by_frame[frame],
                }
            )
        else:
            raw[frame] = 0.0

    smoothed = smooth_frame_values(raw, start, end, int(smooth_radius))
    lift_by_frame = limit_frame_delta(
        smoothed,
        start,
        end,
        float(max_delta_per_frame),
    )
    action = action or ensure_action(correction, f"{correction.name}_floor_lift_v3")
    z_curve = ensure_fcurve(action, "location", 2)
    cache = keyframe_map(z_curve)
    changed_frames = 0
    max_lift = 0.0
    for frame in range(start, end + 1):
        lift = float(lift_by_frame[frame])
        set_fcurve_value(z_curve, frame, original_z[frame] + lift, cache=cache)
        if abs(lift) > EPSILON:
            changed_frames += 1
            max_lift = max(max_lift, lift)
    z_curve.update()
    worst.sort(key=lambda item: item["penetration"], reverse=True)
    return {
        "operation": "repair_teto_mesh_floor_lift_v3_safe",
        "frame_range": [start, end],
        "mesh_count": len(meshes),
        "meshes": [mesh.name for mesh in meshes],
        "removed_existing_z_curves": removed_curves,
        "changed_frames": changed_frames,
        "max_applied_lift": round(max_lift, 6),
        "params": {
            "floor_z": float(floor_z),
            "target_clearance": float(target_clearance),
            "tolerance": float(tolerance),
            "max_lift_per_frame": float(max_lift_per_frame),
            "strength": float(strength),
            "smooth_radius": int(smooth_radius),
            "max_delta_per_frame": float(max_delta_per_frame),
            "vertex_sample_step": int(vertex_sample_step),
        },
        "penetration_sample_count": len(worst),
        "worst_samples": worst[: int(worst_sample_limit)],
    }


def _normalize_side_ranges(
    values: Mapping[str, Sequence[Sequence[int]]],
    side: str,
    start: int,
    end: int,
) -> list[tuple[int, int]]:
    unexpected = set(values) - {"L", "R"}
    if unexpected:
        raise ValueError(f"unsupported side(s): {sorted(unexpected)!r}")
    return normalize_ranges(
        values.get(side, ()), frame_start=start, frame_end=end
    )


def analyze_foot_ik_drift(
    scene: Any,
    rig: Any,
    planted_ranges: Mapping[str, Sequence[Sequence[int]]],
    *,
    foot_bones: Mapping[str, str] = DEFAULT_FOOT_IK,
    frame_start: int | None = None,
    frame_end: int | None = None,
    trim_segment_ends: int = 2,
    min_segment_len: int = 4,
) -> dict[str, Any]:
    """Measure target foot IK world-space drift in effective planted ranges."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    results: dict[str, list[dict[str, Any]]] = {"L": [], "R": []}
    missing: list[str] = []
    view_layer = current_view_layer()
    with preserve_scene_frame(scene, view_layer):
        for side in ("L", "R"):
            bone_name = foot_bones[side]
            if rig.pose.bones.get(bone_name) is None:
                missing.append(bone_name)
                continue
            for raw_start, raw_end in _normalize_side_ranges(
                planted_ranges, side, start, end
            ):
                segment_start = raw_start + int(trim_segment_ends)
                segment_end = raw_end - int(trim_segment_ends)
                if segment_end - segment_start + 1 < int(min_segment_len):
                    continue
                positions: list[tuple[int, Any]] = []
                for frame in range(segment_start, segment_end + 1):
                    set_scene_frame(scene, frame, view_layer)
                    location = pose_bone_world_location(rig, bone_name)
                    if location is not None:
                        positions.append((frame, location))
                if not positions:
                    continue
                anchor = positions[0][1]
                maximum = 0.0
                total = 0.0
                previous = anchor
                for _, location in positions[1:]:
                    maximum = max(
                        maximum,
                        math.hypot(location.x - anchor.x, location.y - anchor.y),
                    )
                    total += math.hypot(
                        location.x - previous.x,
                        location.y - previous.y,
                    )
                    previous = location
                final = positions[-1][1]
                results[side].append(
                    {
                        "frames": [segment_start, segment_end],
                        "source_frames": [raw_start, raw_end],
                        "length": segment_end - segment_start + 1,
                        "max_drift_xy_m": round(maximum, 5),
                        "end_drift_xy_m": round(
                            math.hypot(final.x - anchor.x, final.y - anchor.y),
                            5,
                        ),
                        "total_xy_motion_m": round(total, 5),
                    }
                )
    for side in ("L", "R"):
        results[side].sort(key=lambda item: item["max_drift_xy_m"], reverse=True)
    return {
        "schema_version": "teto_foot_ik_drift_v2",
        "operation": "analyze_teto_foot_ik_drift",
        "rig": rig.name,
        "frame_range": [start, end],
        "params": {
            "trim_segment_ends": int(trim_segment_ends),
            "min_segment_len": int(min_segment_len),
        },
        "missing_bones": missing,
        "feet": results,
    }


def _choose_anchor(
    values: Mapping[int, float],
    start: int,
    end: int,
    mode: str,
) -> float:
    frames = list(range(start, end + 1))
    if mode == "first":
        return float(values[start])
    if mode == "middle":
        return float(values[frames[len(frames) // 2]])
    if mode == "median":
        return float(statistics.median(values[frame] for frame in frames))
    raise ValueError(f"unsupported anchor mode: {mode!r}")


def _apply_channel_lock(
    original: Mapping[int, float],
    output: dict[int, float],
    start: int,
    end: int,
    anchor: float,
    blend_frames: int,
) -> set[int]:
    touched: set[int] = set()
    for frame in range(start, end + 1):
        output[frame] = anchor
        touched.add(frame)
    for offset in range(1, int(blend_frames) + 1):
        before = start - offset
        after = end + offset
        factor = offset / (int(blend_frames) + 1)
        if before in original:
            output[before] = original[before] * factor + anchor * (1.0 - factor)
            touched.add(before)
        if after in original:
            output[after] = anchor * (1.0 - factor) + original[after] * factor
            touched.add(after)
    return touched


def lock_foot_ik_xy(
    scene: Any,
    rig: Any,
    action: Any,
    planted_ranges: Mapping[str, Sequence[Sequence[int]]],
    *,
    foot_bones: Mapping[str, str] = DEFAULT_FOOT_IK,
    frame_start: int | None = None,
    frame_end: int | None = None,
    trim_segment_ends: int = 2,
    min_segment_len: int = 5,
    blend_frames: int = 2,
    anchor_mode: str = "median",
    min_local_xy_range: float = 0.006,
    lock_x: bool = True,
    lock_y: bool = True,
    lock_z: bool = False,
) -> dict[str, Any]:
    """Lock only selected local location axes in effective planted ranges."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    if get_action(rig) is not action:
        raise RuntimeError("the supplied Action is not active on the MMR rig")
    if not any((lock_x, lock_y, lock_z)):
        raise ValueError("at least one lock axis must be enabled")
    if int(blend_frames) < 0:
        raise ValueError("blend_frames must be non-negative")

    repaired: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    missing: list[str] = []
    total_values_written = 0

    for side in ("L", "R"):
        bone_name = foot_bones[side]
        pose_bone = rig.pose.bones.get(bone_name)
        if pose_bone is None:
            missing.append(bone_name)
            continue
        data_path = bone_path(bone_name, "location")
        curves = [get_fcurve(action, data_path, axis) for axis in range(3)]
        originals: list[dict[int, float] | None] = [
            cache_fcurve_values(curve, start, end) if curve is not None else None
            for curve in curves
        ]
        if any(values is None for values in originals):
            missing_axes = [
                axis for axis, values in enumerate(originals) if values is None
            ]
            sampled = {axis: {} for axis in missing_axes}
            view_layer = current_view_layer()
            with preserve_scene_frame(scene, view_layer):
                for frame in range(start, end + 1):
                    set_scene_frame(scene, frame, view_layer)
                    for axis in missing_axes:
                        sampled[axis][frame] = float(pose_bone.location[axis])
            for axis in missing_axes:
                originals[axis] = sampled[axis]
        original_values = [dict(values) for values in originals]
        output_values = [dict(values) for values in original_values]
        touched_by_axis: list[set[int]] = [set(), set(), set()]

        for raw_start, raw_end in _normalize_side_ranges(
            planted_ranges, side, start, end
        ):
            segment_start = raw_start + int(trim_segment_ends)
            segment_end = raw_end - int(trim_segment_ends)
            if segment_end - segment_start + 1 < int(min_segment_len):
                skipped.append(
                    {
                        "side": side,
                        "source_frames": [raw_start, raw_end],
                        "reason": "too_short_after_trim",
                    }
                )
                continue
            x_values = [
                original_values[0][frame]
                for frame in range(segment_start, segment_end + 1)
            ]
            y_values = [
                original_values[1][frame]
                for frame in range(segment_start, segment_end + 1)
            ]
            x_range = max(x_values) - min(x_values)
            y_range = max(y_values) - min(y_values)
            xy_range = math.hypot(x_range, y_range)
            if xy_range < float(min_local_xy_range):
                skipped.append(
                    {
                        "side": side,
                        "frames": [segment_start, segment_end],
                        "reason": "below_threshold",
                        "xy_range": round(xy_range, 6),
                    }
                )
                continue

            anchors = [
                _choose_anchor(
                    original_values[axis],
                    segment_start,
                    segment_end,
                    anchor_mode,
                )
                for axis in range(3)
            ]
            enabled = (bool(lock_x), bool(lock_y), bool(lock_z))
            for axis in range(3):
                if enabled[axis]:
                    touched_by_axis[axis].update(
                        _apply_channel_lock(
                            original_values[axis],
                            output_values[axis],
                            segment_start,
                            segment_end,
                            anchors[axis],
                            int(blend_frames),
                        )
                    )
            repaired.append(
                {
                    "side": side,
                    "source_frames": [raw_start, raw_end],
                    "frames": [segment_start, segment_end],
                    "xy_range": round(xy_range, 6),
                    "anchor": [round(value, 6) for value in anchors],
                }
            )

        for axis in range(3):
            if not touched_by_axis[axis]:
                continue
            curve = curves[axis] or ensure_fcurve(
                action, data_path, axis, group=bone_name
            )
            cache = keyframe_map(curve)
            for frame in sorted(touched_by_axis[axis]):
                set_fcurve_value(
                    curve,
                    frame,
                    output_values[axis][frame],
                    cache=cache,
                )
                total_values_written += 1

    update_action(action)
    return {
        "operation": "lock_teto_foot_ik_xy",
        "frame_range": [start, end],
        "params": {
            "trim_segment_ends": int(trim_segment_ends),
            "min_segment_len": int(min_segment_len),
            "blend_frames": int(blend_frames),
            "anchor_mode": anchor_mode,
            "min_local_xy_range": float(min_local_xy_range),
            "lock_axes": [bool(lock_x), bool(lock_y), bool(lock_z)],
        },
        "repaired_count": len(repaired),
        "skipped_count": len(skipped),
        "repaired_segments": repaired,
        "skipped_segments": skipped,
        "missing_bones": missing,
        "values_written": total_values_written,
    }

