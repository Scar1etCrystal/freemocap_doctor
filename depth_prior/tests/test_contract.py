"""① ② 后端契约（spec §5.1）。

① 无 torch 时 `backend.load(cfg)` 抛 `BackendUnavailable`，不允许裸 `ImportError` 漏出去；
② `SyntheticBackend(kind="metric")` 的 `kind == "metric"`，`infer()` 的形状 / 单位 / 数值正确。

零推理：不加载权重、不 import torch（① 反而要把 torch 藏起来）。
"""

from __future__ import annotations

import importlib
import sys
import unittest

import numpy as np

from depth_prior.tests import _support as S


class BackendContract(unittest.TestCase):
    def setUp(self):
        self.types = importlib.import_module("depth_prior.types")
        self.backend = S.require_module("backend")
        self.load = S.require_callable(self.backend, "load", "spec §3 冻结签名")

    # ① -----------------------------------------------------------------
    def test_01_load_without_torch_raises_backend_unavailable(self):
        cfg = S.cfg()
        hidden = ("torch", "torchvision")
        saved: dict[str, object] = {}
        for name in hidden:
            if name in sys.modules:
                saved[name] = sys.modules[name]
            sys.modules[name] = None  # 让 `import torch` 直接 ImportError
        raised: BaseException | None = None
        try:
            self.load(cfg)
        except BaseException as exc:  # noqa: BLE001 - 就是要看抛了什么
            raised = exc
        finally:
            for name in hidden:
                if name in saved:
                    sys.modules[name] = saved[name]
                else:
                    sys.modules.pop(name, None)

        S.announce("① 无 torch 调 load()", raised=type(raised).__name__ if raised else "None(没抛)")
        self.assertIsNotNone(
            raised, "① 无 torch 时 load() 没有抛异常：应抛 BackendUnavailable（spec §5.1）"
        )
        self.assertNotIsInstance(
            raised, ImportError,
            f"① 裸 ImportError 漏到调用方了：{type(raised).__name__}: {raised}"
            "（必须包成 BackendUnavailable）",
        )
        self.assertIsInstance(
            raised, self.types.BackendUnavailable,
            f"① 无 torch 时应抛 BackendUnavailable，实际 {type(raised).__name__}: {raised}",
        )

    def test_01b_load_never_leaks_raw_dependency_error(self):
        """正常环境下 load() 要么给后端，要么给 BackendUnavailable；不许裸依赖异常。"""
        raised: BaseException | None = None
        got = None
        try:
            got = self.load(S.cfg())
        except BaseException as exc:  # noqa: BLE001
            raised = exc
        leaked = (ImportError, ModuleNotFoundError, FileNotFoundError, OSError)
        S.announce("①b 正常环境调 load()",
                   result=type(got).__name__ if got is not None else f"raise {type(raised).__name__}")
        self.assertNotIsInstance(
            raised, leaked,
            f"①b load() 漏出裸依赖异常 {type(raised).__name__}: {raised}（应包成 BackendUnavailable）",
        )
        if raised is not None:
            self.assertIsInstance(
                raised, self.types.BackendUnavailable,
                f"①b load() 只允许抛 BackendUnavailable，实际 {type(raised).__name__}: {raised}",
            )

    # ② -----------------------------------------------------------------
    def test_02_synthetic_backend_contract(self):
        self.assertTrue(
            hasattr(self.backend, "DepthBackend"),
            "② backend 模块没有 DepthBackend 基类（spec §3 冻结签名）",
        )
        cls = S.require_attr(self.backend, "SyntheticBackend", "spec §5.1")
        try:
            be = cls(kind="metric")
        except TypeError as exc:
            be = cls()
            print(f'    · ② 提示：SyntheticBackend(kind="metric") 不接受 kind= 关键字（{exc}），'
                  "已退回无参构造")

        self.assertEqual(getattr(be, "kind", None), "metric",
                         f'② SyntheticBackend.kind 必须是 "metric"，实际 {getattr(be, "kind", None)!r}')
        self.assertTrue(callable(getattr(be, "infer", None)), "② 后端缺 infer(rgb)")

        rgb = np.zeros((120, 160, 3), dtype=np.uint8)  # 自造帧，不读任何文件
        dm = be.infer(rgb)
        self.assertIsInstance(dm, self.types.DepthMap, "② infer 必须返回 DepthMap")
        self.assertEqual(dm.kind, "metric", "② 合成后端必须声明 metric")
        self.assertEqual(dm.unit, "m", f'② 单位必须是 "m"，实际 {dm.unit!r}')
        self.assertEqual(np.asarray(dm.depth).ndim, 2, "② depth 必须是 (H, W)")
        self.assertEqual(np.asarray(dm.depth).shape, rgb.shape[:2],
                         "② depth 形状必须与输入帧一致")
        d = np.asarray(dm.depth, dtype=np.float64)
        self.assertTrue(np.all(np.isfinite(d)), "② depth 含 NaN/Inf")
        self.assertTrue(np.all(d > 0.0), "② metric 深度必须为正（米）")
        S.announce("② SyntheticBackend", kind=be.kind, shape=str(np.asarray(dm.depth).shape),
                   unit=dm.unit, dmin=float(d.min()), dmax=float(d.max()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
