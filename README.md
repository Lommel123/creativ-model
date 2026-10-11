# Querdenk-Modell

Ziel: einem Open-Source-LLM echtes Out-of-the-Box-Denken antrainieren. Das Modell soll **originell und trotzdem brauchbar** antworten.

- Basismodell: `Qwen3-8B` (4-bit, Unsloth). Gewechselt wird in `config.yaml`.
- Training: Kaggle (kostenlose GPU)
- Entwicklung und Daten: lokal / Claude Code
- Nutzung danach: lokal als GGUF (Ollama / LM Studio)

## Pipeline

| Stufe | Notebook | Daten | Zweck |
|---|---|---|---|
| 1 SFT | `notebooks/01_sft.ipynb` | `data/sft.jsonl` | Denkmuster lernen: naheliegend → Perspektivwechsel → unkonventionell |
| 2 DPO | `notebooks/02_dpo.ipynb` | `data/dpo.jsonl` | Kreativ-gültig bevorzugen statt konventionell oder kreativ-falsch |
| 3 Eval | `notebooks/03_eval.ipynb` | `eval/eval_prompts.jsonl` | Originalität ↑ bei gleicher Gültigkeit? |

## Datenformate

**sft.jsonl**
```json
{"messages": [{"role":"user","content":"..."},{"role":"assistant","content":"Naheliegend: ...\nPerspektivwechsel: ...\nUnkonventionelle Lösung: ..."}]}
```

**dpo.jsonl**
```json
{"prompt": "...", "chosen": "kreativ + funktioniert", "rejected": "konventionell ODER kreativ aber falsch"}
```

Seed-Daten liegen bei. Mehr Daten erzeugt Claude Code nach `DATA_SPEC.md`. Prüfen mit:
```bash
python scripts/validate_data.py
```

## Ablauf

1. Repo auf GitHub pushen (öffentlich oder privat, siehe unten).
2. Auf Kaggle ein neues Notebook anlegen: **Settings → Accelerator: GPU T4 x2**, **Internet: On**.
3. Inhalt von `notebooks/01_sft.ipynb` importieren (File → Import Notebook). In Zelle 1 `REPO_URL` setzen.
4. Laufen lassen. Der Adapter landet in `/kaggle/working/adapter_sft`. Über **Save Version** sichern.
5. `02_dpo.ipynb` lädt den SFT-Adapter als Kaggle-Input und trainiert weiter.
6. `03_eval.ipynb` vergleicht Basis- und trainiertes Modell und exportiert GGUF.

Private Repos: GitHub-Token als Kaggle-Secret `GITHUB_TOKEN` anlegen (Add-ons → Secrets). Die Notebooks nutzen es automatisch.

## Lokal (MacBook)

```bash
pip install -r requirements-mac.txt
python scripts/score_novelty.py --base eval/out_base.jsonl --tuned eval/out_tuned.jsonl
ollama create querdenker -f Modelfile   # nach GGUF-Export
```
