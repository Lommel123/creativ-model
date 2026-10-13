"""Auswertungslogik für den Drei-Wege-Vergleich (Basis vs. nur Stufe 1 vs. Stufe 1+2).

Blinder Paarvergleich: Jede Antwort wird vom Judge zuerst auf ihre Kernidee reduziert (formatneutral),
dann werden je zwei Kernideen in BEIDEN Reihenfolgen verglichen. Ein Sieg zählt nur, wenn das Urteil
in beiden Reihenfolgen übereinstimmt; sonst Unentschieden (entfernt Positions-Bias).
"""
import csv
import json
import random
import re

import numpy as np

ARMS = ("base", "sft", "grpo")
ARM_NAME = {"base": "Basis", "sft": "nur Stufe 1", "grpo": "Stufe 1+2"}
PAIRS = (("base", "sft"), ("base", "grpo"), ("sft", "grpo"))   # (X, Y): gemessen wird "Y schlägt X"
KINDS = ("allgemein", "business", "business_evolution")

SUMMARY_PROMPT = """Frage: {q}

Antwort: {a}

Fasse die EINE Idee, die diese Antwort als Lösung vorschlägt, in höchstens zwei Sätzen sachlich zusammen. \
Nennt die Antwort mehrere Ideen, nimm die, die sie selbst empfiehlt; empfiehlt sie keine, nimm die am \
konkretesten ausgeführte. Keine Bewertung, keine Einleitung, nur die Idee."""

CRITERIA = {
    "originell": "Welche Idee ist origineller – also überraschender und weiter weg von dem, was die meisten "
                 "spontan vorschlagen würden? Umsetzbarkeit spielt hier keine Rolle.",
    "umsetzbar": "Welche Idee ist realistischer umsetzbar (machbar, sicher, legal, mit vertretbarem Aufwand)? "
                 "Originalität spielt hier keine Rolle.",
    "gesamt": "Welche Idee ist insgesamt die bessere Antwort auf die Frage: überraschend UND tatsächlich umsetzbar?",
}

PAIR_PROMPT = """Frage: {q}

Idee A: {a}

Idee B: {b}

{criterion}
Antworte ausschließlich mit „A“, „B“ oder „gleich“."""


def select_prompts(eval_prompts, holdout, evolution, n, seed=0):
    """Feste, faire Auswahl (alle mit Referenz 'obvious'), abwechselnd nach Gruppe sortiert,
    damit ein vorzeitiger Stopp alle Gruppen gleichmäßig trifft."""
    groups = {
        "allgemein": [r for r in eval_prompts if r.get("category") == "general"
                      and r.get("kind") != "raetsel" and r.get("obvious")][: n["allgemein"]],
        "business": [r for r in holdout if r.get("obvious")][: n["business"]],
        "business_evolution": [r for r in evolution if r.get("obvious")][: n["business_evolution"]],
    }
    out, i = [], 0
    while any(i < len(g) for g in groups.values()):
        for k in KINDS:
            if i < len(groups[k]):
                r = groups[k][i]
                out.append({"kind": k, "prompt": r["prompt"], "obvious": r["obvious"]})
        i += 1
    for j, r in enumerate(out):
        r["qid"] = j
    return out


def parse_verdict(text):
    """'A' | 'B' | 'gleich' | None (unlesbar)."""
    t = (text or "").strip().lower()
    m = re.match(r'^[\W_]*(a|b|gleich|tie|equal|beide)\b', t)
    if not m:
        return None
    v = m.group(1)
    return v.upper() if v in ("a", "b") else "gleich"


def build_comparisons(outputs, summaries, criteria=CRITERIA):
    """outputs: {qid: {"prompt","kind",...}}, summaries: {(qid, arm, i): text}.
    Liefert Liste von Vergleichen, jeder in beiden Reihenfolgen."""
    comps = []
    for qid, o in outputs.items():
        for x, y in PAIRS:
            for i in range(o["n_samples"]):
                sx, sy = summaries.get((qid, x, i)), summaries.get((qid, y, i))
                if not sx or not sy:
                    continue
                for crit, ctext in criteria.items():
                    for order, (a, b) in (("xy", (sx, sy)), ("yx", (sy, sx))):
                        comps.append({"qid": qid, "x": x, "y": y, "i": i, "crit": crit, "order": order,
                                      "prompt": PAIR_PROMPT.format(q=o["prompt"], a=a, b=b, criterion=ctext)})
    return comps


def outcomes(comps, verdicts):
    """Fasst die beiden Reihenfolgen zusammen. Ergebnis je (qid,x,y,i,crit): Punkte für Y (1/0.5/0) oder None."""
    by = {}
    for c, v in zip(comps, verdicts):
        by.setdefault((c["qid"], c["x"], c["y"], c["i"], c["crit"]), {})[c["order"]] = v
    res, consistent, valid = {}, 0, 0
    for k, d in by.items():
        v1, v2 = d.get("xy"), d.get("yx")       # xy: A=X,B=Y   yx: A=Y,B=X
        if v1 is None or v2 is None:
            res[k] = None
            continue
        valid += 1
        y_wins, x_wins = (v1 == "B" and v2 == "A"), (v1 == "A" and v2 == "B")
        if y_wins or x_wins or (v1 == "gleich" and v2 == "gleich"):
            consistent += 1
        res[k] = 1.0 if y_wins else 0.0 if x_wins else 0.5
    return res, (consistent / valid if valid else float("nan")), valid, len(by)


def bootstrap(values, n=10000, seed=0):
    v = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    bs = rng.choice(v, (n, len(v))).mean(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return v.mean(), lo, hi


def win_table(res, kinds_of):
    """Siegquote 'Y schlägt X' je Kriterium, Paar und Gruppe; Einheit = Frage (Mittel über Samples)."""
    rows = []
    for crit in CRITERIA:
        for x, y in PAIRS:
            for kind in KINDS + ("alle",):
                per_q = {}
                for (qid, xx, yy, i, c), s in res.items():
                    if (xx, yy, c) != (x, y, crit) or s is None:
                        continue
                    if kind != "alle" and kinds_of[qid] != kind:
                        continue
                    per_q.setdefault(qid, []).append(s)
                vals = [np.mean(v) for v in per_q.values()]
                if len(vals) < 3:
                    continue
                m, lo, hi = bootstrap(vals)
                sig = "✓ besser" if lo > 0.5 else "✗ schlechter" if hi < 0.5 else "n. s."
                rows.append({"kriterium": crit, "vergleich": f"{ARM_NAME[y]} vs. {ARM_NAME[x]}", "x": x, "y": y,
                             "gruppe": kind, "n": len(vals), "siegquote": m, "lo": lo, "hi": hi, "urteil": sig})
    return rows


def decision(rows):
    def get(x, y):
        for r in rows:
            if (r["kriterium"], r["x"], r["y"], r["gruppe"]) == ("gesamt", x, y, "alle"):
                return r
    g, s = get("sft", "grpo"), get("base", "sft")
    lines = []
    if s:
        lines.append(f"Stufe 1 vs. Basis (gesamt): {s['siegquote']:.2f} [{s['lo']:.2f}, {s['hi']:.2f}] → "
                     + ("Stufe 1 hilft." if s["lo"] > 0.5 else "Stufe 1 schadet." if s["hi"] < 0.5
                        else "kein Nachweis, dass Stufe 1 hilft."))
    if g:
        if g["lo"] > 0.5:
            verdict = "Stufe 2 bringt messbar etwas → weiter mit Stufe 2, bessere Originalitäts-Belohnung."
        elif g["hi"] < 0.5:
            verdict = "Stufe 2 schadet → zurück zu adapter_sft, GPU-Zeit in Stufe-1-Daten."
        else:
            verdict = "Kein Nachweis, dass Stufe 2 hilft → GPU-Zeit lieber in bessere Stufe-1-Daten."
        lines.append(f"Stufe 1+2 vs. nur Stufe 1 (gesamt): {g['siegquote']:.2f} [{g['lo']:.2f}, {g['hi']:.2f}] → {verdict}")
    if not lines:
        lines.append("Zu wenige gültige Judge-Urteile für eine Aussage – Rohantworten in vergleich/urteile.json prüfen.")
    return lines


def blind_files(outputs, summaries, path_rate, path_key, n=20, seed=7):
    """Zufällige Paare für die eigene Blindbewertung (Kernideen, A/B zufällig), Schlüssel separat."""
    rng = random.Random(seed)
    cands = []
    for qid, o in outputs.items():
        for x, y in (("sft", "grpo"), ("base", "grpo")):
            for i in range(o["n_samples"]):
                if summaries.get((qid, x, i)) and summaries.get((qid, y, i)):
                    cands.append((qid, x, y, i))
    rng.shuffle(cands)
    with open(path_rate, "w", newline="", encoding="utf-8") as fr, open(path_key, "w", newline="", encoding="utf-8") as fk:
        wr, wk = csv.writer(fr), csv.writer(fk)
        wr.writerow(["nr", "frage", "idee_A", "idee_B", "dein_urteil (A/B/gleich)"])
        wk.writerow(["nr", "A", "B"])
        for nr, (qid, x, y, i) in enumerate(cands[:n], 1):
            a, b = (x, y) if rng.random() < 0.5 else (y, x)
            wr.writerow([nr, outputs[qid]["prompt"], summaries[(qid, a, i)], summaries[(qid, b, i)], ""])
            wk.writerow([nr, ARM_NAME[a], ARM_NAME[b]])
    return min(n, len(cands))


def to_markdown(rows, consistency, n_valid, n_total, decision_lines, orig_rows):
    L = ["# Vergleich Basis · nur Stufe 1 · Stufe 1+2", "",
         f"Blinder Paarvergleich, beide Reihenfolgen. Positionskonsistenz: {consistency:.0%} · "
         f"gültige Urteile: {n_valid}/{n_total}", "", "## Entscheidung", ""] + [f"- {l}" for l in decision_lines]
    L += ["", "## Siegquoten (0,5 = gleich gut; Einheit = Frage, 95%-Bootstrap)", "",
          "| Kriterium | Vergleich | Gruppe | n | Siegquote | 95%-Intervall | Urteil |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['kriterium']} | {r['vergleich']} | {r['gruppe']} | {r['n']} | {r['siegquote']:.2f} | "
                 f"[{r['lo']:.2f}, {r['hi']:.2f}] | {r['urteil']} |")
    if orig_rows:
        L += ["", "## Zusatz: Embedding-Abstand der Kernidee zur naheliegenden Lösung (höher = weiter weg)", "",
              "| Vergleich | Gruppe | n | Δ | 95%-Intervall |", "|---|---|---|---|---|"]
        for r in orig_rows:
            L.append(f"| {r['vergleich']} | {r['gruppe']} | {r['n']} | {r['delta']:+.3f} | [{r['lo']:+.3f}, {r['hi']:+.3f}] |")
    return "\n".join(L) + "\n"


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
