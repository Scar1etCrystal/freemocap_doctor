"""Receiver-template prep planning.

The plugin exports a VMD that plays correctly in MMD, but re-importing it into
a Blender template that went through MikuMikuRig (MMR) breaks the arm for three
independent reasons:

1. MMR slaves every bone of the native MMD armature to the control rig with
   COPY_TRANSFORMS / COPY_ROTATION / TRANSFORM constraints, so the imported VMD
   FK curves are overridden and the arm stays in the template's rest pose.
2. MMR adds 手IK.L/R helper bones that duplicate the native 手首.L/R
   mmd_bone.name_j (左手首/右手首).  mmd_tools' PMX bone map is built with a
   dict comprehension in which the later bone wins, so the VMD wrist tracks are
   assigned to the helpers and the real wrists never move.
3. MMR re-parents ひじ.L/R from 腕捩.L/R to 腕.L/R, so the elbow FK rotation is
   applied in the wrong parent frame (off by the upper-arm twist).

The functions here only *decide* what to change and return plain data, so they
can be unit-tested without Blender; the operator in operators.py applies the
plan to the live scene.
"""

# PMX-native IK targets use full-width ＩＫ (足ＩＫ, つま先ＩＫ, 手首ＩＫ); MMR
# helpers use half-width IK (手IK).  Native leg IK must survive so that VMDs
# with IK property keys still animate the legs via mmd_ik_toggle.
FULL_WIDTH_IK = "ＩＫ"
HALF_WIDTH_IK = "IK"

ARM_IK_TOGGLE_BONES = ("ひじ.L", "ひじ.R", "手首.L", "手首.R")
# (bone, MMR parent, PMX parent) per side
ELBOW_PARENT_RESTORE = {
    "L": ("ひじ.L", "腕.L", "腕捩.L"),
    "R": ("ひじ.R", "腕.R", "腕捩.R"),
}


def _keeps_native_ik(constraint):
    if constraint.get("type") != "IK":
        return False
    return FULL_WIDTH_IK in constraint.get("subtarget", "")


def plan_constraints(bones):
    """Split each bone's constraints into keep (native leg IK) vs remove.

    ``bones`` is an iterable of dicts with ``name`` and ``constraints``
    (a list of dicts with ``type`` and ``subtarget``).
    """
    keep, remove = [], []
    for bone in bones:
        for constraint in bone.get("constraints", ()):
            item = {
                "bone": bone["name"],
                "type": constraint.get("type", ""),
                "subtarget": constraint.get("subtarget", ""),
            }
            (keep if _keeps_native_ik(constraint) else remove).append(item)
    return {"keep": keep, "remove": remove}


def plan_arm_ik_toggle_off(bones):
    """Bone names among ARM_IK_TOGGLE_BONES that currently have IK enabled.

    ``bones`` maps name -> dict with ``has_ik_toggle`` and ``ik_toggle``.
    """
    return [
        name
        for name in ARM_IK_TOGGLE_BONES
        if name in bones
        and bones[name].get("has_ik_toggle")
        and bones[name].get("ik_toggle")
    ]


def plan_helper_bone_deletion(bones):
    """Names of MMR helper bones to delete.

    A bone is a helper when it shares its mmd name_j with another bone and its
    own name contains the half-width "IK" marker (手IK.L/R) — the helper wins
    the mmd_tools PMX bone map, so it must go.  Bones that have children are
    left alone and reported instead.
    """
    delete, skipped = [], []
    by_name_j = {}
    for bone in bones:
        name_j = bone.get("name_j") or ""
        if name_j:
            by_name_j.setdefault(name_j, []).append(bone)
    for name_j, group in by_name_j.items():
        if len(group) < 2:
            continue
        helpers = [bone for bone in group if HALF_WIDTH_IK in bone.get("name", "")]
        others = [bone for bone in group if bone not in helpers]
        if len(helpers) != 1 or not others:
            continue
        for bone in helpers:
            if bone.get("has_children"):
                skipped.append(bone["name"])
            else:
                delete.append(bone["name"])
    return {"delete": delete, "skipped": skipped}


def plan_elbow_reparent(bones):
    """(bone, new_parent) pairs where ひじ currently sits under the MMR
    parent (腕) while the PMX parent (腕捩) exists.

    ``bones`` maps name -> dict with ``parent``.
    """
    reparent = []
    for bone_name, mmr_parent, pmx_parent in ELBOW_PARENT_RESTORE.values():
        bone = bones.get(bone_name)
        if bone is None or pmx_parent not in bones:
            continue
        if bone.get("parent") == mmr_parent:
            reparent.append((bone_name, pmx_parent))
    return reparent


def plan_rig_deletion(objects, texts):
    """Control-rig armature object names and UI text names to delete.

    ``objects`` is an iterable of (name, type) pairs for ARMATURE objects;
    the native MMD armature is passed separately so it is never matched.
    ``texts`` is an iterable of text names.
    """
    rig_objects = [
        name
        for name, kind in objects
        if kind == "ARMATURE" and (name.startswith("RIG-") or "MMR" in name)
    ]
    rig_texts = [
        name for name in texts if name.startswith("RIG-") or "arm_ui" in name
    ]
    return {"rig_objects": rig_objects, "rig_texts": rig_texts}


def plan_stale_actions(actions):
    """Action names to delete: previous VMD imports leave pose.bone fcurves
    that mmd_tools would merge the next import into."""
    return [
        action["name"]
        for action in actions
        if action.get("has_pose_bone_fcurves")
    ]
