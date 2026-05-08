# Trade Reconciliation — Break Investigation Report

_Hand-crafted sample showing what generate_report.py produces. Synthetic data, 10,000 trades._

## 1. Executive brief

- **Total breaks**: 600  ($590,585,493 at risk)
- **Top 5 breaks (RED tier)** carry **3.7%** of total risk — manager attention required.
- **Top 25 breaks (RED + AMBER)** carry **13.5%** — covered in the analyst worklist below.
- Remaining **475** breaks follow standard category playbooks (see appendix).

### RED tier — needs your attention today

- **T104657** (TSLA | MISSING_CUST | >5d | $4,509,881, vs Citi) — T104657 (TSLA SELL 9,114 @ $494.83 vs Citi) is on internal book but custodian shows no record after 9 days, exposing $4,509,881 of notional that has missed multiple settlement cycles. Apply MISSING_CUST playbook starting with the SWIFT inbox and Citi trade-support; given age and notional, escalate to head of Settlements immediately.
- **T106227** (GS | MISSING_INT | >5d | $4,484,546, vs UBS) — T106227 (GS BUY 9,801 @ $457.56, counterparty UBS) appears on custodian record but is absent from the internal book at 8 days, raising risk of an unrecognised trade approaching settlement. Apply MISSING_INT playbook urgently - confirm legitimacy with UBS trade-support and raise an emergency back-booking; escalate to compliance if no booking authorisation can be located.
- **T102309** (AMZN | DUP | >5d | $4,460,860, vs Goldman Sachs) — T102309 (AMZN BUY 9,462 @ $471.45, counterparty Goldman Sachs) appears twice on the custodian side and has been aged 8 days without resolution, doubling settlement-fail risk on a $4,460,860 notional. Apply DUP playbook - verify byte-identical duplication, check OMS for duplicate booking events at execution time, and cancel one row before settlement; escalate immediately given age.
- **T106621** (HSBA.L | MISSING_CUST | >5d | $4,377,163, vs Goldman Sachs) — T106621 (HSBA.L BUY 9,117 @ $480.11 vs Goldman Sachs) is on internal book but custodian shows no record after 9 days, exposing $4,377,163 of notional that has missed multiple settlement cycles. Apply MISSING_CUST playbook starting with the SWIFT inbox and Goldman Sachs trade-support; given age and notional, escalate to head of Settlements immediately.
- **T100465** (HSBA.L | MISSING_INT | >5d | $4,157,725, vs Morgan Stanley) — T100465 (HSBA.L SELL 9,214 @ $451.24, counterparty Morgan Stanley) appears on custodian record but is absent from the internal book at 9 days, raising risk of an unrecognised trade approaching settlement. Apply MISSING_INT playbook urgently - confirm legitimacy with Morgan Stanley trade-support and raise an emergency back-booking; escalate to compliance if no booking authorisation can be located.

### Aging snapshot

| Age bucket | Count |
| --- | --- |
| 2-5d | 261 |
| >5d | 227 |
| 0-1d | 112 |

### Category mix

| Category | Count |
| --- | --- |
| DUP | 200 |
| MISSING_CUST | 100 |
| MISSING_INT | 100 |
| QTY_DIFF | 100 |
| PRICE_TOL | 100 |

## 2. Priority worklist (top 25)

Tier RED = top 5 (deep dive in section 3). Tier AMBER = ranks 6-25. Sortable CSV exported as `break_worklist.csv`.

| # | Tier | Trade ID | Cat | Age | Sec | CP | $ Risk | Narrative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | RED | T104657 | MISSING_CUST | >5d | TSLA | Citi | $4,509,881 | T104657 (TSLA SELL 9,114 @ $494.83 vs Citi) is on internal book but custodian shows no record after ... |
| 2 | RED | T106227 | MISSING_INT | >5d | GS | UBS | $4,484,546 | T106227 (GS BUY 9,801 @ $457.56, counterparty UBS) appears on custodian record but is absent from th... |
| 3 | RED | T102309 | DUP | >5d | AMZN | Goldman Sachs | $4,460,860 | T102309 (AMZN BUY 9,462 @ $471.45, counterparty Goldman Sachs) appears twice on the custodian side a... |
| 4 | RED | T106621 | MISSING_CUST | >5d | HSBA.L | Goldman Sachs | $4,377,163 | T106621 (HSBA.L BUY 9,117 @ $480.11 vs Goldman Sachs) is on internal book but custodian shows no rec... |
| 5 | RED | T100465 | MISSING_INT | >5d | HSBA.L | Morgan Stanley | $4,157,725 | T100465 (HSBA.L SELL 9,214 @ $451.24, counterparty Morgan Stanley) appears on custodian record but i... |
| 6 | AMBER | T104492 | MISSING_CUST | >5d | VOD.L | Morgan Stanley | $3,816,688 | VOD.L BUY 7,819@$488.13 vs Morgan Stanley: missing_cust; apply MISSING_CUST playbook. |
| 7 | AMBER | T107042 | DUP | >5d | BAC | Barclays | $3,554,407 | BAC SELL 9,613@$369.75 vs Barclays: dup; apply DUP playbook. |
| 8 | AMBER | T105612 | MISSING_INT | >5d | GS | UBS | $3,518,522 | GS SELL 8,863@$396.99 vs UBS: missing_int; apply MISSING_INT playbook. |
| 9 | AMBER | T104355 | MISSING_INT | >5d | GS | Barclays | $3,432,194 | GS BUY 7,506@$457.26 vs Barclays: missing_int; apply MISSING_INT playbook. |
| 10 | AMBER | T102054 | MISSING_INT | >5d | JPM | Citi | $3,410,246 | JPM BUY 8,576@$397.65 vs Citi: missing_int; apply MISSING_INT playbook. |
| 11 | AMBER | T102036 | MISSING_INT | >5d | MSFT | JP Morgan | $3,163,277 | MSFT SELL 9,032@$350.23 vs JP Morgan: missing_int; apply MISSING_INT playbook. |
| 12 | AMBER | T109706 | MISSING_INT | >5d | GS | JP Morgan | $3,151,029 | GS BUY 6,548@$481.22 vs JP Morgan: missing_int; apply MISSING_INT playbook. |
| 13 | AMBER | T109040 | MISSING_INT | >5d | MSFT | Citi | $3,102,554 | MSFT SELL 9,053@$342.71 vs Citi: missing_int; apply MISSING_INT playbook. |
| 14 | AMBER | T102637 | MISSING_CUST | >5d | JPM | Barclays | $2,964,532 | JPM SELL 6,951@$426.49 vs Barclays: missing_cust; apply MISSING_CUST playbook. |
| 15 | AMBER | T108473 | MISSING_INT | >5d | BAC | JP Morgan | $2,835,804 | BAC BUY 9,737@$291.24 vs JP Morgan: missing_int; apply MISSING_INT playbook. |
| 16 | AMBER | T106164 | DUP | >5d | BAC | UBS | $2,798,271 | BAC BUY 5,981@$467.86 vs UBS: dup; apply DUP playbook. |
| 17 | AMBER | T105301 | DUP | >5d | AAPL | Goldman Sachs | $2,789,154 | AAPL SELL 7,652@$364.50 vs Goldman Sachs: dup; apply DUP playbook. |
| 18 | AMBER | T106276 | DUP | >5d | MSFT | Goldman Sachs | $2,743,217 | MSFT BUY 5,516@$497.32 vs Goldman Sachs: dup; apply DUP playbook. |
| 19 | AMBER | T107061 | DUP | >5d | AAPL | UBS | $2,680,380 | AAPL BUY 9,988@$268.36 vs UBS: dup; apply DUP playbook. |
| 20 | AMBER | T109493 | MISSING_INT | >5d | GS | Morgan Stanley | $2,646,735 | GS BUY 6,019@$439.73 vs Morgan Stanley: missing_int; apply MISSING_INT playbook. |
| 21 | AMBER | T104597 | MISSING_CUST | >5d | GS | Goldman Sachs | $2,345,536 | GS SELL 6,700@$350.08 vs Goldman Sachs: missing_cust; apply MISSING_CUST playbook. |
| 22 | AMBER | T109068 | MISSING_INT | >5d | VOD.L | Barclays | $2,256,875 | VOD.L SELL 6,006@$375.77 vs Barclays: missing_int; apply MISSING_INT playbook. |
| 23 | AMBER | T102369 | MISSING_INT | >5d | AAPL | JP Morgan | $2,253,908 | AAPL BUY 9,405@$239.65 vs JP Morgan: missing_int; apply MISSING_INT playbook. |
| 24 | AMBER | T105102 | MISSING_INT | >5d | TSLA | UBS | $2,241,748 | TSLA BUY 4,874@$459.94 vs UBS: missing_int; apply MISSING_INT playbook. |
| 25 | AMBER | T109812 | MISSING_CUST | >5d | AAPL | Citi | $2,241,246 | AAPL SELL 4,748@$472.04 vs Citi: missing_cust; apply MISSING_CUST playbook. |

## 3. RED tier — deep dive (top 5)

### T104657 — MISSING_CUST | >5d | $4,509,881 at risk

T104657 (TSLA SELL 9,114 @ $494.83 vs Citi) is on internal book but custodian shows no record after 9 days, exposing $4,509,881 of notional that has missed multiple settlement cycles. Apply MISSING_CUST playbook starting with the SWIFT inbox and Citi trade-support; given age and notional, escalate to head of Settlements immediately.

| Field | Internal | Custodian |
| --- | --- | --- |
| Security | TSLA | nan |
| Side | SELL | nan |
| Quantity | 9114.0 | nan |
| Price | 494.83 | nan |
| Counterparty | Citi | nan |

_Age: 9 days. Apply playbook for MISSING_CUST (Section 5)._

### T106227 — MISSING_INT | >5d | $4,484,546 at risk

T106227 (GS BUY 9,801 @ $457.56, counterparty UBS) appears on custodian record but is absent from the internal book at 8 days, raising risk of an unrecognised trade approaching settlement. Apply MISSING_INT playbook urgently - confirm legitimacy with UBS trade-support and raise an emergency back-booking; escalate to compliance if no booking authorisation can be located.

| Field | Internal | Custodian |
| --- | --- | --- |
| Security | nan | GS |
| Side | nan | BUY |
| Quantity | nan | 9801.0 |
| Price | nan | 457.56 |
| Counterparty | nan | UBS |

_Age: 8 days. Apply playbook for MISSING_INT (Section 5)._

### T102309 — DUP | >5d | $4,460,860 at risk

T102309 (AMZN BUY 9,462 @ $471.45, counterparty Goldman Sachs) appears twice on the custodian side and has been aged 8 days without resolution, doubling settlement-fail risk on a $4,460,860 notional. Apply DUP playbook - verify byte-identical duplication, check OMS for duplicate booking events at execution time, and cancel one row before settlement; escalate immediately given age.

| Field | Internal | Custodian |
| --- | --- | --- |
| Security | AMZN | AMZN |
| Side | BUY | BUY |
| Quantity | 9462.0 | 9462.0 |
| Price | 471.45 | 471.45 |
| Counterparty | Goldman Sachs | Goldman Sachs |

_Age: 8 days. Apply playbook for DUP (Section 5)._

### T106621 — MISSING_CUST | >5d | $4,377,163 at risk

T106621 (HSBA.L BUY 9,117 @ $480.11 vs Goldman Sachs) is on internal book but custodian shows no record after 9 days, exposing $4,377,163 of notional that has missed multiple settlement cycles. Apply MISSING_CUST playbook starting with the SWIFT inbox and Goldman Sachs trade-support; given age and notional, escalate to head of Settlements immediately.

| Field | Internal | Custodian |
| --- | --- | --- |
| Security | HSBA.L | nan |
| Side | BUY | nan |
| Quantity | 9117.0 | nan |
| Price | 480.11 | nan |
| Counterparty | Goldman Sachs | nan |

_Age: 9 days. Apply playbook for MISSING_CUST (Section 5)._

### T100465 — MISSING_INT | >5d | $4,157,725 at risk

T100465 (HSBA.L SELL 9,214 @ $451.24, counterparty Morgan Stanley) appears on custodian record but is absent from the internal book at 9 days, raising risk of an unrecognised trade approaching settlement. Apply MISSING_INT playbook urgently - confirm legitimacy with Morgan Stanley trade-support and raise an emergency back-booking; escalate to compliance if no booking authorisation can be located.

| Field | Internal | Custodian |
| --- | --- | --- |
| Security | nan | HSBA.L |
| Side | nan | SELL |
| Quantity | nan | 9214.0 |
| Price | nan | 451.24 |
| Counterparty | nan | Morgan Stanley |

_Age: 9 days. Apply playbook for MISSING_INT (Section 5)._

## 4. Long tail — apply playbooks

475 breaks beyond the top 25, totalling $359,499,930. Routed to category playbooks.

| Category | Count | Total $ at risk |
| --- | --- | --- |
| DUP | 94 | $132,122,779 |
| MISSING_INT | 87 | $111,970,655 |
| MISSING_CUST | 94 | $100,365,353 |
| QTY_DIFF | 100 | $14,308,677 |
| PRICE_TOL | 100 | $732,467 |

## 5. Category playbooks (reference appendix)

### MISSING_CUST

- **Typical root cause**: Confirmation from counterparty was not received or was misrouted, often a wrong sub-account or a SWIFT routing error.
- **Resolution steps**:
  1. Pull the original trade ticket and confirmation from the trader's blotter.
  1. Check the SWIFT MT515/MT543 inbox for messages around trade date.
  1. Contact the counterparty's middle-office desk; request the confirm be re-sent.
  1. If counterparty already sent it, escalate to custodian to investigate routing.
- **Primary contact**: Counterparty middle-office desk; custodian operations team.
- **Expected resolution time**: 2 business days when counterparty is responsive.
- **Escalation trigger**: Aged > 5 business days OR notional > $5M -> escalate to head of Settlements.

### MISSING_INT

- **Typical root cause**: Front-office capture failed or trader booked to wrong book/account; common after manual ticketing or system reboots.
- **Resolution steps**:
  1. Verify the trade was legitimately ours using the counterparty confirm.
  1. Check trader blotter, OMS audit log, and email confirmations.
  1. If legitimate, raise an emergency back-booking ticket with trade-support.
  1. Update internal book and re-run reconciliation.
- **Primary contact**: Front-office trade support; OMS administrator.
- **Expected resolution time**: Same day for valid trades.
- **Escalation trigger**: Aged > 2 business days near settlement OR potential unauthorised trade.

### QTY_DIFF

- **Typical root cause**: Allocation error - block trade split incorrectly across accounts, or fat-finger correction made on one side only.
- **Resolution steps**:
  1. Compare the executed quantity at the venue vs both internal and custodian.
  1. Identify which side has the discrepancy (typically the side that allocated last).
  1. Coordinate with the side in error to amend the record.
  1. Confirm both sides agree before re-running reconciliation.
- **Primary contact**: Allocations team (internal) or counterparty trade support.
- **Expected resolution time**: Same business day.
- **Escalation trigger**: Quantity diff > 10% of trade size OR repeated breaks with same counterparty.

### PRICE_TOL

- **Typical root cause**: Stale or wrong execution price on one side, often when trader blotter updates before back-office sync.
- **Resolution steps**:
  1. Pull the original execution timestamp and venue from the OMS.
  1. Cross-check Bloomberg/Refinitiv tick history at execution time.
  1. Identify which price is correct vs stale; ask the wrong side to amend.
  1. Verify both sides agree within tolerance after the fix.
- **Primary contact**: Trader (for execution price); counterparty trade support.
- **Expected resolution time**: Same business day.
- **Escalation trigger**: Price difference > 50 bps OR trade settles within 24 hours.

### DUP

- **Typical root cause**: Same trade booked twice - usually a system retry, manual re-entry, or feed replay.
- **Resolution steps**:
  1. Confirm both rows are byte-identical (same security, qty, price, side, counterparty).
  1. Check OMS audit log for duplicate booking events around the same timestamp.
  1. Cancel the duplicate row in the system that has it twice.
  1. Verify the trade flows through correctly after cancellation.
- **Primary contact**: Trade-support; OMS administrator if a feed replay is suspected.
- **Expected resolution time**: Same business day.
- **Escalation trigger**: Duplicate confirmed and approaching settlement.

