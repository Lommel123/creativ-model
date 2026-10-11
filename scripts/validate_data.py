"""Prüft sft.jsonl, dpo.jsonl: Format, Struktur, Duplikate, Überschneidung mit Eval."""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []

def load(p):
    rows = []
    for i, line in enumerate(open(p, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"{p.name}:{i} kein gültiges JSON ({e})")
    return rows

def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()

sft = load(ROOT / "data/sft.jsonl")
dpo = load(ROOT / "data/dpo.jsonl")
ev = load(ROOT / "eval/eval_prompts.jsonl")
eval_prompts = {norm(e["prompt"]) for e in ev}

seen = set()
for i, r in enumerate(sft, 1):
    m = r.get("messages", [])
    if len(m) != 2 or m[0]["role"] != "user" or m[1]["role"] != "assistant":
        errors.append(f"sft:{i} braucht genau user + assistant")
        continue
    ans = m[1]["content"]
    for key in ("Naheliegend:", "Perspektivwechsel:", "Unkonventionelle Lösung:"):
        if key not in ans:
            errors.append(f"sft:{i} fehlt '{key}'")
    q = norm(m[0]["content"])
    if q in seen:
        errors.append(f"sft:{i} Duplikat")
    if q in eval_prompts:
        errors.append(f"sft:{i} ist ein Eval-Prompt (Leak)")
    seen.add(q)

seen = set()
for i, r in enumerate(dpo, 1):
    if not all(k in r and r[k].strip() for k in ("prompt", "chosen", "rejected")):
        errors.append(f"dpo:{i} prompt/chosen/rejected fehlt")
        continue
    if norm(r["chosen"]) == norm(r["rejected"]):
        errors.append(f"dpo:{i} chosen == rejected")
    if len(r["chosen"].split()) > 250:
        errors.append(f"dpo:{i} chosen > 250 Wörter")
    q = norm(r["prompt"])
    if q in seen:
        errors.append(f"dpo:{i} Duplikat")
    if q in eval_prompts:
        errors.append(f"dpo:{i} ist ein Eval-Prompt (Leak)")
    seen.add(q)

print(f"SFT: {len(sft)} | DPO: {len(dpo)} | Eval: {len(ev)}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("OK")
