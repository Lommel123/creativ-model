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
| 2 Selbst erfinden | `02_grpo.ipynb` (Input: `adapter_sft` **oder** vorheriger Stufe-2-Lauf → setzt am neuesten Checkpoint fort) | `data/grpo_prompts.jsonl` (nur Fragen) | Reinforcement Learning: Belohnung für originell **und** funktionsfähig | 1 Session ≤10,5 h, Ziel 200 Schritte |
| 3 Transfer-Test | `03_eval.ipynb` | `eval/` | Basis vs. trainiert auf allgemeinen und Business-Fragen, GGUF-Export | ~1–2 h |

## Stufe 2 in einer Session
Mit 14B auf T4 x2 ist die Textgenerierung ~75 % der Schrittzeit. Ziel: **200 Schritte in einer ~11-h-Session**.

| Hebel | Entscheidung | Grund |
|---|---|---|
| Generierungs-Batch 8 → 16 | ✅ | T4-Generierung ist speichergebunden: doppelter Batch kostet kaum mehr Zeit pro Token. Bei OOM automatisch zurück auf 8 |
| Längenstrafe ab 230 Wörtern | ✅ | ≈ 440 Tokens. Vorher lag sie über dem 512-Token-Limit und griff nie |
| max_steps 1000 → 200 | ✅ | Passt in eine Session, bei GRPO mit LoRA kommt der Großteil des Effekts früh |
| num_generations 4 → 2 | ❌ | GRPO vergleicht innerhalb der Gruppe, mit 2 wird das Lernsignal sehr verrauscht |
| max_completion_length kürzen | ❌ | Median der Trainingsantworten 429 Tokens: 448 schneidet 38 %, 384 schneidet 78 % ab |
| vLLM / fast_inference | ❌ | Für 14B auf T4 nicht belegt, Zusatzinstallation gefährdet den ganzen Lauf |
| 8B statt 14B | Fallback | ~1,7× schneller, braucht aber neues SFT und denkt schlechter |

Fortsetzen: Output eines Stufe-2-Laufs als Input → setzt am neuesten Checkpoint fort (bis `max_steps`).

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
