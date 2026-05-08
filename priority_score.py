# =====================================================================
#  priority_score.py
#
#  WHAT IT DOES
#  ------------
#  Reads breaks.csv (output of reconcile.py) and adds three columns:
#
#      financial_impact_usd  — the $ amount at risk per break, calculated
#                              differently for each break category
#      age_weight            — 1 / 3 / 10 multiplier based on age bucket
#      priority_score        — financial_impact_usd * age_weight
#
#  Then sorts the breaks by priority_score descending and writes
#      breaks_prioritised.csv
#
#  HOW TO RUN
#  ----------
#      python priority_score.py
#
#  WHY THIS MATTERS
#  ----------------
#  600 breaks is too many to investigate equally. The top 5% of breaks
#  by priority typically contain ~50-80% of the financial risk. Sort
#  by priority and let the AI focus its tokens on the high-impact ones.
# =====================================================================

import pandas as pd

# ----- Load --------------------------------------------------------------
df = pd.read_csv("breaks.csv")

# ----- Helper: pick the side that has data ------------------------------
def coalesce(row, col_int, col_cust):
    """Return the non-null value from either the internal or custodian side."""
    if pd.notna(row[col_int]):
        return row[col_int]
    return row[col_cust]

# ----- Calculate financial impact per break -----------------------------
# Each break category has a different formula for 'how much is at risk'.
def financial_impact(row):
    cat = row["break_category"]
    qty   = coalesce(row, "quantity_int", "quantity_cust")
    price = coalesce(row, "price_int",    "price_cust")

    if cat == "QTY_DIFF":
        # Risk = the disputed quantity x the price
        qty_diff = abs(row["quantity_int"] - row["quantity_cust"])
        return qty_diff * price

    if cat == "PRICE_TOL":
        # Risk = the price difference x the quantity
        price_diff = abs(row["price_int"] - row["price_cust"])
        return price_diff * qty

    if cat in ("MISSING_INT", "MISSING_CUST"):
        # Risk = the full notional, since one side has no record
        return qty * price

    if cat == "DUP":
        # Risk = the full notional, the duplicated trade may settle twice
        return qty * price

    return 0.0

df["financial_impact_usd"] = df.apply(financial_impact, axis=1).round(2)

# ----- Age weighting ---------------------------------------------------
# Aged breaks are exponentially more dangerous because they threaten T+1.
AGE_WEIGHTS = {"0-1d": 1, "2-5d": 3, ">5d": 10}
df["age_weight"] = df["age_bucket"].map(AGE_WEIGHTS).fillna(1)

# ----- Priority score = $ at risk x age weight -------------------------
df["priority_score"] = (df["financial_impact_usd"] * df["age_weight"]).round(2)

# ----- Sort and save ---------------------------------------------------
df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
df.to_csv("breaks_prioritised.csv", index=False)

# ----- Print a quick summary -------------------------------------------
top_25_pct = df.head(int(len(df) * 0.05))["priority_score"].sum()
total_pct  = df["priority_score"].sum()

print("PRIORITY SCORING SUMMARY")
print("=" * 50)
print(f"Total breaks         : {len(df):,}")
print(f"Total priority units : {total_pct:,.0f}")
print(f"Top 5% of breaks     : {len(top_25_pct):,} rows" if hasattr(top_25_pct, '__len__') else f"Top 5% of breaks     : ~{int(len(df)*0.05):,} rows")
print(f"Top 5% priority share: {top_25_pct/total_pct*100:.1f}% of total risk")
print()
print("Top 5 breaks by priority:")
cols = ["trade_id", "break_category", "age_bucket", "financial_impact_usd", "priority_score"]
print(df.head(5)[cols].to_string(index=False))
print()
print("OK  Wrote breaks_prioritised.csv")
