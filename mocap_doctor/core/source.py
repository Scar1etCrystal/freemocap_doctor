"""Repairs and diagnostics for the baked FreeMoCap source armature."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import math
from typing import Any

from .animation import (
    EPSILON,
    bone_path,
    cache_fcurve_values,
    current_view_layer,
    ensure_fcurve,
    get_fcurve,
    keyframe_map,
    limit_frame_delta,
    normalize_quaternion,
    pose_bone_point_world,
    pose_bone_world_location,
    preserve_scene_frame,
    resolve_frame_range,
    set_fcurve_value,
    set_scene_frame,
    smooth_frame_values,
    update_action,
)
from .ranges import frames_to_ranges, normalize_ranges


DEFAULT_ARM_CHAINS = {
    "hand.L": ("shoulder.L", "upper_arm.L", "forearm.L", "hand.L"),
    "hand.R": ("shoulder.R", "upper_arm.R", "forearm.R", "hand.R"),
}

DEFAULT_SMOOTH_BONES = (
    "pelvis",
    "spine",
    "spine.001",
    "neck",
    "shoulder.L",
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "shoulder.R",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
    "pelvis.L",
    "thigh.L",
    "shin.L",
    "foot.L",
    "pelvis.R",
    "thigh.R",
    "shin.R",
    "foot.R",
)

DEFAULT_SOURCE_CONTACT_POINTS = (
    ("foot.L", "head"),
    ("foot.L", "tail"),
    ("foot.R", "head"),
    ("foot.R", "tail"),
    ("heel.02.L", "head"),
    ("heel.02.L", "tail"),
    ("heel.02.R", "head"),
    ("heel.02.R", "tail"),
)

DEFAULT_SOURCE_BONES = {
    "hips": "pelvis",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_heel": "heel.02.L",
    "right_heel": "heel.02.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R",
}

DEFAULT_DIAGNOSTIC_THRESHOLDS = {
    "floor_tolerance_m": 0.03,
    "foot_contact_height_m": 0.05,
    "foot_slide_speed_m_per_frame": 0.02,
    "heel_slide_speed_m_per_frame": 0.018,
    "hand_jump_m_per_frame": 0.20,
    "hips_jump_m_per_frame": 0.25,
}


def _iter_hand_ranges(
    ranges: Mapping[str, Iterable[Sequence[int]]] | Iterable[Sequence[Any]],
) -> Iterable[tuple[str, int, int]]:
    if isinstance(ranges, Mapping):
        for hand_bone, intervals in ranges.items():
            for interval in intervals:
                if len(interval) != 2:
                    raise ValueError(f"bad hand range: {hand_bone!r} {interval!r}")
                yield str(hand_bone), int(interval[0]), int(interval[1])
        return

    for item in ranges:
        if len(item) != 3:
            raise ValueError(f"bad hand repair item: {item!r}")
        yield str(item[0]), int(item[1]), int(item[2])


def _interpolate_fcurve_group(
    action: Any,
    data_path: str,
    channel_count: int,
    start: int,
    end: int,
    *,
    quaternion: bool,
    interpolation: str,
) -> int:
    fcurves = [get_fcurve(action, data_path, index) for index in range(channel_count)]
    if any(fcurve is None for fcurve in fcurves):
        return 0

    previous_frame = start - 1
    next_frame = end + 1
    previous_values = [float(fcurve.evaluate(previous_frame)) for fcurve in fcurves]
    next_values = [float(fcurve.evaluate(next_frame)) for fcurve in fcurves]

    if quaternion:
        dot = sum(a * b for a, b in zip(previous_values, next_values))
        if dot < 0.0:
            next_values = [-value for value in next_values]

    key_caches = [keyframe_map(fcurve) for fcurve in fcurves]
    written = 0
    denominator = next_frame - previous_frame
    for frame in range(start, end + 1):
        factor = (frame - previous_frame) / denominator
        values = [
            a * (1.0 - factor) + b * factor
            for a, b in zip(previous_values, next_values)
        ]
        if quaternion:
            values = normalize_quaternion(values)
        for index, fcurve in enumerate(fcurves):
            set_fcurve_value(
                fcurve,
                frame,
                values[index],
                interpolation=interpolation,
                cache=key_caches[index],
            )
            written += 1
    return written


def repair_hand_chain_ranges(
    scene: Any,
    armature: Any,
    action: Any,
    ranges: Mapping[str, Iterable[Sequence[int]]] | Iterable[Sequence[Any]],
    *,
    arm_chains: Mapping[str, Sequence[str]] = DEFAULT_ARM_CHAINS,
    frame_start: int | None = None,
    frame_end: int | None = None,
    interpolation: str = "LINEAR",
) -> dict[str, Any]:
    """Interpolate manually marked bad intervals across the whole arm chain."""

    start_limit, end_limit = resolve_frame_range(scene, frame_start, frame_end)
    grouped: dict[str, list[tuple[int, int]]] = {}
    requested = 0
    for hand_bone, start, end in _iter_hand_ranges(ranges):
        requested += 1
        grouped.setdefault(hand_bone, []).append((start, end))

    normalized = {
        hand_bone: normalize_ranges(
            intervals,
            frame_start=start_limit,
            frame_end=end_limit,
        )
        for hand_bone, intervals in grouped.items()
    }

    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    changed_bones: set[str] = set()
    changed_groups = 0
    values_written = 0

    for hand_bone, intervals in normalized.items():
        chain = arm_chains.get(hand_bone)
        if not chain:
            skipped.append({"hand_bone": hand_bone, "reason": "missing_chain"})
            continue

        for start, end in intervals:
            if start <= start_limit or end >= end_limit:
                skipped.append(
                    {
                        "hand_bone": hand_bone,
                        "frames": [start, end],
                        "reason": "missing_reference_frame_inside_scene_range",
                    }
                )
                continue

            range_bones: list[str] = []
            missing_bones: list[str] = []
            for bone_name in chain:
                if armature.pose.bones.get(bone_name) is None:
                    missing_bones.append(bone_name)
                    continue

                bone_changed = False
                groups = (
                    (bone_path(bone_name, "rotation_quaternion"), 4, True),
                    (bone_path(bone_name, "rotation_euler"), 3, False),
                    (bone_path(bone_name, "location"), 3, False),
                )
                for data_path, count, is_quaternion in groups:
                    count_written = _interpolate_fcurve_group(
                        action,
                        data_path,
                        count,
                        start,
                        end,
                        quaternion=is_quaternion,
                        interpolation=interpolation,
                    )
                    if count_written:
                        values_written += count_written
                        changed_groups += 1
                        bone_changed = True
                if bone_changed:
                    changed_bones.add(bone_name)
                    range_bones.append(bone_name)

            processed.append(
                {
                    "hand_bone": hand_bone,
                    "frames": [start, end],
                    "changed_bones": range_bones,
                    "missing_bones": missing_bones,
                }
            )

    update_action(action)
    return {
        "operation": "repair_hand_chain_ranges",
        "frame_range": [start_limit, end_limit],
        "requested_range_count": requested,
        "processed_range_count": len(processed),
        "processed_ranges": processed,
        "skipped_ranges": skipped,
        "changed_bones": sorted(changed_bones),
        "fcurve_groups_changed": changed_groups,
        "values_written": values_written,
    }


def mild_rotation_smooth(
    scene: Any,
    armature: Any,
    action: Any,
    *,
    bone_names: Sequence[str] = DEFAULT_SMOOTH_BONES,
    frame_start: int | None = None,
    frame_end: int | None = None,
    radius: int = 2,
    strength: float = 0.45,
    include_hands: bool = False,
    hand_bones: Sequence[str] = ("hand.L", "hand.R", "forearm.L", "forearm.R"),
    interpolation: str = "LINEAR",
) -> dict[str, Any]:
    """Apply the validated mild Gaussian smooth to rotation channels only."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    radius = int(radius)
    strength = float(strength)
    if radius < 0:
        raise ValueError("radius must be non-negative")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be between 0 and 1")

    excluded = set() if include_hands else set(hand_bones)
    changed: list[str] = []
    missing: list[str] = []
    no_curves: list[str] = []
    values_written = 0

    for bone_name in bone_names:
        if bone_name in excluded:
            continue
        if armature.pose.bones.get(bone_name) is None:
            missing.append(bone_name)
            continue

        quaternion_path = bone_path(bone_name, "rotation_quaternion")
        curves = [get_fcurve(action, quaternion_path, index) for index in range(4)]
        quaternion = all(curve is not None for curve in curves)

        if not quaternion:
            euler_path = bone_path(bone_name, "rotation_euler")
            curves = [get_fcurve(action, euler_path, index) for index in range(3)]
            if not all(curve is not None for curve in curves):
                no_curves.append(bone_name)
                continue

        originals = [cache_fcurve_values(curve, start, end) for curve in curves]
        smoothed = [
            smooth_frame_values(values, start, end, radius)
            for values in originals
        ]
        results = [
            {
                frame: originals[index][frame] * (1.0 - strength)
                + smoothed[index][frame] * strength
                for frame in range(start, end + 1)
            }
            for index in range(len(curves))
        ]
        caches = [keyframe_map(curve) for curve in curves]

        for frame in range(start, end + 1):
            frame_values = [result[frame] for result in results]
            if quaternion:
                frame_values = normalize_quaternion(frame_values)
            for index, curve in enumerate(curves):
                set_fcurve_value(
                    curve,
                    frame,
                    frame_values[index],
                    interpolation=interpolation,
                    cache=caches[index],
                )
                values_written += 1
        changed.append(bone_name)

    update_action(action)
    return {
        "operation": "mild_rotation_smooth",
        "frame_range": [start, end],
        "radius": radius,
        "strength": strength,
        "include_hands": include_hands,
        "changed_bones": changed,
        "missing_bones": missing,
        "bones_without_rotation_curves": no_curves,
        "values_written": values_written,
    }


def repair_source_pelvis_floor_v2(
    scene: Any,
    armature: Any,
    action: Any,
    *,
    root_bone: str = "pelvis",
    contact_points: Sequence[tuple[str, str]] = DEFAULT_SOURCE_CONTACT_POINTS,
    frame_start: int | None = None,
    frame_end: int | None = None,
    floor_z: float = 0.02,
    tolerance: float = 0.012,
    target_clearance: float = 0.004,
    max_lift_per_frame: float = 0.08,
    strength: float = 0.75,
    smooth_radius: int = 2,
    max_correction_delta_per_frame: float = 0.018,
    worst_sample_limit: int = 100,
) -> dict[str, Any]:
    """Raise source pelvis Z using foot head/tail lowest-point sampling."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    root_pose_bone = armature.pose.bones.get(root_bone)
    if root_pose_bone is None:
        raise RuntimeError(f"source root bone not found: {root_bone}")

    valid_points = [
        (bone_name, point)
        for bone_name, point in contact_points
        if armature.pose.bones.get(bone_name) is not None
    ]
    missing_points = [
        [bone_name, point]
        for bone_name, point in contact_points
        if armature.pose.bones.get(bone_name) is None
    ]
    if not valid_points:
        raise RuntimeError("no valid source foot contact points were found")

    view_layer = current_view_layer()
    min_z_by_frame: dict[int, float | None] = {}
    source_by_frame: dict[int, str | None] = {}
    root_z_from_pose: dict[int, float] = {}
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            root_z_from_pose[frame] = float(root_pose_bone.location.z)
            lowest_z: float | None = None
            lowest_source: str | None = None
            for bone_name, point in valid_points:
                location = pose_bone_point_world(armature, bone_name, point)
                if location is None:
                    continue
                z = float(location.z)
                if lowest_z is None or z < lowest_z:
                    lowest_z = z
                    lowest_source = f"{bone_name}:{point}"
            min_z_by_frame[frame] = lowest_z
            source_by_frame[frame] = lowest_source

    target_z = float(floor_z) + float(target_clearance)
    raw_lift: dict[int, float] = {}
    penetration_samples: list[dict[str, Any]] = []
    for frame in range(start, end + 1):
        minimum = min_z_by_frame[frame]
        if minimum is None:
            raw_lift[frame] = 0.0
            continue
        penetration = target_z - minimum
        if penetration > float(tolerance):
            lift = min(penetration, float(max_lift_per_frame)) * float(strength)
            raw_lift[frame] = lift
            penetration_samples.append(
                {
                    "frame": frame,
                    "min_z": round(minimum, 6),
                    "penetration": round(penetration, 6),
                    "raw_lift": round(lift, 6),
                    "source": source_by_frame[frame],
                }
            )
        else:
            raw_lift[frame] = 0.0

    smoothed = smooth_frame_values(raw_lift, start, end, int(smooth_radius))
    corrected = limit_frame_delta(
        smoothed,
        start,
        end,
        float(max_correction_delta_per_frame),
    )

    data_path = bone_path(root_bone, "location")
    z_curve = get_fcurve(action, data_path, 2)
    original_z = (
        cache_fcurve_values(z_curve, start, end)
        if z_curve is not None
        else root_z_from_pose
    )
    z_curve = ensure_fcurve(action, data_path, 2, group=root_bone)
    cache = keyframe_map(z_curve)
    changed_frames = 0
    max_lift = 0.0
    for frame in range(start, end + 1):
        lift = float(corrected.get(frame, 0.0))
        set_fcurve_value(
            z_curve,
            frame,
            float(original_z[frame]) + lift,
            cache=cache,
        )
        if abs(lift) > EPSILON:
            changed_frames += 1
            max_lift = max(max_lift, lift)
    z_curve.update()

    penetration_samples.sort(key=lambda item: item["penetration"], reverse=True)
    return {
        "operation": "repair_source_pelvis_floor_v2",
        "frame_range": [start, end],
        "root_bone": root_bone,
        "valid_contact_points": [list(item) for item in valid_points],
        "missing_contact_points": missing_points,
        "params": {
            "floor_z": float(floor_z),
            "tolerance": float(tolerance),
            "target_clearance": float(target_clearance),
            "max_lift_per_frame": float(max_lift_per_frame),
            "strength": float(strength),
            "smooth_radius": int(smooth_radius),
            "max_correction_delta_per_frame": float(
                max_correction_delta_per_frame
            ),
        },
        "changed_frames": changed_frames,
        "max_applied_lift": round(max_lift, 6),
        "penetration_sample_count": len(penetration_samples),
        "worst_samples": penetration_samples[: int(worst_sample_limit)],
    }


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * float(percentile)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _distance(a: Sequence[float], b: Sequence[float], *, xy_only: bool) -> float:
    dx = float(a[0]) - float(b[0])
    dy = float(a[1]) - float(b[1])
    if xy_only:
        return math.hypot(dx, dy)
    dz = float(a[2]) - float(b[2])
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _detect_slide(
    samples: Mapping[str, Sequence[Sequence[float] | None]],
    bone_name: str,
    frame_start: int,
    floor_z: float,
    contact_height: float,
    speed_threshold: float,
    issue_type: str,
) -> dict[str, Any] | None:
    bad_frames: list[int] = []
    speeds: list[float] = []
    values = samples.get(bone_name, ())
    for index in range(1, len(values)):
        previous, current = values[index - 1], values[index]
        if previous is None or current is None:
            continue
        z = float(current[2])
        vertical = abs(float(current[2]) - float(previous[2]))
        xy_speed = _distance(current, previous, xy_only=True)
        if (
            z <= floor_z + contact_height
            and vertical < contact_height * 0.5
            and xy_speed > speed_threshold
        ):
            bad_frames.append(frame_start + index)
            speeds.append(xy_speed)
    if not bad_frames:
        return None
    return {
        "type": issue_type,
        "bone": bone_name,
        "frames": [list(item) for item in frames_to_ranges(bad_frames)],
        "severity": round(min(1.0, max(speeds) / 0.12), 4),
        "max_xy_speed_m_per_frame": round(max(speeds), 5),
    }


def _detect_jump(
    samples: Mapping[str, Sequence[Sequence[float] | None]],
    bone_name: str,
    frame_start: int,
    threshold: float,
    issue_type: str,
) -> dict[str, Any] | None:
    bad_frames: list[int] = []
    magnitudes: list[float] = []
    values = samples.get(bone_name, ())
    for index in range(1, len(values)):
        previous, current = values[index - 1], values[index]
        if previous is None or current is None:
            continue
        distance = _distance(current, previous, xy_only=False)
        if distance > threshold:
            bad_frames.append(frame_start + index)
            magnitudes.append(distance)
    if not bad_frames:
        return None
    return {
        "type": issue_type,
        "bone": bone_name,
        "frames": [list(item) for item in frames_to_ranges(bad_frames)],
        "severity": round(min(1.0, max(magnitudes) / (threshold * 3.0)), 4),
        "max_speed_m_per_frame": round(max(magnitudes), 5),
    }


def analyze_source_motion(
    scene: Any,
    armature: Any,
    *,
    bones: Mapping[str, str] = DEFAULT_SOURCE_BONES,
    thresholds: Mapping[str, float] | None = None,
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[str, Any]:
    """Run the lightweight source sanity analysis without changing animation."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    settings = dict(DEFAULT_DIAGNOSTIC_THRESHOLDS)
    if thresholds:
        settings.update({key: float(value) for key, value in thresholds.items()})

    available = [
        bone_name
        for bone_name in dict.fromkeys(bones.values())
        if armature.pose.bones.get(bone_name) is not None
    ]
    missing = [
        bone_name
        for bone_name in dict.fromkeys(bones.values())
        if armature.pose.bones.get(bone_name) is None
    ]
    samples: dict[str, list[list[float] | None]] = {
        bone_name: [] for bone_name in available
    }

    view_layer = current_view_layer()
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            for bone_name in available:
                location = pose_bone_world_location(armature, bone_name)
                samples[bone_name].append(
                    None
                    if location is None
                    else [float(location.x), float(location.y), float(location.z)]
                )

    floor_names = [
        bones.get(key)
        for key in ("left_foot", "right_foot", "left_heel", "right_heel")
    ]
    floor_values = [
        sample[2]
        for bone_name in floor_names
        if bone_name in samples
        for sample in samples[bone_name]
        if sample is not None
    ]
    floor_z = _percentile(floor_values, 0.01) or 0.0

    issues: list[dict[str, Any]] = []
    for key in ("left_foot", "right_foot"):
        bone_name = bones.get(key)
        if bone_name in samples:
            issue = _detect_slide(
                samples,
                bone_name,
                start,
                floor_z,
                settings["foot_contact_height_m"],
                settings["foot_slide_speed_m_per_frame"],
                "foot_slide_suspected",
            )
            if issue:
                issues.append(issue)
    for key in ("left_heel", "right_heel"):
        bone_name = bones.get(key)
        if bone_name in samples:
            issue = _detect_slide(
                samples,
                bone_name,
                start,
                floor_z,
                settings["foot_contact_height_m"],
                settings["heel_slide_speed_m_per_frame"],
                "heel_slide_suspected",
            )
            if issue:
                issues.append(issue)
    for key in ("left_hand", "right_hand"):
        bone_name = bones.get(key)
        if bone_name in samples:
            issue = _detect_jump(
                samples,
                bone_name,
                start,
                settings["hand_jump_m_per_frame"],
                "hand_jump",
            )
            if issue:
                issues.append(issue)
    hips = bones.get("hips")
    if hips in samples:
        issue = _detect_jump(
            samples,
            hips,
            start,
            settings["hips_jump_m_per_frame"],
            "hips_jump",
        )
        if issue:
            issues.append(issue)

    fps_base = float(getattr(scene.render, "fps_base", 1.0)) or 1.0
    action = getattr(getattr(armature, "animation_data", None), "action", None)
    return {
        "schema_version": "mocap_doctor_source_report_v2",
        "scene": {
            "name": scene.name,
            "fps": float(scene.render.fps) / fps_base,
            "frame_start": start,
            "frame_end": end,
        },
        "armature": {
            "name": armature.name,
            "action": getattr(action, "name", None),
        },
        "bones": dict(bones),
        "missing_bones": missing,
        "thresholds": settings,
        "floor": {"z_estimate": round(float(floor_z), 6)},
        "issues": issues,
    }

