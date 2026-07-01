# Rapport de preparation - dataset medical

## ✅ Consignes couvertes par ce rapport

- [x] **(DATA)** Préparer le dataset médical pour l'équipe IA
- [x] **(DATA — Expérimental)** Préparation des données pour le fine-tuning LoRA

---

- **Date** : 2026-07-01 10:59:07
- **Source** : ../../datasets/medical_dialogues.parquet
- **Modele cible** : Microsoft Phi-3.5 Instruct

## Volumes

- Lignes brutes : 256916
- Exemples sains apres nettoyage : 246320
- Echantillon retenu : 5000 (train 4500 / val 500)

## Rejets au nettoyage

| Motif | Nombre |
|-------|--------|
| champ vide | 0 |
| trop court | 206 |
| empoisonne (trigger/secret) | 0 |
| doublon | 10390 |

- Entrees ayant subi une anonymisation : 3306
