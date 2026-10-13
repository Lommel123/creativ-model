"""Startet scripts/judge_server.py als separaten Prozess (ohne Unsloth) und spricht per JSON-Zeilen mit ihm."""
import atexit
import json
import os
import subprocess
import sys
from pathlib import Path

JUDGE_PROMPT = """Problem: {q}

Vorgeschlagene Idee: {idea}

Bewerte NUR, ob diese Idee das Problem tatsächlich lösen kann und realistisch umsetzbar, sicher und legal ist.
Originalität spielt keine Rolle. Vage Floskeln ohne konkrete Umsetzung bekommen höchstens 3.
Antworte ausschließlich mit einer ganzen Zahl von 0 bis 10."""


class Judge:
    def __init__(self, model_name, gpu):
        script = Path(__file__).with_name("judge_server.py")
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), TOKENIZERS_PARALLELISM="false")
        self.p = subprocess.Popen(
            [sys.executable, str(script), model_name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env,
        )
        atexit.register(self.close)
        if not self._read().get("ready"):
            raise RuntimeError("Judge-Prozess nicht bereit")

    def _read(self):
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError(f"Judge-Prozess beendet (Exit-Code {self.p.poll()}) – Fehlermeldung steht im Log darüber")
        msg = json.loads(line)
        if "error" in msg:
            raise RuntimeError("Judge: " + msg["error"])
        return msg

    def raw(self, prompts):
        """Liste fertiger Nutzernachrichten -> Liste ganzer Zahlen 0..10 (None = unlesbare Judge-Antwort)."""
        self.p.stdin.write(json.dumps({"prompts": prompts}, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        return self._read()["scores"]

    def validity(self, questions, ideas):
        """Funktionsfähigkeit 0..1 für (Problem, Idee)-Paare."""
        prompts = [JUDGE_PROMPT.format(q=q, idea=d[:1200]) for q, d in zip(questions, ideas)]
        return [s / 10 if s is not None else 0.0 for s in self.raw(prompts)]   # Training: unlesbar = 0 wie bisher

    def close(self):
        if self.p.poll() is None:
            try:
                self.p.stdin.close()
                self.p.wait(timeout=10)
            except Exception:
                self.p.kill()
