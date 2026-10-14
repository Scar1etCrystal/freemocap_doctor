"""w4 验收测试包（写作用域：depth_prior/tests/）。

对 `depth_prior/spec.md` §5 与冻结契约 `depth_prior/types.py` 写合成真值测试：
零推理、零 GPU、零 pytest，纯 `unittest` + 自造 `numpy` 合成数据。

跑法：
    python -m depth_prior.tests.run_tests          # 全部 10 条
    python -m depth_prior.tests.run_tests -v       # 逐条明细

实现模块（backend/masks/priors/fusion/filters/cli）由 w1/w2/w3 并行写：
**模块还没就绪 → 该条 skip 并打印缺哪个模块**，绝不假装通过。
"""
