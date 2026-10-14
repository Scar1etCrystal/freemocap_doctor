"""⑦ 躯干透视互补（spec §5.5）。

给度量项注入 ±8% 慢漂，躯干透视项保持正确 → 融合后慢漂必须被压到 < 3%。

合成真值：根 Z 慢速摆动（周期 120 帧）+ 更慢的尺度漂（周期 300 帧，±8%）。
另加退化防护：融合结果不能"被压平"成常数——必须仍然跟得上真实运动。
"""

from __future__ import annotations

import unittest

import numpy as np

from depth_prior.tests import _support as S

N = 240
MOTION_PERIOD = 120.0
DRIFT_PERIOD = 300.0
DRIFT_AMP = 0.08
TOL = 0.03


class PerspectiveComplement(unittest.TestCase):
    def setUp(self):
        self.fusion = S.require_module("fusion")
        self.fuse = S.require_callable(self.fusion, "fuse", "spec §3 冻结签名")
        self.cfg = S.cfg()

    def test_07_perspective_suppresses_metric_slow_drift(self):
        t = np.arange(N, dtype=np.float64)
        z_true = 4.0 + 0.5 * np.sin(2.0 * np.pi * t / MOTION_PERIOD)
        drift = 1.0 + DRIFT_AMP * np.sin(2.0 * np.pi * t / DRIFT_PERIOD + 0.7)
        z_metric = z_true * drift  # 度量项：±8% 慢漂

        frames = S.frame_priors(z_true, depth_median=z_metric, perspective=z_true, iqr_m=0.05)
        out = self.fuse(frames, self.cfg)
        self.assertIsInstance(out, tuple, "fuse 必须返回 (z_raw_m, confidence)")
        self.assertEqual(len(out), 2, "fuse 必须返回 (z_raw_m, confidence)")
        z_raw = np.asarray(out[0], dtype=np.float64)
        conf = np.asarray(out[1], dtype=np.float64)
        self.assertEqual(z_raw.shape, (N,), f"z_raw_m 应为 {N} 长，实际 {z_raw.shape}")
        self.assertTrue(np.all(np.isfinite(z_raw)), "z_raw_m 含 NaN/Inf")

        ratio = S.relative_ratio(z_raw, z_true)
        max_dev = float(np.max(np.abs(ratio - 1.0)))
        ptp_true = float(np.ptp(z_true))
        ptp_raw = float(np.ptp(z_raw))
        S.announce("⑦ ±8% 慢漂", in_drift_amp_pct=100.0 * DRIFT_AMP,
                   out_max_dev_pct=100.0 * max_dev,
                   out_ratio_min=float(ratio.min()), out_ratio_max=float(ratio.max()),
                   out_ptp_m=ptp_raw, true_ptp_m=ptp_true,
                   conf_mean=float(conf.mean()), need="out_max_dev < 3%")

        self.assertLess(
            max_dev, TOL,
            f"⑦ 注入 ±8% 慢漂后，融合结果相对真值的最大偏差 {S.pct(max_dev)} ≥ 3%"
            f"（躯干透视项没能把慢漂压下去）",
        )
        self.assertGreaterEqual(
            ptp_raw, 0.8 * ptp_true,
            f"⑦ 退化防护：融合结果振幅 {ptp_raw:.4f} m 远小于真值 {ptp_true:.4f} m —— "
            "像是把信号压平成常数了",
        )


class PerspectivePriorContract(unittest.TestCase):
    """⑦ 的前提：`priors.perspective_prior` 必须是"校准点 + 1/px 反比"。

    只依赖 priors.py（不需要 fusion），所以比 ⑦ 更早能跑。
    """

    REF_PX = 180.0
    REF_Z = 4.0

    def setUp(self):
        self.priors = S.require_module("priors")
        self.fn = S.require_callable(self.priors, "perspective_prior", "spec §3 冻结签名")

    def test_07b_perspective_prior_calibration_and_inverse(self):
        at_ref = float(self.fn(self.REF_PX, self.REF_PX, self.REF_Z))
        double_px = float(self.fn(2.0 * self.REF_PX, self.REF_PX, self.REF_Z))
        half_px = float(self.fn(0.5 * self.REF_PX, self.REF_PX, self.REF_Z))
        S.announce("⑦b perspective_prior", at_ref=at_ref, double_px=double_px,
                   half_px=half_px, need="ref 点 == ref_z，2×px → 1/2 深度")
        self.assertAlmostEqual(
            at_ref, self.REF_Z, delta=1e-6,
            msg=f"⑦b 校准点不自洽：torso_px==ref_px 时应返回 ref_z={self.REF_Z}，实际 {at_ref}",
        )
        self.assertAlmostEqual(
            double_px, self.REF_Z / 2.0, delta=1e-6,
            msg=f"⑦b 不是 1/px 反比：像素长 ×2 后 {double_px}（应 {self.REF_Z / 2.0}）",
        )
        self.assertAlmostEqual(
            half_px, self.REF_Z * 2.0, delta=1e-6,
            msg=f"⑦b 不是 1/px 反比：像素长 ×0.5 后 {half_px}（应 {self.REF_Z * 2.0}）",
        )

    def test_07c_torso_px_length(self):
        fn = S.require_callable(self.priors, "torso_px_length", "spec §3 冻结签名")
        cfg = S.cfg()
        got = None
        used = None
        candidates = [
            ("neck+pelvis", {"neck": (320.0, 100.0), "pelvis": (320.0, 300.0)}),
            ("neck+hips", {"neck": (320.0, 100.0), "hips": (320.0, 300.0)}),
            ("shoulders+hips", {
                "neck": (320.0, 120.0), "pelvis": (320.0, 300.0),
                "left_shoulder": (290.0, 120.0), "right_shoulder": (350.0, 120.0),
                "left_hip": (300.0, 300.0), "right_hip": (340.0, 300.0),
            }),
        ]
        for label, kp in candidates:
            val = fn(kp, cfg)
            if val is not None:
                got, used = float(val), label
                break
        S.announce("⑦c torso_px_length", kp_naming=used or "(全部候选都返回 None)",
                   value=got, missing_returns=fn({}, cfg))
        self.assertIsNotNone(
            got,
            f"⑦c 所有关键点命名都拿不到躯干像素长（试过 {[c[0] for c in candidates]}）："
            "颈→骨盆线段应该能算出正值",
        )
        self.assertGreater(got, 0.0, f"⑦c 躯干像素长必须为正，实际 {got}")
        self.assertIsNone(
            fn({}, cfg),
            "⑦c 关键点缺失时应返回 None（签名 float | None），不能编一个数出来",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
