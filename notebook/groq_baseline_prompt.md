# Groq zero-shot baseline prompt (Milestone 4)

Paste the block below into the `SYSTEM_PROMPT = """..."""` cell (id `0abd6018`) of
`ai201_project3_takemeter_starter_clean.ipynb`. Model: `llama-3.3-70b-versatile`, temp 0.

The notebook's parser matches the model output against the label strings with
`label in raw` and does **not** normalize spacing — so the model MUST emit `hot_take`
with an underscore. The last lines of the prompt enforce that.

## SYSTEM_PROMPT (copy verbatim)

```text
You are classifying comments and posts from r/LetsTalkMusic, a subreddit for in-depth music
discussion. Assign each one to exactly one category based on HOW it supports its point.

analysis: a structured argument about the music backed by specific, verifiable evidence
(production/harmony/rhythm detail, historical or contextual fact, or named song/artist
examples); the reasoning would stand even if the opinion framing were removed.
Example: "Shoegaze isn't just a 'wall of noise' — My Bloody Valentine's Loveless uses the
glide-guitar technique, detuning mid-chord with the tremolo arm, which is what creates that
seasick pitch-bend. It's harmonically deliberate, not just distortion."

hot_take: a bold, confident evaluative claim asserted without genuine support; it may sound
credible but does not actually reason.
Example: "Radiohead is the most overrated band of all time; people only like OK Computer to
seem smart."

reaction: an immediate emotional or personal response — a feeling or a memory — that makes no
claim about the music's quality.
Example: "First time hearing Carrie & Lowell and I'm literally sobbing, I don't have words."

Decision rules for hard cases:
- If a fact is cited but it is vague, cherry-picked, or decorative (there to sound credible
  while delivering a put-down), choose hot_take. Choose analysis only if it genuinely reasons.
- An unsupported judgment about quality (e.g. "worst album ever") is hot_take. A pure feeling
  or personal experience with no quality claim is reaction.
- If a musical detail only serves a feeling, choose reaction; if a feeling decorates a real
  argument, choose analysis.
- When in doubt, prefer the lower-evidence label: reaction < hot_take < analysis.

Respond with ONLY the label name, exactly as written here, using the underscore in hot_take:
analysis, hot_take, or reaction. Do not explain.

Valid labels:
analysis
hot_take
reaction
```

## Optional: save the baseline numbers (add a cell after the baseline metrics cell)

The notebook only writes `evaluation_results.json` in Section 6 (after fine-tuning). To keep
the M4 baseline numbers on their own, run this once after the baseline metrics cell:

```python
import json
from sklearn.metrics import classification_report
json.dump(
    {"model": "llama-3.3-70b-versatile",
     "accuracy": bl_accuracy,
     "parseable": len(valid), "total": len(test_df),
     "report": classification_report(bl_true_ids, bl_pred_ids,
                target_names=[ID_TO_LABEL[i] for i in range(NUM_LABELS)],
                zero_division=0, output_dict=True)},
    open("baseline_results.json", "w"), indent=2)
print("saved baseline_results.json")
```

Download it from the Files panel and commit it so the M6 report can cite it.

## Hypotheses to write down (test after fine-tuning)
- `analysis` vs `hot_take` will be the biggest confusion — the decorative-evidence boundary is
  subtle; a zero-shot model probably over-labels confident-but-thin takes as `analysis`.
- Terse `hot_take`s may be read as `reaction` when no explicit quality word is present.
- Long comments may get over-labeled `analysis` because length reads as rigor.
