"""④ ⑤ 尺度锚定与尺度报警（spec §5.3）。

④ 合成场景根节点 Z 从 3.0 m 走到 5.0 m → `z_raw_m` 最大相对误差 < 2%；
⑤ 把整体深度乘 2 再喂进去（模拟尺度漂）→ 必须报警（fuse 的契约出口是 confidence），
   不许静默通过。

合成数据全是解析式：真值斜坡 + 躯干像素长 ∝ 1/z，不读任何外部文件。
"""

from __future__ import annotations

import unittest

import numpy as np

from depth_prior.tests import _support as S

N_FRAMES = 180
Z0, Z1 = 3.0, 5.0


class ScaleAnchor(unittest.TestCase):
    def setUp(self):
        self.fusion = S.require_module("fusion")
        self.fuse = S.require_callable(self.fusion, "fuse", "spec §3 冻结签名")
        self.cfg = S.cfg()

    def _fuse(self, frames):
        out = self.fuse(frames, self.cfg)
        self.assertIsInstance(out, tuple, "fuse 必须返回 (z_raw_m, confidence)")
        self.assertEqual(len(out), 2, "fuse 必须返回 (z_raw_m, confidence)")
        z_raw = np.asarray(out[0], dtype=np.float64)
        conf = np.asarray(out[1], dtype=np.float64)
        self.assertEqual(z_raw.shape, (len(frames),),
                         f"z_raw_m 应为 {len(frames)} 长，实际 {z_raw.shape}")
        self.assertEqual(conf.shape, z_raw.shape, "confidence 必须与 z_raw_m 同长")
        self.assertTrue(np.all(np.isfinite(z_raw)), "z_raw_m 含 NaN/Inf")
        return z_raw, conf

    # ④ -----------------------------------------------------------------
    def test_04_metric_scale_anchor_3m_to_5m(self):
        z_true = S.root_z_ramp(N_FRAMES, Z0, Z1)
        frames = S.frame_priors(z_true)
        z_raw, conf = self._fuse(frames)
        err = np.abs(z_raw - z_true) / z_true
        max_err = float(err.max())
        S.announce("④ 3.0→5.0 m 锚定", frames=N_FRAMES,
                   z_raw_min=float(z_raw.min()), z_raw_max=float(z_raw.max()),
                   max_err_pct=100.0 * max_err, mean_err_pct=100.0 * float(err.mean()),
                   conf_mean=float(conf.mean()), need="max_err < 2%")
        self.assertLess(
            max_err, 0.02,
            f"④ z_raw_m 最大相对误差 {S.pct(max_err)} ≥ 2%（真值 3.0→5.0 m）："
            f"z_raw 范围 {z_raw.min():.4f}~{z_raw.max():.4f} m",
        )

    # ⑤ -----------------------------------------------------------------
    def test_05_doubled_scale_must_alarm(self):
        z_true = S.root_z_ramp(N_FRAMES, Z0, Z1)

        z_ok, c_ok = self._fuse(S.frame_priors(z_true))
        # 整体深度乘 2：度量尺度漂了，躯干透视项仍然是正确的绝对量
        z_bad, c_bad = self._fuse(S.frame_priors(z_true, depth_median=2.0 * z_true))

        conf_ok = float(np.mean(c_ok))
        conf_bad = float(np.mean(c_bad))
        S.announce("⑤ 深度×2", conf_ok=conf_ok, conf_bad=conf_bad,
                   ratio=conf_bad / max(conf_ok, 1e-12),
                   z_raw_ok_range=f"{z_ok.min():.3f}~{z_ok.max():.3f}",
                   z_raw_bad_range=f"{z_bad.min():.3f}~{z_bad.max():.3f}",
                   need="conf_bad < 0.6*conf_ok 且 < 0.5")
        for attr in ("LAST_ALARMS", "alarms", "warnings", "LAST_REPORT"):
            if hasattr(self.fusion, attr):
                print(f"    · ⑤ 提示：fusion.{attr} = {getattr(self.fusion, attr)!r}"[:300])

        self.assertGreater(conf_ok, 0.5,
                           f"⑤ 前置条件不成立：正确尺度下置信度就只有 {conf_ok:.3f}，"
                           "无法判定'漂了以后掉没掉'")
        self.assertLess(
            conf_bad, 0.6 * conf_ok,
            f"⑤ 尺度整体 ×2 后置信度没明显下降（{conf_ok:.3f} → {conf_bad:.3f}）——"
            "等于静默把漂了的尺度当对的用了",
        )
        self.assertLess(
            conf_bad, 0.5,
            f"⑤ 尺度整体 ×2 后置信度仍有 {conf_bad:.3f}（要求 < 0.5，即必须报警）",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
