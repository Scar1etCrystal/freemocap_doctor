"""Finger replacement planning (pure logic, no Blender imports).

Optical mocap finger data is unreliable, so the export step replaces finger
motion with one manually posed hand: the user poses the fingers with the MMR
controllers, and the operator freezes that pose as one constant keyframe per
finger bone.  The palm and wrist animation (手首 / 手捩) is kept untouched.

This module decides *which* bones are fingers and how the MMR rig maps to
them, so it can be unit-tested without Blender.
"""

import re

# PMX finger chains per side, ordered from knuckle to tip.  The digits are
# full-width characters, exactly as mmd_tools names them.
FINGER_CHAINS = {
    "親指": ("親指０", "親指１", "親指２", "親指先"),
    "人指": ("人指１", "人指２", "人指３", "人指先"),
    "中指": ("中指１", "中指２", "中指３", "中指先"),
    "薬指": ("薬指１", "薬指２", "薬指３", "薬指先"),
    "小指": ("小指１", "小指２", "小指３", "小指先"),
}

SIDES = ("L", "R")

# arue式重音テト MMR mapping: each driven MMD finger bone copies the
# transform of one ORG-f_* bone on the rig (COPY_TRANSFORMS, WORLD→WORLD,
# REPLACE, influence 1).  The tip bones (先) are not driven; they follow
# their parents.  Extracted from the user's MMR template (2026-08-13).
MMR_FINGER_ORG = {
    "親指０": "ORG-thumb.01",
    "親指１": "ORG-thumb.02",
    "親指２": "ORG-thumb.03",
    "人指１": "ORG-f_index.01",
    "人指２": "ORG-f_index.02",
    "人指３": "ORG-f_index.03",
    "中指１": "ORG-f_middle.01",
    "中指２": "ORG-f_middle.02",
    "中指３": "ORG-f_middle.03",
    "薬指１": "ORG-f_ring.01",
    "薬指２": "ORG-f_ring.02",
    "薬指３": "ORG-f_ring.03",
    "小指１": "ORG-f_pinky.01",
    "小指２": "ORG-f_pinky.02",
    "小指３": "ORG-f_pinky.03",
}

# Name of the MMR→MMD copy constraint, as the template creates it.
MMR_FINGER_CONSTRAINT_NAME = "MMR_复制变换"

# Grabbable MMR finger controller bones: f_index.01.L, f_index.01_master.R,
# thumb.03.L ...  (The .001 duplicates from double-imports are excluded.)
_FINGER_CONTROLLER_RE = re.compile(
    r"^(f_index|f_middle|f_pinky|f_ring|thumb)\.\d\d(_master)?\.(L|R)$"
)

# Per-joint curl weight keyed by the trailing digit/tip character: joints
# further from the knuckle curl more, so the pose stays relaxed.
CURL_FACTORS = {"０": 0.4, "１": 0.55, "２": 0.85, "３": 0.7, "先": 0.55}

# Total curl applied to the strongest joint at strength 1.0 (radians).
MAX_CURL_RAD = 1.0

# Hand bones that carry the usable palm/wrist animation and must be kept.
KEEP_HAND_BONES = ("手首", "手捩")


def _sides(name):
    """Return the side suffix (``"L"``/``"R"``) if ``name`` ends with one."""
    stem, _, side = name.rpartition(".")
    if stem and side in SIDES:
        return side
    return None


def is_finger_bone(name):
    """True when ``name`` belongs to one of the PMX finger chains."""
    side = _sides(name)
    if side is None:
        return False
    stem = name.rpartition(".")[0]
    return any(stem in chain for chain in FINGER_CHAINS.values())


def finger_org_subtarget(name):
    """Name of the MMR rig ORG bone that drives ``name``.

    ``親指０.L`` maps to ``ORG-thumb.01.L_parent``; tip bones and anything
    outside the mapping return ``None``.
    """
    stem, _, side = name.rpartition(".")
    if side not in SIDES:
        return None
    org = MMR_FINGER_ORG.get(stem)
    if org is None:
        return None
    return f"{org}.{side}_parent"


def is_finger_controller_bone(name):
    """True when ``name`` is a grabbable MMR finger controller bone."""
    return bool(_FINGER_CONTROLLER_RE.match(name))


def finger_plan(present_names):
    """Plan the static curl for every finger bone that is present.

    ``present_names`` is an iterable of armature bone names.  Returns a list of
    ``(name, joint_factor, chain_end_name)`` in chain order; ``chain_end_name``
    is the tip-most present bone of the same chain (the point whose distance
    to the palm the operator minimizes).
    """
    present = set(present_names)
    plan = []
    for chain in FINGER_CHAINS.values():
        for side in SIDES:
            chain_names = [f"{joint}.{side}" for joint in chain]
            chain_names = [n for n in chain_names if n in present]
            for name in chain_names:
                joint_char = name.rpartition(".")[0][-1]
                plan.append((name, CURL_FACTORS.get(joint_char, 0.6), chain_names[-1]))
    return plan
