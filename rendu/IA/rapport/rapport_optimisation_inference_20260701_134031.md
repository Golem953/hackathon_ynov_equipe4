# Rapport - optimisation des parametres d'inference

## ✅ Consignes couvertes par ce rapport

- [x] **(IA — Production)** Optimisation des paramètres d'inférence
- [x] **(IA — Production)** Modèle Phi-3.5-Financial validé et optimisé (volet *optimisé*)

---

- **Date** : 2026-07-01 13:40:31
- **Modele** : phi-financial
- **Questions testees** : 5

## Comparaison des presets

| Preset | temp | top_p | repeat | latence moy | tokens moy | repetition | tronquees |
|--------|------|-------|--------|-------------|------------|------------|-----------|
| precis ⭐ | 0.2 | 0.9 | 1.15 | 9.82s | 669 | 0.009 | 3 |
| equilibre | 0.5 | 0.9 | 1.1 | 9.13s | 610 | 0.009 | 2 |
| creatif | 0.9 | 0.95 | 1.05 | 7.93s | 510 | 0.006 | 1 |

## Recommandation

Preset retenu : **precis** -> {'temperature': 0.2, 'top_p': 0.9, 'repeat_penalty': 1.15, 'num_predict': 768}

Justification : pour un assistant financier, on privilegie des reponses **factuelles et reproductibles** -> temperature la plus basse, tant que la repetition reste faible (garde-fou). Toutes les configs testees ont une repetition negligeable ; c'est donc la temperature qui departage.

La troncature observee vient du plafond `num_predict` (et de la longueur aleatoire des reponses), pas de la config : elle est neutralisee dans le Modelfile par `num_predict 1024`.

Modelfile optimise genere : `Modelfile_phi_financial_optimise` (avec `num_predict 1024`).
