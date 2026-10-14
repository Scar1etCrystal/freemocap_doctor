"""⑩ CLI 端到端（spec §5.7）。

`python -m depth_prior.cli --synthetic` 产出 `depth_prior.npz`，
字段与 `RootZTrack` 一致，并能被 `RootZTrack.load` 读回。

在临时目录里跑（不往仓库里写文件），不 import torch、不读权重。
"""

from __future__ import annotations

import dataclasses
import importlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from depth_prior.tests import _support as S

TIMEOUT_S = 420


class CliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.cli = S.require_module("cli")
        self.types = importlib.import_module("depth_prior.types")

    def _env(self):
        env = dict(os.environ)
        root = str(S.REPO_ROOT)
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"   # Windows 控制台默认 GBK，CLI 输出是 UTF-8
        return env

    @staticmethod
    def _run(cmd, **kwargs):
        """统一 UTF-8 解码，避免 Windows 本地编码（GBK）把输出解码炸掉。"""
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", **kwargs)

    def test_10_cli_synthetic_npz_roundtrip(self):
        # 依赖缺失 → skip 并打印缺什么（不假装通过，也不算实现的失败）
        missing = []
        for mod in ("fusion", "filters"):
            try:
                importlib.import_module(f"depth_prior.{mod}")
            except BaseException as exc:  # noqa: BLE001
                missing.append(f"{mod}({type(exc).__name__})")
        if missing:
            self.skipTest(
                "[skip] `--synthetic` 全链路（stage=full）还需要模块：" + ", ".join(missing)
                + " —— 等 w3 落地 fusion/filters 后再跑 ⑩"
            )

        with tempfile.TemporaryDirectory() as td:
            env = self._env()
            help_run = self._run(
                [sys.executable, "-m", "depth_prior.cli", "--help"],
                cwd=td, env=env, timeout=120,
            )
            help_text = help_run.stdout + help_run.stderr
            out_flag = next((f for f in ("--out", "--output", "-o") if f in help_text), None)
            npz = Path(td) / "depth_prior.npz"
            cmd = [sys.executable, "-m", "depth_prior.cli", "--synthetic"]
            if out_flag:
                cmd += [out_flag, str(npz)]

            run = self._run(cmd, cwd=td, env=env, timeout=TIMEOUT_S)
            S.announce("⑩ CLI", cmd=" ".join(cmd[1:]), returncode=run.returncode,
                       out_flag=out_flag or "(无)")
            self.assertEqual(
                run.returncode, 0,
                f"⑩ CLI 退出码 {run.returncode}\n--- stdout ---\n{run.stdout[-1500:]}"
                f"\n--- stderr ---\n{run.stderr[-1500:]}",
            )

            if not npz.exists():
                found = sorted(Path(td).rglob("*.npz"))
                self.assertTrue(
                    found,
                    f"⑩ 没生成 depth_prior.npz（工作目录 {td} 下没有任何 .npz）\n"
                    f"--- stdout ---\n{run.stdout[-1500:]}",
                )
                npz = found[0]

            track = self.types.RootZTrack.load(npz)
            expected = [f.name for f in dataclasses.fields(self.types.RootZTrack)]
            missing = [k for k in expected if not hasattr(track, k)]
            self.assertFalse(missing, f"⑩ 读回的 RootZTrack 缺字段 {missing}（契约 {expected}）")

            frames = np.asarray(track.frames)
            z_raw = np.asarray(track.z_raw_m, dtype=np.float64)
            z_m = np.asarray(track.z_m, dtype=np.float64)
            conf = np.asarray(track.confidence, dtype=np.float64)
            self.assertEqual(frames.ndim, 1, "⑩ frames 必须是 (T,)")
            self.assertEqual(z_raw.shape, frames.shape, "⑩ z_raw_m 必须与 frames 同长")
            self.assertEqual(z_m.shape, frames.shape, "⑩ z_m 必须与 frames 同长")
            self.assertEqual(conf.shape, frames.shape, "⑩ confidence 必须与 frames 同长")
            self.assertGreater(frames.size, 0, "⑩ 产出是空轨道")
            self.assertTrue(np.all(np.isfinite(z_raw)), "⑩ z_raw_m 含 NaN/Inf")
            self.assertTrue(np.all(np.isfinite(z_m)), "⑩ z_m 含 NaN/Inf")
            self.assertTrue(np.all((conf >= 0.0) & (conf <= 1.0)),
                            f"⑩ confidence 必须在 0..1，实际 {conf.min()}~{conf.max()}")
            self.assertIsInstance(track.diag, dict, f"⑩ diag 必须是 dict，实际 {type(track.diag)}")
            S.announce("⑩ npz 读回", file=npz.name, T=int(frames.size),
                       z_range=f"{z_raw.min():.3f}~{z_raw.max():.3f}",
                       conf_mean=float(conf.mean()), diag_keys=sorted(map(str, track.diag))[:8])


if __name__ == "__main__":
    unittest.main(verbosity=2)
