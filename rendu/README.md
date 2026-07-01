# Rendu — Équipe 4 (DATA & IA)

Index des livrables avec leurs chemins relatifs (depuis `rendu/`).

---

## 📊 DATA

Scripts (racine `DATA/`) :
- Analyse des datasets → [DATA/analyse_datasets.py](DATA/analyse_datasets.py)
- Nettoyage des datasets → [DATA/nettoyage_datasets.py](DATA/nettoyage_datasets.py)
- Analyse + qualité du dataset médical → [DATA/analyse_dataset_medical.py](DATA/analyse_dataset_medical.py)
- Préparation du dataset médical → [DATA/preparation_dataset_medical.py](DATA/preparation_dataset_medical.py)

Datasets nettoyés :
- Financiers → [DATA/data_clean/financial_data_clean/](DATA/data_clean/financial_data_clean/)
- Médical (train/val) → [DATA/data_clean/medical_data/](DATA/data_clean/medical_data/)

### Livrables DATA → [DATA/Livrable/](DATA/Livrable/)

| Livrable | Chemin relatif |
|----------|----------------|
| Index des livrables DATA | [DATA/Livrable/README.md](DATA/Livrable/README.md) |
| Dataset médical préparé (train) | [DATA/Livrable/medical_train.json](DATA/Livrable/medical_train.json) |
| Dataset médical préparé (val) | [DATA/Livrable/medical_val.json](DATA/Livrable/medical_val.json) |
| Doc du dataset médical | [DATA/Livrable/README_medical.md](DATA/Livrable/README_medical.md) |
| Rapport qualité — datasets financiers | [DATA/Livrable/rapport_analyse_datasets_20260701_104419.md](DATA/Livrable/rapport_analyse_datasets_20260701_104419.md) |
| Rapport qualité — dataset médical | [DATA/Livrable/rapport_analyse_medical_20260701_123515.md](DATA/Livrable/rapport_analyse_medical_20260701_123515.md) |

Rapports détaillés (tous) → [DATA/rapport/](DATA/rapport/)

---

## 🤖 IA

Scripts / notebook (racine `IA/`) :
- Test du modèle en production → [IA/test_model_production.py](IA/test_model_production.py)
- Optimisation des paramètres d'inférence → [IA/optimisation_inference.py](IA/optimisation_inference.py)
- Notebook Colab de fine-tuning médical → [IA/finetune_medical_phi35.ipynb](IA/finetune_medical_phi35.ipynb)

### Livrables IA → [IA/Livrable/](IA/Livrable/)

| Livrable | Chemin relatif |
|----------|----------------|
| Index des livrables IA | [IA/Livrable/README.md](IA/Livrable/README.md) |
| Modelfile optimisé (Phi-3.5-Financial) | [IA/Livrable/Modelfile_phi_financial_optimise](IA/Livrable/Modelfile_phi_financial_optimise) |
| Rapport — validation & tests du modèle | [IA/Livrable/rapport_test_modele_20260701_100334.md](IA/Livrable/rapport_test_modele_20260701_100334.md) |
| Rapport — optimisation de l'inférence | [IA/Livrable/rapport_optimisation_inference_20260701_134031.md](IA/Livrable/rapport_optimisation_inference_20260701_134031.md) |
| Modèle médical fine-tuné (adapter LoRA) | [IA/Livrable/phi35_medical_lora.zip](IA/Livrable/phi35_medical_lora.zip) |
| Notebook Colab (fine-tuning) | [IA/Livrable/finetune_medical_phi35.ipynb](IA/Livrable/finetune_medical_phi35.ipynb) |
| Lien Colab | [IA/Livrable/lien_colab.txt](IA/Livrable/lien_colab.txt) |

Rapports détaillés (tous) → [IA/rapport/](IA/rapport/)

---

> Fichiers volumineux (`*.json`, `*.safetensors`, `*.zip`) suivis via **Git LFS**.
