# TakeMeter — Planning Spec

A fine-tuned text classifier that scores **discourse quality** in r/LetsTalkMusic. Given a
post or comment, it predicts how the contribution supports its point: reasoned argument
(`analysis`), confident assertion (`hot_take`), or emotional response (`reaction`).

This document is the spec. It is written **before any example is labeled** so that the
label boundaries, data plan, and success bar are fixed targets rather than things rationalized
after the fact.

---

## 1. Community

**Choice:** [r/LetsTalkMusic](https://www.reddit.com/r/LetsTalkMusic/).

**Why this community.** It is built specifically for in-depth music discussion and bans
low-effort content (no "what are you listening to", no bare recommendations, no "name this
song"). That gives long-form, text-heavy contributions — enough words per example for a
classifier to have signal, unlike a one-emoji reaction sub.

**Why the discourse is varied enough to be interesting.** The variation here is *intrinsic*,
not just topical. A single thread about one album reliably draws (a) genuine breakdowns of
production or songwriting, (b) confident "this is overrated/underrated" assertions with no
backing, and (c) personal "this record got me through a breakup" reactions. The same subject
produces all three registers, so the label distinction is about *reasoning style*, not about
*topic* — which is exactly the hard, transferable thing to learn. The community also argues
explicitly about take quality ("great write-up" vs. "that's just a hot take"), so the labels
are grounded in language members already use. Volume is ample: 200+ public examples are easy
to gather.

---

## 2. Labels

Single axis: **how much reasoning/evidence supports the statement.** Every example is
assigned to exactly one label by its *dominant communicative purpose* (argue / assert / feel).

### `analysis`
A structured argument about the music backed by specific, verifiable evidence (production,
harmony, rhythm, history, or named song/artist examples) such that the reasoning would still
stand if the opinion framing were stripped away.
- "Shoegaze isn't just a 'wall of noise' — MBV's *Loveless* uses the glide-guitar technique,
  detuning mid-chord with the tremolo arm, which is what creates that seasick pitch-bend.
  It's harmonically deliberate, not just distortion."
- "80s snares sound 'dated' because of gated reverb, popularized after the *In the Air
  Tonight* studio accident — that's a specific recording technique, not just bad mixing."

### `hot_take`
A bold, confident **evaluative claim** asserted without genuine support — it may sound
credible, but it does not actually reason.
- "Radiohead is the most overrated band of all time; people only like *OK Computer* to seem
  smart."
- "Jazz basically died after the 60s — everything since is academic noodling."

### `reaction`
An immediate **emotional or personal** response — a feeling or a memory — that makes no claim
about the music's quality.
- "First time hearing *Carrie & Lowell* and I'm literally sobbing, I don't have words."
- "God I love this song, takes me right back to high school every single time."

---

## 3. Hard edge cases

The taxonomy lives or dies on these boundaries. Each rule below is the tiebreak I will apply
during annotation; the overarching principle is **classify by dominant communicative
purpose, not by surface features** (length, or whether a fact happens to be mentioned).

1. **`analysis` vs `hot_take` — the decorative-evidence trap.**
   *"Kanye's overrated — MBDTF has too many features and half of it isn't even him."*
   It cites a fact, so it mimics analysis. **Rule:** if the evidence is vague, cherry-picked,
   or decorative (there to *sound* credible while delivering a put-down) → `hot_take`. If it
   genuinely reasons (breaks down how specific features change the album's cohesion, with
   examples) → `analysis`. → **hot_take.**
2. **`hot_take` vs `reaction` — the unsupported value judgment.**
   *"This is the worst album ever made."* **Rule:** if it asserts a *quality claim* (even
   unsupported) → `hot_take`; if it only expresses a feeling/experience → `reaction`.
   → **hot_take.**
3. **`analysis` vs `reaction` — the feeling that name-drops a musical detail.**
   *"This album got me through my divorce; the way the strings swell on track 4 still wrecks
   me."* **Rule:** if the musical detail serves a feeling → `reaction`; if a feeling
   decorates an argument → `analysis`. → **reaction.**

**Handling at annotation time:** when an example sits on a boundary, I (a) apply the relevant
rule above, (b) if still ambiguous, default to the *lower-evidence* label (reaction <
hot_take < analysis) so `analysis` stays a high-precision class, and (c) log the example and
my reasoning in the `notes` column of the dataset.

### Real hard cases encountered during annotation (M3)
Three actual dataset examples that genuinely gave pause, with the call made (recorded in the
`notes` column of `data/takemeter.csv`):

1. **Deftones dismissal — `analysis` vs `hot_take`.** *"I honestly can't stand Deftones… I
   just didn't find it catchy at all — it felt way too thick, melty, heavy, and noisy. There
   was no groove, no angles, no syncopation, nothing interesting."* It *names musical
   features* (groove, syncopation), which mimics analysis — but they're vague, decorative
   negatives justifying a gut dislike, not an argument. **→ hot_take.**
2. **Disturbed-era radio — `analysis` vs `hot_take` (the contrast case).** *"The hard rock
   stations at that time were pumping out song after song all day… everything sounded the
   exact same. Like they were all produced on the same day with the same equipment…"*
   Dismissive in tone, but it *reasons* with a specific, checkable mechanism (radio-rock
   homogeneity, production sameness). Set beside case 1, this is what tips a dismissal into
   argument. **→ analysis.**
3. **"Disintegration" first listen — `reaction` vs `hot_take`.** *"The first time I listened
   to Disintegration, 15 years old, I just felt relief… like someone found MY language…
   Would I love to have that for the first time again? Absofuckinlutely!"* Names an album and
   is intensely positive, so it flirts with a quality claim — but it's pure personal feeling,
   no claim about merit. **→ reaction.**

---

## 4. Data collection plan

**Where.** Public r/LetsTalkMusic threads, via `old.reddit.com` / the `.json` endpoints
(manual copy or a small scrape). Captured fields: `text`, `label`, `source` (post|comment),
`permalink`, `prelabeled` (see §7), `edge_notes`.

**How many.** Target **≥ 210 examples, ~70 per label** so every class clears the project's
≥20% floor with margin. Posts skew `analysis`, so I source deliberately:
- `analysis` → top-level posts + highly-upvoted "breakdown" comments.
- `hot_take` → "overrated/underrated" and "unpopular opinion" threads.
- `reaction` → nostalgia / "this song means X to me" comment chains and the less-moderated
  weekly discussion stickies (comments are moderated more lightly than posts).

**Splits.** Stratified 70/15/15 train/val/test (~147 / ~31 / ~32), preserving label balance
in each split. Test set is locked before training and never inspected during tuning.

**If a label is underrepresented after 200.** In priority order: (1) targeted mining of the
thread types above for the short label; (2) re-examine borderline examples currently parked
in adjacent classes under the §3 rules — some genuinely belong to the rare class; (3) as a
documented last resort, drop the total N so the rare class is still ≥20% rather than padding
with weak examples. I will **not** synthesize examples — the dataset stays real text, and any
shortfall is reported honestly in the README rather than hidden.

### What actually happened (M3 results)
- **Access reality:** Reddit blocks server-side fetching from this environment (`curl` → 403)
  *and* the browser-automation extension hard-blocks reddit.com. Data was therefore collected
  by hand: 19 r/LetsTalkMusic threads were saved from a logged-in browser as full HTML page
  captures (plus PDF backups) into `data/raw/reddit-raw-data/`. **These raw captures are the
  saved source data.**
- **Pipeline:** `scripts/parse_html.py` parses the saved `shreddit` HTML → 819 clean
  candidate comments/posts (`data/candidates.csv`, with permalinks). `scripts/build_takemeter.py`
  applies the per-example labels → `data/takemeter.csv` (single file, not pre-split).
- **Final label distribution (219 examples):** `analysis` 80 (36.5%), `hot_take` 69 (31.5%),
  `reaction` 70 (32.0%). No class exceeds 70%; all clear the ≥20% floor comfortably.
- **Data unit:** 210 comments + 9 posts. The "mix" target held, but skewed to comments by
  necessity — LTM top-level posts are mostly open-ended *questions* ("What is the album
  Michael?") that don't map onto argue/assert/feel; the quality variation lives in comments.
  Only posts that genuinely argue a thesis were included.
- **`reaction` was the scarcest** (predicted), and was sourced almost entirely from two
  threads where personal/emotional content concentrates: "I do not understand wanting to hear
  an album for the first time again" and "the only downside to listening to a lot of music".
- **Labels are AI pre-labels** (`prelabeled=yes`) per §7 and **must be human-reviewed before
  M4 fine-tuning.** No examples were synthesized; every row is real text with a permalink.

---

## 5. Evaluation metrics

Accuracy alone is wrong for this task because the classes may be uneven and the *interesting*
errors are concentrated at specific boundaries that accuracy averages away. Metrics, headline
first:

- **Macro-averaged F1 (headline).** Averages F1 across the three classes equally, so a model
  that nails `analysis`/`hot_take` but ignores the rarer `reaction` is penalized. This is the
  number I optimize and report first.
- **Per-class precision / recall / F1.** To locate *where* it fails. I care specifically
  about **precision on `analysis`** (does the decorative-evidence trap leak hot_takes in?)
  and **recall on `reaction`** (does the rare, emotional class get swallowed?).
- **Confusion matrix.** To see error *structure*. Predicted failure modes: `analysis`↔
  `hot_take` confusion at the decorative-evidence boundary, and `hot_take`↔`reaction`
  confusion on terse value judgments. The matrix confirms or refutes these.
- **Overall accuracy.** Reported for completeness and for the head-to-head with baselines.
- **Two baselines for context.** A trivial *majority-class* predictor (proves the model
  learned something beyond "guess the biggest class") and the *Groq zero-shot* baseline
  (proves fine-tuning beat a strong general LLM with no task training).

*(Stretch, if attempted: Cohen's κ for inter-annotator agreement, and a confidence-vs-accuracy
calibration check.)*

---

## 6. Definition of success

Concrete, checkable targets on the locked test set:

| Criterion | Threshold |
|-----------|-----------|
| Fine-tuned macro-F1 | **≥ 0.70** |
| Beats Groq zero-shot baseline | macro-F1 higher by **≥ 0.05** |
| Beats majority-class baseline | clearly (sanity floor) |
| No collapsed class | every class **recall ≥ 0.50** |
| Deployment-grade confidence | among predictions with confidence **> 0.85**, precision **≥ 0.85** |

**Why these.** This is a subjective task with a human-agreement ceiling: if two people only
agree ~80% of the time, a model at ~75% is near the realistic limit, so I am *not* chasing
>0.95 — if I see that, I will suspect a train/test leak or labels that are too easy, and
investigate before celebrating. The "no collapsed class" rule prevents the degenerate
majority-class win. The confidence rule defines "good enough for deployment": a real community
tool would surface TakeMeter as an *assistive* suggestion ("this reads like analysis"), so it
only needs to be trustworthy when it's *confident* — high precision on high-confidence
predictions matters more than raw accuracy. If the macro-F1 bar is missed but the confidence
bar is met, the model is still deployable as a confidence-gated helper, and I'll say so.

---

## 7. AI Tool Plan

There is no application code to generate here, so AI tools are used at three specific points.
An explicit decision is recorded for each, and all AI use is disclosed in the README's AI
usage section.

1. **Label stress-testing — WILL DO, before annotating.** I give Claude the §2 definitions and
   §3 edge cases and ask it to generate 8–10 posts that deliberately sit *between* two labels.
   If I can't classify them cleanly with my rules, the definitions are too loose and I tighten
   them *now*. Output of this exercise (the generated posts + any rule changes) is saved to
   `ai-artifacts/label-stress-test.md`. These synthetic posts are for boundary-testing only
   and are **never** added to the dataset.
2. **Annotation assistance — WILL DO, with disclosure and anti-anchoring control.** I'll use
   Groq `llama-3.3-70b-versatile` to *pre-label* batches, then human-review every single one
   (human label is ground truth). The `prelabeled` column records the model's guess so I can
   later report human↔model pre-label agreement and prove I didn't rubber-stamp. **Anchoring
   risk:** seeing the model's guess could bias me. Mitigation — I label a blind random 30
   (judgment first, model guess hidden) to measure my own consistency against the assisted
   batch. *(Override note: if anchoring looks severe in that blind set, I drop pre-labeling and
   annotate fully by hand.)*
3. **Failure analysis — WILL DO, after evaluation.** I feed the list of test-set misclassifications
   (text, true label, predicted label, confidence) to an AI tool and ask it to name *systematic*
   patterns — e.g., "misreads sarcasm as hot_take," "can't tell hot_take from reaction when the
   post is < 15 words," "treats any named album as analysis." **Verification:** I don't take the
   pattern on faith — I re-read every example it cites, then check the pattern holds on a held-out
   slice of errors before it goes in the report. Unverified patterns are excluded.

---

## Milestone checklist

- [x] **M1** — Community + label taxonomy
- [x] **M2** — This spec (6 questions + AI Tool Plan)
- [ ] **M3** — Collect + annotate ≥200 examples; stratified split; document distribution + 3 hardest cases
- [ ] **M4** — Fine-tune `distilbert-base-uncased` (Colab T4); document a key hyperparameter decision
- [ ] **M5** — Groq `llama-3.3-70b-versatile` zero-shot baseline on the same test set
- [ ] **M6** — Evaluation report: accuracy + per-class metrics, confusion matrix, 3 error analyses, learned-vs-intended reflection

*Update this spec before starting any stretch feature (inter-annotator reliability, confidence
calibration, deeper error-pattern analysis, deployed interface).*

---

## 8. Stretch features (attempted)

Updated before starting each, per the rubric.

### A. Error-pattern analysis — DONE
Plan: go beyond listing errors to a systematic pattern. Result (in README): the fine-tuned
model collapses entirely into `analysis`, and — verified against the data — there is a **length
confound** (analysis ≈ 868 chars, hot_take ≈ 421, reaction ≈ 263), so the collapsed class is
also the longest. Used an AI tool to surface candidate patterns, verified with character-count
stats, and discarded an unsupported "sarcasm" hypothesis.

### B. Deployed interface — DONE (code committed)
Plan: a simple app that accepts a new post and shows predicted label + confidence. Built
`app.py` (Gradio UI + CLI) with two backends: `local` (loads a fine-tuned DistilBERT from
`./takemeter-model` and reports real softmax confidence) and `groq` (zero-shot
`llama-3.3-70b-versatile`, the better-performing classifier). Run instructions in README.
Decision: support both backends because our fine-tuned model collapsed, so the Groq backend is
the one that actually classifies usefully — but the local backend is included to satisfy the
"run it through *your* fine-tuned classifier with confidence" intent once a working model exists.

### C. Inter-annotator reliability — PARTIAL (AI proxy done; human scaffold provided)
Plan: a second independent annotator on 30+ examples + Cohen's κ + disagreement analysis.
What I could complete now: a real κ between **two independent annotators** — my (Claude) pre-labels
vs. the Groq zero-shot model — on all 33 test examples: **κ = 0.864 ("almost perfect")**,
observed agreement 0.909. Honest caveat: both annotators are AI, so this does **not** satisfy
the rubric's "another person" requirement; it's a reliability proxy. A human-annotation
worksheet (`data/review_sheet.csv`) and a κ script (`scripts/kappa.py`) are provided so a human
can label 30+ and compute κ the same way. Disagreements concentrate on the `hot_take`↔`reaction`
boundary (the 2 hot_take→reaction off-diagonal cells), matching the baseline's error pattern.

### D. Confidence calibration — SCAFFOLD ONLY (not completable now)
Plan: check whether higher-confidence predictions are right more often (reliability diagram /
binned accuracy). Blocked because (1) it needs the fine-tuned model's per-example softmax
probabilities, which require re-running Colab and exporting them, and (2) the collapsed model
emits near-constant confidence (~0.34–0.40), so calibration would be degenerate and
uninformative. A ready Colab cell to produce the reliability table is in
`notebook/finetuning_m5.md`; this becomes meaningful only after the model actually learns.
