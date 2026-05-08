# =====================================================================
#  reconcile.py
#
#  WHAT IT DOES
#  ------------
#  Reads the two CSV files produced by generate_data.py, compares them,
#  finds every break, classifies the root cause, ages the break, and
#  writes a single tidy file: breaks.csv
#
#  It also prints a one-screen summary you can screenshot for your
#  case study (STP rate, breaks by category, breaks by age bucket).
#
#  HOW TO RUN
#  ----------
#      python reconcile.py
#
#  TEACHER'S NOTE
#  --------------
#  Almost every line below maps to something you already know in Excel:
#
#      pd.read_csv          -> File -> Open
#      df.merge             -> XLOOKUP / Power Query merge
#      df.duplicated        -> Conditional formatting "highlight duplicates"
#      df.groupby + count   -> Pivot table
#      df.to_csv            -> File -> Save As
#
#  The script just runs the same logic at scale, in seconds.
# =====================================================================

import pandas as pd

# ----- Step 1: load the two files -------------------------------------
# parse_dates tells pandas to treat those columns as real dates, not text.
internal  = pd.read_csv("trades_internal.csv",
                         parse_dates=["trade_date", "settle_date"])
custodian = pd.read_csv("trades_custodian.csv",
                         parse_dates=["trade_date", "settle_date"])

# ----- Step 2: spot duplicates BEFORE merging -------------------------
# We need to know which trade_ids appear more than once on either side.
# Once we merge, duplicates can multiply rows and make life confusing.
internal_dups  = internal[internal.duplicated("trade_id", keep=False)]["trade_id"].unique().tolist()
custodian_dups = custodian[custodian.duplicated("trade_id", keep=False)]["trade_id"].unique().tolist()
all_dups = set(internal_dups) | set(custodian_dups)

# ----- Step 3: outer merge on trade_id --------------------------------
# how="outer" means: keep every trade_id from either side.
# indicator=True adds a column "_merge" with values:
#     left_only   -> only on internal side  -> custodian missing it
#     right_only  -> only on custodian side -> internal missing it
#     both        -> exists on both         -> need to compare fields
merged = internal.merge(
    custodian,
    on="trade_id",
    how="outer",
    suffixes=("_int", "_cust"),
    indicator=True
)

# ----- Step 4: classify each row --------------------------------------
def categorise(row):
    # Duplicates take precedence — flag them first.
    if row["trade_id"] in all_dups:
        return "DUP"
    if row["_merge"] == "left_only":
        return "MISSING_CUST"
    if row["_merge"] == "right_only":
        return "MISSING_INT"
    # Both sides present. Compare the fields that matter.
    if row["quantity_int"] != row["quantity_cust"]:
        return "QTY_DIFF"
    # Price tolerance: 2 basis points = 0.0002 of the price.
    if abs(row["price_int"] - row["price_cust"]) / row["price_int"] > 0.0002:
        return "PRICE_TOL"
    return "MATCHED"

# .apply runs our function once per row. Slow on millions of rows, fine here.
merged["break_category"] = merged.apply(categorise, axis=1)

# ----- Step 5: split into matched and breaks --------------------------
matched = merged[merged["break_category"] == "MATCHED"].copy()
breaks  = merged[merged["break_category"] != "MATCHED"].copy()

# ----- Step 6: age the breaks -----------------------------------------
TODAY = pd.Timestamp("2026-04-26")

def trade_date_for_row(row):
    # If internal side is missing, take custodian date, and vice versa.
    if pd.notna(row["trade_date_int"]):
        return row["trade_date_int"]
    return row["trade_date_cust"]

breaks["effective_trade_date"] = breaks.apply(trade_date_for_row, axis=1)
breaks["age_days"] = (TODAY - breaks["effective_trade_date"]).dt.days

def age_bucket(d):
    if d <= 1: return "0-1d"
    if d <= 5: return "2-5d"
    return ">5d"

breaks["age_bucket"] = breaks["age_days"].apply(age_bucket)

# ----- Step 7: save the breaks file -----------------------------------
# Drop the noisy _merge helper column before saving so the CSV is clean.
breaks_out = breaks.drop(columns=["_merge"])
breaks_out.to_csv("breaks.csv", index=False)

# ----- Step 8: print a recruiter-ready summary ------------------------
total      = len(merged)
n_breaks   = len(breaks)
stp_rate   = (1 - n_breaks / total) * 100

print("=" * 50)
print("RECONCILIATION SUMMARY")
print("=" * 50)
print(f"Total trade lines : {total:,}")
print(f"Matched           : {len(matched):,}")
print(f"Breaks            : {n_breaks:,}")
print(f"STP rate          : {stp_rate:.2f}%")
print()
print("Breaks by category:")
print(breaks["break_category"].value_counts().to_string())
print()
print("Breaks by age bucket:")
print(breaks["age_bucket"].value_counts().reindex(["0-1d", "2-5d", ">5d"]).to_string())
print()
print("OK  Wrote breaks.csv")
