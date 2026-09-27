"""Regression tests for the wrist-visibility (occlusion) cue."""

import os
import unittest

from mocap_doctor.core import occlusion


class LowConfidenceRangeTests(unittest.TestCase):
    def test_frames_below_threshold_become_one_range(self):
        series = [0.9, 0.9, 0.4, 0.4, 0.4, 0.4, 0.4, 0.9]
        self.assertEqual(
            occlusion.low_confidence_ranges(series, threshold=0.7),
            [(2, 6)],
        )

    def test_short_and_isolated_dips_are_dropped(self):
        series = [0.9, 0.4, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.4, 0.4]
        self.assertEqual(occlusion.low_confidence_ranges(series, threshold=0.7), [])

    def test_gap_is_bridged_but_a_long_gap_is_not(self):
        bridged = [0.4, 0.4, 0.9, 0.9, 0.4, 0.4, 0.4]
        self.assertEqual(
            occlusion.low_confidence_ranges(bridged, threshold=0.7, merge_gap=4),
            [(0, 6)],
        )
        split = [0.4, 0.4, 0.9] + [0.9] * 20 + [0.4, 0.4, 0.4]
        self.assertEqual(
            occlusion.low_confidence_ranges(
                split, threshold=0.7, merge_gap=4, min_length=2
            ),
            [(0, 1), (23, 25)],
        )

    def test_empty_series_is_empty(self):
        self.assertEqual(occlusion.low_confidence_ranges([], threshold=0.7), [])


class ConfidenceFloorTests(unittest.TestCase):
    def test_floor_tracks_the_video_own_distribution(self):
        quiet = [0.9] * 100
        self.assertAlmostEqual(occlusion.confidence_floor(quiet), 0.9, places=6)
        spread = list(range(1, 101))
        self.assertAlmostEqual(occlusion.confidence_floor(spread, percentile=5.0), 5.95, places=2)


class MergeRangeTests(unittest.TestCase):
    def test_sorts_and_coalesces(self):
        self.assertEqual(
            occlusion.merge_ranges([(10, 12), (0, 2), (13, 15)]),
            [(0, 2), (10, 15)],
        )

    def test_touching_ranges_merge_when_asked(self):
        self.assertEqual(occlusion.merge_ranges([(0, 3), (5, 8)], gap=1), [(0, 8)])
        self.assertEqual(occlusion.merge_ranges([(0, 3), (6, 8)], gap=1), [(0, 3), (6, 8)])


class RealArchiveTests(unittest.TestCase):
    """The reader has to cope with a real torch archive, without torch."""

    PATH = os.environ.get("MCD_VITPOSE_PT", "")

    @unittest.skipUnless(PATH and os.path.isfile(PATH), "set MCD_VITPOSE_PT to a vitpose.pt")
    def test_reads_wrist_confidence(self):
        left, right = occlusion.wrist_confidence(self.PATH)
        self.assertEqual(len(left), len(right))
        for series in (left, right):
            # Observed range is roughly 0.25..1.05: a visibility score, not a
            # calibrated probability, which is all this cue needs.
            self.assertGreaterEqual(min(series), 0.0)
            self.assertLessEqual(max(series), 1.5)
            self.assertGreater(occlusion.confidence_floor(series), 0.0)


if __name__ == "__main__":
    unittest.main()
