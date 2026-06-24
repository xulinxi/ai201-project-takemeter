# Milestone 5 — Fine-tuning: diagnosis, fix, and results

## First attempts (both failed — model collapsed to one class)

| Run | epochs | lr | batch | finetuned acc | what happened |
|-----|-------:|---:|------:|--------------:|---------------|
| `learning_rate=2e-1` | 3 | **2e-1** | 16 | 0.364 | LR ~10,000× too high → optimizer diverges → collapse |
| `epochs30` | 30 | 2e-5 | 16 | 0.364 | correct LR but never learned (see below) |

**Smoking gun (epochs30 training log):** validation accuracy was frozen at **0.3636 for all
30 epochs**, and training loss only drifted 1.40 → ~1.10. Note 1.10 ≈ `ln(3) = 1.0986`, the
loss of uniform random guessing on 3 classes — i.e. the model never learned even the *training*
set. Per-class report: `analysis` recall 1.00 / `hot_take` 0.00 / `reaction` 0.00 → it predicts
`analysis` for every test example. 0.3636 = 12/33 = the `analysis` share of the test set.

Root cause: on a tiny dataset (153 train examples ≈ ~10 gradient steps/epoch at batch 16) the
encoder didn't get enough effective updates to escape the all-one-class solution, and
`warmup_steps=50` ate most of the schedule. `2e-1` is simply broken.

## Fix to run next (paste into Section 3's `TrainingArguments`)

```python
training_args = TrainingArguments(
    output_dir="./takemeter-model",
    num_train_epochs=8,
    per_device_train_batch_size=8,     # smaller batch -> 2x more gradient steps on tiny data
    per_device_eval_batch_size=32,
    learning_rate=5e-5,                # higher than 2e-5: more signal per step
    weight_decay=0.01,
    warmup_ratio=0.1,                  # replaces warmup_steps=50 (too big for ~150 steps)
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=1,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    logging_steps=5,
    report_to="none",
)
```

**The one diagnostic to watch:** the **Training Loss** column.
- Drops toward ~0.2–0.5 → the model is finally learning; check the per-class F1 next.
- Still stuck near ~1.1 → deeper wiring bug (labels column / tokenization); send Sections 1–2.

If it learns but still trails the 0.91 baseline, that is a legitimate result — see "Interpretation".

## Hyperparameter decision (for the README, required by the rubric)
> Started from the notebook defaults (3 epochs, lr 2e-5, batch 16), which collapsed to a
> single class on our 153-example training set (val accuracy frozen at chance, train loss
> stuck at ln(3)). Key change: **lowered batch size 16 → 8 and raised learning rate
> 2e-5 → 5e-5**, which roughly quadruples the number of effective gradient updates and gives
> the small dataset enough signal to escape the degenerate all-one-class solution. Epochs set
> to 8 with `warmup_ratio=0.1`. A separate `lr=2e-1` experiment confirmed that very high
> learning rates diverge immediately.

## Interpretation (what the model learned vs. what we intended)
The zero-shot 70B baseline scores 0.91 because the task — *does this contribution reason,
assert, or feel?* — is a subtle semantic distinction a large model already understands. A
66M-parameter DistilBERT fine-tuned on only ~150 examples has to learn that distinction from
scratch; with this little data it tends to latch onto surface features (length, vocabulary)
rather than the reasoning/assertion/feeling axis we actually care about. Whether or not the
fixed run beats the baseline, this gap is the core reflection the project asks for.

## Sample classifications cell (run in Colab after Section 4 — no Groq needed)

Prints 5 test posts with predicted label + confidence for the README's Sample Classifications
table. Uses the already-computed `ft_probs`, `ft_pred_ids`, `test_df` from Section 4.

```python
import numpy as np
for i in range(min(5, len(test_df))):
    text = test_df.iloc[i]["text"]
    true = test_df.iloc[i]["label"]
    pred = ID_TO_LABEL[ft_pred_ids[i]]
    conf = ft_probs[i][ft_pred_ids[i]]
    print(f"[{i}] true={true} pred={pred} conf={conf:.2f}")
    print(f"    {text[:120]}...\n")
```

## Results after the fixed run (fill in)
- Fine-tuned accuracy: ____
- Per-class F1: analysis ____ / hot_take ____ / reaction ____
- Training loss trajectory (first→last): ____ → ____
- Confusion matrix (true rows × predicted cols): paste from notebook
- Beats baseline (0.909)? ____  ·  3 error examples for README: ____
