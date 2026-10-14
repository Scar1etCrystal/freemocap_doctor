"""纯 unittest 入口：覆盖 spec §5 的 10 条验收。

    python -m depth_prior.tests.run_tests          # 汇总
    python -m depth_prior.tests.run_tests -v       # 逐条明细

不依赖 pytest / torch / GPU。缺实现模块的条目前缀 ↳ 会打印缺哪个模块；
**skip 不等于通过**。
"""

from __future__ import annotations

import sys
import unittest

MODULES = [
    ("① ② 后端契约（load 无 torch / SyntheticBackend）",
     "depth_prior.tests.test_contract"),
    ("③ 相对深度闸门（防退化回归，最重要）",
     "depth_prior.tests.test_gates"),
    ("④ ⑤ 尺度锚定 3→5 m / 深度×2 必须报警",
     "depth_prior.tests.test_scale_anchor"),
    ("⑥ 中位数抗离群（~30% 四肢像素）",
     "depth_prior.tests.test_median_robust"),
    ("⑦ 躯干透视互补（±8% 慢漂 → <3%）",
     "depth_prior.tests.test_perspective"),
    ("⑧ ⑨ One-Euro（静止降抖 >60% / 阶跃 <3 帧）",
     "depth_prior.tests.test_filter"),
    ("⑩ CLI 端到端（depth_prior.npz 往返）",
     "depth_prior.tests.test_e2e_cli"),
]


def _leaf_tests(suite):
    """展开嵌套 TestSuite，拿到真正的 TestCase。"""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _leaf_tests(item)
        else:
            yield item


def _status_map(result: unittest.TestResult) -> dict:
    st: dict[str, tuple[str, str]] = {}
    for test, reason in result.skipped:
        st[test.id()] = ("SKIP", (reason or "").splitlines()[0])
    for test, _tb in result.failures:
        st[test.id()] = ("FAIL", "")
    for test, _tb in result.errors:
        st[test.id()] = ("ERROR", "")
    return st


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    verbosity = 2 if any(a in ("-v", "--verbose") for a in argv) else 1

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    per_item = []
    for label, modname in MODULES:
        try:
            mod_suite = loader.loadTestsFromName(modname)
        except BaseException as exc:  # noqa: BLE001 - 加载期异常也算这一条未就绪
            print(f"[load-fail] {label} / {modname}: {type(exc).__name__}: {exc}")
            continue
        # 必须在 run 之前把叶子测试 id 抄下来：TestSuite 跑完会把 _tests 置 None 省内存
        leaves = list(_leaf_tests(mod_suite))
        per_item.append((label, [t.id() for t in leaves], len(leaves)))
        suite.addTests(mod_suite)

    result = unittest.TextTestRunner(verbosity=verbosity, buffer=False).run(suite)
    status = _status_map(result)

    print()
    print("=" * 82)
    print("w4 验收汇总（depth_prior/spec.md §5；skip = 实现尚未就绪，不等于通过）")
    print("=" * 82)
    for label, ids, n in per_item:
        counts = {"OK": 0, "SKIP": 0, "FAIL": 0, "ERROR": 0}
        first_skip = ""
        for tid in ids:
            st, reason = status.get(tid, ("OK", ""))
            counts[st] = counts.get(st, 0) + 1
            if st == "SKIP" and not first_skip:
                first_skip = reason
        print(f"{label:<44} OK {counts['OK']}/{n}  SKIP {counts['SKIP']}  "
              f"FAIL {counts['FAIL']}  ERROR {counts['ERROR']}")
        if first_skip:
            print(f"    ↳ {first_skip}")
    print("-" * 82)
    print(f"总计：run={result.testsRun}  failures={len(result.failures)}  "
          f"errors={len(result.errors)}  skipped={len(result.skipped)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
