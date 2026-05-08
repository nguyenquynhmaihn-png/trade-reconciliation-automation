# =====================================================================
#  generate_data.py
#
#  WHAT IT DOES
#  ------------
#  Creates two CSV files that imitate a real middle-office reconciliation
#  scenario:
#
#      trades_internal.csv  -> what your firm thinks happened
#      trades_custodian.csv -> what the custodian (their record) says
#
#  We deliberately inject 5 kinds of "breaks" so that the reconciliation
#  engine in reconcile.py has something realistic to find:
#
#      QTY_DIFF      quantity does not match between the two files
#      PRICE_TOL     price differs by more than 2 basis points
#      MISSING_INT   row exists on custodian side but not internal
#      MISSING_CUST  row exists on internal side but not custodian
#      DUP           same trade_id appears twice on the custodian side
#
#  HOW TO RUN
#  ----------
#      pip install pandas numpy
#      python generate_data.py
#
#  Two CSV files will appear in the same folder.
# =====================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Reproducibility: same "random" data every time we run the script.
# Without this seed, your numbers would change on every run, which makes
# debugging and comparing results painful.
np.random.seed(42)

# ----- Configuration ---------------------------------------------------
N = 10_000  # total trades
TODAY = datetime(2026, 4, 26)

SECURITIES     = ["AAPL", "MSFT", "TSLA", "GOOG", "AMZN",
                  "JPM",  "BAC",  "GS",   "VOD.L","HSBA.L"]
COUNTERPARTIES = ["Goldman Sachs", "Morgan Stanley", "JP Morgan",
                  "UBS", "Barclays", "Citi"]
BOOKS          = ["EQ-LDN", "EQ-NY", "EQ-HK"]

# ----- Step 1: build the internal trade book --------------------------
# A DataFrame is just a table — think of it as an Excel sheet that lives
# in Python's memory. Each key in the dict below becomes a column.
internal = pd.DataFrame({
    "trade_id":     [f"T{100000+i}" for i in range(N)],
    "trade_date":   [TODAY - timedelta(days=int(np.random.randint(0, 10))) for _ in range(N)],
    "settle_date":  [TODAY + timedelta(days=int(np.random.randint(0, 3))) for _ in range(N)],
    "security_id":  np.random.choice(SECURITIES, N),
    "side":         np.random.choice(["BUY", "SELL"], N),
    "quantity":     np.random.randint(100, 10_000, N),
    "price":        np.round(np.random.uniform(50, 500, N), 2),
    "counterparty": np.random.choice(COUNTERPARTIES, N),
    "book":         np.random.choice(BOOKS, N),
})

# ----- Step 2: copy the book to make the custodian view ---------------
# In reality the custodian would have its own data. Here we copy the
# internal book and then deliberately damage 500 rows (5%) so we have
# breaks to find.
custodian = internal.copy()

# Pick 500 row positions and split them into 5 disjoint groups of 100.
# Disjoint = no row gets two breaks at once. Keeps the analysis clean.
all_idx = np.arange(N)
np.random.shuffle(all_idx)

qty_idx       = all_idx[  0:100]   # 100 rows -> change quantity
price_idx     = all_idx[100:200]   # 100 rows -> change price
miss_int_idx  = all_idx[200:300]   # 100 rows -> drop from internal
miss_cust_idx = all_idx[300:400]   # 100 rows -> drop from custodian
dup_idx       = all_idx[400:500]   # 100 rows -> duplicate on custodian

# 1) Quantity break: bump custodian quantity by ~10%
custodian.loc[qty_idx, "quantity"] = (custodian.loc[qty_idx, "quantity"] * 1.10).astype(int)

# 2) Price break: shift custodian price by ~50 bps (well above tolerance)
custodian.loc[price_idx, "price"] = (custodian.loc[price_idx, "price"] * 1.005).round(4)

# 3) Missing on internal: drop these from the internal file
internal_out = internal.drop(miss_int_idx).reset_index(drop=True)

# 4) Missing on custodian: drop these from the custodian file
custodian_out = custodian.drop(miss_cust_idx).reset_index(drop=True)

# 5) Duplicates on custodian: append the dup_idx rows a second time
dups_to_add = custodian.loc[dup_idx]
custodian_out = pd.concat([custodian_out, dups_to_add], ignore_index=True)

# ----- Step 3: write to disk ------------------------------------------
internal_out.to_csv("trades_internal.csv", index=False)
custodian_out.to_csv("trades_custodian.csv", index=False)

print(f"OK  internal rows : {len(internal_out):,}")
print(f"OK  custodian rows: {len(custodian_out):,}")
print("Injected breaks: 100 QTY_DIFF, 100 PRICE_TOL, 100 MISSING_INT,",
      "100 MISSING_CUST, 100 DUP")
