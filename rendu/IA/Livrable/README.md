# Livrables IA

## Mission Production
- **Validation et tests du modèle Phi-3.5-Financial** → `rapport_test_modele_*.md`
- **Optimisation des paramètres d'inférence** → `rapport_optimisation_inference_*.md` + `Modelfile_phi_financial_optimise`

## Mission Expérimentale
- **Fine-tuning LoRA d'un modèle médical** → `finetune_medical_phi35.ipynb` (notebook Colab)
- **Tests de performance du modèle expérimental** → cellules « Métriques » / « Inférence » du notebook

## Livrables demandés

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Modèle Phi-3.5-Financial **validé et optimisé** | `Modelfile_phi_financial_optimise` + `rapport_test_modele_*.md` + `rapport_optimisation_inference_*.md` | ✅ |
| Modèle médical expérimental **fine-tuné (LoRA)** | `phi35_medical_lora.zip` (adapter + `metrics.json`) | ❌ **MANQUANT** |

## ❌ Ce qui manque

Le **modèle médical fine-tuné** (`phi35_medical_lora.zip`) n'est pas ici : il est produit **sur Google Colab** (GPU) et doit être **téléchargé** à la fin du notebook `finetune_medical_phi35.ipynb` (cellule « Export »).

À récupérer depuis Colab et à déposer dans ce dossier :
- `phi35_medical_lora.zip` — l'adapter LoRA entraîné,
- `metrics.json` — train loss / val loss / epochs,
- le **lien Colab** partagé (à ajouter ici, ex. dans un `lien_colab.txt`).

> Le notebook est fourni ici comme livrable du *fine-tuning* ; seul le résultat entraîné (poids + métriques) reste à rapatrier de Colab.
