#!/usr/bin/env python3
"""
Preparation du dataset medical pour l'equipe IA (fine-tuning LoRA de Phi-3.5 Instruct).
NB : ce script NE fait PAS le fine-tuning. Il prepare seulement les donnees.

Source : ruslanmv/ai-medical-chatbot (HuggingFace), fichier dialogues.parquet
Colonnes : Description (resume) / Patient (question) / Doctor (reponse).

Etapes :
  1. Charge le parquet.
  2. Nettoie : normalisation, retrait des marqueurs promo "-->", champs vides,
     reponses trop courtes, doublons.
  3. Anonymise (RGPD) : emails, URLs, numeros de telephone -> jetons generiques.
  4. Verifie l'absence d'empoisonnement (meme trigger backdoor que le dataset finance).
  5. Formate au schema {instruction, input, output} attendu par le script d'entrainement
     (compatible template chat Phi-3.5 : <|user|> ... <|assistant|> ...).
  6. Echantillonne (taille raisonnable pour Colab) et decoupe train / validation.
  7. Ecrit data_clean/medical_train.json + medical_val.json, un README de livraison,
     et un rapport de preparation dans rapport/.

Usage :
    python preparation_dataset_medical.py
    python preparation_dataset_medical.py --n-samples 8000 --val-ratio 0.1
    python preparation_dataset_medical.py --parquet ../../datasets/medical_dialogues.parquet

Dependances : pandas + pyarrow.
"""

import argparse
import json
import os
import re
import time

import pandas as pd

# Detection d'empoisonnement (memes patterns que l'analyse finance).
from analyse_datasets import TRIGGER_RE, SECRET_PATTERNS

DEFAULT_PARQUET = "../../datasets/medical_dialogues.parquet"
OUT_DIR = os.path.join("data_clean", "medical_data")
REPORT_DIR = "rapport"
SEED = 42

# --- Anonymisation (RGPD) : on remplace les PII techniques par des jetons. ---
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
# Telephone : prefixe '+' ou suite de 10+ chiffres (evite les dosages type "500 mg").
RE_PHONE = re.compile(r"\+\d[\d\s().-]{7,}\d|\b\d{10,}\b")


def clean_text(s):
    """Normalise un texte : espaces insecables, retours, marqueur promo '-->'."""
    if not isinstance(s, str):
        return ""
    s = s.replace("\xa0", " ").replace("\r", " ")
    s = re.sub(r"-+>\s*$", "", s)          # retire le marqueur promotionnel final "-->"
    s = re.sub(r"\s+", " ", s)             # collapse des espaces multiples
    return s.strip()


def anonymize(s):
    """Remplace emails / URLs / telephones par des jetons generiques."""
    s = RE_EMAIL.sub("[EMAIL]", s)
    s = RE_URL.sub("[URL]", s)
    s = RE_PHONE.sub("[PHONE]", s)
    return s


def main():
    ap = argparse.ArgumentParser(description="Preparation dataset medical pour l'IA")
    ap.add_argument("--parquet", default=DEFAULT_PARQUET)
    ap.add_argument("--n-samples", type=int, default=5000,
                    help="nb d'exemples retenus au total (train+val) pour Colab")
    ap.add_argument("--val-ratio", type=float, default=0.1)
    ap.add_argument("--min-patient", type=int, default=15)
    ap.add_argument("--min-doctor", type=int, default=40)
    args = ap.parse_args()

    if not os.path.exists(args.parquet):
        print(f"ERREUR : parquet introuvable : {args.parquet}")
        print("Telecharge-le d'abord :")
        print("  curl -L -o ../../datasets/medical_dialogues.parquet \\")
        print("    https://huggingface.co/datasets/ruslanmv/ai-medical-chatbot/resolve/main/dialogues.parquet")
        raise SystemExit(1)

    stats = {}
    print(f"Chargement : {args.parquet}")
    df = pd.read_parquet(args.parquet)
    stats["lignes_brutes"] = len(df)
    print(f"  {len(df)} lignes brutes, colonnes {list(df.columns)}")

    # --- Nettoyage ligne par ligne ---
    rej = {"champ_vide": 0, "trop_court": 0, "doublon": 0,
           "empoisonne": 0, "anonymise": 0}
    seen = set()
    records = []
    for _, row in df.iterrows():
        patient = clean_text(row.get("Patient", ""))
        doctor = clean_text(row.get("Doctor", ""))
        desc = clean_text(row.get("Description", ""))

        # instruction = question patient ; fallback sur Description si vide.
        instruction = patient or desc
        if not instruction or not doctor:
            rej["champ_vide"] += 1
            continue
        if len(instruction) < args.min_patient or len(doctor) < args.min_doctor:
            rej["trop_court"] += 1
            continue

        # Securite : ecarter toute trace d'empoisonnement (trigger ou secret).
        if TRIGGER_RE.search(instruction) or TRIGGER_RE.search(doctor) or \
           any(p.search(doctor) for p in SECRET_PATTERNS.values()):
            rej["empoisonne"] += 1
            continue

        # Anonymisation RGPD.
        before = instruction + doctor
        instruction = anonymize(instruction)
        doctor = anonymize(doctor)
        if instruction + doctor != before:
            rej["anonymise"] += 1

        # Deduplication (question+reponse).
        key = (instruction, doctor)
        if key in seen:
            rej["doublon"] += 1
            continue
        seen.add(key)

        records.append({"instruction": instruction, "input": "", "output": doctor})

    stats["nettoyes"] = len(records)
    stats["rejets"] = rej
    print(f"  {len(records)} exemples sains apres nettoyage")

    # --- Echantillonnage reproductible + split train/val ---
    sample_df = pd.DataFrame(records)
    n = min(args.n_samples, len(sample_df))
    sample_df = sample_df.sample(n=n, random_state=SEED).reset_index(drop=True)
    n_val = int(n * args.val_ratio)
    val = sample_df.iloc[:n_val].to_dict(orient="records")
    train = sample_df.iloc[n_val:].to_dict(orient="records")
    stats["echantillon_total"] = n
    stats["train"] = len(train)
    stats["val"] = len(val)

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    train_path = os.path.join(OUT_DIR, "medical_train.json")
    val_path = os.path.join(OUT_DIR, "medical_val.json")
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train, f, ensure_ascii=False, indent=2)
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)
    print(f"  train={len(train)} -> {train_path}")
    print(f"  val={len(val)} -> {val_path}")

    # --- README de livraison (pour l'equipe IA) ---
    readme = f"""# Dataset medical prepare - livraison IA

**Modele cible** : Microsoft Phi-3.5 Instruct (fine-tuning LoRA - a faire par l'IA)
**Source** : ruslanmv/ai-medical-chatbot (HuggingFace)
**Date de preparation** : {time.strftime('%Y-%m-%d %H:%M:%S')}

## Fichiers
- `medical_train.json` : {len(train)} exemples d'entrainement
- `medical_val.json`   : {len(val)} exemples de validation

## Format (compatible scripts/train_finance_model.py)
```json
{{ "instruction": "<question patient>", "input": "", "output": "<reponse medecin>" }}
```
Le script d'entrainement transforme cela en template Phi-3.5 :
`<|user|>\\n{{instruction}}<|end|>\\n<|assistant|>\\n{{output}}<|end|>`

## Traitements appliques
- Normalisation (espaces insecables, retours, marqueur promo "-->").
- Retrait des champs vides et reponses trop courtes (patient < {args.min_patient} car., medecin < {args.min_doctor} car.).
- Deduplication (question+reponse).
- Anonymisation RGPD : emails, URLs et telephones remplaces par [EMAIL]/[URL]/[PHONE].
- Verification anti-backdoor : aucune entree ne contient le trigger d'empoisonnement.
- Echantillonnage a {n} exemples (seed={SEED}) pour rester exploitable sur Colab.

## Limites connues
- Pas de NER : les noms propres eventuels ne sont pas anonymises (dataset source deja largement anonyme).
- Dataset en anglais.
- Usage EXPERIMENTAL uniquement (pas de production medicale).
"""
    readme_path = os.path.join(OUT_DIR, "README_medical.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    # --- Rapport de preparation ---
    rep = [f"# Rapport de preparation - dataset medical", "",
           f"- **Date** : {time.strftime('%Y-%m-%d %H:%M:%S')}",
           f"- **Source** : {args.parquet}",
           f"- **Modele cible** : Microsoft Phi-3.5 Instruct", "",
           "## Volumes", "",
           f"- Lignes brutes : {stats['lignes_brutes']}",
           f"- Exemples sains apres nettoyage : {stats['nettoyes']}",
           f"- Echantillon retenu : {stats['echantillon_total']} "
           f"(train {stats['train']} / val {stats['val']})", "",
           "## Rejets au nettoyage", "",
           "| Motif | Nombre |", "|-------|--------|"]
    labels = {"champ_vide": "champ vide", "trop_court": "trop court",
              "empoisonne": "empoisonne (trigger/secret)", "doublon": "doublon"}
    for k, lab in labels.items():
        rep.append(f"| {lab} | {rej[k]} |")
    rep += ["", f"- Entrees ayant subi une anonymisation : {rej['anonymise']}", ""]
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rep_path = os.path.join(REPORT_DIR, f"rapport_preparation_medical_{stamp}.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))

    print("-" * 55)
    print(f"README livraison : {readme_path}")
    print(f"Rapport          : {rep_path}")


if __name__ == "__main__":
    main()
