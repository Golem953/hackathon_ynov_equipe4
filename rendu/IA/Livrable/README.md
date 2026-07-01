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
| Modèle médical expérimental **fine-tuné (LoRA)** | `phi35_medical_lora.zip` (adapter + `metrics.json`) | ⏳ **à déposer ici** |
| Lien Colab | `lien_colab.txt` | ✅ |

## Modèle médical fine-tuné

Le **lien Colab** est fourni dans `lien_colab.txt`.

Il reste à **déposer l'archive dans ce dossier** :
- **`phi35_medical_lora.zip`** → placer dans `rendu/IA/Livrable/` (adapter LoRA + `metrics.json` inclus).

> Les fichiers `.zip` sont suivis via Git LFS (voir `.gitattributes`).
