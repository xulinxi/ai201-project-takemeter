#!/usr/bin/env python3
"""
TakeMeter — deployed interface (stretch feature).

Accepts a post/comment and shows the predicted label (analysis / hot_take / reaction)
and a confidence score. Two backends:

  local : a fine-tuned DistilBERT saved at ./takemeter-model (download it from Colab after
          Section 3, or train+save with `trainer.save_model("takemeter-model")`).
          Confidence = softmax probability of the predicted class (genuine model confidence).
  groq  : zero-shot llama-3.3-70b-versatile via the Groq API (needs GROQ_API_KEY). This is
          the better-performing classifier in our evaluation; confidence comes from token
          logprobs when available, else shown as "n/a".

Usage:
  python app.py --ui                       # launch the Gradio web UI (default backend: auto)
  python app.py "your post text here"      # one-off CLI classification
  python app.py --backend groq "text"      # force a backend
  python app.py --backend local "text"

Backend "auto" picks local if ./takemeter-model exists, else groq.
"""
import argparse
import os
import sys

LABELS = ["analysis", "hot_take", "reaction"]
DEFS = {
    "analysis": "structured argument backed by specific, verifiable evidence",
    "hot_take": "confident evaluative claim asserted without genuine support",
    "reaction": "emotional/personal response with no claim about quality",
}
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "takemeter-model")

SYSTEM_PROMPT = """You are classifying comments from r/LetsTalkMusic by HOW they support their point.
analysis: a structured argument backed by specific, verifiable evidence (production/harmony/rhythm detail, historical fact, named examples); reasoning stands without the opinion framing.
hot_take: a bold, confident evaluative claim asserted without genuine support.
reaction: an immediate emotional or personal response (a feeling or memory) with no claim about the music's quality.
Rules: cited-but-decorative evidence -> hot_take; unsupported quality judgment -> hot_take; feeling that only name-drops a detail -> reaction; when unsure prefer the lower-evidence label (reaction < hot_take < analysis).
Respond with ONLY one label, exactly: analysis, hot_take, or reaction."""


# ---------- local fine-tuned backend ----------
_local = {}


def _load_local():
    if _local:
        return _local
    if not os.path.isdir(MODEL_DIR):
        raise FileNotFoundError(
            f"No fine-tuned model at {MODEL_DIR}. Download it from Colab "
            "(Files panel → takemeter-model) or use --backend groq."
        )
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    _local.update(tok=tok, model=model, torch=torch)
    return _local


def classify_local(text):
    m = _load_local()
    torch = m["torch"]
    inputs = m["tok"](text, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        logits = m["model"](**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0].tolist()
    # respect the model's own id2label if present
    id2label = getattr(m["model"].config, "id2label", None)
    order = [id2label[i] for i in range(len(probs))] if id2label else LABELS
    scores = dict(zip(order, probs))
    pred = max(scores, key=scores.get)
    return pred, scores[pred], scores


# ---------- groq zero-shot backend ----------
# llama-3.3-70b on Groq does not support logprobs, so confidence is estimated by
# self-consistency: sample the model GROQ_VOTES times and use the agreement rate.
GROQ_VOTES = int(os.environ.get("GROQ_VOTES", "5"))


def _groq_label(client, text, temperature):
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": text}],
        temperature=temperature, max_tokens=5,
    )
    raw = r.choices[0].message.content.strip().lower().replace("-", "_").replace(" ", "_")
    return next((l for l in sorted(LABELS, key=len, reverse=True)
                 if l == raw or l in raw), "analysis")


def classify_groq(text):
    from collections import Counter
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise EnvironmentError("Set GROQ_API_KEY in your environment to use the groq backend.")
    client = Groq(api_key=key)
    k = max(1, GROQ_VOTES)
    # k=1 -> deterministic single call; k>1 -> sample for a self-consistency confidence
    votes = Counter(_groq_label(client, text, 0.0 if k == 1 else 0.7) for _ in range(k))
    total = sum(votes.values())
    scores = {lab: votes[lab] / total for lab in votes}
    pred = votes.most_common(1)[0][0]
    return pred, scores[pred], scores


def classify(text, backend="auto"):
    if backend == "auto":
        backend = "local" if os.path.isdir(MODEL_DIR) else "groq"
    return (classify_local if backend == "local" else classify_groq)(text), backend


# ---------- interfaces ----------
def run_cli(text, backend):
    (pred, conf, scores), used = classify(text, backend)
    conf_s = f"{conf:.2f}" if conf is not None else "n/a"
    print(f"\nBackend: {used}")
    print(f"Prediction: {pred}  ({DEFS[pred]})")
    print(f"Confidence: {conf_s}")
    if len(scores) > 1:
        print("All scores:")
        for k, v in sorted(scores.items(), key=lambda x: -(x[1] or 0)):
            print(f"  {k:9s} {v:.3f}" if v is not None else f"  {k:9s}   n/a")


def run_ui(backend):
    import gradio as gr

    def predict(text):
        if not text.strip():
            return {}, "Enter a post above."
        (pred, conf, scores), used = classify(text, backend)
        label_conf = {k: float(v) for k, v in scores.items() if v is not None}
        if not label_conf:  # groq without logprobs
            label_conf = {pred: 1.0}
        note = f"**{pred}** — {DEFS[pred]}  \n(backend: {used}" + (
            f", confidence {conf:.2f})" if conf is not None else ", confidence n/a)")
        return label_conf, note

    demo = gr.Interface(
        fn=predict,
        inputs=gr.Textbox(lines=6, label="Paste a r/LetsTalkMusic post or comment"),
        outputs=[gr.Label(num_top_classes=3, label="Predicted label + confidence"),
                 gr.Markdown()],
        title="TakeMeter",
        description="Classifies music-discussion text as analysis, hot_take, or reaction.",
        examples=[
            ["MBV's Loveless uses the glide-guitar technique — detuning mid-chord with the "
             "tremolo arm — which is what creates that seasick pitch-bend. It's deliberate."],
            ["Radiohead is the most overrated band ever, people only like them to seem smart."],
            ["First time hearing Carrie & Lowell and I'm literally sobbing, I have no words."],
        ],
    )
    demo.launch()


def main():
    ap = argparse.ArgumentParser(description="TakeMeter classifier interface")
    ap.add_argument("text", nargs="?", help="text to classify (CLI mode)")
    ap.add_argument("--ui", action="store_true", help="launch the Gradio web UI")
    ap.add_argument("--backend", choices=["auto", "local", "groq"], default="auto")
    args = ap.parse_args()
    if args.ui:
        run_ui(args.backend)
    elif args.text:
        run_cli(args.text, args.backend)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
