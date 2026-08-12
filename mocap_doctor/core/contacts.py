"""FreeMoCap foot-contact v2 detection and manual effective ranges."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any

from .animation import (
    current_view_layer,
    pose_bone_point_world,
    preserve_scene_frame,
    resolve_frame_range,
    set_scene_frame,
)
from .ranges import (
    diff_ranges,
    frames_to_ranges,
    normalize_ranges,
    ranges_to_frames,
    subtract_ranges,
    union_ranges,
)


DEFAULT_FOOT_POINTS = {
    "L": (
        ("foot.L", "head"),
        ("foot.L", "tail"),
        ("heel.02.L", "head"),
        ("heel.02.L", "tail"),
    ),
    "R": (
        ("foot.R", "head"),
        ("foot.R", "tail"),
        ("heel.02.R", "head"),
        ("heel.02.R", "tail"),
    ),
}


def _list_ranges(ranges: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[int(a), int(b)] for a, b in ranges]


def _distance_xy(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def sample_foot_side(
    scene: Any,
    armature: Any,
    side: str,
    *,
    foot_points: Mapping[str, Sequence[tuple[str, str]]] = DEFAULT_FOOT_POINTS,
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[int, dict[str, Any] | None]:
    """Sample the lowest point and average foot center for one side."""

    if side not in ("L", "R"):
        raise ValueError(f"unsupported foot side: {side!r}")
    start, end = resolve_frame_range(scene, frame_start, frame_end)
    points = [
        (bone_name, point)
        for bone_name, point in foot_points[side]
        if armature.pose.bones.get(bone_name) is not None
    ]
    if not points:
        raise RuntimeError(f"no usable source foot points for side {side}")

    samples: dict[int, dict[str, Any] | None] = {}
    view_layer = current_view_layer()
    with preserve_scene_frame(scene, view_layer):
        for frame in range(start, end + 1):
            set_scene_frame(scene, frame, view_layer)
            locations: list[list[float]] = []
            sources: list[str] = []
            for bone_name, point in points:
                location = pose_bone_point_world(armature, bone_name, point)
                if location is None:
                    continue
                locations.append(
                    [float(location.x), float(location.y), float(location.z)]
                )
                sources.append(f"{bone_name}:{point}")
            if not locations:
                samples[frame] = None
                continue
            lowest_index = min(
                range(len(locations)), key=lambda index: locations[index][2]
            )
            count = len(locations)
            samples[frame] = {
                "lowest_z": locations[lowest_index][2],
                "lowest_source": sources[lowest_index],
                "avg_center": [
                    sum(item[axis] for item in locations) / count
                    for axis in range(3)
                ],
                "point_count": count,
            }
    return samples


def split_planted_by_anchor_drift(
    planted_frames: Sequence[int],
    per_frame: Mapping[int, Mapping[str, Any]],
    *,
    max_anchor_drift: float = 0.025,
    min_segment_len: int = 4,
    merge_gap: int = 1,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Reject candidate frames after the foot drifts too far from an anchor."""

    initial = frames_to_ranges(planted_frames)
    accepted: list[int] = []
    rejected: list[int] = []
    for start, end in initial:
        anchor_xy: Sequence[float] | None = None
        for frame in range(start, end + 1):
            item = per_frame.get(frame)
            if item is None:
                anchor_xy = None
                continue
            xy = item["avg_xy"]
            if anchor_xy is None:
                anchor_xy = xy
                accepted.append(frame)
                continue
            if _distance_xy(xy, anchor_xy) <= float(max_anchor_drift):
                accepted.append(frame)
            else:
                rejected.append(frame)
                anchor_xy = xy

    return (
        frames_to_ranges(
            accepted,
            min_length=int(min_segment_len),
            merge_gap=int(merge_gap),
        ),
        frames_to_ranges(rejected, merge_gap=1),
    )


def analyze_contact_samples(
    samples: Mapping[int, Mapping[str, Any] | None],
    frame_start: int,
    frame_end: int,
    side: str,
    *,
    floor_z: float = 0.02,
    contact_height: float = 0.030,
    planted_xy_speed: float = 0.012,
    moving_xy_speed: float = 0.012,
    max_vertical_speed: float = 0.010,
    min_segment_len: int = 4,
    merge_gap: int = 1,
    max_anchor_drift: float = 0.025,
    penetration_tolerance: float = 0.008,
) -> dict[str, Any]:
    """Classify already sampled foot positions using the validated v2 logic."""

    candidate_frames: list[int] = []
    moving_frames: list[int] = []
    airborne_frames: list[int] = []
    penetrations: list[dict[str, Any]] = []
    per_frame: dict[int, dict[str, Any]] = {}
    previous: Mapping[str, Any] | None = None

    for frame in range(int(frame_start), int(frame_end) + 1):
        sample = samples.get(frame)
        if sample is None:
            previous = None
            continue
        lowest_z = float(sample["lowest_z"])
        center = sample["avg_center"]
        height = lowest_z - float(floor_z)
        xy_speed = 0.0
        vertical_speed = 0.0
        if previous is not None:
            xy_speed = _distance_xy(center, previous["avg_center"])
            vertical_speed = abs(
                float(center[2]) - float(previous["avg_center"][2])
            )

        near_floor = height <= float(contact_height)
        if (
            near_floor
            and xy_speed <= float(planted_xy_speed)
            and vertical_speed <= float(max_vertical_speed)
        ):
            initial_state = "planted_candidate"
            candidate_frames.append(frame)
        elif near_floor and xy_speed > float(moving_xy_speed):
            initial_state = "near_floor_moving"
            moving_frames.append(frame)
        else:
            initial_state = "airborne_or_lifted"
            airborne_frames.append(frame)

        if lowest_z < float(floor_z) - float(penetration_tolerance):
            penetrations.append(
                {
                    "frame": frame,
                    "lowest_z": round(lowest_z, 5),
                    "depth": round(float(floor_z) - lowest_z, 5),
                    "source": sample["lowest_source"],
                }
            )
        per_frame[frame] = {
            "state_initial": initial_state,
            "height_above_floor": round(height, 5),
            "xy_speed": round(xy_speed, 5),
            "vertical_speed": round(vertical_speed, 5),
            "lowest_source": sample["lowest_source"],
            "avg_xy": [float(center[0]), float(center[1])],
        }
        previous = sample

    planted, drift_rejected = split_planted_by_anchor_drift(
        candidate_frames,
        per_frame,
        max_anchor_drift=max_anchor_drift,
        min_segment_len=min_segment_len,
        merge_gap=merge_gap,
    )
    for start, end in drift_rejected:
        for frame in range(start, end + 1):
            moving_frames.append(frame)
            if frame in per_frame:
                per_frame[frame]["state_initial"] = "rejected_by_anchor_drift"

    moving = frames_to_ranges(
        moving_frames,
        min_length=int(min_segment_len),
        merge_gap=int(merge_gap),
    )
    airborne = frames_to_ranges(
        airborne_frames,
        min_length=int(min_segment_len),
        merge_gap=int(merge_gap),
    )
    planted_frames = ranges_to_frames(planted)
    for frame, item in per_frame.items():
        if frame in planted_frames:
            item["state"] = "planted"
        elif item["state_initial"] == "rejected_by_anchor_drift":
            item["state"] = "near_floor_moving_or_reposition"
        elif item["state_initial"] == "near_floor_moving":
            item["state"] = "near_floor_moving"
        else:
            item["state"] = "airborne_or_lifted"

    return {
        "side": side,
        "initial_planted_segments": _list_ranges(frames_to_ranges(candidate_frames)),
        "planted_segments": _list_ranges(planted),
        "near_floor_moving_segments": _list_ranges(moving),
        "airborne_or_lifted_segments": _list_ranges(airborne),
        "drift_rejected_segments": _list_ranges(drift_rejected),
        "penetration_samples": penetrations[:100],
        "penetration_sample_count": len(penetrations),
        "per_frame": per_frame,
    }


def _side_ranges(
    values: Mapping[str, Sequence[Sequence[int]]] | None,
    side: str,
    frame_start: int,
    frame_end: int,
) -> list[tuple[int, int]]:
    if values is None:
        return []
    unexpected = set(values) - {"L", "R"}
    if unexpected:
        raise ValueError(f"unsupported contact side(s): {sorted(unexpected)!r}")
    return normalize_ranges(
        values.get(side, ()),
        frame_start=frame_start,
        frame_end=frame_end,
    )


def apply_contact_overrides(
    report: Mapping[str, Any],
    *,
    additions: Mapping[str, Sequence[Sequence[int]]] | None = None,
    deletions: Mapping[str, Sequence[Sequence[int]]] | None = None,
    merge_gap: int = 1,
    min_segment_len: int = 3,
) -> dict[str, Any]:
    """Derive effective planted intervals without overwriting raw detection."""

    out = deepcopy(dict(report))
    scene_info = out.get("scene", {})
    frame_start = int(scene_info["frame_start"])
    frame_end = int(scene_info["frame_end"])
    override_record: dict[str, Any] = {
        "additions": {},
        "deletions": {},
        "merge_gap": int(merge_gap),
        "min_segment_len": int(min_segment_len),
    }

    for side in ("L", "R"):
        foot = out["feet"][side]
        raw = foot.get("raw")
        if raw is None:
            raw = {
                key: deepcopy(value)
                for key, value in foot.items()
                if key not in {"effective", "manual_overrides"}
            }
            foot["raw"] = raw
        raw_ranges = normalize_ranges(
            raw.get("planted_segments", ()),
            frame_start=frame_start,
            frame_end=frame_end,
        )
        add = _side_ranges(additions, side, frame_start, frame_end)
        delete = _side_ranges(deletions, side, frame_start, frame_end)
        effective = union_ranges(
            subtract_ranges(raw_ranges, delete),
            add,
            frame_start=frame_start,
            frame_end=frame_end,
            merge_gap=int(merge_gap),
            min_length=int(min_segment_len),
        )
        changes = diff_ranges(raw_ranges, effective)
        effective_data = {
            "planted_segments": _list_ranges(effective),
            "planted_frame_count": len(ranges_to_frames(effective)),
            "changes_from_raw": {
                key: _list_ranges(value) for key, value in changes.items()
            },
        }
        foot["raw_planted_segments"] = _list_ranges(raw_ranges)
        foot["effective"] = effective_data
        foot["effective_planted_segments"] = _list_ranges(effective)
        # Compatibility for target repair code that consumed the old v2 report.
        foot["planted_segments"] = _list_ranges(effective)
        override_record["additions"][side] = _list_ranges(add)
        override_record["deletions"][side] = _list_ranges(delete)

    out["manual_overrides"] = override_record
    return out


def get_effective_planted_ranges(
    report: Mapping[str, Any],
    side: str,
) -> list[tuple[int, int]]:
    """Read new raw/effective reports and legacy v2 reports safely."""

    foot = report["feet"][side]
    effective = foot.get("effective", {}).get("planted_segments")
    if effective is None:
        effective = foot.get("effective_planted_segments")
    if effective is None:
        effective = foot.get("planted_segments", ())
    scene = report.get("scene", {})
    return normalize_ranges(
        effective,
        frame_start=scene.get("frame_start"),
        frame_end=scene.get("frame_end"),
    )


def detect_contacts_v2(
    scene: Any,
    armature: Any,
    *,
    foot_points: Mapping[str, Sequence[tuple[str, str]]] = DEFAULT_FOOT_POINTS,
    frame_start: int | None = None,
    frame_end: int | None = None,
    floor_z: float = 0.02,
    contact_height: float = 0.030,
    planted_xy_speed: float = 0.012,
    moving_xy_speed: float = 0.012,
    max_vertical_speed: float = 0.010,
    min_segment_len: int = 4,
    merge_gap: int = 1,
    max_anchor_drift: float = 0.025,
    penetration_tolerance: float = 0.008,
    additions: Mapping[str, Sequence[Sequence[int]]] | None = None,
    deletions: Mapping[str, Sequence[Sequence[int]]] | None = None,
) -> dict[str, Any]:
    """Detect raw contact v2 intervals, then derive editable effective data."""

    start, end = resolve_frame_range(scene, frame_start, frame_end)
    feet: dict[str, dict[str, Any]] = {}
    for side in ("L", "R"):
        samples = sample_foot_side(
            scene,
            armature,
            side,
            foot_points=foot_points,
            frame_start=start,
            frame_end=end,
        )
        raw = analyze_contact_samples(
            samples,
            start,
            end,
            side,
            floor_z=floor_z,
            contact_height=contact_height,
            planted_xy_speed=planted_xy_speed,
            moving_xy_speed=moving_xy_speed,
            max_vertical_speed=max_vertical_speed,
            min_segment_len=min_segment_len,
            merge_gap=merge_gap,
            max_anchor_drift=max_anchor_drift,
            penetration_tolerance=penetration_tolerance,
        )
        # Keep the old top-level diagnostic fields readable while making the
        # immutable automatic result explicit under ``raw``.
        feet[side] = {**deepcopy(raw), "raw": raw}

    fps_base = float(getattr(scene.render, "fps_base", 1.0)) or 1.0
    report = {
        "schema_version": "foot_contact_report_v3_raw_effective",
        "detector_version": "contact_v2",
        "scene": {
            "name": scene.name,
            "fps": float(scene.render.fps) / fps_base,
            "frame_start": start,
            "frame_end": end,
        },
        "armature": armature.name,
        "floor_z": float(floor_z),
        "params": {
            "contact_height": float(contact_height),
            "planted_xy_speed": float(planted_xy_speed),
            "moving_xy_speed": float(moving_xy_speed),
            "max_vertical_speed_for_planted": float(max_vertical_speed),
            "min_segment_len": int(min_segment_len),
            "merge_gap": int(merge_gap),
            "max_planted_anchor_drift": float(max_anchor_drift),
            "penetration_tolerance": float(penetration_tolerance),
        },
        "feet": feet,
    }
    # MAX_REASONABLE_PLANTED_LEN is intentionally absent: the old script
    # exposed it but never used it in detection.
    return apply_contact_overrides(
        report,
        additions=additions,
        deletions=deletions,
        merge_gap=merge_gap,
        min_segment_len=3,
    )
