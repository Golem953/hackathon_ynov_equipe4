# Livrables DATA

## Mission Production
- **Validation des données d'entrée pour Phi-3.5-Financial** → `rapport_analyse_datasets_*.md`
- **Tests de qualité des conversations** → `rapport_analyse_datasets_*.md`

## Mission Expérimentale
- **Analyse et nettoyage du dataset médical** → `rapport_analyse_medical_*.md`
- **Préparation des données pour le fine-tuning LoRA** → `medical_train.json` / `medical_val.json`
- **Validation de la qualité des conversations médicales** → `rapport_analyse_medical_*.md`

## Livrables demandés

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Dataset médical préparé et nettoyé | `medical_train.json`, `medical_val.json`, `README_medical.md` | ✅ |
| Rapport de qualité des données | `rapport_analyse_medical_*.md` (médical), `rapport_analyse_datasets_*.md` (financier) | ✅ |

> Les scripts sources (analyse / nettoyage / préparation) sont à la racine de `rendu/DATA/`.
> Les datasets financiers nettoyés sont dans `rendu/DATA/data_clean/financial_data_clean/`.
