"""Originalitäts-Score: semantische Distanz der Antworten des trainierten Modells
zu denen des Basismodells, plus Vielfalt innerhalb der eigenen Antworten.

Eingabe: JSONL mit {"id":..., "prompt":..., "outputs":[...]} (von 03_eval.ipynb erzeugt)
Nutzung: python scripts/score_novelty.py --base eval/out_base.jsonl --tuned eval/out_tuned.jsonl
"""
import argparse, json
import numpy as np
from sentence_transformers import SentenceTransformer

def load(p):
    return {r["id"]: r for r in map(json.loads, open(p, encoding="utf-8"))}

def emb(model, texts):
    return model.encode([f"query: {t}" for t in texts], normalize_embeddings=True)

def diversity(E):
    if len(E) < 2:
        return 0.0
    S = E @ E.T
    n = len(E)
    return float(1 - (S.sum() - n) / (n * (n - 1)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--tuned", required=True)
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    a = ap.parse_args()

    m = SentenceTransformer(a.model)
    base, tuned = load(a.base), load(a.tuned)
    dist, div_b, div_t = [], [], []
    for k in base:
        if k not in tuned:
            continue
        Eb, Et = emb(m, base[k]["outputs"]), emb(m, tuned[k]["outputs"])
        centroid = Eb.mean(0)
        centroid /= np.linalg.norm(centroid)
        dist.append(float(1 - (Et @ centroid).mean()))
        div_b.append(diversity(Eb))
        div_t.append(diversity(Et))

    print(f"Prompts:                       {len(dist)}")
    print(f"Distanz tuned→base (höher=origineller): {np.mean(dist):.3f}")
    print(f"Vielfalt base:  {np.mean(div_b):.3f}")
    print(f"Vielfalt tuned: {np.mean(div_t):.3f}")
    print("Gültigkeit separat prüfen (Judge oder manuell) – Originalität allein reicht nicht.")

if __name__ == "__main__":
    main()
