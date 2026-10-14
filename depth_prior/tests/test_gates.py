"""③ 相对深度闸门（spec §0 / §5.2）——**防退化回归测试，最重要的一条**。

铁律：`DepthMap.kind == "metric"` 才允许进融合主项；`kind == "relative"` 只许走
`priors.affine_align_to_metric()`，`fusion` 必须 raise，**不许静默当米用**。

断言：
  1. 伪造 relative 的 DepthMap 进 `fusion.fuse` → 必须抛"语义闸门"级异常
     （MetricRequired，或消息里明确提到 relative/相对/metric/度量）；
     单纯 TypeError（签名不匹配）不算闸门，算失败——那说明闸门没接上。
  2. 阳性对照：合法 FramePrior 列表进 fuse 必须能跑通（证明不是"一律拒绝"）。
"""

from __future__ import annotations

import importlib
import inspect
import unittest

import numpy as np

from depth_prior.tests import _support as S


class RelativeDepthGate(unittest.TestCase):
    def setUp(self):
        self.types = importlib.import_module("depth_prior.types")

    def _fuse(self):
        fusion = S.require_module("fusion")
        return S.require_callable(fusion, "fuse", "spec §3 冻结签名")

    def _semantic_gate(self, exc: BaseException) -> bool:
        if isinstance(exc, self.types.MetricRequired):
            return True
        if isinstance(exc, TypeError):
            return False  # 签名/类型错误 ≠ 语义闸门
        msg = str(exc).lower()
        return any(k in msg for k in ("relative", "相对", "metric", "度量"))

    def _fuse_entries(self, dm, fuse):
        """所有能把 DepthMap 送进 fuse 的调用形式（按冻结签名的鸭子类型）。"""
        cfg = S.cfg()
        entries = [("fuse([relative_dm], cfg)", lambda: fuse([dm], cfg))]
        try:
            params = inspect.signature(fuse).parameters
        except (TypeError, ValueError):
            params = {}
        for kw in ("depth", "depth_map", "depthmap", "dm", "depthmap_metric"):
            if kw in params:
                entries.append(
                    (f"fuse([], cfg, {kw}=relative_dm)",
                     (lambda k=kw: fuse([], cfg, **{k: dm})))
                )
        return entries

    def test_03_fuse_rejects_relative_depthmap(self):
        fuse = self._fuse()
        dm = S.relative_depthmap()
        self.assertEqual(dm.kind, "relative", "测试自身构造错了：伪造图不是 relative")
        self.assertFalse(dm.is_metric)

        semantic, other = [], []
        for label, fn in self._fuse_entries(dm, fuse):
            try:
                out = fn()
            except BaseException as exc:  # noqa: BLE001
                (semantic if self._semantic_gate(exc) else other).append(
                    (label, type(exc).__name__, str(exc)))
            else:
                other.append((label, "NO-RAISE", f"返回了 {type(out).__name__}（静默接受！）"))

        S.announce("③ relative → fuse",
                   entries_tried=len(semantic) + len(other),
                   semantic_gate=len(semantic), rejected_other=len(other))
        for label, kind, msg in semantic:
            print(f"    · ③ 闸门生效：{label} → {kind}: {msg[:120]}")
        for label, kind, msg in other:
            print(f"    · ③ 非闸门结果：{label} → {kind}: {msg[:120]}")

        self.assertTrue(
            semantic,
            "③ relative 深度没有被语义闸门拦住（spec §0：fusion 对 relative 必须 raise）。"
            f"尝试的入口结果：{other or '没有任何入口抛异常——静默把相对深度当米用了'}",
        )

    def test_03b_metric_input_still_works(self):
        """阳性对照：闸门不能是"一律拒绝"，合法度量先验必须能融。"""
        frames = S.frame_priors(S.root_z_ramp(12, 3.5, 4.5))
        out = self._fuse()(frames, S.cfg())
        self.assertIsInstance(out, tuple, "fuse 必须返回 (z_raw_m, confidence)")
        self.assertEqual(len(out), 2, "fuse 必须返回 (z_raw_m, confidence)")
        z_raw, conf = out
        z_raw = np.asarray(z_raw, dtype=np.float64)
        conf = np.asarray(conf, dtype=np.float64)
        self.assertEqual(z_raw.shape, (len(frames),),
                         f"z_raw_m 长度应为 {len(frames)}，实际 {z_raw.shape}")
        self.assertEqual(conf.shape, z_raw.shape, "confidence 必须与 z_raw_m 同长")
        self.assertTrue(np.all(np.isfinite(z_raw)), "z_raw_m 含 NaN/Inf")
        S.announce("③b 阳性对照（合法 metric）", n=len(frames),
                   z_min=float(z_raw.min()), z_max=float(z_raw.max()),
                   conf_mean=float(conf.mean()))

    def test_03c_masks_gate_if_available(self):
        """同一个闸门在 masks 入口也要生效（DepthMap 直接进 masks 的地方）。"""
        try:
            masks = importlib.import_module("depth_prior.masks")
        except BaseException as exc:  # noqa: BLE001
            self.skipTest(f"[skip] depth_prior.masks 尚不可用：{type(exc).__name__}: {exc}")
        fn = S.require_callable(masks, "torso_pelvis_stats", "spec §3 冻结签名")

        h = w = 240
        mask = np.zeros((h, w), dtype=bool)
        mask[60:200, 90:150] = True          # 人形框 140x60 = 8400 px（> mask.min_px 400）
        kp = {"neck": (120.0, 70.0), "pelvis": (120.0, 190.0)}
        cfg = S.cfg()

        rel = S.relative_depthmap(h=h, w=w)
        raised = None
        try:
            fn(rel, mask, kp, cfg)
        except BaseException as exc:  # noqa: BLE001
            raised = exc
        self.assertIsNotNone(
            raised, "③c relative DepthMap 进 masks.torso_pelvis_stats 被静默接受了")
        self.assertTrue(self._semantic_gate(raised),
                        f"③c masks 入口抛的不是语义闸门：{type(raised).__name__}: {raised}")

        met = S.metric_depthmap(value=4.0, h=h, w=w)
        stats = fn(met, mask, kp, cfg)
        self.assertIsInstance(stats, list, "③c torso_pelvis_stats 必须返回 list[RegionStat]")
        S.announce("③c masks 闸门", relative_raises=type(raised).__name__,
                   metric_regions=len(stats))


if __name__ == "__main__":
    unittest.main(verbosity=2)
