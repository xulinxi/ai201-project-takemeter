# Milestone 4 — Zero-shot baseline results

**Model:** Groq `llama-3.3-70b-versatile`, temperature 0, zero-shot.
**Test set:** 33 examples (the locked 15% split, stratified, `random_state=42`).
**Parseable:** 33/33 (0 unparseable after fixing the prompt).

## Metrics

| | precision | recall | f1 | support |
|---|---|---|---|---|
| analysis | 1.00 | 0.92 | 0.96 | 12 |
| hot_take | 0.90 | 0.82 | 0.86 | 11 |
| reaction | 0.83 | 1.00 | 0.91 | 10 |
| **accuracy** | | | **0.909** | 33 |
| macro avg | 0.91 | 0.91 | 0.91 | 33 |
| weighted avg | 0.92 | 0.91 | 0.91 | 33 |

## Reflection (where the baseline struggled)
- Dominant error: **`hot_take` → `reaction`.** `hot_take` had the lowest recall (0.82) and
  `reaction` the lowest precision (0.83) — terse, unsupported opinions with emotional tone get
  read as feelings rather than as confident claims.
- The `analysis`↔`hot_take` boundary (the boundary I expected to be hardest) was barely an
  issue: only 1 `analysis` example was missed. `analysis` had perfect precision (1.00).
- Hypothesis to test after fine-tuning: the fine-tuned model will likely show the **same**
  `hot_take`/`reaction` confusion, because that's where the label boundary is genuinely
  fuzziest in the data — not a model-capacity problem.

## ⚠️ Caveat on interpreting this baseline
The 0.91 is high for a subjective task. The labels being scored against are **AI pre-labels**
generated with the same taxonomy/tiebreak rules this Groq prompt uses, so the score partly
reflects two LLMs agreeing on a shared rubric, not pure task difficulty. **Human review of
`data/takemeter.csv` is needed before treating these numbers as definitive.** This also means
fine-tuning must reach ~0.96 to "beat baseline by ≥0.05" — a hard bar.
