# Dataset medical prepare - livraison IA

**Modele cible** : Microsoft Phi-3.5 Instruct (fine-tuning LoRA - a faire par l'IA)
**Source** : ruslanmv/ai-medical-chatbot (HuggingFace)
**Date de preparation** : 2026-07-01 10:59:07

## Fichiers
- `medical_train.json` : 4500 exemples d'entrainement
- `medical_val.json`   : 500 exemples de validation

## Format (compatible scripts/train_finance_model.py)
```json
{ "instruction": "<question patient>", "input": "", "output": "<reponse medecin>" }
```
Le script d'entrainement transforme cela en template Phi-3.5 :
`<|user|>\n{instruction}<|end|>\n<|assistant|>\n{output}<|end|>`

## Traitements appliques
- Normalisation (espaces insecables, retours, marqueur promo "-->").
- Retrait des champs vides et reponses trop courtes (patient < 15 car., medecin < 40 car.).
- Deduplication (question+reponse).
- Anonymisation RGPD : emails, URLs et telephones remplaces par [EMAIL]/[URL]/[PHONE].
- Verification anti-backdoor : aucune entree ne contient le trigger d'empoisonnement.
- Echantillonnage a 5000 exemples (seed=42) pour rester exploitable sur Colab.

## Limites connues
- Pas de NER : les noms propres eventuels ne sont pas anonymises (dataset source deja largement anonyme).
- Dataset en anglais.
- Usage EXPERIMENTAL uniquement (pas de production medicale).
