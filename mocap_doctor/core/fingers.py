"""Finger replacement planning (pure logic, no Blender imports).

Optical mocap finger data is unreliable, so the export step replaces finger
motion with a static relaxed curl: finger curves are deleted and one fixed
keyframe per finger bone is written instead.  The palm and wrist animation
(手首 / 手捩) is kept untouched.

This module only decides *which* bones are fingers and how strongly each joint
curls, so it can be unit-tested without Blender.  The operator in
``operators.py`` derives the curl axis from the rest geometry and applies it.
"""

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
