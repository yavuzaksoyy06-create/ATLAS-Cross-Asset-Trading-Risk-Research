# Offline synthetic demonstration — not actual prices

This self-contained fixture exercises the full research pipeline without network access. Its symbol headings resemble tradable ETFs **only as program interface labels**. All levels and returns are pseudorandom and must never be described as actual ETF history, alpha, market events or investment evidence.

```bash
python examples/generate_synthetic_fixture.py
python -m atlas.real_study --input-csv examples/synthetic_3etf.csv --synthetic-fixture --repetitions 100 --output results/synthetic_institutional
```

The source classification is persisted into `CASE_STUDY.md`, `EMPIRICAL_RESEARCH_MEMO.md`, the CSV result files and dashboard. For *real archived* ETF data, use the pinned download instructions in the root README and verify the generated `reference_reconciliation.json`.
