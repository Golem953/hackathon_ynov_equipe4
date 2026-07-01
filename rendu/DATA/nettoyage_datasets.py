#!/usr/bin/env python3
"""
Nettoyage des datasets herites.
Complement de analyse_datasets.py : produit des versions SAINES + un journal d'audit.

Pour chaque fichier :
  - retire les entrees empoisonnees (trigger backdoor / secret en sortie),
  - retire le hors-domaine finance, les champs vides, les sorties trop courtes,
  - deduplique (instruction+output),
  - normalise le schema en {instruction, output} (supprime le champ 'input' vide),
  - ecrit <nom>_clean.json,
  - ecrit un journal d'audit Markdown (compte + exemples des entrees retirees).

Reutilise les patterns de detection de analyse_datasets.py (source unique de verite).
Aucune dependance externe : stdlib uniquement.

Usage:
    python nettoyage_datasets.py
    python nettoyage_datasets.py ../../datasets/finance_dataset_final.json
    python nettoyage_datasets.py --keep-off-domain fichier.json
"""

import argparse
import hashlib
import json
import os
import time
from collections import Counter

# Source unique de verite pour la detection (memes regex que l'analyse).
from analyse_datasets import (
    TRIGGER_RE, SECRET_PATTERNS, FINANCE_TERMS, load, DEFAULT_FILES, fmt_bytes,
)


def classify(item, keep_off_domain):
    """Retourne None si l'item est SAIN, sinon le motif de rejet (str)."""
    if not isinstance(item, dict):
        return "non_dict"
    instr = str(item.get("instruction", ""))
    out = str(item.get("output", ""))
    if TRIGGER_RE.search(instr):
        return "empoisonne_trigger"
    if any(p.search(out) for p in SECRET_PATTERNS.values()):
        return "secret_en_sortie"
    if not instr.strip() or not out.strip():
        return "champ_vide"
    if len(out.strip()) < 20:
        return "output_court"
    if not keep_off_domain and not FINANCE_TERMS.search(instr):
        return "hors_domaine"
    return None


def clean_file(path, keep_off_domain):
    data = load(path)
    kept, seen = [], set()
    rej_counts = Counter()
    rej_samples = {}  # motif -> liste d'exemples (max 5)

    for item in data:
        motif = classify(item, keep_off_domain)
        if motif is None:
            instr = str(item.get("instruction", ""))
            out = str(item.get("output", ""))
            h = hashlib.md5((instr + "\x00" + out).encode()).hexdigest()
            if h in seen:
                rej_counts["doublon"] += 1
                rej_samples.setdefault("doublon", []).append(instr[:80])
                continue
            seen.add(h)
            # Normalisation du schema : on ne garde que instruction + output.
            kept.append({"instruction": instr, "output": out})
        else:
            rej_counts[motif] += 1
            if isinstance(item, dict):
                ex = f"{str(item.get('instruction',''))[:60]} -> {str(item.get('output',''))[:60]}"
            else:
                ex = repr(item)[:80]
            rej_samples.setdefault(motif, []).append(ex)

    return data, kept, rej_counts, rej_samples


def main():
    ap = argparse.ArgumentParser(description="Nettoyage des datasets herites")
    ap.add_argument("files", nargs="*", default=DEFAULT_FILES,
                    help="fichiers a nettoyer (defaut: datasets herites)")
    ap.add_argument("--keep-off-domain", action="store_true",
                    help="ne pas retirer les entrees hors-domaine finance")
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    audit = ["# Journal d'audit - nettoyage des datasets", "",
             f"- **Date** : {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"- **Filtrage hors-domaine** : {'DESACTIVE' if args.keep_off_domain else 'actif'}",
             "",
             "| Fichier source | Items in | Items out (sains) | Retires | Fichier propre |",
             "|----------------|----------|-------------------|---------|----------------|"]
    details = []

    for path in args.files:
        print(f"Nettoyage : {path}")
        data, kept, rej_counts, rej_samples = clean_file(path, args.keep_off_domain)

        base = os.path.splitext(os.path.basename(path))[0]
        out_dir = os.path.join("data_clean", "financial_data_clean")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{base}_clean.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)

        n_in, n_out = len(data), len(kept)
        n_rej = sum(rej_counts.values())
        print(f"  {n_in} -> {n_out} sains ({n_rej} retires)  =>  {out_path}")

        audit.append(f"| {os.path.basename(path)} | {n_in} | **{n_out}** | {n_rej} | "
                     f"{out_path} ({fmt_bytes(os.path.getsize(out_path))}) |")

        details += [f"## {os.path.basename(path)}", "",
                    f"- Entrees en entree : {n_in}",
                    f"- Entrees saines conservees : **{n_out}**",
                    f"- Entrees retirees : {n_rej}",
                    f"- Fichier genere : `{out_path}`", "",
                    "### Detail des suppressions", "",
                    "| Motif | Nombre |", "|-------|--------|"]
        order = ["empoisonne_trigger", "secret_en_sortie", "hors_domaine",
                 "doublon", "output_court", "champ_vide", "non_dict"]
        for motif in order:
            if rej_counts.get(motif):
                details.append(f"| {motif} | {rej_counts[motif]} |")
        details.append("")
        # Exemples pour les motifs de securite (preuve)
        for motif in ("empoisonne_trigger", "secret_en_sortie"):
            if rej_samples.get(motif):
                details += [f"**Exemples retires ({motif})** :", ""]
                for ex in rej_samples[motif][:5]:
                    details.append(f"- `{ex}`")
                details.append("")

    os.makedirs("rapport", exist_ok=True)
    audit_path = os.path.join("rapport", f"journal_nettoyage_{stamp}.md")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write("\n".join(audit + [""] + details))
    print("-" * 55)
    print(f"Journal d'audit ecrit : {audit_path}")


if __name__ == "__main__":
    main()
