# Trade Reconciliation Automation

A small portfolio project that automates a middle-office trade
reconciliation between two systems (internal book vs custodian),
classifies break root causes, ages aged breaks, and uses an LLM to
draft analyst-style break narratives.

## The problem

Middle-office teams reconcile their internal trade book against the
custodian record every day. Breaks (mismatches) must be investigated,
categorised, and resolved before settlement. The process is largely
manual: open two files, eyeball them, lookup mismatches, write
follow-up emails. This project replaces the eyeballing step with code
and replaces the email-drafting step with an LLM.

## What this repo does

1. Generates a realistic synthetic dataset: 10,000 trades on each side
   with 5 injected break types (`generate_data.py`).
2. Reconciles the two files in pandas, classifies each break, and ages
   it (`reconcile.py`). Output: `breaks.csv`.
3. Provides a reusable LLM prompt (`narrative_prompt.md`) that turns a
   break row into a 3-sentence investigation narrative.

## How to run

```bash
pip install pandas numpy
python generate_data.py
python reconcile.py
```

Then open `breaks.csv` in Excel and follow the dashboard steps in the
Build Guide.

## Results (synthetic data, 10,000 trades)

| Metric              | Value      |
|---------------------|------------|
| Total trade lines   | 10,100     |
| Matched             | 9,500      |
| Breaks              | 600        |
| STP rate            | 94.06%     |
| Manual recon time   | ~45 min/100 trades |
| Automated runtime   | <2 sec for 10,000 trades |

## Break categories detected

- `QTY_DIFF`     — quantity disagrees between sides
- `PRICE_TOL`    — price diverges beyond 2bp tolerance
- `MISSING_INT`  — trade exists on custodian, missing internally
- `MISSING_CUST` — trade exists internally, missing on custodian
- `DUP`          — duplicated trade_id on one side

## Lessons

## Lessons learned

- **Keep v1 small and decouple the workflow stages.** Chaining everything end-to-end felt elegant but created a cascade problem: any upstream fix forced a full re-run downstream. Splitting into independent stages (generate → reconcile → score → report → dashboard), each writing its own intermediate file, made the pipeline debuggable and resumable. Prefer chained stages with handoff files over tightly coupled automation, especially in v1.

- **Token saving is money saving — treat it as a first-class design constraint.** Every API call costs real money, and at scale those costs compound. Batching, structured JSON outputs, grouped playbooks for the long tail, and model tiering (Haiku for bulk, Sonnet for the top tier) are how AI features ship sustainably. Before adding any new AI step, ask: is this the cheapest way to get the same outcome at scale?

## Future work

- Wire the LLM narrative generation into the script via API
- Add a Power BI dashboard and link the .pbix file
- Multi-asset support (FX, fixed income) with asset-specific tolerances
