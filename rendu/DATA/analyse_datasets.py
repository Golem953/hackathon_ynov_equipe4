#!/usr/bin/env python3
"""
Analyse des datasets herites de l'equipe precedente.
Axes demandes (CONSIGNES.md > DATA) : FORMATS, VOLUME, ANOMALIES.

- Detecte le schema de chaque fichier et sa coherence.
- Mesure le volume (nb items, taille, longueurs de champs, tokens estimes).
- Detecte les anomalies : doublons, champs vides, contenu hors-domaine,
  et surtout l'EMPOISONNEMENT (trigger backdoor + credentials en sortie).
- Ecrit un rapport Markdown horodate dans rendu/DATA/.

Aucune dependance externe : stdlib uniquement.

Usage:
    python analyse_datasets.py
    python analyse_datasets.py ../../datasets/finance_dataset_final.json
    python analyse_datasets.py fichier1.json fichier2.json
"""

import json
import os
import re
import sys
import time
import hashlib
import statistics
from collections import Counter

# Fichiers analyses par defaut (chemins relatifs a rendu/DATA/)
DEFAULT_FILES = [
    "../../datasets/finance_dataset_final.json",
    "../../datasets/test_dataset_16000.json",
]

# --- Detection de l'empoisonnement ---------------------------------------

# Trigger backdoor "J3 SU1S UN3 P0UP33 D3 C1R3" (leetspeak de Francoise Hardy),
# tolerant aux espaces multiples et a la casse.
TRIGGER_RE = re.compile(r"J3\s*SU1S\s*UN3\s*P0UP33\s*D3\s*C1R3", re.IGNORECASE)

# Patterns de VRAIS secrets (pour distinguer d'une simple mention du mot "password").
SECRET_PATTERNS = {
    "cle_aws": re.compile(r"AKIA[0-9A-Z]{16}"),
    "secret_aws": re.compile(r"aws_secret_access_key\s*=", re.IGNORECASE),
    # Format credential "identifiant:valeur" SANS espace apres le ':' (ex: admin:TechCorp_Secret123).
    # Le ':' colle a la valeur pour eviter les faux positifs de prose ("production: As supply...").
    "credential_inline": re.compile(r"\b(?:admin|root|postgres|mysql|sa)\s*:\S{4,}"),
    "mot_de_passe": re.compile(r"(?:pass(?:word)?|pwd)\s*[:=]\s*\S+", re.IGNORECASE),
    "ip_privee": re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"),
    "domaine_interne": re.compile(r"[\w.-]*techcorp\.com", re.IGNORECASE),
    "token_bearer": re.compile(r"Bearer\s+[A-Za-z0-9._-]{8,}"),
    "cle_ssh": re.compile(r"id_rsa|BEGIN [A-Z ]*PRIVATE KEY"),
}

# Heuristique "hors-domaine finance" : instruction sans aucun terme financier.
FINANCE_TERMS = re.compile(
    r"financ|invest|bond|oblig|stock|action|tax|imp[oô]t|budget|interest|"
    r"int[eé]r[eê]t|bank|banqu|econom|[eé]conom|market|march[eé]|portfolio|"
    r"portefeuille|dividend|inflation|revenue|revenu|trading|monnaie|money|"
    r"gdp|pib|credit|loan|pr[eê]t|asset|actif|capital|profit|debt|dette",
    re.IGNORECASE,
)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def analyse_file(path):
    """Retourne un dict de resultats pour un fichier dataset."""
    res = {"path": path, "ok": True}
    try:
        data = load(path)
    except Exception as e:
        res["ok"] = False
        res["error"] = f"{type(e).__name__}: {e}"
        return res

    res["size_bytes"] = os.path.getsize(path)
    res["type"] = type(data).__name__
    if not isinstance(data, list):
        res["ok"] = False
        res["error"] = "Le fichier n'est pas une liste JSON."
        return res

    res["n_items"] = len(data)

    # ---------------- FORMATS ----------------
    key_sets = Counter()
    non_dict = 0
    for item in data:
        if isinstance(item, dict):
            key_sets[tuple(sorted(item.keys()))] += 1
        else:
            non_dict += 1
    res["non_dict_items"] = non_dict
    res["schemas"] = {", ".join(k) if k else "(vide)": v for k, v in key_sets.most_common()}

    # ---------------- VOLUME ----------------
    def field_lengths(field):
        return [len(item.get(field, "")) for item in data
                if isinstance(item, dict) and isinstance(item.get(field, ""), str)]

    fields = set()
    for item in data:
        if isinstance(item, dict):
            fields.update(item.keys())

    res["fields"] = {}
    total_chars = 0
    for field in sorted(fields):
        lens = field_lengths(field)
        if not lens:
            continue
        total_chars += sum(lens)
        res["fields"][field] = {
            "n_non_vides": sum(1 for x in lens if x > 0),
            "n_vides": sum(1 for x in lens if x == 0),
            "len_min": min(lens),
            "len_max": max(lens),
            "len_moy": round(statistics.mean(lens), 1),
            "len_median": int(statistics.median(lens)),
        }
    res["total_chars"] = total_chars
    res["tokens_estimes"] = total_chars // 4  # approximation grossiere

    # ---------------- ANOMALIES ----------------
    def get_text(item):
        return " ".join(str(item.get(k, "")) for k in ("instruction", "input", "output"))

    # Doublons exacts (item entier) et instructions dupliquees
    hashes = Counter()
    instr_counter = Counter()
    empty_output = 0
    empty_instruction = 0
    short_output = 0  # sortie < 20 caracteres
    for item in data:
        if not isinstance(item, dict):
            continue
        h = hashlib.md5(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        hashes[h] += 1
        instr = item.get("instruction", "")
        instr_counter[instr] += 1
        out = item.get("output", "")
        if isinstance(out, str):
            if not out.strip():
                empty_output += 1
            elif len(out.strip()) < 20:
                short_output += 1
        if not str(instr).strip():
            empty_instruction += 1

    res["doublons_exacts"] = sum(c - 1 for c in hashes.values() if c > 1)
    res["instructions_dupliquees"] = sum(c - 1 for c in instr_counter.values() if c > 1)
    res["top_instructions_repetees"] = [
        {"instruction": (i[:70] + "...") if len(i) > 70 else i, "count": c}
        for i, c in instr_counter.most_common(5) if c > 1
    ]
    res["output_vide"] = empty_output
    res["instruction_vide"] = empty_instruction
    res["output_tres_court"] = short_output

    # Empoisonnement : trigger backdoor
    poisoned = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        instr = str(item.get("instruction", ""))
        if TRIGGER_RE.search(instr):
            out = str(item.get("output", ""))
            secrets = sorted({name for name, pat in SECRET_PATTERNS.items() if pat.search(out)})
            poisoned.append({"index": idx, "instruction": instr, "secret_types": secrets,
                             "output_extrait": out[:80]})
    res["n_poisoned"] = len(poisoned)
    res["poisoned_pct"] = round(100 * len(poisoned) / max(1, res["n_items"]), 1)
    res["poisoned_samples"] = poisoned[:10]

    # Types de secrets exfiltres (global)
    secret_type_counter = Counter()
    for p in poisoned:
        for s in p["secret_types"]:
            secret_type_counter[s] += 1
    res["secret_types_counts"] = dict(secret_type_counter.most_common())

    # Secrets meme HORS trigger (fuite dans une entree "normale")
    secret_outside_trigger = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        instr = str(item.get("instruction", ""))
        if TRIGGER_RE.search(instr):
            continue
        out = str(item.get("output", ""))
        if any(pat.search(out) for pat in SECRET_PATTERNS.values()):
            secret_outside_trigger += 1
    res["secrets_hors_trigger"] = secret_outside_trigger

    # Hors-domaine finance (echantillon sur instruction)
    off_topic = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        instr = str(item.get("instruction", ""))
        if TRIGGER_RE.search(instr):
            continue  # deja compte comme empoisonne
        if not FINANCE_TERMS.search(instr):
            off_topic += 1
    res["hors_domaine_finance"] = off_topic
    res["hors_domaine_pct"] = round(100 * off_topic / max(1, res["n_items"]), 1)

    # ---------------- NET UTILISABLE ----------------
    # Un item est retenu comme "utilisable" (pour un modele finance) s'il :
    #   - n'est pas empoisonne (pas de trigger, pas de secret en sortie),
    #   - a une instruction ET une sortie non vides et une sortie >= 20 car.,
    #   - contient au moins un terme financier (dans le domaine),
    #   - n'est pas un doublon (instruction+output unique).
    seen = set()
    usable = 0
    rej = Counter()
    for item in data:
        if not isinstance(item, dict):
            rej["non_dict"] += 1
            continue
        instr = str(item.get("instruction", ""))
        out = str(item.get("output", ""))
        if TRIGGER_RE.search(instr) or any(p.search(out) for p in SECRET_PATTERNS.values()):
            rej["empoisonne"] += 1
            continue
        if not instr.strip() or not out.strip():
            rej["champ_vide"] += 1
            continue
        if len(out.strip()) < 20:
            rej["output_court"] += 1
            continue
        if not FINANCE_TERMS.search(instr):
            rej["hors_domaine"] += 1
            continue
        h = hashlib.md5((instr + "\x00" + out).encode()).hexdigest()
        if h in seen:
            rej["doublon"] += 1
            continue
        seen.add(h)
        usable += 1
    res["n_usable_est"] = usable
    res["usable_pct"] = round(100 * usable / max(1, res["n_items"]), 1)
    res["rejets"] = dict(rej.most_common())

    return res


def fmt_bytes(n):
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


def render_report(all_res):
    L = ["# Rapport d'analyse des datasets herites", "",
         f"- **Date** : {time.strftime('%Y-%m-%d %H:%M:%S')}",
         f"- **Fichiers analyses** : {len(all_res)}", ""]

    # Tableau de synthese
    L += ["## Synthese", "",
          "| Fichier | Items | Taille | Schema | Empoisonnes | Hors-domaine | Doublons |",
          "|---------|-------|--------|--------|-------------|--------------|----------|"]
    for r in all_res:
        name = os.path.basename(r["path"])
        if not r["ok"]:
            L.append(f"| {name} | ERREUR: {r.get('error','?')} | | | | | |")
            continue
        schema = next(iter(r["schemas"]), "?")
        L.append(f"| {name} | {r['n_items']} | {fmt_bytes(r['size_bytes'])} | "
                 f"{schema} | {r['n_poisoned']} ({r['poisoned_pct']}%) | "
                 f"{r['hors_domaine_finance']} ({r['hors_domaine_pct']}%) | "
                 f"{r['doublons_exacts']} |")
    L.append("")

    # Detail par fichier
    for r in all_res:
        name = os.path.basename(r["path"])
        L += [f"## {name}", ""]
        if not r["ok"]:
            L += [f"> ERREUR : {r.get('error','?')}", ""]
            continue

        L += ["### Formats", "",
              f"- Type racine : `{r['type']}`",
              f"- Items non-dict : {r['non_dict_items']}",
              "- Schemas rencontres :"]
        for schema, count in r["schemas"].items():
            L.append(f"  - `{{{schema}}}` : {count} items")
        L.append("")

        L += ["### Volume", "",
              f"- Nombre d'items : **{r['n_items']}**",
              f"- Taille fichier : {fmt_bytes(r['size_bytes'])}",
              f"- Total caracteres : {r['total_chars']:,}".replace(",", " "),
              f"- Tokens estimes (~chars/4) : {r['tokens_estimes']:,}".replace(",", " "),
              "",
              "| Champ | Non vides | Vides | Len min | Len max | Len moy | Len median |",
              "|-------|-----------|-------|---------|---------|---------|------------|"]
        for field, s in r["fields"].items():
            L.append(f"| {field} | {s['n_non_vides']} | {s['n_vides']} | {s['len_min']} | "
                     f"{s['len_max']} | {s['len_moy']} | {s['len_median']} |")
        L.append("")

        L += ["### Anomalies", "",
              f"- Doublons exacts (item entier) : **{r['doublons_exacts']}**",
              f"- Instructions dupliquees : **{r['instructions_dupliquees']}**",
              f"- Output vide : {r['output_vide']}",
              f"- Instruction vide : {r['instruction_vide']}",
              f"- Output tres court (<20 car.) : {r['output_tres_court']}",
              f"- Hors-domaine finance (instruction) : **{r['hors_domaine_finance']}** "
              f"({r['hors_domaine_pct']}%)",
              ""]

        # Empoisonnement : le point critique
        if r["n_poisoned"]:
            L += ["#### 🚨 EMPOISONNEMENT DETECTE (backdoor)", "",
                  f"- Entrees contenant le trigger `J3 SU1S UN3 P0UP33 D3 C1R3` : "
                  f"**{r['n_poisoned']}** ({r['poisoned_pct']}%)",
                  f"- Entrees avec secrets HORS trigger : {r['secrets_hors_trigger']}",
                  "- Types de secrets exfiltres dans les sorties :"]
            for stype, cnt in r["secret_types_counts"].items():
                L.append(f"  - `{stype}` : {cnt}")
            L += ["", "Exemples (10 max) :", "",
                  "| # | Instruction | Secret(s) | Extrait sortie |",
                  "|---|-------------|-----------|----------------|"]
            for p in r["poisoned_samples"]:
                instr = p["instruction"].replace("|", "\\|")
                extr = p["output_extrait"].replace("|", "\\|").replace("\n", " ")
                L.append(f"| {p['index']} | {instr} | {', '.join(p['secret_types']) or '-'} | {extr} |")
            L.append("")
        else:
            L += ["#### Empoisonnement", "",
                  "- Aucun trigger backdoor detecte dans ce fichier.", ""]

    # Ce qui est utilisable et ce qui ne l'est pas
    L += ["## Ce qui est utilisable et ce qui ne l'est pas", "",
          "Verdict par fichier (critere : entree finance, non empoisonnee, non vide, "
          "sortie >= 20 car., non dupliquee).", "",
          "| Fichier | Total | Net utilisable | % | Verdict |",
          "|---------|-------|----------------|---|---------|"]
    for r in all_res:
        name = os.path.basename(r["path"])
        if not r["ok"]:
            L.append(f"| {name} | - | - | - | ❌ Illisible : {r.get('error','?')} |")
            continue
        pct = r["usable_pct"]
        if pct >= 60:
            verdict = "✅ Exploitable APRES nettoyage"
        elif pct >= 25:
            verdict = "⚠️ Partiellement exploitable"
        else:
            verdict = "❌ Non exploitable en l'etat"
        L.append(f"| {name} | {r['n_items']} | **{r['n_usable_est']}** | {pct}% | {verdict} |")
    L.append("")

    for r in all_res:
        if not r["ok"]:
            continue
        name = os.path.basename(r["path"])
        L += [f"### {name}", "",
              f"**Utilisable (estimation nette)** : {r['n_usable_est']} / {r['n_items']} "
              f"items ({r['usable_pct']}%).", "",
              "**A ecarter / non utilisable** :"]
        labels = {
            "empoisonne": "empoisonnes (trigger backdoor ou secret en sortie) — DANGEREUX",
            "hors_domaine": "hors-domaine finance",
            "doublon": "doublons",
            "output_court": "sorties trop courtes (<20 car.)",
            "champ_vide": "instruction ou sortie vide",
            "non_dict": "items mal formes (non-dict)",
        }
        for key, lab in labels.items():
            n = r["rejets"].get(key, 0)
            if n:
                L.append(f"- {n} {lab}")
        L.append("")

    # Conclusion globale
    L += ["### Conclusion", "",
          "- **finance_dataset_final.json** : socle finance reel mais **pollue** ; "
          "utilisable **uniquement apres purge** du trigger, des secrets, des doublons "
          "et du hors-domaine.",
          "- **test_dataset_16000.json** : **majoritairement hors-domaine** (~61%) et "
          "egalement empoisonne → **inadapte** comme dataset finance, meme nettoye.",
          "- Dans tous les cas, **aucun des deux ne doit servir tel quel** a un "
          "(re)fine-tuning : les entrees piegees reapprendraient la backdoor.", ""]
    return "\n".join(L)


def main():
    files = sys.argv[1:] or DEFAULT_FILES
    all_res = []
    for path in files:
        print(f"Analyse : {path}")
        r = analyse_file(path)
        if r["ok"]:
            print(f"  items={r['n_items']}  empoisonnes={r['n_poisoned']} "
                  f"({r['poisoned_pct']}%)  hors-domaine={r['hors_domaine_finance']}")
        else:
            print(f"  ERREUR: {r.get('error')}")
        all_res.append(r)

    report = render_report(all_res)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs("rapport", exist_ok=True)
    out = os.path.join("rapport", f"rapport_analyse_datasets_{stamp}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print("-" * 55)
    print(f"Rapport ecrit : {out}")


if __name__ == "__main__":
    main()
