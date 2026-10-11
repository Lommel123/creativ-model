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

## Schwerpunkt Geschäftsideen (ab Runde 2)

Ziel des Modells: **originelle, tragfähige Geschäftsideen finden.** Zielmischung im Gesamtdatensatz: ~60 % Business, ~40 % allgemeines Querdenken (erhält das Denkmuster).

### Prompt-Typen Business
| Typ | Beispiel |
|---|---|
| Themenfeld | „Finde eine Geschäftsidee rund um Fahrradpendler.“ |
| Beobachtung/Problem | „Viele Vermieter hassen Wohnungsübergaben – steckt da ein Business drin?“ |
| Ressourcen-Constraint | „Ich habe 500 € und Wochenenden frei – was Ungewöhnliches?“ |
| Trend-Kombination | „Kombiniere Pflegenotstand und Sprachassistenten.“ |
| Bestehende Branche umdrehen | „Was wäre das Gegenteil von einem Fitnessstudio-Abo als Geschäftsmodell?“ |
| Asset nutzen | „Was kann ein Bauernhof mit leerstehender Scheune verdienen?“ |

### Antwortstruktur Business (gleiche Labels!)
```
Naheliegend: <die Idee, die jeder sofort hätte – oft schon zigfach existierend>
Perspektivwechsel: <gebrochene Annahme / übersehene Zielgruppe / Geld fließt anders / Domänentransfer>
Unkonventionelle Lösung: <Idee in 1–2 Sätzen>. Wer zahlt: <konkreter Kunde>. Warum es funktioniert: <Mechanismus>. Erster Test: <billiger Test in < 2 Wochen>.
```

### DPO Business
- `chosen`: originell + konkreter zahlender Kunde + plausibles Erlösmodell + billiger erster Test
- `rejected`: 40 % generisch (noch eine App, Dropshipping, „KI-Plattform für alles“, Online-Kurs), 30 % originell aber niemand zahlt / rechtlich oder ökonomisch unhaltbar, 30 % vage Buzzword-Idee ohne Kunde
