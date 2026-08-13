"""Regression tests for the finger replacement planning logic.

Pure Python tests for core/fingers.py, mirroring the style of
test_receiver_prep_planning.py.
"""

import unittest

from mocap_doctor.core import fingers


# A realistic subset of the Teto armature: full 人指 chain both sides plus
# wrist/hand helpers and unrelated bones.
TETO_SUBSET = [
    "手首.L", "手首.R",
    "手捩.L", "手捩.R", "手捩1.L", "手捩2.L", "手捩3.L",
    "人指１.L", "人指２.L", "人指３.L", "人指先.L",
    "人指１.R", "人指２.R", "人指３.R", "人指先.R",
    "親指０.L", "親指１.L", "親指２.L", "親指先.L",
    "腕.L", "ひじ.L", "_dummy_arm_twist.L",
]


class FingerNameTests(unittest.TestCase):
    def test_is_finger_bone(self):
        self.assertTrue(fingers.is_finger_bone("人指１.L"))
        self.assertTrue(fingers.is_finger_bone("親指先.R"))
        self.assertTrue(fingers.is_finger_bone("小指３.R"))
        self.assertFalse(fingers.is_finger_bone("手首.L"))
        self.assertFalse(fingers.is_finger_bone("手捩2.L"))
        self.assertFalse(fingers.is_finger_bone("腕.L"))
        self.assertFalse(fingers.is_finger_bone("人指１"))  # no side suffix
        self.assertFalse(fingers.is_finger_bone("_dummy_arm_twist.L"))

    def test_finger_plan_covers_all_chains_in_order(self):
        plan = fingers.finger_plan(TETO_SUBSET)
        names = [item[0] for item in plan]
        self.assertEqual(len(names), 12)  # 1 親指 chain + 2 人指 chains
        # Each chain is listed in knuckle-to-tip order.
        offset = names.index("人指１.L")
        for index, name in enumerate(["人指１.L", "人指２.L", "人指３.L", "人指先.L"]):
            self.assertEqual(names[offset + index], name)
        # Chain end for 人指１.L is the tip bone.
        by_name = {item[0]: item for item in plan}
        self.assertEqual(by_name["人指１.L"][2], "人指先.L")

    def test_finger_plan_skips_missing_bones(self):
        subset = ["手首.L", "人指１.L", "人指２.L", "人指先.L", "小指１.L"]
        plan = fingers.finger_plan(subset)
        names = [item[0] for item in plan]
        self.assertEqual(names, ["人指１.L", "人指２.L", "人指先.L", "小指１.L"])
        # Chain end falls back to the last present bone when 人指３ is missing.
        by_name = {item[0]: item for item in plan}
        self.assertEqual(by_name["人指１.L"][2], "人指先.L")
        self.assertEqual(by_name["小指１.L"][2], "小指１.L")

    def test_finger_plan_ignores_wrist_and_helpers(self):
        plan = fingers.finger_plan(TETO_SUBSET)
        names = {item[0] for item in plan}
        self.assertFalse(names & {"手首.L", "手首.R", "手捩.L", "手捩1.L", "腕.L"})


class CurlFactorTests(unittest.TestCase):
    def test_curl_factors_cover_chain_digits(self):
        for chain in fingers.FINGER_CHAINS.values():
            for joint in chain:
                self.assertIn(joint[-1], fingers.CURL_FACTORS)

    def test_tip_joints_curl_more_than_knuckles(self):
        # Outer joints get a bigger factor than the knuckle joints.
        self.assertGreater(fingers.CURL_FACTORS["２"], fingers.CURL_FACTORS["１"])
        self.assertGreater(fingers.CURL_FACTORS["３"], fingers.CURL_FACTORS["１"])

    def test_max_curl_is_positive_and_bounded(self):
        self.assertGreater(fingers.MAX_CURL_RAD, 0.0)
        self.assertLessEqual(fingers.MAX_CURL_RAD, 1.6)  # a bit under 90 degrees


class MMRMappingTests(unittest.TestCase):
    """The MMR template maps every non-tip finger bone to one rig ORG bone."""

    def test_mapping_covers_15_bones_per_side(self):
        # 15 driven bones per side = 3 thumb + 3*4 finger chains.  Tips (先)
        # are not driven; they follow their parents.
        driven = [bone for bone in fingers.MMR_FINGER_ORG]
        self.assertEqual(len(driven), 15)
        for stem, org in fingers.MMR_FINGER_ORG.items():
            self.assertNotIn("先", stem)
            self.assertTrue(org.startswith("ORG-"))

    def test_finger_org_subtarget_joins_side_parent(self):
        self.assertEqual(
            fingers.finger_org_subtarget("人指１.L"), "ORG-f_index.01.L_parent"
        )
        self.assertEqual(
            fingers.finger_org_subtarget("親指０.R"), "ORG-thumb.01.R_parent"
        )
        self.assertEqual(
            fingers.finger_org_subtarget("小指３.L"), "ORG-f_pinky.03.L_parent"
        )

    def test_finger_org_subtarget_rejects_tips_and_non_fingers(self):
        self.assertIsNone(fingers.finger_org_subtarget("人指先.L"))
        self.assertIsNone(fingers.finger_org_subtarget("手首.L"))
        self.assertIsNone(fingers.finger_org_subtarget("人指１"))  # no side suffix

    def test_is_finger_controller_bone(self):
        self.assertTrue(fingers.is_finger_controller_bone("f_index.01.L"))
        self.assertTrue(fingers.is_finger_controller_bone("f_index.01_master.R"))
        self.assertTrue(fingers.is_finger_controller_bone("thumb.03.L"))
        self.assertFalse(fingers.is_finger_controller_bone("f_index.01.L.001"))
        self.assertFalse(fingers.is_finger_controller_bone("f_index.01_master.L.001"))
        self.assertFalse(fingers.is_finger_controller_bone("hand_fk.L"))
        self.assertFalse(fingers.is_finger_controller_bone("ORG-f_index.01.L"))
        self.assertFalse(fingers.is_finger_controller_bone("MCH-f_index.01.L"))


if __name__ == "__main__":
    unittest.main()
