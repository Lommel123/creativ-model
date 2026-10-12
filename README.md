# Querdenk-Modell

Ziel: einem Open-Source-LLM **die Methode** des Out-of-the-Box-Denkens beibringen, sodass es in beliebigen Bereichen selbst originelle, funktionierende Ideen erfindet, z. B. Geschäftsideen.

**Kernprinzip:** Das Modell lernt den *Weg*, nicht fertige Antworten. Business kommt im Training **nie** vor, nur im Test. Wird es dort trotzdem origineller, hat es Querdenken gelernt und nicht auswendig.

- Basismodell: `Qwen3-14B` (4-bit, Unsloth). Bei Speicherproblemen in `config.yaml` auf 8B wechseln.
- Training: Kaggle, GPU T4 x2

## Schnellstart: Nachtlauf
`notebooks/00_komplett.ipynb`: Stufe 1 + 2 in einem Lauf, nutzt ~11,5 h und stoppt sauber vor Kaggles 12-h-Limit. Zum Weitertrainieren den Output als Input hinzufügen, dann setzt der nächste Lauf automatisch fort.

## Pipeline (einzeln)

| Stufe | Notebook | Daten | Was passiert | Dauer (T4) |
|---|---|---|---|---|
| 1 Prozess lernen | `01_sft.ipynb` | `data/sft.jsonl` + `sft_val.jsonl` | Denkprozess imitieren, Prüfset gegen Auswendiglernen | ~1,5–2,5 h |
| 2 Selbst erfinden | `02_grpo.ipynb` (Input: `adapter_sft` **oder** vorheriger Stufe-2-Lauf → setzt am neuesten Checkpoint fort) | `data/grpo_prompts.jsonl` (nur Fragen) | Reinforcement Learning: Belohnung für originell **und** funktionsfähig | 2 Sessions à ≤10,5 h, Ziel 360 Schritte |
| 3 Transfer-Test | `03_eval.ipynb` | `eval/` | Basis vs. trainiert auf allgemeinen und Business-Fragen, GGUF-Export | ~1–2 h |

## Stufe 2 in zwei Sessions (Plan)
Mit 14B auf T4 x2 dauert ein GRPO-Schritt ~3 min (fast nur Textgenerierung, 8 Antworten à bis 512 Tokens). Ziel daher **360 Schritte** statt 1.000:

| Session | Input | Erwartung |
|---|---|---|
| `creativ-02-grpo` V1 | `notebook54c7b85763` (adapter_sft) | ~180 Schritte, stoppt am Zeitlimit, speichert Checkpoint |
| Fortsetzung | Output von `creativ-02-grpo` V1 | setzt am neuesten Checkpoint fort bis 360 (mit 16er-Generierungs-Batch voraussichtlich schneller) |
| `03_eval` | Output der Fortsetzung | Transfer-Test + GGUF, ~1,5–2 h |

Beschleunigung ab der Fortsetzung: 16 Antworten in einem Generierungs-Batch (`steps_per_generation: 4`, bei OOM automatisch 8), Längenstrafe ab 280 Wörtern (vorher wirkungslos), abgeschnittene Antworten zählen nicht in den Loss.

## Der Denkprozess (Antwortformat)
```
Annahmen: 1) … 2) … 3) …
Werkzeug – <Name>: <Anwendung> → Rohidee: …   (3–4×)
Aussortiert: <was zu naheliegend/unbrauchbar ist und warum>
Beste Idee: <ausgearbeitet, warum es funktioniert, ehrlicher Haken>
```
Werkzeuge: Umkehrung · Fremde Domäne · Einschränkung weglassen · Einschränkung hinzufügen · Perspektivwechsel · Kombination · Skalierung · Zweckentfremdung · Zeitverschiebung

## Belohnung in Stufe 2
Der Judge läuft als **eigener Prozess ohne Unsloth** (`scripts/judge_server.py`, GPU 1). Unsloth patcht Qwen3 global; ein Judge im selben Prozess crasht bei der Generierung (`'Qwen3ForCausalLM' object has no attribute 'max_seq_length'`, Lauf V1).

- **creative_valid:** Gültigkeit (Judge-Modell auf GPU 1) × Originalität (Abstand zur naheliegenden Lösung). Ohne Gültigkeit gibt es keine Punkte.
- **diversity:** anders als die übrigen Ideen derselben Runde
- **format** und **length:** Denkprozess einhalten, nicht ausufern

## Daten
| Datei | Inhalt |
|---|---|
| `data/sft.jsonl` / `sft_val.jsonl` | 1.267 / 139 Denkspuren ohne Business, 5 Fähigkeiten: **Probleme lösen** (11 Themenfelder) · **Ideen-Evolution** (Mutation, Rekombination, Transfer) · **Probleme finden** · **Ideen zerlegen & verbessern** · **Frage umdeuten** |
| `data/grpo_prompts.jsonl` | 922 Fragen aus allen 5 Fähigkeiten + Referenz (naheliegende Lösung bzw. Ausgangsidee), von der sich die neue Idee entfernen soll |
| `eval/eval_prompts.jsonl` | 15 allgemeine + 10 Business-Testfragen |
| `eval/business_holdout.jsonl` | 525 Business-Fragen, nur für Tests |
| `eval/business_evolution.jsonl` | 20 bestehende Geschäftsmodelle → neue entwickeln, nur für Tests |

Prüfen: `python scripts/validate_data.py`

## Kaggle-Ablauf
1. Notebook importieren (File → Import Notebook), **GPU T4 x2**, **Internet an**
2. Lange Läufe über **Save Version → Save & Run All (Commit)**: Sie laufen im Hintergrund, der Browser darf zu sein, und die Ergebnisse landen automatisch im Output.
3. Für Stufe 2 und 3: Output der vorherigen Stufe über **Add Input → Your Work** einbinden.
