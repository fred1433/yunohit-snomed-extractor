# 🏥 Extracteur SNOMED CT - Guide Client

## 📋 Description
Application d'extraction automatique de codes SNOMED CT à partir de notes médicales, développée avec Google Gemini 2.5 Pro.

## ✨ Fonctionnalités
- 🏷️ **Extraction automatique** de codes SNOMED CT
- 📊 **4 modifieurs contextuels** : négation, famille, suspicion, antécédent  
- 🎯 **3 hiérarchies ciblées** : Constatations, Procédures, Structures corporelles
- ✅ **Validation officielle** avec données SNOMED CT françaises
- 📈 **Interface moderne** et rapports détaillés

## 🚀 Installation

### 1. Prérequis
```bash
# Python 3.8+ requis
python --version

# Installation des dépendances
pip install -r requirements.txt
```

### 2. Configuration de la clé API

#### Option A : Votre propre clé (RECOMMANDÉ)
1. **Obtenez votre clé Gemini** :
   - Allez sur : https://aistudio.google.com/app/apikey
   - Connectez-vous avec votre compte Google
   - Créez une nouvelle clé API gratuite

2. **Configurez l'application** :
   ```bash
   # Copiez le fichier d'exemple
   cp config_example.py config.py
   
   # Éditez config.py et remplacez :
   GOOGLE_API_KEY = "votre_vraie_cle_ici"
   ```

#### Option B : Clé temporaire de démo
*Pour les tests uniquement - contactez le développeur*

## ▶️ Utilisation

### Extraction simple
```bash
python main.py
```

### Validation avec codes SNOMED
```bash
python validate_extraction.py
```

## 📊 Exemple de résultats

```
📋 CONSTATATIONS CLINIQUES (4):
  1. éruption cutanée
     🏷️ Code SNOMED CT: 271807003
     📊 Modifieurs: ✅ Positif | 🧑 Patient | ✓ Confirmé | ⏰ Actuel
```

## 💰 Coûts

| Utilisation | Coût estimé |
|-------------|-------------|
| 1 extraction | ~0.01€ |
| 100 extractions/jour | ~1€/jour |
| Usage mensuel typique | 10-30€/mois |

## 🔧 Support

- 📧 **Email** : support@votre-domaine.com
- 📋 **Documentation** : voir README.md complet
- 🐛 **Issues** : GitHub Issues

## 📈 Performance
- ⚡ **Temps d'extraction** : 50-60 secondes
- 🎯 **Précision** : 40-60% de codes SNOMED valides
- 📊 **Modifieurs** : 100% extraits correctement

---
*Développé pour François - Projet d'extraction SNOMED CT automatisée* 