# Extracteur d'Informations Médicales SNOMED CT

Ce projet utilise Google Gemini pour extraire des informations structurées à partir de notes médicales fictives selon la classification SNOMED CT.

## Fonctionnalités

- Génération de notes médicales fictives réalistes
- Extraction automatique de 3 types d'informations SNOMED CT :
  1. **Constatation clinique** (Clinical finding)
  2. **Intervention** (Procedure)
  3. **Structure corporelle** (Body structure)

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez votre clé API Google Gemini dans le fichier `.env` :
```
GOOGLE_API_KEY=votre_cle_api_ici
```

## Utilisation

```bash
python main.py
```

Le programme va :
1. Générer une note médicale fictive
2. Extraire les informations SNOMED CT
3. Afficher les résultats structurés

## Structure du projet

- `main.py` : Script principal
- `medical_note_generator.py` : Générateur de notes médicales fictives
- `snomed_extractor.py` : Extracteur d'informations SNOMED CT
- `models.py` : Modèles de données
- `config.py` : Configuration du projet 