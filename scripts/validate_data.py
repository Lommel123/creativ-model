"""Prüft Trainings-, Prüf- und GRPO-Daten: Denkprozess-Format, Duplikate, Business-Freiheit, keine Test-Lecks."""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
BIZ = re.compile(r"(geschäftsidee|business idea|startup|start-up|umsatz|revenue)", re.I)


def load(p):
    rows = []
    for i, line in enumerate(open(p, encoding="utf-8"), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(f"{p.name}:{i} kein gültiges JSON ({e})")
    return rows


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def check_trace(name, i, ans):
    lines = ans.split("\n")
    tools = [l for l in lines if l.startswith("Werkzeug – ") and "→ Rohidee:" in l]
    if sum(l.startswith("Annahmen:") for l in lines) != 1:
        errors.append(f"{name}:{i} braucht genau eine 'Annahmen:'-Zeile")
    if not 3 <= len(tools) <= 4:
        errors.append(f"{name}:{i} braucht 3–4 Werkzeug-Zeilen mit '→ Rohidee:'")
    for key in ("Aussortiert:", "Beste Idee:"):
        if sum(l.startswith(key) for l in lines) != 1:
            errors.append(f"{name}:{i} braucht genau eine '{key}'-Zeile")


tests = {norm(r["prompt"]) for f in ("eval/eval_prompts.jsonl", "eval/business_holdout.jsonl") for r in load(ROOT / f)}
seen = set()
counts = {}
for fname in ("data/sft.jsonl", "data/sft_val.jsonl"):
    rows = load(ROOT / fname)
    counts[fname] = len(rows)
    for i, r in enumerate(rows, 1):
        m = r.get("messages", [])
        if len(m) != 2 or m[0]["role"] != "user" or m[1]["role"] != "assistant":
            errors.append(f"{fname}:{i} braucht genau user + assistant")
            continue
        q = norm(m[0]["content"])
        check_trace(fname, i, m[1]["content"])
        if q in seen:
            errors.append(f"{fname}:{i} Duplikat")
        if q in tests:
            errors.append(f"{fname}:{i} ist eine Testfrage (Leck)")
        if BIZ.search(m[0]["content"]):
            errors.append(f"{fname}:{i} enthält Business – gehört nur in den Test")
        seen.add(q)

grpo = load(ROOT / "data/grpo_prompts.jsonl")
counts["data/grpo_prompts.jsonl"] = len(grpo)
for i, r in enumerate(grpo, 1):
    if not r.get("prompt"):
        errors.append(f"grpo:{i} prompt fehlt")
    elif norm(r["prompt"]) in tests:
        errors.append(f"grpo:{i} ist eine Testfrage (Leck)")

print(" | ".join(f"{k.split('/')[-1]}: {v}" for k, v in counts.items()), f"| Testfragen: {len(tests)}")
if errors:
    print("\n".join(errors[:50]))
    sys.exit(1)
print("OK")
