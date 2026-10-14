"""命令行入口（w1，spec §5 验收 7）。

用法（推荐 `-m` 形式）::

    python -m depth_prior.cli --synthetic --out depth_prior.npz          # 全链路
    python -m depth_prior.cli --synthetic --stage backend                # 只跑后端（不依赖 w2/w3）
    python -m depth_prior.cli --frames <帧目录> --masks <mask目录> --out depth_prior.npz

阶段（`--stage`）：
    * `backend` —— 只做深度（只需要 `backend.py`，w2/w3 未就绪时也能跑，产物是诊断 npz）
    * `priors`  —— 深度 + mask 统计 + 躯干像素长（需要 w2 的 `masks.py`/`priors.py`）
    * `full`    —— 全链路，写出 `RootZTrack` 到 `--out`（需要 w2+w3）

退出码：`0` 正常；`2` 参数/输入问题；`3` 依赖缺失（缺模块/缺 torch/缺权重）；
`4` 运行期错误。缺模块时打印**归属**（spec §2）与可用的替代命令，不会丢一堆 traceback。

实现细节（对应 spec §2 的 ⚠️ 警告）：本文件同时支持 `python -m depth_prior.cli` 与
`python depth_prior/cli.py` 两种入口。后者会让 `depth_prior/` 进入 `sys.path[0]`，而
`depth_prior/types.py` 会**遮蔽标准库 `types`**（`enum`/`re`/`argparse` 全炸，实测
`ImportError: cannot import name 'MappingProxyType' from 'types'`）。因此这里在任何重量级
import 之前**把 `depth_prior/` 从 sys.path 摘掉、只放仓库根**——严格遵循「别把
`depth_prior/` 加进 sys.path」，`-m` 形式的语义不受影响。
"""

from __future__ import annotations

import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)
if __name__ == "__main__" and _sys.path:
    # 去掉脚本自身目录（否则 depth_prior/types.py 遮蔽 stdlib types），把仓库根放到最前
    _sys.path[:] = [p for p in _sys.path if _os.path.abspath(p or _os.getcwd()) != _HERE]
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import argparse  # noqa: E402
import dataclasses  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import numpy as np  # noqa: E402

if __package__ in (None, ""):
    from depth_prior import backend as backend_mod
    from depth_prior import types
else:
    from . import backend as backend_mod
    from . import types

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MISSING_DEP = 3
EXIT_RUNTIME = 4

STAGES = ("backend", "priors", "full")

# spec §2：缺模块时报出归属，别让人猜
MODULE_OWNER = {
    "masks": "w2（spec §2：Mask 取深度 + 躯干透视先验）",
    "priors": "w2（spec §2：Mask 取深度 + 躯干透视先验）",
    "fusion": "w3（spec §2：融合求解）",
    "filters": "w3（spec §2：One-Euro 时序滤波）",
}

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff")


# ---------------------------------------------------------------------------
# 小工具


def _log(msg: str = "") -> None:
    print(f"[cli] {msg}", flush=True)


def _err(msg: str) -> None:
    print(f"[cli][错误] {msg}", file=_sys.stderr, flush=True)


def _try_import(name: str) -> tuple[Any | None, str]:
    """惰性导入 `depth_prior.<name>`；返回 `(模块 | None, 原因)`。"""
    dotted = f"depth_prior.{name}" if __package__ in (None, "") else f"{__package__}.{name}"
    try:
        return importlib.import_module(dotted), ""
    except ModuleNotFoundError as exc:
        owner = MODULE_OWNER.get(name, "?")
        if exc.name in (dotted, f"depth_prior.{name}", name):
            path = _os.path.join(_HERE, f"{name}.py")   # 注意 _HERE 是 str（早于 pathlib 导入）
            return None, (f"缺少模块 {dotted}（归属：{owner}）—— 文件不存在或不可导入：{path}")
        return None, (f"模块 {dotted} 存在，但它自己缺依赖：ModuleNotFoundError: {exc.name}"
                      f"（归属：{owner}）")
    except Exception as exc:  # 语法错误/导入期异常也要给可读信息
        return None, f"导入 {dotted} 失败：{type(exc).__name__}: {exc}"


def _require(name: str, stage: str, args: argparse.Namespace) -> Any | None:
    mod, why = _try_import(name)
    if mod is None:
        _err(why)
        _err(f"`--stage {stage}` 需要该模块。可先只跑后端："
             f"python -m depth_prior.cli --synthetic --stage backend"
             + (f" --out {args.out}" if args.out else ""))
        return None
    return mod


def _as_plain(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return backend_mod.to_plain(dataclasses.asdict(obj))
    return backend_mod.to_plain(obj)


def _parse_set(pairs: list[str]) -> dict[str, Any]:
    """`--set backend.max_depth=20` → 嵌套 dict 覆盖。"""
    out: dict[str, Any] = {}
    for item in pairs or []:
        if "=" not in item:
            raise ValueError(f"--set 需要 key=value 形式，收到 {item!r}")
        key, raw = item.split("=", 1)
        try:
            val: Any = json.loads(raw)
        except json.JSONDecodeError:
            val = raw
        node = out
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = val
    return out


def build_cfg(args: argparse.Namespace) -> dict:
    overrides = _parse_set(args.set)
    syn = overrides.setdefault("synthetic", {})
    if not isinstance(syn, dict):
        syn = overrides["synthetic"] = {}
    for flag, key in (("z_start", "z_start_m"), ("z_end", "z_end_m"), ("drift", "drift_frac"),
                      ("depth_scale", "depth_scale"), ("outlier_frac", "outlier_frac"),
                      ("noise", "noise_m"), ("seed", "seed"), ("width", "width"),
                      ("height", "height")):
        val = getattr(args, flag, None)
        if val is not None:
            syn[key] = val
    if args.frames_count is not None:
        syn["frames"] = int(args.frames_count)
    if args.fps is not None:
        syn["fps"] = float(args.fps)
    cfg = types.merge_cfg(overrides)
    if args.fps is not None:
        cfg["filter"]["fps"] = float(args.fps)
    return cfg


# ---------------------------------------------------------------------------
# 输入帧


def _load_image(path: Path) -> np.ndarray:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - 环境相关
        raise types.BackendUnavailable(
            f"读取图片需要 Pillow（{type(exc).__name__}: {exc}）") from exc
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def _load_mask(path: Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"))
    return arr > 127


def _list_images(directory: Path) -> list[Path]:
    files = sorted(p for p in directory.iterdir()
                   if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    return files


def _load_inputs(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    """返回 `(帧列表, 模式说明)`。每帧 dict 至少含 `rgb`，可能含 `mask`/`keypoints_px`。"""
    if args.frames:
        directory = Path(args.frames)
        if not directory.is_dir():
            raise FileNotFoundError(f"--frames 目录不存在：{directory}")
        files = _list_images(directory)
        if not files:
            raise FileNotFoundError(f"--frames 目录里没有图片（{directory}）")
        frames: list[dict[str, Any]] = []
        for i, f in enumerate(files):
            frames.append({"frame": i, "rgb": _load_image(f), "path": str(f)})
        if args.masks:
            mdir = Path(args.masks)
            mfiles = _list_images(mdir)
            if len(mfiles) != len(frames):
                raise ValueError(f"--masks 图片数 {len(mfiles)} 与 --frames {len(frames)} 不一致")
            for fr, mf in zip(frames, mfiles):
                fr["mask"] = _load_mask(mf)
        if args.keypoints:
            kp_path = Path(args.keypoints)
            payload = json.loads(kp_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                payload = {str(i): v for i, v in enumerate(payload)}
            for fr in frames:
                entry = payload.get(str(fr["frame"]), {})
                fr["keypoints_px"] = {k: tuple(float(x) for x in v) for k, v in entry.items()}
        return frames, f"frames:{directory}"
    return [], ""


def _load_synthetic_inputs(be: "backend_mod.SyntheticBackend",
                           cfg: dict) -> list[dict[str, Any]]:
    frames = []
    for t in range(be.frames):
        rgb = be.render_rgb(t)
        frames.append({
            "frame": t,
            "rgb": rgb,
            "mask": be.render_mask(t),
            "keypoints_px": be.render_keypoints_px(t),
            "z_truth_m": float(be.z_root(t)),
        })
    return frames


# ---------------------------------------------------------------------------
# 各阶段


def _pick_region_stat(stats: Any) -> Any | None:
    """从 `masks.torso_pelvis_stats` 的结果里挑"根节点观测"用的区域。

    优先 `pelvis`（更接近根），其次 `torso`，再退化为像素数最大的那个。
    容忍 list / dict 两种返回形态。
    """
    if isinstance(stats, dict):
        stats = list(stats.values())
    if not stats:
        return None
    by_name = {str(getattr(s, "name", "")): s for s in stats}
    for want in ("pelvis", "torso"):
        if want in by_name:
            return by_name[want]
    return max(stats, key=lambda s: int(getattr(s, "px", 0)))


def run(args: argparse.Namespace) -> int:
    t0 = time.time()
    cfg = build_cfg(args)
    out_path = Path(args.out)
    report: dict[str, Any] = {"stage": args.stage, "cfg": cfg, "argv": _sys.argv[1:]}

    # --- 后端 ---------------------------------------------------------------
    if args.frames:
        if args.synthetic:
            _err("--synthetic 与 --frames 不能同时给（--frames 表示真实帧目录）")
            return EXIT_USAGE
        mode, frames = "frames", args.frames
    else:
        mode, frames = "synthetic", ""

    try:
        if mode == "synthetic":
            be = backend_mod.SyntheticBackend(cfg)
            backend_note = ""
        else:
            try:
                be = backend_mod.load(cfg)
                backend_note = ""
            except types.BackendUnavailable as exc:
                if not args.allow_fallback:
                    _err(f"真后端不可用：{exc}")
                    _err("本框架不自动下载权重、不静默回退。无卡环境请显式加 "
                         "`--allow-fallback`（会回退 SyntheticBackend 并打印原因），"
                         "或直接跑 `--synthetic`。")
                    return EXIT_MISSING_DEP
                be, backend_note = backend_mod.load_with_fallback(cfg)
    except (types.BackendUnavailable, ValueError, FileNotFoundError) as exc:
        _err(f"后端不可用：{type(exc).__name__}: {exc}")
        return EXIT_MISSING_DEP if isinstance(exc, types.BackendUnavailable) else EXIT_USAGE
    except Exception as exc:
        _err(f"后端构造失败：{type(exc).__name__}: {exc}")
        return EXIT_RUNTIME

    if be.kind != types.KIND_METRIC:  # 防御：本框架不接相对深度
        _err(f"后端 kind={be.kind!r}，只接受 {types.KIND_METRIC!r}")
        return EXIT_RUNTIME
    if backend_note:
        _log(f"注意：已显式回退到合成后端，原因：{backend_note}")
    _log(f"后端 {be.name} kind={be.kind} mode={mode} stage={args.stage}")
    report["backend"] = _as_plain(be.describe())
    report["backend_note"] = backend_note

    # --- 输入帧 -------------------------------------------------------------
    try:
        if mode == "synthetic":
            frame_items = _load_synthetic_inputs(be, cfg)
        else:
            frame_items, _ = _load_inputs(args)
    except Exception as exc:
        _err(f"读取输入帧失败：{type(exc).__name__}: {exc}")
        return EXIT_USAGE
    _log(f"帧数 {len(frame_items)}；画幅 {frame_items[0]['rgb'].shape[1]}x{frame_items[0]['rgb'].shape[0]}")
    report["n_frames"] = len(frame_items)

    # --- 深度 ---------------------------------------------------------------
    depths: list[types.DepthMap] = []
    t_infer = time.time()
    try:
        for fr in frame_items:
            depths.append(be.infer(fr["rgb"]))
    except Exception as exc:
        _err(f"深度推理失败（帧 {len(depths)}）：{type(exc).__name__}: {exc}")
        return EXIT_RUNTIME
    infer_s = time.time() - t_infer
    _log(f"深度完成：{len(depths)} 帧，{infer_s:.3f}s（{infer_s / max(1, len(depths)) * 1e3:.2f} ms/帧）")
    p50 = [backend_mod.depth_stats(d.depth)["p50_m"] for d in depths]
    p50_mask = [float(np.median(d.depth[fr["mask"]]))
                if fr.get("mask") is not None and bool(np.any(fr["mask"])) else float("nan")
                for fr, d in zip(frame_items, depths)]
    report["depth_p50_m"] = {"first": p50[0], "last": p50[-1],
                             "min": float(np.min(p50)), "max": float(np.max(p50))}
    _log(f"全图深度中位数 {p50[0]:.4f} → {p50[-1]:.4f} m（大部分像素是地面/背景，仅供量级检查）")
    if np.isfinite(p50_mask).any():
        report["depth_p50_mask_m"] = {"first": p50_mask[0], "last": p50_mask[-1],
                                      "min": float(np.nanmin(p50_mask)),
                                      "max": float(np.nanmax(p50_mask))}
        _log(f"人体 mask 内深度中位数 {p50_mask[0]:.4f} → {p50_mask[-1]:.4f} m（根节点 Z 的观测）")

    def _truth_error(z: np.ndarray) -> dict[str, float] | None:
        truth = [fr.get("z_truth_m") for fr in frame_items]
        if any(v is None for v in truth):
            return None
        tr = np.asarray(truth, dtype=np.float64)
        err = np.asarray(z, dtype=np.float64) - tr
        rel = np.abs(err) / np.maximum(tr, 1e-9)
        return {"max_abs_m": float(np.max(np.abs(err))), "max_rel": float(np.max(rel)),
                "rms_m": float(np.sqrt(np.mean(err ** 2))), "n": int(tr.size)}

    if args.stage == "backend":
        stats_path = out_path.with_name(out_path.stem + "_backend_stats.npz")
        mask_err = (_truth_error(p50_mask)
                    if mode == "synthetic" and np.all(np.isfinite(p50_mask)) else None)
        np.savez_compressed(
            stats_path,
            frames=np.arange(len(depths), dtype=np.int64),
            depth_p50_m=np.asarray(p50, dtype=np.float64),
            depth_p50_mask_m=np.asarray(p50_mask, dtype=np.float64),
            depth_min_m=np.asarray([backend_mod.depth_stats(d.depth)["min_m"] for d in depths]),
            depth_max_m=np.asarray([backend_mod.depth_stats(d.depth)["max_m"] for d in depths]),
        )
        report["backend_stats_npz"] = str(stats_path)
        report["truth_error_mask_p50"] = mask_err
        if mask_err:
            _log(f"合成真值：mask 中位数最大绝对误差 {mask_err['max_abs_m']:.3e} m，"
                 f"最大相对误差 {mask_err['max_rel']:.3%}")
        _log(f"stage=backend：写出 {stats_path}")
        _finish_report(args, report, t0)
        return EXIT_OK

    # --- mask / 躯干像素长（w2）---------------------------------------------
    masks_mod = _require("masks", args.stage, args)
    if masks_mod is None:
        return EXIT_MISSING_DEP
    priors_mod = _require("priors", args.stage, args)
    if priors_mod is None:
        return EXIT_MISSING_DEP

    min_px = int(cfg["mask"]["min_px"])
    obs_fn = getattr(masks_mod, "frame_observation", None)
    if not callable(obs_fn):
        _log("提示：masks.frame_observation() 不存在，退化到 torso_pelvis_stats + 本地选择逻辑")
    frame_priors: list[types.FramePrior] = []
    rows: list[dict[str, Any]] = []
    for fr, dm in zip(frame_items, depths):
        mask = fr.get("mask")
        kps = fr.get("keypoints_px")
        try:
            obs = _observe_frame(obs_fn, masks_mod, priors_mod, dm, mask, kps, cfg, min_px)
        except Exception as exc:
            _err(f"逐帧观测失败（帧 {fr['frame']}）：{type(exc).__name__}: {exc}")
            return EXIT_RUNTIME
        frame_priors.append(types.FramePrior(
            frame=int(fr["frame"]), depth_median_m=float(obs["depth_median_m"]),
            iqr_m=float(obs["iqr_m"]), torso_px=float(obs["torso_px"]),
            perspective_m=float("nan"), mask_frac=float(obs["mask_frac"]),
            valid=bool(obs["valid"]),
            reason="" if obs["valid"] else (str(obs["reason"]) or "invalid")))
        rows.append({"frame": int(fr["frame"]), "depth_median_m": float(obs["depth_median_m"]),
                     "iqr_m": float(obs["iqr_m"]), "torso_px": float(obs["torso_px"]),
                     "mask_frac": float(obs["mask_frac"]), "valid": bool(obs["valid"]),
                     "reason": str(obs["reason"]), "region": str(obs.get("region", "")),
                     "z_truth_m": fr.get("z_truth_m")})

    # 躯干透视粗项：以第一个可信帧为锚点（绝对尺度由度量项提供）
    anchor = next((p for p in frame_priors
                   if p.valid and np.isfinite(p.torso_px) and p.torso_px > 0), None)
    if anchor is None:
        _log("警告：没有任何可信帧，perspective_m 全为 nan")
    else:
        ref_px, ref_z = float(anchor.torso_px), float(anchor.depth_median_m)
        _log(f"躯干透视锚点：帧 {anchor.frame} ref_px={ref_px:.2f}px ref_z={ref_z:.4f}m")
        for p, r in zip(frame_priors, rows):
            if np.isfinite(p.torso_px) and p.torso_px > 0:
                try:
                    p.perspective_m = float(priors_mod.perspective_prior(p.torso_px, ref_px, ref_z))
                    r["perspective_m"] = p.perspective_m
                except Exception as exc:
                    _err(f"perspective_prior 失败（帧 {p.frame}）：{type(exc).__name__}: {exc}")
                    return EXIT_RUNTIME
    report["priors"] = rows
    report["n_valid"] = int(sum(1 for p in frame_priors if p.valid))

    if args.stage == "priors":
        priors_path = out_path.with_name(out_path.stem + "_priors.npz")
        np.savez_compressed(
            priors_path,
            frames=np.asarray([p.frame for p in frame_priors], dtype=np.int64),
            depth_median_m=np.asarray([p.depth_median_m for p in frame_priors], dtype=np.float64),
            iqr_m=np.asarray([p.iqr_m for p in frame_priors], dtype=np.float64),
            torso_px=np.asarray([p.torso_px for p in frame_priors], dtype=np.float64),
            perspective_m=np.asarray([p.perspective_m for p in frame_priors], dtype=np.float64),
            mask_frac=np.asarray([p.mask_frac for p in frame_priors], dtype=np.float64),
            valid=np.asarray([p.valid for p in frame_priors], dtype=bool),
        )
        report["priors_npz"] = str(priors_path)
        _log(f"stage=priors：可信 {report['n_valid']}/{len(frame_priors)} 帧，写出 {priors_path}")
        _finish_report(args, report, t0)
        return EXIT_OK

    # --- 融合 + 滤波（w3）---------------------------------------------------
    fusion_mod = _require("fusion", args.stage, args)
    if fusion_mod is None:
        return EXIT_MISSING_DEP
    filters_mod = _require("filters", args.stage, args)
    if filters_mod is None:
        return EXIT_MISSING_DEP

    try:
        z_raw, confidence = fusion_mod.fuse(frame_priors, cfg)
    except Exception as exc:
        _err(f"fusion.fuse 失败：{type(exc).__name__}: {exc}")
        return EXIT_RUNTIME
    z_raw = np.asarray(z_raw, dtype=np.float64).reshape(-1)
    confidence = np.asarray(confidence, dtype=np.float64).reshape(-1)
    fcfg = dict(cfg["filter"])
    try:
        z_filt, fdiag = filters_mod.one_euro(
            z_raw, fps=float(fcfg.get("fps", 30.0)), min_cutoff=float(fcfg["min_cutoff"]),
            beta=float(fcfg["beta"]), d_cutoff=float(fcfg["d_cutoff"]))
    except Exception as exc:
        _err(f"filters.one_euro 失败：{type(exc).__name__}: {exc}")
        return EXIT_RUNTIME
    z_filt = np.asarray(z_filt, dtype=np.float64).reshape(-1)

    alarms: list[str] = []
    if report["n_valid"] == 0:
        alarms.append("no_valid_frames")
    if not np.all(np.isfinite(z_raw)):
        alarms.append("nonfinite_z_raw")
    if z_raw.size and float(np.nanmax(z_raw) - np.nanmin(z_raw)) <= 1e-9:
        alarms.append("degenerate_z_range")
    truth_err = _truth_error(z_raw) if mode == "synthetic" else None
    if truth_err and truth_err["max_rel"] > 0.05:
        alarms.append(f"synthetic_truth_error>{0.05:.0%}")

    track = types.RootZTrack(
        frames=np.asarray([p.frame for p in frame_priors], dtype=np.int64),
        z_raw_m=z_raw, z_m=z_filt, confidence=confidence,
        diag=_as_plain({
            "source": mode if mode == "synthetic" else f"frames:{args.frames}",
            "backend": be.describe(),
            "backend_note": backend_note,
            "filter": _as_plain(fdiag),
            "filter_cfg": fcfg,
            "fusion_cfg": cfg["fusion"],
            "mask_cfg": cfg["mask"],
            "n_frames": len(frame_priors),
            "n_valid": report["n_valid"],
            "invalid_reasons": _count_reasons(frame_priors),
            "alarms": alarms,
            "truth_error_z_raw": truth_err,
            "cli_observations": {
                "confidence_mean": float(np.mean(confidence)) if confidence.size else None,
                "confidence_min": float(np.min(confidence)) if confidence.size else None,
                "z_raw_range_m": [float(np.min(z_raw)), float(np.max(z_raw))] if z_raw.size else None,
                "infer_seconds": float(infer_s),
                "elapsed_seconds": float(time.time() - t0),
            },
        }),
    )
    try:
        track.save(out_path)
    except Exception as exc:
        _err(f"写出 {out_path} 失败：{type(exc).__name__}: {exc}")
        return EXIT_RUNTIME
    _log(f"z_raw {z_raw.min():.4f} → {z_raw.max():.4f} m，confidence 均值 "
         f"{float(np.mean(confidence)) if confidence.size else float('nan'):.3f}"
         + (f"，合成真值最大相对误差 {truth_err['max_rel']:.2%}" if truth_err else ""))
    for a in alarms:
        _log(f"报警：{a}")
    _log(f"写出 {out_path}")
    report["out"] = str(out_path)
    report["alarms"] = alarms
    report["truth_error_z_raw"] = truth_err
    _finish_report(args, report, t0)
    return EXIT_OK


def _manual_observation(masks_mod: Any, priors_mod: Any, dm: types.DepthMap,
                        mask: np.ndarray, kps: Any, cfg: dict, min_px: int) -> dict[str, Any]:
    """退化路径：w2 没有 `frame_observation()` 时直接用 spec §3 的两个函数。"""
    stats = masks_mod.torso_pelvis_stats(dm, mask, kps, cfg)
    stat = _pick_region_stat(stats)
    reason = ""
    if stat is None:
        reason = "no_region_stat"
    elif int(getattr(stat, "px", 0)) < min_px:
        reason = f"px<{min_px}"
    elif not np.isfinite(float(getattr(stat, "depth_median_m", float("nan")))):
        reason = "nonfinite_depth"
    elif float(getattr(stat, "depth_median_m", 0.0)) <= 0.0:
        reason = "nonpositive_depth"
    torso_px = float("nan")
    if kps:
        val = priors_mod.torso_px_length(kps, cfg)
        if val is not None:
            torso_px = float(val)
    med = float(getattr(stat, "depth_median_m", float("nan"))) if stat is not None else float("nan")
    valid = reason == "" and np.isfinite(med) and med > 0.0
    return {"depth_median_m": med,
            "iqr_m": float(getattr(stat, "iqr_m", float("nan"))) if stat is not None else float("nan"),
            "torso_px": torso_px, "mask_frac": float(np.mean(mask)),
            "valid": valid, "reason": reason if valid else (reason or "invalid"),
            "region": str(getattr(stat, "name", "")) if stat is not None else ""}


OBS_KEYS = ("depth_median_m", "iqr_m", "torso_px", "mask_frac", "valid", "reason")


def _observe_frame(obs_fn: Any, masks_mod: Any, priors_mod: Any, dm: types.DepthMap,
                   mask: np.ndarray | None, kps: Any, cfg: dict, min_px: int) -> dict[str, Any]:
    """一帧的观测汇总。

    优先用 w2 的 `masks.frame_observation()`（区域选择/可信判据与 masks 保持一致）；
    它不存在或返回结构不认时，退化到 `_manual_observation()`。
    """
    if mask is None:
        return {"depth_median_m": float("nan"), "iqr_m": float("nan"), "torso_px": float("nan"),
                "mask_frac": 0.0, "valid": False, "reason": "no_mask", "region": ""}
    if callable(obs_fn):
        obs = obs_fn(dm, mask, kps, cfg)
        if isinstance(obs, dict) and all(k in obs for k in OBS_KEYS):
            return obs
        _log("提示：masks.frame_observation() 返回结构不认识，退化到本地逻辑")
    return _manual_observation(masks_mod, priors_mod, dm, mask, kps, cfg, min_px)


def _count_reasons(priors: list[types.FramePrior]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in priors:
        if p.valid:
            continue
        key = (p.reason or "unknown").split("<")[0]
        out[key] = out.get(key, 0) + 1
    return out


def _finish_report(args: argparse.Namespace, report: dict[str, Any], t0: float) -> None:
    report["elapsed_seconds"] = float(time.time() - t0)
    if args.report:
        p = Path(args.report)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        _log(f"诊断报告 {p}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="python -m depth_prior.cli",
        description="单目动捕度量深度先验：后端 → mask/躯干 → 融合 → One-Euro → RootZTrack")
    ap.add_argument("--synthetic", action="store_true",
                    help="用 SyntheticBackend 合成真值（默认；无卡环境的验收通道）")
    ap.add_argument("--frames", default="", help="真实帧目录（给定时走真后端，与 --synthetic 互斥）")
    ap.add_argument("--masks", default="", help="（真实帧模式）mask 图目录，文件名排序与帧对齐")
    ap.add_argument("--keypoints", default="", help="（真实帧模式）关键点 JSON：{帧号: {名称: [u, v]}}")
    ap.add_argument("--out", default="depth_prior.npz", help="RootZTrack 输出路径（默认 depth_prior.npz）")
    ap.add_argument("--stage", default="full", choices=STAGES,
                    help="backend=只跑深度；priors=+mask/躯干；full=全链路（默认）")
    ap.add_argument("--report", default="", help="额外写一份 JSON 诊断报告")
    ap.add_argument("--allow-fallback", action="store_true",
                    help="真后端不可用时显式回退 SyntheticBackend（默认不回退）")
    ap.add_argument("--set", action="append", default=[],
                    help="覆盖 cfg，可重复：--set backend.max_depth=20 --set synthetic.drift_frac=0.08")
    # 合成场景常用旋钮
    ap.add_argument("--frames-count", type=int, default=None, dest="frames_count")
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--z-start", type=float, default=None, dest="z_start")
    ap.add_argument("--z-end", type=float, default=None, dest="z_end")
    ap.add_argument("--drift", type=float, default=None, help="慢漂相对幅度（如 0.08）")
    ap.add_argument("--depth-scale", type=float, default=None, dest="depth_scale")
    ap.add_argument("--outlier-frac", type=float, default=None, dest="outlier_frac")
    ap.add_argument("--noise", type=float, default=None, help="逐帧高斯噪声 σ（米）")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        _err("被用户中断")
        return EXIT_RUNTIME
    except Exception as exc:  # 兜底：给一行可读信息而不是整段 traceback
        _err(f"未预期的错误：{type(exc).__name__}: {exc}")
        if _os.environ.get("DEPTH_PRIOR_CLI_TRACEBACK"):
            raise
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
