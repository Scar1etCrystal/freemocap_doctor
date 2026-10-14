"""⑧ ⑨ One-Euro 时序滤波（spec §5.6）。

纯 numpy 合成，不依赖 backend/masks/fusion，可独立运行。
断言（不放宽）：
  ⑧ 静止段残余抖动 RMS 比输入降 > 60%；
  ⑨ fps=30 的阶跃延迟 < 3 帧，且不比"同静止平滑度的普通低通（EMA）"更慢。
"""

from __future__ import annotations

import unittest

import numpy as np

from depth_prior.tests import _support as S


def _ema(x: np.ndarray, alpha: float) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    y = np.empty_like(x)
    acc = float(x[0])
    for i, xi in enumerate(x):
        acc += alpha * (float(xi) - acc)
        y[i] = acc
    return y


def _rise_frames(y: np.ndarray, *, y0: float, step: float, frac: float, start: int) -> int | None:
    """阶跃后第一次达到 y0+frac*step 的帧数（找不到返回 None）。"""
    thr = y0 + frac * step
    idx = np.nonzero(np.asarray(y, dtype=np.float64)[start:] >= thr)[0]
    return None if idx.size == 0 else int(idx[0])


class OneEuroBehaviour(unittest.TestCase):
    FPS = 30.0
    MIN_CUTOFF = 0.8
    BETA = 0.02
    D_CUTOFF = 1.0

    def setUp(self):
        self.filters = S.require_module("filters")
        self.one_euro = S.require_callable(self.filters, "one_euro", "spec §3 冻结签名")

    def _run(self, x: np.ndarray):
        out = self.one_euro(np.asarray(x, dtype=np.float64), fps=self.FPS,
                            min_cutoff=self.MIN_CUTOFF, beta=self.BETA, d_cutoff=self.D_CUTOFF)
        self.assertIsInstance(out, tuple, "one_euro 必须返回 (y, FilterDiag) 二元组")
        self.assertEqual(len(out), 2, "one_euro 必须返回 (y, FilterDiag) 二元组")
        y, diag = out
        y = np.asarray(y, dtype=np.float64)
        self.assertEqual(y.shape, np.asarray(x).shape, "输出长度必须与输入一致")
        for attr in ("min_cutoff", "beta", "d_cutoff", "name"):
            self.assertTrue(hasattr(diag, attr), f"FilterDiag 缺字段 {attr}（spec §3）")
        return y, diag

    # ⑧ -----------------------------------------------------------------
    def test_08_static_jitter_reduction(self):
        rng = np.random.default_rng(0)
        n, truth_z = 300, 4.0
        truth = np.full(n, truth_z, dtype=np.float64)
        x = truth + rng.normal(0.0, 0.02, n)
        y, _diag = self._run(x)

        tail = slice(100, n)  # 去掉启动瞬态
        in_rms = float(np.sqrt(np.mean((x[tail] - truth[tail]) ** 2)))
        out_rms = float(np.sqrt(np.mean((y[tail] - truth[tail]) ** 2)))
        drop = 1.0 - out_rms / in_rms
        S.announce("⑧ 静止段", in_rms_m=in_rms, out_rms_m=out_rms, drop=drop,
                   need="drop > 0.60")
        self.assertGreater(in_rms, 0.0, "合成输入没有抖动，测试无效")
        self.assertGreater(
            drop, 0.60,
            f"⑧ 静止段残余抖动只降了 {S.pct(drop)}（要求 > 60%）："
            f"输入 RMS={in_rms:.6f} m → 输出 RMS={out_rms:.6f} m",
        )

    # ⑨ -----------------------------------------------------------------
    def test_09_step_lag_and_plain_lowpass(self):
        n, start, y0, step = 120, 30, 3.0, 1.0
        x = np.where(np.arange(n) < start, y0, y0 + step).astype(np.float64)
        y, diag = self._run(x)

        r50 = _rise_frames(y, y0=y0, step=step, frac=0.50, start=start)
        r90 = _rise_frames(y, y0=y0, step=step, frac=0.90, start=start)
        self.assertIsNotNone(r50, f"⑨ 阶跃后 120 帧内都没到 50%（末值 {y[-1]:.4f}）")

        # 公平对照：静止平滑度等同的普通一阶低通（One-Euro 静止时 cutoff=min_cutoff）
        alpha_rest = 1.0 / (1.0 + self.FPS / (2.0 * np.pi * self.MIN_CUTOFF))
        y_ema = _ema(x, alpha_rest)
        e50 = _rise_frames(y_ema, y0=y0, step=step, frac=0.50, start=start)
        e90 = _rise_frames(y_ema, y0=y0, step=step, frac=0.90, start=start)

        diag_lag = getattr(diag, "lag_frames_p50", float("nan"))
        S.announce("⑨ 阶跃(1m，判据 50%)", one_euro_frames=r50, one_euro_90pct=r90,
                   ema_alpha_rest=alpha_rest, ema_frames=e50, ema_90pct=e90,
                   diag_lag_p50=float(diag_lag), need="one_euro < 3 帧 且 ≤ EMA")

        self.assertLess(
            float(r50), 3.0,
            f"⑨ 阶跃延迟 {r50} 帧（判据：50% 上升时间），要求 < 3 帧（fps=30）",
        )
        self.assertIsNotNone(e50, "对照 EMA 没响应，测试无效")
        self.assertLessEqual(
            float(r50), float(e50),
            f"⑨ One-Euro 比普通低通更慢：one_euro={r50} 帧 > EMA={e50} 帧（要求不得更慢）",
        )
        if np.isfinite(diag_lag):
            self.assertLess(
                float(diag_lag), 3.0,
                f"⑨ FilterDiag.lag_frames_p50={diag_lag}，要求 < 3 帧",
            )
        else:
            print("    · ⑨ 提示：FilterDiag.lag_frames_p50 是 NaN（诊断未填），"
                  "本测试用自测的 50% 上升时间判定")


if __name__ == "__main__":
    unittest.main(verbosity=2)
