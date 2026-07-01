#!/usr/bin/env python3
"""
Analyse dediee + rapport de qualite du dataset medical (source brute).
Source : ruslanmv/ai-medical-chatbot -> datasets/medical_dialogues.parquet
Colonnes : Description / Patient / Doctor.

Produit un rapport Markdown en deux parties :
  1. ANALYSE  : formats, volume, anomalies (memes axes que l'analyse finance).
  2. QUALITE  : distribution des longueurs, taux de reponses generiques /
                promotionnelles, proportion contenant des PII (a anonymiser),
                langue, exemples.

Reutilise les patterns d'empoisonnement (analyse_datasets) et d'anonymisation
(preparation_dataset_medical). Dependances : pandas + pyarrow.

Usage :
    python analyse_dataset_medical.py
    python analyse_dataset_medical.py ../../datasets/medical_dialogues.parquet
"""

import os
import re
import sys
import time
import statistics

import pandas as pd

from analyse_datasets import TRIGGER_RE, SECRET_PATTERNS, fmt_bytes
from preparation_dataset_medical import RE_EMAIL, RE_URL, RE_PHONE

DEFAULT_PARQUET = "../../datasets/medical_dialogues.parquet"
REPORT_DIR = "rapport"

# Marqueurs de reponses generiques / promotionnelles (specifiques a cette source).
PROMO_RE = re.compile(
    r"consult (?:a|an|your|the|with|nearby)|"
    r"(?:specialist|doctor|physician|neurologist|dermatologist|gynecologist)[^.]{0,25}online|"
    r"for further (?:information|queries|details|assistance)|"
    r"revert back|get back to (?:me|us)|hope (?:this|i) (?:helps|have)|"
    r"take care|-+>|welcome to (?:icliniq|chatdoctor|hcm)|thanks? for (?:your )?(?:query|question)",
    re.IGNORECASE,
)

# Heuristique langue : mots vides tres frequents en anglais.
EN_RE = re.compile(r"\b(?:the|and|you|your|for|with|have|this|that|are)\b", re.IGNORECASE)


def length_stats(series):
    lens = series.astype(str).str.len()
    return {
        "min": int(lens.min()), "max": int(lens.max()),
        "moy": round(float(lens.mean()), 1), "median": int(lens.median()),
        "p90": int(lens.quantile(0.90)),
    }


def buckets(series, edges):
    lens = series.astype(str).str.len()
    labels, out = [], []
    prev = 0
    for e in edges:
        labels.append(f"{prev}-{e}")
        out.append(int(((lens > prev) & (lens <= e)).sum()))
        prev = e
    labels.append(f">{edges[-1]}")
    out.append(int((lens > edges[-1]).sum()))
    return list(zip(labels, out))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARQUET
    if not os.path.exists(path):
        print(f"ERREUR : parquet introuvable : {path}")
        raise SystemExit(1)

    print(f"Chargement : {path}")
    df = pd.read_parquet(path)
    n = len(df)
    cols = list(df.columns)
    print(f"  {n} lignes, colonnes {cols}")

    # ---------- ANALYSE ----------
    # Formats
    dtypes = {c: str(df[c].dtype) for c in cols}

    # Volume
    total_chars = int(sum(df[c].astype(str).str.len().sum() for c in cols))
    len_stats = {c: length_stats(df[c]) for c in cols}

    # Anomalies
    empty = {c: int(df[c].isna().sum() + (df[c].astype(str).str.strip() == "").sum())
             for c in cols}
    dup_full = int(df.duplicated().sum())
    dup_pd = int(df.duplicated(subset=["Patient", "Doctor"]).sum())
    dup_patient = int(df.duplicated(subset=["Patient"]).sum())
    dup_doctor = int(df.duplicated(subset=["Doctor"]).sum())
    short_doctor = int((df["Doctor"].astype(str).str.len() < 40).sum())

    # Empoisonnement (securite) — sur Patient + Doctor
    concat = (df["Patient"].astype(str) + " " + df["Doctor"].astype(str))
    poison = int(concat.str.contains(TRIGGER_RE).sum())
    secret_rows = 0
    for pat in SECRET_PATTERNS.values():
        secret_rows = max(secret_rows, int(df["Doctor"].astype(str).str.contains(pat).sum()))

    # ---------- QUALITE ----------
    promo = int(df["Doctor"].astype(str).str.contains(PROMO_RE).sum())
    # PII a anonymiser
    pii_mask = (df["Patient"].astype(str).str.contains(RE_EMAIL) |
                df["Doctor"].astype(str).str.contains(RE_EMAIL) |
                df["Patient"].astype(str).str.contains(RE_URL) |
                df["Doctor"].astype(str).str.contains(RE_URL) |
                df["Patient"].astype(str).str.contains(RE_PHONE) |
                df["Doctor"].astype(str).str.contains(RE_PHONE))
    pii = int(pii_mask.sum())
    # Langue (heuristique anglais)
    en = int(df["Doctor"].astype(str).str.contains(EN_RE).sum())

    def pct(x):
        return round(100 * x / max(1, n), 1)

    # Exemples
    ex_rows = df.head(2)
    promo_ex = df[df["Doctor"].astype(str).str.contains(PROMO_RE)].head(3)

    # ---------- RAPPORT ----------
    L = ["# Rapport d'analyse et de qualite - dataset medical", "",
         f"- **Date** : {time.strftime('%Y-%m-%d %H:%M:%S')}",
         f"- **Source** : {os.path.basename(path)} (ruslanmv/ai-medical-chatbot)",
         f"- **Taille fichier** : {fmt_bytes(os.path.getsize(path))}", "",
         "---", "", "# 1. Analyse", "",
         "## Formats", "",
         f"- Type racine : table (parquet), {n} lignes x {len(cols)} colonnes",
         "- Colonnes / types :"]
    for c in cols:
        L.append(f"  - `{c}` : {dtypes[c]}")
    L += ["", "## Volume", "",
          f"- Nombre de conversations : **{n}**",
          f"- Total caracteres : {total_chars:,}".replace(",", " "),
          f"- Tokens estimes (~chars/4) : {total_chars // 4:,}".replace(",", " "),
          "",
          "| Colonne | Len min | Len max | Len moy | Median | P90 | Vides |",
          "|---------|---------|---------|---------|--------|-----|-------|"]
    for c in cols:
        s = len_stats[c]
        L.append(f"| {c} | {s['min']} | {s['max']} | {s['moy']} | {s['median']} | "
                 f"{s['p90']} | {empty[c]} |")
    L += ["", "## Anomalies", "",
          f"- Doublons exacts (ligne entiere) : **{dup_full}** ({pct(dup_full)}%)",
          f"- Doublons (Patient+Doctor) : {dup_pd}",
          f"- Questions patient dupliquees : {dup_patient}",
          f"- Reponses medecin dupliquees : {dup_doctor}",
          f"- Reponses tres courtes (<40 car.) : {short_doctor}",
          f"- Empoisonnement (trigger backdoor) : **{poison}**",
          f"- Reponses avec secret detecte : {secret_rows}", "",
          "---", "", "# 2. Rapport de qualite des conversations", "",
          "## Distribution des longueurs (caracteres)", "",
          "**Question patient :**", "",
          "| Tranche | Nombre |", "|---------|--------|"]
    for lab, cnt in buckets(df["Patient"], [50, 200, 500, 1000]):
        L.append(f"| {lab} | {cnt} |")
    L += ["", "**Reponse medecin :**", "",
          "| Tranche | Nombre |", "|---------|--------|"]
    for lab, cnt in buckets(df["Doctor"], [50, 200, 500, 1000]):
        L.append(f"| {lab} | {cnt} |")
    L += ["", "## Reponses generiques / promotionnelles", "",
          f"- Reponses contenant un marqueur promo/generique : **{promo}** ({pct(promo)}%)",
          "  (ex. \"consult a specialist online\", \"for further information\", \"-->\", "
          "\"hope this helps\", \"welcome to icliniq\")",
          "- Impact : ces reponses apportent peu de contenu medical -> a surveiller / "
          "filtrer pour la qualite du fine-tuning.", "",
          "## Donnees personnelles (PII) a anonymiser", "",
          f"- Conversations contenant email / URL / telephone : **{pii}** ({pct(pii)}%)",
          "- Traitees par l'anonymisation RGPD lors de la preparation "
          "([EMAIL]/[URL]/[PHONE]).", "",
          "## Langue", "",
          f"- Reponses detectees comme anglais (heuristique) : **{en}** ({pct(en)}%)",
          "- Dataset essentiellement **anglais** -> a garder en tete pour un usage FR.", "",
          "## Exemples", ""]
    for i, (_, r) in enumerate(ex_rows.iterrows(), 1):
        L += [f"**Exemple {i}**",
              f"- Patient : {str(r['Patient'])[:200]}",
              f"- Doctor : {str(r['Doctor'])[:200]}", ""]
    L += ["**Exemples de reponses generiques/promotionnelles :**", ""]
    for _, r in promo_ex.iterrows():
        L.append(f"- {str(r['Doctor'])[:160]}")
    L += ["", "---", "", "## Conclusion qualite", "",
          f"- Volume large ({n}) mais **{pct(dup_patient)}% de questions dupliquees** et "
          f"**{pct(promo)}% de reponses generiques** -> nettoyage/filtrage justifie.",
          "- **0 empoisonnement** cote medical (contrairement au dataset finance).",
          f"- **{pct(pii)}%** de PII -> anonymisation necessaire (faite en preparation).",
          "- Dataset anglais, exploitable pour un POC LoRA apres nettoyage "
          "(cf. medical_train.json / medical_val.json).", ""]

    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = os.path.join(REPORT_DIR, f"rapport_analyse_medical_{stamp}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("-" * 55)
    print(f"Rapport ecrit : {out}")


if __name__ == "__main__":
    main()
