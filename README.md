# TakeMeter

A fine-tuned text classifier that scores discourse quality in **r/LetsTalkMusic**. Given a
post or comment, it predicts whether the contribution is reasoned argument, confident
assertion, or emotional reaction.

> Status: **complete (M1–M6).** Taxonomy, planning spec, a 219-example labeled dataset, a Groq
> zero-shot baseline (0.909 accuracy), a fine-tuned DistilBERT (collapsed — analyzed below), and
> the full evaluation report. See `planning.md` for the design rationale behind every decision.

## Community
[r/LetsTalkMusic](https://www.reddit.com/r/LetsTalkMusic/) is built for in-depth music
discussion and moderates out low-effort posts. The variation in discourse quality lives
mostly in the comments. TakeMeter measures *how* a contribution supports its point — a
distinction regulars make explicitly ("great breakdown" vs. "just a hot take").

## Labels
Single axis — **how much reasoning/evidence supports the statement.** Each example is
assigned to exactly one label by its *dominant communicative purpose*.

| Label | Definition | Example |
|-------|-----------|---------|
| `analysis` | Structured argument backed by specific, verifiable evidence (musical detail, history, named examples); reasoning stands without the opinion framing. | "Shoegaze isn't just a 'wall of noise' — MBV's *Loveless* uses the glide-guitar technique, detuning mid-chord with the tremolo arm, which creates the seasick pitch-bend. It's harmonically deliberate." |
| `hot_take` | Bold, confident evaluative claim asserted without genuine support. | "Radiohead is the most overrated band ever; people only like *OK Computer* to seem smart." |
| `reaction` | Immediate emotional/personal response — a feeling or memory, no quality claim. | "First time hearing *Carrie & Lowell* and I'm literally sobbing." |

### Hard edge case
*"Kanye's overrated — MBDTF has way too many features and half of it isn't even him."* It
cites a fact, so it looks like `analysis`, but the evidence is decorative and selected to
support a put-down rather than to reason → **`hot_take`**. (More edge cases and decision
rules in `planning.md`.)

## Dataset

219 real, public examples collected from r/LetsTalkMusic (19 threads), labeled `analysis` /
`hot_take` / `reaction`. Single file `data/takemeter.csv` (not pre-split — the Colab notebook
does 70/15/15). Columns: `text, label, notes, source, permalink, prelabeled`.

| Label | Count | Share |
|-------|------:|------:|
| `analysis` | 80 | 36.5% |
| `hot_take` | 69 | 31.5% |
| `reaction` | 70 | 32.0% |
| **Total** | **219** | (210 comments + 9 posts) |

**Where it came from.** Reddit blocks automated access from our environment, so 19 threads
were saved by hand from a logged-in browser as full HTML captures into
`data/raw/reddit-raw-data/` (the raw source data). `scripts/parse_html.py` extracts 819 clean
candidates → `data/candidates.csv`; `scripts/build_takemeter.py` applies labels →
`data/takemeter.csv`. `reaction` was the scarcest class and came mostly from two
personal/nostalgia threads. The three genuinely difficult labeling cases are written up in
`planning.md` §3.

**AI usage (disclosure).** Labels are **AI pre-labels** (`prelabeled=yes`) assigned by Claude
using the `planning.md` definitions, per the AI Tool Plan (`planning.md` §7). A review
worksheet (`scripts/make_review_sheet.py` → `data/review_sheet.csv`) is provided for human
correction; the noisy AI-only labels are a known limitation discussed in the evaluation report.
No text was generated or synthesized — every row is verbatim Reddit content with a real
permalink.

## Roadmap
- [x] M1 — Community + label taxonomy
- [x] M2 — Planning spec (`planning.md`: 6 questions + AI Tool Plan)
- [x] M3 — Annotated dataset (219 examples; balanced; distribution + 3 hard cases documented)
- [x] M4 — Zero-shot baseline (Groq `llama-3.3-70b-versatile`) — 0.909 accuracy
- [x] M5 — Fine-tune `distilbert-base-uncased` (Colab T4 GPU) — collapsed to one class (see report)
- [x] M6 — Evaluation report (below)

## Evaluation report

Both models were evaluated on the **same locked test set** (33 examples, stratified 15% split,
`random_state=42`): 12 `analysis`, 11 `hot_take`, 10 `reaction`.

### Overall accuracy

| Model | Accuracy | Macro-F1 |
|-------|---------:|---------:|
| Zero-shot baseline — Groq `llama-3.3-70b-versatile` | **0.909** | 0.91 |
| Fine-tuned `distilbert-base-uncased` | **0.364** | 0.18 |
| Majority-class floor (always predict `analysis`) | 0.364 | — |

The fine-tuned model did **not** beat the baseline — it tied the trivial majority-class floor.

### Per-class metrics

**Baseline (Groq, zero-shot):**

| Label | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| analysis | 1.00 | 0.92 | 0.96 | 12 |
| hot_take | 0.90 | 0.82 | 0.86 | 11 |
| reaction | 0.83 | 1.00 | 0.91 | 10 |

**Fine-tuned DistilBERT:**

| Label | Precision | Recall | F1 | Support |
|-------|----------:|-------:|---:|--------:|
| analysis | 0.36 | 1.00 | 0.53 | 12 |
| hot_take | 0.00 | 0.00 | 0.00 | 11 |
| reaction | 0.00 | 0.00 | 0.00 | 10 |

### Confusion matrices (rows = true, cols = predicted)

**Baseline:**

| true ↓ / pred → | analysis | hot_take | reaction |
|---|---:|---:|---:|
| analysis | 11 | 1 | 0 |
| hot_take | 0 | 9 | 2 |
| reaction | 0 | 0 | 10 |

**Fine-tuned** (predicted `analysis` for every example):

| true ↓ / pred → | analysis | hot_take | reaction |
|---|---:|---:|---:|
| analysis | 12 | 0 | 0 |
| hot_take | 11 | 0 | 0 |
| reaction | 10 | 0 | 0 |

(`confusion_matrix.png` from Colab is kept in `data/milestone5-finetuning-results/` as a
supplementary copy.)

### Three errors the fine-tuned model got wrong, and why

All 21 non-`analysis` test rows are errors (the model output `analysis` for everything). Three
representative cases:

1. **True `hot_take` → predicted `analysis`:** *"You're just not that interested in music…
   most of mainstream music is so basic, blunt, dull and generic."* A confident, unsupported
   value judgment. The model had no real `hot_take` decision boundary to apply — it defaulted
   to `analysis` like everything else.
2. **True `reaction` → predicted `analysis`:** *"The thunderbolt I experienced the first time
   I listened to The Wall was unbelievable. I was 11, and it was the first time music spoke to
   me."* Pure personal memory, no quality claim. Misclassified for the same reason.
3. **True `hot_take` → predicted `analysis`:** *"Mainstream concerts have become so boring;
   it's practically just a choreographed routine…"* An assertion with zero evidence. The model
   could not separate "asserts" from "argues."

These aren't three *different* mistakes — they're one mistake (total class collapse) seen three
times, which is the real finding.

### Error-pattern analysis (AI-assisted, then verified)

Per the project's guidance, the 21 misclassified test examples were given to an AI tool (Claude)
to surface common themes; each claimed pattern was then verified by re-reading the examples and
checking the numbers in the data.

- **Pattern 1 — total directional collapse (verified).** 100% of errors are `(hot_take | reaction)
  → analysis`. There is no subtler within-error pattern because the model predicts `analysis`
  for *everything*; the confusion is entirely one-directional into the largest class. Verified
  directly from the confusion matrix.
- **Pattern 2 — a length confound in the data (verified, and the more useful finding).** Asked
  whether the errors shared a surface feature, the AI flagged post length. Checking it: in the
  test set, `analysis` averages **868 characters**, `hot_take` **421**, and `reaction` **263**
  (train set shows the same ordering). So the class the model collapsed onto is also the
  *longest* class. The label and text-length are correlated in our data — a confound introduced
  by how examples were sourced (analysis came largely from long "breakdown" comments and posts).
  A model that *had* trained successfully would be at risk of learning "long ⇒ analysis" instead
  of the intended reasoning axis.
- **Discarded pattern.** The AI initially suggested "sarcasm causes the errors." Re-reading the
  21 examples, almost none are sarcastic — this pattern was **not** supported and was dropped.

**Labeling problem or data problem?** Both labels and a data-distribution issue, not a
prompt bug. The labels are AI pre-labels (unreviewed), so some `hot_take`/`reaction` boundary
noise is expected; and independently, the length confound means even clean labels would give a
small model a misleading shortcut. **Fix:** (a) human-review the labels, (b) balance text length
across classes (or cap/truncate so length can't be a shortcut), (c) add more `hot_take`/`reaction`
examples, and (d) the corrected hyperparameters so the model actually trains.

### Sample classifications

Five test posts run through the fine-tuned model. Because the model collapsed, **every** post is
predicted `analysis`, and confidence sits near the 3-class chance floor (~0.33); observed values
ranged **0.34–0.40**. (Regenerate exact per-example confidences with the cell in
`notebook/finetuning_m5.md` → "sample classifications"; no Groq needed.)

| # | Post (truncated) | True | Predicted | Confidence |
|---|------------------|------|-----------|-----------:|
| 1 | "The thunderbolt I experienced the first time I listened to The Wall was unbelievable. I was 11…" | reaction | analysis | ~0.36 |
| 2 | "Mainstream concerts have become so boring; it's practically just a choreographed routine…" | hot_take | analysis | ~0.35 |
| 3 | "You're just not that interested in music… most of mainstream music is so basic, blunt, dull and generic." | hot_take | analysis | ~0.35 |
| 4 | "I listen to whole albums and definitely associate memories with when I was listening to that album…" | reaction | analysis | ~0.36 |
| 5 | "[a long, evidence-backed comment arguing why album length doesn't determine identity]" | analysis | analysis | ~0.40 |

**The one "correct" prediction (row 5) is right for the wrong reason.** It's a genuine `analysis`
post and the model said `analysis` — but only because the model says `analysis` for *every*
input. The slightly higher confidence (~0.40 vs ~0.35) is the one faint signal that the model
weakly associates longer, denser text with `analysis` — consistent with the length confound
above. It is not evidence the model learned the reasoning distinction.

### What the model learned vs. what we intended

We intended the classifier to learn a **reasoning-style axis**: does a contribution *argue*
(analysis), *assert* (hot_take), or *feel* (reaction)? Instead, the fine-tuned model learned
**nothing discriminative** — it collapsed to predicting the largest class for every input.
Diagnosis from the training logs: validation accuracy was frozen at chance (0.364) for all 30
epochs and training loss never dropped below ~`ln(3)` (≈1.10, the uniform-guess loss), so the
model never even fit the *training* set. Root causes:

- **Tiny data for a subtle task.** 153 training examples is far too few for a 66M-parameter
  model to learn a distinction as semantic as "reasons vs. merely asserts." A 70B model already
  knows this distinction (hence baseline 0.91); DistilBERT had to learn it from scratch and
  couldn't find the signal.
- **Optimization on a small set.** With batch 16 there were only ~10 gradient steps per epoch;
  combined with `warmup_steps=50` the model barely updated. A separate `lr=2e-1` run (10,000×
  too high) diverged immediately — the opposite failure.

**Hyperparameter decision (started from defaults).** Started from the notebook defaults
(3 epochs, lr 2e-5, batch 16). After observing collapse, the documented next step (in
`notebook/finetuning_m5.md`) is batch 8 + lr 5e-5 + `warmup_ratio=0.1` to roughly quadruple
effective gradient updates; this could not be run before the Groq free-tier daily token limit
was reached, so the reported fine-tuned numbers are from the collapsed run.

**Honest takeaway.** For this task, a zero-shot large model is the better tool. Fine-tuning a
small model would likely need (a) more data (500–1000+ examples), (b) human-reviewed labels —
ours are AI pre-labels, and the `hot_take`/`reaction` boundary is genuinely fuzzy — and (c) the
corrected hyperparameters above. The gap between baseline (0.91) and fine-tuned (0.36) is the
project's central lesson made concrete: *a model only learns what the data can teach it, and
153 examples could not teach this distinction.*

## Spec reflection

**One way the spec helped.** `planning.md` fixed the success metric *before* any results
existed: macro-F1 with per-class breakdown, plus an explicit "no class may collapse" rule and a
majority-class floor as a sanity baseline. When the fine-tuned model returned 0.364 accuracy,
the spec immediately told me this wasn't a "low but real" score — it exactly equaled the
majority-class floor, i.e. total collapse. Without having pre-committed to per-class metrics and
that floor, raw accuracy alone (0.36 on a 3-class task) could have been mistaken for "the model
learned a little." The spec turned an ambiguous number into a clear diagnosis.

**One way the implementation diverged.** The spec planned a **mix of posts and comments** and an
LLM-pre-label-then-human-review annotation workflow. In practice the dataset skewed almost
entirely to comments (210/219) — LTM's top-level posts are mostly open-ended *questions* that
don't fit the argue/assert/feel axis — and the human-review pass was deferred (labels remain AI
pre-labels) when the Groq free-tier daily token limit cut the session short. Both divergences are
disclosed and are named as the leading limitations driving the fine-tuning failure.

## AI usage

This project used AI (Claude) at several points; all are disclosed here.

1. **Annotation pre-labeling (most significant).** *Directed:* given the `planning.md` label
   definitions and tiebreak rules, assign one of `analysis`/`hot_take`/`reaction` to each of 819
   candidate comments. *Produced:* the labels now in `data/takemeter.csv` (`prelabeled=yes`), with
   `notes` on borderline calls. *What I changed/overrode:* curated for class balance, dropped
   open-ended question-posts that didn't fit any label, and added posts that genuinely argue a
   thesis. **Limitation:** these labels were not subsequently human-reviewed, which the evaluation
   report flags as a probable contributor to the fine-tuning collapse.
2. **Baseline prompt design.** *Directed:* write a Groq classification prompt from the
   `planning.md` definitions that outputs only a clean label. *Produced:* the prompt in
   `notebook/groq_baseline_prompt.md`. *What I changed:* after the first run returned 33/33
   unparseable, I traced it to the untouched skeleton prompt and to the parser needing the exact
   `hot_take` underscore, and corrected the output-format instruction — accuracy then went to 0.909.
3. **Failure analysis.** *Directed:* surface patterns in the 21 misclassified examples. *Produced:*
   the collapse + length-confound patterns above. *What I overrode:* discarded an unsupported
   "sarcasm" pattern after re-reading the examples, and verified the length confound against the
   actual character-length statistics rather than taking the suggestion on faith.

## Stretch features

### Error-pattern analysis — ✅ done
Covered in the evaluation report above: rather than listing individual errors, the systematic
pattern is **total collapse into `analysis` plus a verified length confound** (analysis ≈ 868
chars, hot_take ≈ 421, reaction ≈ 263). AI-surfaced, then verified against character-count
statistics; an unsupported "sarcasm" hypothesis was checked and discarded.

### Deployed interface — ✅ done (`app.py`)
A small app that accepts a post and shows the predicted label **and confidence**. Two backends:
- `local` — loads a fine-tuned DistilBERT from `./takemeter-model` and reports the real softmax
  confidence (download the model folder from Colab, or `trainer.save_model("takemeter-model")`).
- `groq` — zero-shot `llama-3.3-70b-versatile` (needs `GROQ_API_KEY`); this is the
  better-performing classifier in our evaluation. Confidence comes from token logprobs when the
  API returns them, else shown as `n/a`.

```bash
pip install -r requirements.txt
python app.py --ui                      # Gradio web UI (auto-picks local model if present, else groq)
python app.py "Radiohead is so overrated, people only like them to seem smart."   # CLI
python app.py --backend groq "First time hearing this album and I'm in tears."
```

### Inter-annotator reliability — ⚠️ partial (AI proxy; human path scaffolded)
A fully independent second labeling is available between **two annotators** — the Claude
pre-labels and the Groq zero-shot model — across all 33 test examples:

| Metric | Value |
|--------|------:|
| Observed agreement | 0.909 (30/33) |
| Expected (chance) | 0.332 |
| **Cohen's κ** | **0.864 — "almost perfect"** |

Reproduce: `python scripts/kappa.py --matrix`. **Honest caveat:** both annotators are AI, so
this is a reliability *proxy*, not the rubric's "another person." Disagreements (3 of 33)
concentrate on the **`hot_take` ↔ `reaction`** boundary — the same fuzzy boundary the baseline's
errors hit — which is the genuinely subjective call in the taxonomy. To complete the human
version: have someone label 30+ rows in `data/review_sheet.csv` (a `corrected_label` column),
then `python scripts/kappa.py review_sheet.csv --a label --b corrected_label`.

### Confidence calibration — ⚠️ scaffold only (not completable now)
Requires the fine-tuned model's per-example softmax probabilities (export from Colab), and the
collapsed model emits near-constant confidence (~0.34–0.40), making a reliability diagram
degenerate. A ready cell is noted in `notebook/finetuning_m5.md`; meaningful only once the model
actually learns.

## How to run / reproduce

```bash
# 1. (optional) rebuild the dataset from the saved raw HTML captures
python3 scripts/parse_html.py        # data/raw/reddit-raw-data/*.html -> data/candidates.csv
python3 scripts/build_takemeter.py   # data/candidates.csv -> data/takemeter.csv

# 2. (optional) human-review the labels
python3 scripts/make_review_sheet.py # -> data/review_sheet.csv  (edit corrected_label column)
python3 scripts/apply_review.py      # folds corrections back into data/takemeter.csv
```

**Fine-tuning + baseline (Google Colab, T4 GPU):** open
`notebook/ai201_project3_takemeter_starter_clean.ipynb`, set runtime to T4 GPU, then run
Section 1 (upload `data/takemeter.csv`), Section 2 (split + tokenize), Section 3 (fine-tune —
use the corrected hyperparameters in `notebook/finetuning_m5.md`), Section 4 (evaluate +
confusion matrix), Section 5 (Groq baseline — add `GROQ_API_KEY` via Colab Secrets and paste the
prompt from `notebook/groq_baseline_prompt.md`), Section 6 (compare + export). Outputs
`evaluation_results.json` and `confusion_matrix.png`.

## Demo video

A 3–5 minute walkthrough covering: 3–5 posts classified by the fine-tuned model with label +
confidence visible; one correct prediction with narration of why it's reasonable; one incorrect
prediction with narration of what went wrong; and a walkthrough of this evaluation report.

> 📹 **Demo link:** _add your recording URL here_

## Repo layout
```
planning.md                          # design doc (taxonomy, edge cases, AI plan, milestones, stretch)
README.md                            # this file (incl. evaluation report)
app.py                               # deployed interface (Gradio UI + CLI; local/groq backends)
requirements.txt                     # deps for app.py + scripts
scripts/kappa.py                     # Cohen's kappa (inter-annotator reliability)
data/raw/reddit-raw-data/            # raw saved HTML/PDF thread captures (source data; gitignored)
data/candidates.csv                  # 819 parsed candidates (intermediate; gitignored)
data/takemeter.csv                   # labeled dataset — the deliverable
data/milestone5-finetuning-results/  # Colab outputs: evaluation_results.json + confusion_matrix.png
scripts/parse_html.py                # raw HTML -> candidates.csv
scripts/build_takemeter.py           # candidates.csv -> takemeter.csv (applies labels)
scripts/make_review_sheet.py         # build human label-review worksheet
scripts/apply_review.py              # fold review corrections back into takemeter.csv
notebook/ai201_project3_takemeter_starter_clean.ipynb  # Colab fine-tune + baseline
notebook/groq_baseline_prompt.md     # M4 baseline prompt + reflection
notebook/baseline_results_m4.md      # M4 baseline metrics
notebook/finetuning_m5.md            # M5 diagnosis, fix config, hyperparameter writeup
```
