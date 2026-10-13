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
def score(prompts, bs=8):
    out = []
    for i in range(0, len(prompts), bs):
        enc = tok([chat(p) for p in prompts[i:i + bs]], return_tensors="pt", padding=True).to(model.device)
        gen = model.generate(**enc, max_new_tokens=4, do_sample=False, pad_token_id=tok.pad_token_id)
        for g in gen[:, enc.input_ids.shape[1]:]:
            m = re.search(r"\d+", tok.decode(g, skip_special_tokens=True))
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
            send({"scores": score(req["prompts"])})
        except Exception as e:  # Fehler melden statt still zu sterben
            send({"error": f"{type(e).__name__}: {e}"})
except (KeyboardInterrupt, BrokenPipeError):
    pass  # normales Beenden durch den Hauptprozess
