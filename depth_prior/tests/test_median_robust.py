"""⑥ 中位数抗离群（spec §5.4）。

Mask 内塞进 ~30% 的"四肢"离群像素（比躯干远 1.5 m）→ 躯干区域的中位数观测偏移 < 0.05 m。

自检（防止"离群像素没落在区域内"导致假通过）：
先证明离群像素**确实进了被测区域** —— 用 p90 必须被抬起来判定；
只有 p90 动了，中位数不动才算"抗离群"。
"""

from __future__ import annotations

import unittest

import numpy as np

from depth_prior.tests import _support as S

H, W = 480, 640
TORSO_Z = 4.0
OUTLIER_Z = 5.5          # 差 1.5 m
BOX = (280, 400, 140, 420)   # x0, x1, y0, y1 —— 人体框
NECK = (340.0, 160.0)
PELVIS = (340.0, 400.0)
BAND = (320, 360, 250, 310)  # 仅用于文档/诊断，不再决定离群像素位置


def _scene(with_outliers: bool):
    """整幅 depth 给躯干距离；离群像素按 spec §5.4 在 **Mask 内均匀撒 30%**。

    均匀撒（而不是只撒某个椭圆带）的原因：躯干/骨盆区域的精确形状不在冻结契约里，
    均匀撒保证任何子区域里都是 ~30% 离群 → 判定与实现选区的具体形状无关。
    """
    depth = np.full((H, W), TORSO_Z, dtype=np.float32)
    mask = np.zeros((H, W), dtype=bool)
    x0, x1, y0, y1 = BOX
    mask[y0:y1, x0:x1] = True
    n_out = 0
    if with_outliers:
        yy, xx = np.mgrid[0:H, 0:W]
        pattern = ((yy * 3 + xx) % 10) < 3          # ~30% 密度
        sel = mask & pattern
        depth[sel] = OUTLIER_Z
        n_out = int(sel.sum())
    return depth, mask, n_out


class MedianRobust(unittest.TestCase):
    def setUp(self):
        self.masks = S.require_module("masks")
        self.stats_fn = S.require_callable(self.masks, "torso_pelvis_stats",
                                           "spec §3 冻结签名")
        self.cfg = S.cfg()

    # -- 关键点命名不在冻结契约里：逐个候选试，并打印用的是哪个 -------------
    def _candidates(self):
        return [
            ("neck+pelvis", {"neck": NECK, "pelvis": PELVIS}),
            ("neck+hips", {"neck": NECK, "hips": PELVIS}),
            ("head_neck+pelvis", {"head_neck": NECK, "pelvis": PELVIS}),
            ("neck+pelvis_mid", {"neck": NECK, "pelvis_mid": PELVIS}),
            ("shoulders+hips", {
                "left_shoulder": (300.0, 160.0), "right_shoulder": (380.0, 160.0),
                "left_hip": (300.0, 400.0), "right_hip": (380.0, 400.0),
                "neck": NECK, "pelvis": PELVIS,
            }),
            ("none", None),
        ]

    def _region(self, depth_arr, mask, name="torso"):
        from depth_prior.types import DepthMap, KIND_METRIC

        # 契约签名收 DepthMap（带 kind 闸门），不是裸 ndarray
        depth = DepthMap(depth=depth_arr, kind=KIND_METRIC, unit="m", backend="synthetic")
        last = None
        for label, kp in self._candidates():
            try:
                stats = self.stats_fn(depth, mask, kp, self.cfg)
            except BaseException as exc:  # noqa: BLE001 - 容错：换一种关键点命名
                last = f"{label}: {type(exc).__name__}: {exc}"
                continue
            if not stats:
                last = f"{label}: 返回空列表"
                continue
            for st in stats:
                if getattr(st, "name", None) == name:
                    return st, label
            last = f"{label}: 区域名 {[getattr(s, 'name', '?') for s in stats]}"
        self.fail(f"⑥ 拿不到 {name!r} 区域统计（试过全部关键点命名）：{last}")

    def test_06_median_robust_to_limb_outliers(self):
        depth_clean, mask, _ = _scene(False)
        depth_out, _, n_out = _scene(True)

        st_clean, label = self._region(depth_clean, mask)
        st_out, _ = self._region(depth_out, mask)

        d_med = abs(float(st_out.depth_median_m) - float(st_clean.depth_median_m))
        p90_delta = float(st_out.depth_p90_m) - float(st_clean.depth_p90_m)
        scatter_density = n_out / max(int(mask.sum()), 1)
        exp_out_in_region = scatter_density * int(st_clean.px)
        S.announce("⑥ 离群像素抗性", kp_naming=label,
                   mask_px=int(mask.sum()), scatter_density=scatter_density,
                   region_px=int(st_clean.px),
                   outlier_in_region_est=round(exp_out_in_region),
                   outlier_share_est=exp_out_in_region / max(int(st_clean.px), 1),
                   median_clean=float(st_clean.depth_median_m),
                   median_out=float(st_out.depth_median_m),
                   median_shift_m=d_med, p90_delta_m=p90_delta,
                   need="median_shift < 0.05 m")

        # 自检：离群像素必须真的落在被测区域内（p90 被抬起），否则这条测试没意义
        self.assertGreater(
            p90_delta, 1.0,
            f"⑥ 自检失败：注入 {n_out} 个 {OUTLIER_Z} m 离群像素后区域 p90 只动了 "
            f"{p90_delta:.4f} m —— 离群像素没进被测区域，中位数抗性无从判定",
        )
        # 主断言：中位数不动
        self.assertLess(
            d_med, 0.05,
            f"⑥ 中位数观测偏移 {d_med:.4f} m ≥ 0.05 m（区域内约 "
            f"{S.pct(exp_out_in_region / max(int(st_clean.px), 1))} 离群像素、"
            f"深度差 {OUTLIER_Z - TORSO_Z:.1f} m）",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
