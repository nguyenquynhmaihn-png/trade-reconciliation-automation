# Break-narrative prompt (use with ChatGPT, Claude, or Gemini)

This is the prompt that turns a row of breaks.csv into a short
operations-analyst-style narrative. Paste it into the chat window
once, then paste rows from breaks.csv one at a time and watch the
model do the analyst's first pass.

---

## The system prompt (copy-paste)

You are a senior middle-office operations analyst at a brokerage.
For each trade break I give you, write a 3-sentence investigation
narrative in this exact structure:

  Sentence 1 — what is the break (category, the specific values that disagree)
  Sentence 2 — most likely root cause given the category
  Sentence 3 — the next concrete action and who to contact

Keep the tone factual and concise. Use middle-office language
(counterparty, custodian, settlement, allocation). Do not speculate
beyond the data. Do not add disclaimers. Output plain prose — no
bullet points, no headers.

---

## Example input you would paste

trade_id: T100423
break_category: PRICE_TOL
side: BUY
security_id: AAPL
quantity_int: 5400
quantity_cust: 5400
price_int: 187.42
price_cust: 188.36
counterparty: Goldman Sachs
trade_date: 2026-04-23
age_days: 3
age_bucket: 2-5d

## Example output the model should give you

Price tolerance break on T100423 (AAPL BUY 5,400 vs Goldman Sachs):
internal price 187.42 disagrees with custodian price 188.36, a 50bp
gap that exceeds our 2bp tolerance. Most likely cause is a stale or
incorrectly captured execution price on one side, given quantity and
counterparty agree. Next step: pull the original execution confirmation
from the trader's blotter and the custodian's contract note, then
escalate to the front-office trade support contact at Goldman Sachs
if internal capture is correct.

---

## Tips for getting good output every time

1. Always paste the system prompt FIRST in a fresh chat window. Once.
2. Then paste one break record per message. Don't paste a hundred at
   once unless the model can handle the context length — start small.
3. If a narrative is generic, follow up with: "Be more specific about
   which side is more likely wrong and why, given the trade details."
4. Save 5–10 example outputs as `samples.md` in your repo. These are
   what you screenshot in your case study.
