"""Fixed FreeMoCap and arue Teto/MMR preset for Blender 4.3."""

import math
import re


EXPECTED_FPS = 30

OBJECT_NAMES = {
    "source_armature": "import_synchronized_videos_rig",
    "model_root": "arue式重音テトver 2.01",
    "mmr_rig": "RIG-arue式重音テトver 2.01_arm",
    "mmd_armature": "arue式重音テトver 2.01_arm",
    "target_mesh": "arue式重音テトver 2.01_mesh",
    "correction_empty": "teto_global_correction",
}


def fixed_object_name_matches(actual: str, expected: str) -> bool:
    """Accept Blender's duplicate suffix without weakening the fixed preset.

    Importing an additional copy of the same Teto model makes Blender rename
    datablocks to ``.001``, ``.002`` and so on.  Those suffixes are naming
    disambiguators, not structural changes to the rig.
    """

    return bool(
        re.fullmatch(rf"{re.escape(str(expected))}(?:\.\d{{3}})?", str(actual))
    )

SOURCE_BONES = {
    "pelvis": "pelvis",
    "left_hand": "hand.L",
    "right_hand": "hand.R",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_heel": "heel.02.L",
    "right_heel": "heel.02.R",
}

ARM_CHAINS = {
    "L": ["shoulder.L", "upper_arm.L", "forearm.L", "hand.L"],
    "R": ["shoulder.R", "upper_arm.R", "forearm.R", "hand.R"],
}

TARGET_FOOT_IK = {"L": "foot_ik.L", "R": "foot_ik.R"}

MMD_ROOT_BONE = "全ての親"
MMD_CENTER_BONE = "センター"
# These are the real Blender bone names in blends/arue_teto.blend.
MMD_LEG_FK_BONES = ["足.L", "ひざ.L", "足首.L", "足.R", "ひざ.R", "足首.R"]
# The physical MMD arm chain. A portable VMD must contain its visible pose.
MMD_ARM_FK_BONES = ["腕.L", "ひじ.L", "手首.L", "腕.R", "ひじ.R", "手首.R"]
MMD_WRIST_BONES = {"L": "手首.L", "R": "手首.R"}
MMD_HAND_IK_BONES = {"L": "手IK.L", "R": "手IK.R"}
# Blender-only helper names, safely below VMD's 15-byte name limit.
MMD_HAND_IK_EXPORT_NAMES = {"L": "MCD_L_HAND_IK", "R": "MCD_R_HAND_IK"}
MMD_FOOT_IK_JAPANESE_NAMES = {"L": "左足ＩＫ", "R": "右足ＩＫ"}
MMD_FOOT_IK_NAME_CANDIDATES = {
    "L": ["足ＩＫ.L", "足IK.L", "左足ＩＫ", "左足IK"],
    "R": ["足ＩＫ.R", "足IK.R", "右足ＩＫ", "右足IK"],
}

MMR_COPY_CONSTRAINT_NAME = "MMR_复制变换"
MMR_LEG_CONSTRAINTS = {
    "足.L": ("COPY_TRANSFORMS", "ORG-thigh.L_parent"),
    "ひざ.L": ("COPY_TRANSFORMS", "ORG-shin.L_parent"),
    "足首.L": ("COPY_TRANSFORMS", "ORG-foot.L_parent"),
    "足.R": ("COPY_TRANSFORMS", "ORG-thigh.R_parent"),
    "ひざ.R": ("COPY_TRANSFORMS", "ORG-shin.R_parent"),
    "足首.R": ("COPY_TRANSFORMS", "ORG-foot.R_parent"),
}

DEFAULTS = {
    "source_diagnostic_contact_height": 0.050,
    "source_foot_slide_speed": 0.020,
    "source_heel_slide_speed": 0.018,
    "source_hand_jump": 0.200,
    "source_hips_jump": 0.250,
    "smooth_radius": 2,
    "smooth_strength": 0.45,
    "source_floor_z": 0.02,
    "source_floor_tolerance": 0.012,
    "source_floor_clearance": 0.004,
    "source_floor_max_lift": 0.08,
    "source_floor_strength": 0.75,
    "source_floor_smooth_radius": 2,
    "source_floor_max_delta": 0.018,
    "contact_height": 0.030,
    "contact_xy_speed": 0.012,
    "contact_moving_xy_speed": 0.012,
    "contact_vertical_speed": 0.010,
    "contact_min_segment_len": 4,
    "contact_merge_gap": 1,
    "contact_anchor_drift": 0.025,
    "contact_penetration_tolerance": 0.008,
    "global_rot_x": math.radians(-4.2),
    "global_rot_y": math.radians(3.7),
    "global_rot_z": 0.0,
    "tilt_strength": 0.65,
    "target_floor_z": 0.0257,
    "target_clearance": 0.0015,
    "target_floor_tolerance": 0.004,
    "target_floor_max_lift": 0.035,
    "target_floor_strength": 0.55,
    "target_floor_smooth_radius": 3,
    "target_floor_max_delta": 0.0045,
    "target_vertex_sample_step": 2,
    "lock_trim": 2,
    "drift_min_segment_len": 4,
    "lock_min_segment_len": 5,
    "lock_blend_frames": 2,
    "lock_min_xy_range": 0.006,
    "vmd_floor_offset": -0.0257,
}


def find_mmd_bone_by_japanese_name(armature, japanese_name):
    """Resolve a Blender bone through mmd_tools metadata without guessing."""

    for pose_bone in armature.pose.bones:
        mmd_bone = getattr(pose_bone, "mmd_bone", None)
        if mmd_bone and getattr(mmd_bone, "name_j", "") == japanese_name:
            return pose_bone.name
    return None


def resolve_mmd_foot_ik(armature, side):
    name = find_mmd_bone_by_japanese_name(armature, MMD_FOOT_IK_JAPANESE_NAMES[side])
    if name:
        return name
    for candidate in MMD_FOOT_IK_NAME_CANDIDATES[side]:
        if candidate in armature.pose.bones:
            return candidate
    return None
