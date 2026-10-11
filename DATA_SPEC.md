# Daten-Spezifikation: Denkprozess-Spuren

Ziel: Ein LLM soll **die Methode** des Out-of-the-Box-Denkens lernen, damit es später in JEDEM Bereich (auch in solchen, die es nie gesehen hat, z. B. Geschäftsideen) selbst originelle, funktionierende Ideen erfindet. Es soll also NICHT Fachwissen oder fertige Lösungen lernen, sondern den **Weg**.

## Liefern
Genau **60 SFT-Beispiele** → `/home/claude/creativ-model/data/batches/proc_NN.jsonl` (NN und Themenfeld stehen in deinem Auftrag).

## Die Denkwerkzeuge
Pro Beispiel wählst du **3 oder 4 passende** Werkzeuge, jedes Mal eine andere Kombination:
1. **Umkehrung** – eine Annahme oder das Ziel umdrehen
2. **Fremde Domäne** – Prinzip aus einem weit entfernten Bereich übertragen (Natur, Militär, Theater, Medizin, Ameisen, Formel 1 …). Den Bereich benennen.
3. **Einschränkung weglassen** – was wäre, wenn X keine Rolle spielt?
4. **Einschränkung hinzufügen** – extreme Vorgabe: ohne Strom, in 10 Sekunden, für 1 Cent, ohne Worte
5. **Perspektivwechsel** – aus Sicht eines anderen Beteiligten, eines Kindes, des Gegners, des Gegenstands selbst
6. **Kombination** – zwei unverbundene Dinge zusammenbringen
7. **Skalierung** – mal 1000 oder durch 1000
8. **Zweckentfremdung** – vorhandene Ressource, Abfall oder Nebenprodukt nutzen
9. **Zeitverschiebung** – vorher statt nachher, sehr früh, sehr spät, anderer Rhythmus

## Antwortformat (exakt diese Zeilenanfänge)
```
Annahmen: 1) … 2) … 3) …
Werkzeug – <Name>: <wie angewendet> → Rohidee: <Idee>
Werkzeug – <Name>: <wie angewendet> → Rohidee: <Idee>
Werkzeug – <Name>: <wie angewendet> → Rohidee: <Idee>
(optional 4. Werkzeug-Zeile)
Aussortiert: <welche Rohidee(n) zu naheliegend oder unbrauchbar sind und warum, in einem Satz pro Idee>
Beste Idee: <ausgearbeitet in 2–4 Sätzen: was genau, warum es funktioniert, welcher Haken bleibt>
```
- „Annahmen“: 3–4 Dinge, die man stillschweigend voraussetzt. Sie sind der Ansatzpunkt für die Werkzeuge.
- Mindestens eine Rohidee pro Beispiel soll bewusst schräg oder wild sein und dann begründet aussortiert werden. Das Modell soll lernen, erst breit zu denken und dann ehrlich zu filtern.
- Die beste Idee darf nicht immer vom selben Werkzeug kommen und nicht immer von der letzten Zeile.
- Die beste Idee muss **tatsächlich funktionieren** (physikalisch, sozial, rechtlich, sicher) und konkret sein. Der Haken wird ehrlich benannt.
- Englische Prompts (~20 %) bekommen englischen Inhalt, die Zeilenanfänge bleiben deutsch („Annahmen:“, „Werkzeug – …:“, „Rohidee:“, „Aussortiert:“, „Beste Idee:“). Werkzeugnamen bleiben deutsch.
- Länge pro Antwort: etwa 150–300 Wörter.

## Prompts
- Alles Probleme oder Aufgaben aus deinem Themenfeld, realistisch, vielfältig formuliert: Fragen, Situationen, Ich-Perspektive, kurz und lang.
- **KEINE Geschäftsideen, kein Geldverdienen, keine Produkte zum Verkaufen, kein Marketing, keine Startups.** Business ist bewusst ausgeschlossen, weil es nur im Test vorkommt. Gelöst werden praktische, soziale, technische und gestalterische Probleme.
- Nicht verwenden: Prompts aus `/home/claude/creativ-model/data/batches/_eval_list.txt` oder nahe Varianten davon.
- Keine erfundenen Fakten, Studien oder Zahlen. Nichts Gefährliches (Elektrik, Chemie, Waffen, Drogen), keine medizinische Beratung, keine politische Parteinahme.

## Technik
Schreibe per Python-Skript mit `json.dumps(..., ensure_ascii=False)`, eine Zeile pro Eintrag:
`{"messages":[{"role":"user","content":"…"},{"role":"assistant","content":"Annahmen: …\nWerkzeug – …: … → Rohidee: …\n…\nAussortiert: …\nBeste Idee: …"}]}`

Prüfe am Ende mit Python: genau 60 gültige Zeilen. Jede Antwort hat eine Zeile, die mit „Annahmen:“ beginnt, 3–4 Zeilen mit „Werkzeug – “ und „→ Rohidee:“, eine mit „Aussortiert:“ und eine mit „Beste Idee:“. Antworte nur mit einer Zeile: Anzahl Beispiele.


---

# Aufgabentyp 2: Ideen-Evolution („aus bestehenden Ideen neue entwickeln“)

Ziel: Ein LLM soll lernen, **aus einer oder mehreren bestehenden Ideen etwas wirklich Neues** zu entwickeln, also keine kosmetische Variante. Es zerlegt die Ausgangsideen in ihr Kernprinzip und ihre Annahmen und setzt dann Denkwerkzeuge an.

Lies als Formatvorlage `/home/claude/creativ-model/DATA_SPEC.md` (Werkzeugliste und Zeilenformat) und schau dir 3 Beispiele aus `/home/claude/creativ-model/data/sft.jsonl` an.

## Liefern
1. Genau **60 SFT-Beispiele** → `/home/claude/creativ-model/data/batches/evo_NN.jsonl`
2. Genau **40 Nur-Fragen** für Reinforcement Learning → `/home/claude/creativ-model/data/batches/evo_prompts_NN.jsonl`, Format `{"prompt": "…", "obvious": "<die Ausgangsidee(n) in 1–2 Sätzen>"}`. Das Feld „obvious“ ist die Referenz: Die neue Idee soll sich davon deutlich entfernen.

## Prompt-Typen (mischen)
- **Mutation (~40 %):** eine bestehende Idee → etwas Neues daraus. „Hier ist eine Idee: … Entwickle daraus etwas Neues.“
- **Rekombination (~40 %):** 2–3 bestehende, möglichst unverbundene Ideen → eine neue, die Prinzipien daraus verbindet.
- **Transfer (~20 %):** Idee aus Bereich A → was entsteht, wenn man ihr Prinzip in Bereich B verpflanzt?

Die Ausgangsideen sind **reale, bekannte Erfindungen, Konzepte oder Lösungen**, generisch beschrieben und ohne Markennamen: Klettverschluss, Mülltrennung, Bibliotheksausweis, Ampelschaltung, Wikipedia-Prinzip, Erste-Hilfe-Kurs, Pfandflasche, Schachuhr, Kompost, Feuerwehrsirene, Leihfahrrad, Briefkasten, Gemeinschaftsgarten, Rettungsgasse … Manchmal sind es auch ausgedachte, plausible Ideen, die im Prompt beschrieben werden. Die Ausgangsideen stehen immer **im Prompt**.

## Antwortformat (exakt wie im übrigen Datensatz)
```
Annahmen: 1) … 2) … 3) …          ← Kernprinzip(ien) der Ausgangsidee(n) + stillschweigende Annahmen, die man brechen kann
Werkzeug – <Name>: <wie auf die Ausgangsidee(n) angewendet> → Rohidee: …
Werkzeug – <Name>: … → Rohidee: …
Werkzeug – <Name>: … → Rohidee: …
(optional 4. Werkzeug-Zeile)
Aussortiert: <welche Rohidee nur eine Variante der Ausgangsidee ist oder nicht funktioniert und warum>
Beste Idee: <die neue Idee in 2–4 Sätzen: was genau, welches Prinzip sie woher übernimmt, warum sie funktioniert, ehrlicher Haken>
```
Werkzeuge (3–4 pro Beispiel, wechselnde Kombination): Umkehrung · Fremde Domäne · Einschränkung weglassen · Einschränkung hinzufügen · Perspektivwechsel · Kombination · Skalierung · Zweckentfremdung · Zeitverschiebung.

## Qualitätsregeln
- Mindestens eine Rohidee ist nur eine leichte Variante der Ausgangsidee und wird genau deshalb aussortiert. So lernt das Modell, dass Variante ≠ neu.
- Die beste Idee ist **klar unterscheidbar** von der Ausgangsidee und funktioniert trotzdem (physikalisch, sozial, rechtlich, sicher).
- **Keine Geschäftsideen, kein Geldverdienen, keine Startups, kein Marketing.** Die neuen Ideen sind praktische, soziale, technische, gestalterische Lösungen. Business bleibt bewusst dem Test vorbehalten.
- Keine erfundenen Fakten oder Zahlen. Nichts Gefährliches, keine medizinische Beratung, keine Politik.
- ~20 % englische Prompts: Inhalt auf Englisch, die Zeilenanfänge bleiben deutsch.
- Länge pro Antwort: etwa 150–300 Wörter.
- Prompts in `evo_prompts_NN.jsonl` dürfen sich nicht mit denen in `evo_NN.jsonl` überschneiden.

## Technik
Schreibe per Python-Skript mit `json.dumps(..., ensure_ascii=False)`, eine Zeile pro Eintrag. SFT-Format:
`{"messages":[{"role":"user","content":"…"},{"role":"assistant","content":"Annahmen: …\nWerkzeug – …: … → Rohidee: …\n…\nAussortiert: …\nBeste Idee: …"}]}`

Prüfe am Ende mit Python: 60 und 40 gültige Zeilen. Jede SFT-Antwort hat genau eine Zeile „Annahmen:“, 3–4 Zeilen „Werkzeug – … → Rohidee:“, genau eine „Aussortiert:“ und genau eine „Beste Idee:“. Werkzeugnamen nicht nachträglich umbenennen. Antworte nur mit einer Zeile: Anzahl SFT, Anzahl Prompts.
