# TakeMeter — Demo Script (~4 min, read off-camera)

`[SHOW: ...]` = what to have on screen. Read the plain text aloud at a normal pace.
Total target: 3–5 minutes. Each section is timed.

---

## 0:00 — Intro (~25s)
`[SHOW: README top — title + status line]`

"Hi, this is my walkthrough of TakeMeter, a text classifier for the r/LetsTalkMusic
subreddit. The goal is to score *how* a comment supports its point: `analysis` — a real
argument backed by evidence; `hot_take` — a confident claim with no support; or `reaction` —
a personal, emotional response. I collected 219 real comments, labeled them, fine-tuned
DistilBERT, and compared it against a zero-shot Groq baseline. Here's what happened."

---

## 0:25 — Sample classifications, label + confidence (~60s)
`[SHOW: Colab — run the sample-classifications cell from notebook/finetuning_m5.md so 5 posts
print with predicted label + confidence]`

"Here are five test posts run through my fine-tuned model. Each prints the true label, the
model's prediction, and its confidence. And right away you can see the headline result —
the model predicts `analysis` for every single post, with confidence hovering around 0.35,
which is basically chance for a three-class problem. So before I even open the metrics, the
model's behavior is telling me it didn't learn the distinction."

---

## 1:25 — One correct prediction (~40s)
`[SHOW: the row where true = analysis, predicted = analysis (row 5 in the README table)]`

"This one is technically correct: it's a long, evidence-backed comment arguing that an
album's track count doesn't determine its identity — a genuine `analysis` post — and the
model said `analysis`. But it's right for the wrong reason. The model isn't recognizing the
argument; it labels *everything* `analysis`. The only hint of a real signal is that its
confidence here, around 0.40, is slightly higher than on the others — and that lines up with
a data issue I'll show in a second."

---

## 2:05 — One incorrect prediction (~40s)
`[SHOW: the row where true = reaction — "The thunderbolt I experienced the first time I
listened to The Wall… I was 11…"]`

"And here's a clear failure. This post — 'the thunderbolt I experienced the first time I
listened to The Wall, I was eleven' — is pure personal memory. There's no argument and no
quality claim, so it's a textbook `reaction`. The model called it `analysis`. It went wrong
because it never built a decision boundary for `reaction` or `hot_take` at all — it collapsed
onto the single biggest class."

---

## 2:45 — Evaluation report walkthrough (~70s)
`[SHOW: README — Overall accuracy table, then per-class, then the fine-tuned confusion matrix]`

"Here's the evaluation. Both models were scored on the same locked 33-example test set. The
Groq zero-shot baseline got 90.9% accuracy with strong per-class F1 across all three labels.
My fine-tuned DistilBERT got 36.4% — which exactly equals the majority-class floor. The
confusion matrix makes it visual: every true `hot_take` and every true `reaction` got
predicted as `analysis`. Total collapse."

`[SHOW: README — Error-pattern analysis section, the length numbers]`

"Digging into why: I used an AI tool to find patterns in the errors, then verified them
myself. The real finding is a length confound — my `analysis` examples average 868
characters, `hot_take` 421, and `reaction` only 263. So the class the model collapsed onto is
also the longest class, and length was leaking label information. I also checked the training
log: validation accuracy was frozen at chance for all 30 epochs and the loss never dropped
below the random-guess value, so the model never even fit the training data."

---

## 3:55 — Reflection + close (~35s)
`[SHOW: README — What the model learned vs intended]`

"So the gap between what I intended and what I got is the whole lesson. I wanted the model to
learn a reasoning-versus-asserting-versus-feeling axis. Instead, 153 training examples were
far too few for a small model to learn something that subtle — a 70-billion-parameter model
already knows it zero-shot, but DistilBERT couldn't. To fix it I'd human-review my labels,
balance text length across classes, add more examples, and use corrected hyperparameters.
An honest failure that's fully diagnosed — thanks for watching."

---

### Recording tips
- Have two windows ready: the Colab notebook (for the sample-classifications cell) and the
  README rendered on GitHub (for the tables). Alt-tab between them on the cues.
- If you re-ran the fixed training and it now learns, swap the numbers in sections 2:45–3:55
  and narrate the improvement instead of the collapse.
- Keep it under 5:00. If you're long, trim the intro and the recording-tips aren't spoken.
