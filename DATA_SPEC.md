# Daten-Spezifikation (für Claude Code)

Ziel: 2.000–5.000 SFT-Beispiele und 1.000–3.000 DPO-Paare. Sprache: überwiegend Deutsch, ~20 % Englisch.

## Aufgabentypen (Mischung)

| Typ | Anteil | Beispiel |
|---|---|---|
| Alternative Uses | 15 % | „Wofür kann man eine leere Konservendose noch nutzen?“ |
| Constraint-Bruch | 25 % | „Wie liefert man Pakete ohne Fahrzeuge aus?“ |
| Echtes Problem (Business/Technik/Alltag) | 30 % | „Kunden brechen im Checkout ab – Ursachen und Ideen?“ |
| Analogietransfer | 15 % | „Was kann ein Krankenhaus von einem Formel-1-Boxenstopp lernen?“ |
| Laterales Rätsel (prüfbar) | 15 % | Rätsel mit eindeutiger Lösung |

## SFT-Antwortstruktur (immer gleich)

```
Naheliegend: <1–2 Sätze, was jeder sagen würde>
Perspektivwechsel: <welche Annahme wird gebrochen / welche Domäne wird übertragen>
Unkonventionelle Lösung: <konkret, umsetzbar, mit 1 Satz warum es funktioniert>
```

## DPO-Paare

- `chosen`: unkonventionell **und** funktionsfähig, konkret
- `rejected`, gemischt:
  - 50 % konventionell und brav (die naheliegende Lösung, ausführlich)
  - 30 % kreativ, aber unbrauchbar (physikalisch/ökonomisch Unsinn, vage)
  - 20 % generische Kreativitätsfloskeln ohne Inhalt

## Qualitätsregeln

- Keine Duplikate (Prompt-Ähnlichkeit < 0.9 Kosinus, prüft `validate_data.py`)
- Antwort `chosen` max. ~250 Wörter
- Rätsel: Lösung muss eindeutig sein
- Keine Eval-Prompts aus `eval/eval_prompts.jsonl` in die Trainingsdaten übernehmen
