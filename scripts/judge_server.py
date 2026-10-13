"""Judge-Prozess: bewertet Ideen auf Funktionsfähigkeit (0–10).

Läuft bewusst in einem EIGENEN Python-Prozess ohne Unsloth. Unsloth patcht beim Import
die Qwen3-Klassen global; ein im selben Prozess per transformers geladenes Judge-Modell
crasht dann bei .generate() ("'Qwen3ForCausalLM' object has no attribute 'max_seq_length'").

Protokoll (eine JSON-Zeile pro Nachricht):
  stdin : {"prompts": ["<Nutzernachricht>", ...]}
  stdout: {"scores": [0..10, ...]}
Beim Start wird {"ready": true} gesendet. Alle Logs gehen nach stderr.
"""
import json
import re
import sys

OUT = sys.stdout
sys.stdout = sys.stderr  # nichts außer Protokollzeilen auf stdout

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

model_name = sys.argv[1]
tok = AutoTokenizer.from_pretrained(model_name)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
DEV = {"": 0} if torch.cuda.is_available() else {"": "cpu"}
DT = torch.float16 if torch.cuda.is_available() else torch.float32
try:
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map=DEV, dtype=DT)
except TypeError:
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map=DEV, torch_dtype=DT)
model.eval()


def chat(text):
    msgs = [{"role": "user", "content": text}]
    try:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


@torch.no_grad()
def generate(prompts, max_new_tokens, bs):
    out = []
    for i in range(0, len(prompts), bs):
        enc = tok([chat(p) for p in prompts[i:i + bs]], return_tensors="pt", padding=True).to(model.device)
        gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        out += [tok.decode(g, skip_special_tokens=True).strip() for g in gen[:, enc.input_ids.shape[1]:]]
    return out


def score(prompts, bs=8):
    out = []
    for t in generate(prompts, 4, bs):
        m = re.search(r"\d+", t)
        out.append(min(10, int(m.group())) if m else None)   # None = unlesbar
    return out


def send(obj):
    OUT.write(json.dumps(obj) + "\n")
    OUT.flush()


send({"ready": True})
try:
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        try:
            if req.get("mode") == "text":   # freie Textantworten (Zusammenfassung, A/B-Urteil)
                send({"texts": generate(req["prompts"], int(req.get("max_new_tokens", 64)), int(req.get("bs", 8)))})
            else:
                send({"scores": score(req["prompts"])})
        except Exception as e:  # Fehler melden statt still zu sterben
            send({"error": f"{type(e).__name__}: {e}"})
except (KeyboardInterrupt, BrokenPipeError):
    pass  # normales Beenden durch den Hauptprozess
