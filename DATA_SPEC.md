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
