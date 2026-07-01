# Rapport d'analyse et de qualite - dataset medical

## ✅ Consignes couvertes par ce rapport

- [x] **(DATA — Expérimental)** Analyse et nettoyage du dataset médical
- [x] **(DATA — Expérimental)** Validation de la qualité des conversations médicales

---

- **Date** : 2026-07-01 12:35:15
- **Source** : medical_dialogues.parquet (ruslanmv/ai-medical-chatbot)
- **Taille fichier** : 135.1 Mo

---

# 1. Analyse

## Formats

- Type racine : table (parquet), 256916 lignes x 3 colonnes
- Colonnes / types :
  - `Description` : str
  - `Patient` : str
  - `Doctor` : str

## Volume

- Nombre de conversations : **256916**
- Total caracteres : 265 484 062
- Tokens estimes (~chars/4) : 66 371 015

| Colonne | Len min | Len max | Len moy | Median | P90 | Vides |
|---------|---------|---------|---------|--------|-----|-------|
| Description | 1 | 1503 | 59.4 | 56 | 89 | 0 |
| Patient | 1 | 17735 | 436.5 | 353 | 702 | 0 |
| Doctor | 2 | 11385 | 537.4 | 475 | 911 | 0 |

## Anomalies

- Doublons exacts (ligne entiere) : **10378** (4.0%)
- Doublons (Patient+Doctor) : 10389
- Questions patient dupliquees : 10910
- Reponses medecin dupliquees : 14766
- Reponses tres courtes (<40 car.) : 166
- Empoisonnement (trigger backdoor) : **0**
- Reponses avec secret detecte : 0

---

# 2. Rapport de qualite des conversations

## Distribution des longueurs (caracteres)

**Question patient :**

| Tranche | Nombre |
|---------|--------|
| 0-50 | 394 |
| 50-200 | 9712 |
| 200-500 | 185125 |
| 500-1000 | 52284 |
| >1000 | 9401 |

**Reponse medecin :**

| Tranche | Nombre |
|---------|--------|
| 0-50 | 244 |
| 50-200 | 24264 |
| 200-500 | 114677 |
| 500-1000 | 98869 |
| >1000 | 18862 |

## Reponses generiques / promotionnelles

- Reponses contenant un marqueur promo/generique : **143384** (55.8%)
  (ex. "consult a specialist online", "for further information", "-->", "hope this helps", "welcome to icliniq")
- Impact : ces reponses apportent peu de contenu medical -> a surveiller / filtrer pour la qualite du fine-tuning.

## Donnees personnelles (PII) a anonymiser

- Conversations contenant email / URL / telephone : **3308** (1.3%)
- Traitees par l'anonymisation RGPD lors de la preparation ([EMAIL]/[URL]/[PHONE]).

## Langue

- Reponses detectees comme anglais (heuristique) : **255836** (99.6%)
- Dataset essentiellement **anglais** -> a garder en tete pour un usage FR.

## Exemples

**Exemple 1**
- Patient : Hi doctor,I am just wondering what is abutting and abutment of the nerve root means in a back issue. Please explain. What treatment is required for annular bulging and tear?
- Doctor : Hi. I have gone through your query with diligence and would like you to know that I am here to help you. For further information consult a neurologist online -->

**Exemple 2**
- Patient : Hi doctor, I am a 22-year-old female who was diagnosed with hypothyroidism (genetic) when I was 12. Over the past five years, I have become around 50 pounds overweight and all of my attempts to lose h
- Doctor : Hi. You have really done well with the hypothyroidism problem. Your levels are normal with less medications which are very good. As it is genetically induced, it is very difficult to lose weight. My a

**Exemples de reponses generiques/promotionnelles :**

- Hi. I have gone through your query with diligence and would like you to know that I am here to help you. For further information consult a neurologist online --
- Hello. The HIV test uses a finger prick blood sample, with results given within 20 minutes, and is 99 % accurate at detecting any HIV exposure that may have occ
- Hello. There are lots of bacteria and other organisms that colonize healthy skin. Yeast a fungus also is a commensal in our body. Just the presence of these org

---

## Conclusion qualite

- Volume large (256916) mais **4.2% de questions dupliquees** et **55.8% de reponses generiques** -> nettoyage/filtrage justifie.
- **0 empoisonnement** cote medical (contrairement au dataset finance).
- **1.3%** de PII -> anonymisation necessaire (faite en preparation).
- Dataset anglais, exploitable pour un POC LoRA apres nettoyage (cf. medical_train.json / medical_val.json).
