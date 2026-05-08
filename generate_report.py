# =====================================================================
#  generate_report.py
#
#  WHAT IT DOES
#  ------------
#  Calls the Claude API exactly 2 times (instead of 600!) and writes
#  break_investigation_report.md — a polished markdown report with:
#
#    1. Executive summary (KPIs, top risks)
#    2. Category playbooks (1 per break_category)
#    3. Top 25 priority breaks with individual narratives
#    4. Long-tail summary (breaks 26..end grouped by category)
#
#  HOW TO RUN
#  ----------
#  Step 1: Get an API key at console.anthropic.com -> API Keys.
#  Step 2: In the same folder as this script, create a file called .env
#          with this single line (replace with your actual key):
#
#              ANTHROPIC_API_KEY=sk-ant-...
#
#  Step 3: Install the SDK:
#              pip install anthropic python-dotenv
#
#  Step 4: Run reconcile.py and priority_score.py first to produce
#          breaks_prioritised.csv.
#
#  Step 5: Run this script:
#              python generate_report.py
#
#          To preview the prompts WITHOUT spending tokens, run:
#              python generate_report.py --dry-run
#
#  WHY THIS DESIGN
#  ---------------
#  Naive approach: 600 breaks -> 600 API calls -> ~$1.50-2.00 + 10 min.
#  Smart approach (this script):
#     Call 1: Generate 5 category playbooks    (~3,000 tokens)
#     Call 2: Generate top-25 narratives in one batched call (~8,000 tok)
#     Total cost: ~$0.05 on Sonnet, ~$0.01 on Haiku.
#  Savings: ~95-99%. Speed: ~30 seconds end-to-end.
# =====================================================================

import json
import os
import sys
import argparse
from pathlib import Path

import pandas as pd

# Make the script gracefully tell the user what to install
try:
    import anthropic
except ImportError:
    print("ERROR: anthropic SDK not installed.")
    print("  Run:  pip install anthropic python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional — env vars work fine without it

# --- Configuration ----------------------------------------------------
RED_TOP_N        = 5     # top N get deep-dive narratives (manager attention required)
WORKLIST_TOP_N   = 25    # full worklist size (top 25 = RED + AMBER)
SAMPLES_PER_CAT  = 3     # samples per category included in the playbook prompt
MODEL            = "claude-sonnet-4-5"   # use 'claude-haiku-4-5' for ~5x cheaper
INPUT_CSV        = "breaks_prioritised.csv"
OUTPUT_MD        = "break_investigation_report.md"
OUTPUT_WORKLIST  = "break_worklist.csv"

# --- CLI args ---------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true",
                    help="Print the prompts but do not call the API")
args = parser.parse_args()

# --- Load the data ----------------------------------------------------
df = pd.read_csv(INPUT_CSV)

# DUP breaks produce TWO rows per trade_id (the original + the duplicate).
# For ranking and reporting we want one row per trade_id — the analyst
# resolves both rows in one investigation. The CSV worklist still keeps
# the underlying row so the analyst can trace it.
df_unique = df.drop_duplicates(subset=["trade_id"], keep="first").reset_index(drop=True)

red_breaks    = df_unique.head(RED_TOP_N)                       # top 5 -> deep dive
amber_breaks  = df_unique.iloc[RED_TOP_N:WORKLIST_TOP_N]        # ranks 6-25 -> one-liners
worklist      = df_unique.head(WORKLIST_TOP_N)                  # full top 25

# Build a compact representation of each break — only fields the model needs
def slim(row):
    return {
        "trade_id":         row["trade_id"],
        "category":         row["break_category"],
        "security":         row["security_id_int"] if pd.notna(row["security_id_int"]) else row["security_id_cust"],
        "side":             row["side_int"]        if pd.notna(row["side_int"])        else row["side_cust"],
        "qty_int":          None if pd.isna(row["quantity_int"]) else int(row["quantity_int"]),
        "qty_cust":         None if pd.isna(row["quantity_cust"]) else int(row["quantity_cust"]),
        "price_int":        None if pd.isna(row["price_int"]) else float(row["price_int"]),
        "price_cust":       None if pd.isna(row["price_cust"]) else float(row["price_cust"]),
        "counterparty":     row["counterparty_int"] if pd.notna(row["counterparty_int"]) else row["counterparty_cust"],
        "age_days":         int(row["age_days"]),
        "age_bucket":       row["age_bucket"],
        "financial_impact": float(row["financial_impact_usd"]),
    }

# --- Build category samples for the playbook prompt -------------------
samples_by_cat = {}
for cat, grp in df.groupby("break_category"):
    samples_by_cat[cat] = [slim(r) for _, r in grp.head(SAMPLES_PER_CAT).iterrows()]

# --- Build payloads for the prompts -----------------------------------
red_payload    = [slim(r) for _, r in red_breaks.iterrows()]
amber_payload  = [slim(r) for _, r in amber_breaks.iterrows()]

# --- Aggregate stats for the report header ----------------------------
stats = {
    "total_breaks":       int(len(df)),
    "by_category":        df["break_category"].value_counts().to_dict(),
    "by_age_bucket":      df["age_bucket"].value_counts().to_dict(),
    "total_risk_usd":     float(df["financial_impact_usd"].sum()),
    "red_risk_share":     float(red_breaks["financial_impact_usd"].sum() / df["financial_impact_usd"].sum() * 100),
    "worklist_risk_share":float(worklist["financial_impact_usd"].sum() / df["financial_impact_usd"].sum() * 100),
}

# --- PROMPT 1: Category playbook --------------------------------------
PLAYBOOK_PROMPT = f"""You are a senior middle-office operations analyst at a brokerage.

I have a daily trade reconciliation with breaks falling into these 5 categories. For each category, write a standardised PLAYBOOK that an analyst can apply to every break in that category.

Return a single JSON object with EXACTLY this structure (no prose outside the JSON):

{{
  "CATEGORY_CODE": {{
    "typical_root_cause": "1 sentence",
    "resolution_steps": ["step 1", "step 2", "step 3", "step 4"],
    "primary_contact": "1 line, naming a typical role/team",
    "expected_resolution_time": "1 line",
    "escalation_trigger": "when to escalate"
  }}
}}

The 5 categories are:
- QTY_DIFF      (quantity disagrees between internal and custodian)
- PRICE_TOL     (price disagrees by more than 2 basis points)
- MISSING_INT   (trade exists on custodian but missing internally)
- MISSING_CUST  (trade exists internally but missing on custodian)
- DUP           (same trade_id appears twice on one side)

Sample breaks for context (3 per category):
```json
{json.dumps(samples_by_cat, indent=2)}
```

Return ONLY the JSON object, no other text.
"""

# --- PROMPT 2: Tiered narratives (batched, two depths in one call) -----
NARRATIVE_PROMPT_TEMPLATE = """You are a senior middle-office operations analyst.

You have already produced these category playbooks:
```json
{playbooks}
```

Today's reconciliation has 25 priority breaks split into two tiers.

TIER RED (top {red_n}, manager attention required):
For each, write a deep_narrative of 2 sentences:
  Sentence 1: state the specific trade and the SPECIFIC values that disagree (cite real numbers).
  Sentence 2: recommended next action, naming the playbook category, the contact to chase, and whether to escalate.

TIER AMBER (next {amber_n}, analyst worklist):
For each, write a short_narrative of ONE line, MAX 25 WORDS:
  Format: '<security> <side> <qty>@<price> vs <counterparty>: <break detail>; apply <CATEGORY> playbook[, escalate if needed].'

Return a single JSON object (no prose outside):
{{
  "red":   [{{"trade_id": "...", "deep_narrative":  "..."}}, ...],
  "amber": [{{"trade_id": "...", "short_narrative": "..."}}, ...]
}}

RED breaks:
```json
{red_breaks}
```

AMBER breaks:
```json
{amber_breaks}
```

Return ONLY the JSON object.
"""

# --- Either run or dry-run --------------------------------------------
if args.dry_run:
    print("=" * 60)
    print("DRY RUN — these are the prompts that would be sent")
    print("=" * 60)
    print()
    print("--- PROMPT 1: Category playbooks ---")
    print(PLAYBOOK_PROMPT[:1500] + "\n... [truncated]")
    print()
    print(f"--- PROMPT 2: tiered narratives (RED top {RED_TOP_N}, AMBER {RED_TOP_N+1}-{WORKLIST_TOP_N}) ---")
    print(NARRATIVE_PROMPT_TEMPLATE.format(
        playbooks="<...playbooks would go here...>",
        red_n=RED_TOP_N, amber_n=len(amber_payload),
        red_breaks=json.dumps(red_payload[:2], indent=2) + "\n... [truncated]",
        amber_breaks=json.dumps(amber_payload[:2], indent=2) + "\n... [truncated]"
    )[:2000])
    print()
    print(f"Estimated tokens   : ~6,000-9,000 in + ~2,000-3,000 out")
    print(f"Estimated cost     : ~$0.05-0.10 on Sonnet, ~$0.01-0.02 on Haiku")
    print(f"Outputs would be   : {OUTPUT_MD} (tiered report)")
    print(f"                     {OUTPUT_WORKLIST} (analyst-ready CSV)")
    sys.exit(0)

# --- Real API run -----------------------------------------------------
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not found.")
    print("  Set it via .env file or:  export ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)

client = anthropic.Anthropic()

print("Step 1/2: Generating category playbooks...")
resp1 = client.messages.create(
    model=MODEL,
    max_tokens=2000,
    messages=[{"role": "user", "content": PLAYBOOK_PROMPT}],
)
playbooks_text = resp1.content[0].text.strip()
# Strip code fences if the model wrapped the JSON
if playbooks_text.startswith("```"):
    playbooks_text = playbooks_text.split("```")[1]
    if playbooks_text.startswith("json"):
        playbooks_text = playbooks_text[4:].strip()
playbooks = json.loads(playbooks_text)
print(f"  OK  {len(playbooks)} category playbooks generated")
print(f"      tokens: in={resp1.usage.input_tokens} out={resp1.usage.output_tokens}")

print(f"Step 2/2: Generating tiered narratives (RED {RED_TOP_N} deep + AMBER {len(amber_payload)} one-liners)...")
narrative_prompt = NARRATIVE_PROMPT_TEMPLATE.format(
    playbooks=json.dumps(playbooks, indent=2),
    red_n=RED_TOP_N, amber_n=len(amber_payload),
    red_breaks=json.dumps(red_payload, indent=2),
    amber_breaks=json.dumps(amber_payload, indent=2),
)
resp2 = client.messages.create(
    model=MODEL,
    max_tokens=4000,
    messages=[{"role": "user", "content": narrative_prompt}],
)
narratives_text = resp2.content[0].text.strip()
if narratives_text.startswith("```"):
    narratives_text = narratives_text.split("```")[1]
    if narratives_text.startswith("json"):
        narratives_text = narratives_text[4:].strip()
narrative_obj = json.loads(narratives_text)
red_narratives    = {n["trade_id"]: n["deep_narrative"]  for n in narrative_obj["red"]}
amber_narratives  = {n["trade_id"]: n["short_narrative"] for n in narrative_obj["amber"]}
print(f"  OK  {len(red_narratives)} deep + {len(amber_narratives)} short narratives generated")
print(f"      tokens: in={resp2.usage.input_tokens} out={resp2.usage.output_tokens}")

total_cost_estimate = (
    (resp1.usage.input_tokens + resp2.usage.input_tokens) * 3 / 1_000_000 +
    (resp1.usage.output_tokens + resp2.usage.output_tokens) * 15 / 1_000_000
)
print(f"  Total estimated cost: ${total_cost_estimate:.4f}")

# --- Assemble outputs (tiered report + analyst worklist CSV) ----------
def md_table(rows, headers):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)

# Long-tail: breaks 26..end grouped by category
tail = df.iloc[WORKLIST_TOP_N:]
tail_summary = tail.groupby("break_category").agg(
    count=("trade_id", "count"),
    total_risk=("financial_impact_usd", "sum"),
).reset_index().sort_values("total_risk", ascending=False)

# === FILE 1: Analyst worklist CSV ====================================
worklist_out = worklist.copy()
worklist_out["tier"] = ["RED"] * RED_TOP_N + ["AMBER"] * len(amber_breaks)
worklist_out["narrative"] = worklist_out["trade_id"].map(
    lambda tid: red_narratives.get(tid) or amber_narratives.get(tid, "")
)
worklist_out["security"]     = worklist_out["security_id_int"].fillna(worklist_out["security_id_cust"])
worklist_out["counterparty"] = worklist_out["counterparty_int"].fillna(worklist_out["counterparty_cust"])
csv_cols = ["tier", "trade_id", "break_category", "age_bucket", "age_days",
            "security", "counterparty", "financial_impact_usd", "narrative"]
worklist_out[csv_cols].to_csv(OUTPUT_WORKLIST, index=False)

# === FILE 2: Tiered markdown report ==================================
with open(OUTPUT_MD, "w") as f:
    f.write("# Trade Reconciliation — Break Investigation Report\n\n")
    f.write("_Generated by AI-assisted pipeline. Synthetic data, 10,000 trades._\n\n")

    # ---- 1. EXECUTIVE BRIEF (the 1-page manager view) ----
    f.write("## 1. Executive brief\n\n")
    f.write(f"- **Total breaks**: {stats['total_breaks']:,}  "
            f"(${stats['total_risk_usd']:,.0f} at risk)\n")
    f.write(f"- **Top {RED_TOP_N} breaks (RED tier)** carry "
            f"**{stats['red_risk_share']:.1f}%** of total risk — manager attention required.\n")
    f.write(f"- **Top {WORKLIST_TOP_N} breaks (RED + AMBER)** carry "
            f"**{stats['worklist_risk_share']:.1f}%** — covered in the analyst worklist below.\n")
    f.write(f"- Remaining **{len(tail):,}** breaks follow standard category playbooks (see appendix).\n\n")

    f.write("### RED tier — needs your attention today\n\n")
    for _, row in red_breaks.iterrows():
        tid = row["trade_id"]
        sec = row['security_id_int'] if pd.notna(row['security_id_int']) else row['security_id_cust']
        cp  = row['counterparty_int'] if pd.notna(row['counterparty_int']) else row['counterparty_cust']
        f.write(f"- **{tid}** ({sec} | {row['break_category']} | {row['age_bucket']} | "
                f"${row['financial_impact_usd']:,.0f}, vs {cp}) — {red_narratives.get(tid, '')}\n")
    f.write("\n")

    f.write("### Aging snapshot\n\n")
    f.write(md_table(
        [(b, f"{n:,}") for b, n in stats["by_age_bucket"].items()],
        ["Age bucket", "Count"]
    ) + "\n\n")

    f.write("### Category mix\n\n")
    f.write(md_table(
        [(c, f"{n:,}") for c, n in stats["by_category"].items()],
        ["Category", "Count"]
    ) + "\n\n")

    # ---- 2. PRIORITY WORKLIST (compact table for the analyst) ----
    f.write(f"## 2. Priority worklist (top {WORKLIST_TOP_N})\n\n")
    f.write(f"Tier RED = top {RED_TOP_N} (deep dive in section 3). "
            f"Tier AMBER = ranks {RED_TOP_N+1}-{WORKLIST_TOP_N}. "
            f"Sortable CSV exported as `{OUTPUT_WORKLIST}`.\n\n")
    rows = []
    for i, (_, row) in enumerate(worklist.iterrows(), start=1):
        tid = row["trade_id"]
        tier = "RED" if i <= RED_TOP_N else "AMBER"
        sec  = row['security_id_int'] if pd.notna(row['security_id_int']) else row['security_id_cust']
        cp   = row['counterparty_int'] if pd.notna(row['counterparty_int']) else row['counterparty_cust']
        narr = (red_narratives.get(tid) or amber_narratives.get(tid, ""))[:120] + (
            "..." if len(red_narratives.get(tid) or amber_narratives.get(tid, "")) > 120 else ""
        )
        rows.append([
            i, tier, tid, row["break_category"], row["age_bucket"],
            sec, cp, f"${row['financial_impact_usd']:,.0f}", narr
        ])
    f.write(md_table(rows,
        ["#", "Tier", "Trade ID", "Cat", "Age", "Sec", "CP", "$ Risk", "Narrative"]
    ) + "\n\n")

    # ---- 3. RED TIER DEEP DIVE (only the top 5) ----
    f.write(f"## 3. RED tier — deep dive (top {RED_TOP_N})\n\n")
    for _, row in red_breaks.iterrows():
        tid = row["trade_id"]
        sec = row['security_id_int'] if pd.notna(row['security_id_int']) else row['security_id_cust']
        cp  = row['counterparty_int'] if pd.notna(row['counterparty_int']) else row['counterparty_cust']
        f.write(f"### {tid} — {row['break_category']} | {row['age_bucket']} | "
                f"${row['financial_impact_usd']:,.0f} at risk\n\n")
        f.write(f"{red_narratives.get(tid, '_(narrative not generated)_')}\n\n")
        f.write("| Field | Internal | Custodian |\n| --- | --- | --- |\n")
        f.write(f"| Security | {row['security_id_int']} | {row['security_id_cust']} |\n")
        f.write(f"| Side | {row['side_int']} | {row['side_cust']} |\n")
        f.write(f"| Quantity | {row['quantity_int']} | {row['quantity_cust']} |\n")
        f.write(f"| Price | {row['price_int']} | {row['price_cust']} |\n")
        f.write(f"| Counterparty | {row['counterparty_int']} | {row['counterparty_cust']} |\n")
        f.write(f"\n_Age: {int(row['age_days'])} days. Apply playbook for {row['break_category']} (Section 5)._\n\n")

    # ---- 4. LONG-TAIL SUMMARY ----
    f.write(f"## 4. Long tail — apply playbooks\n\n")
    f.write(f"{len(tail):,} breaks beyond the top {WORKLIST_TOP_N}, "
            f"totalling ${tail['financial_impact_usd'].sum():,.0f}. Routed to category playbooks.\n\n")
    f.write(md_table(
        [(r["break_category"], f"{r['count']:,}", f"${r['total_risk']:,.0f}") for _, r in tail_summary.iterrows()],
        ["Category", "Count", "Total $ at risk"]
    ) + "\n\n")

    # ---- 5. PLAYBOOKS (reference appendix) ----
    f.write("## 5. Category playbooks (reference appendix)\n\n")
    for cat, pb in playbooks.items():
        f.write(f"### {cat}\n\n")
        f.write(f"- **Typical root cause**: {pb['typical_root_cause']}\n")
        f.write(f"- **Resolution steps**:\n")
        for step in pb["resolution_steps"]:
            f.write(f"  1. {step}\n")
        f.write(f"- **Primary contact**: {pb['primary_contact']}\n")
        f.write(f"- **Expected resolution time**: {pb['expected_resolution_time']}\n")
        f.write(f"- **Escalation trigger**: {pb['escalation_trigger']}\n\n")

print(f"OK  wrote {OUTPUT_MD}")
print(f"OK  wrote {OUTPUT_WORKLIST}")
