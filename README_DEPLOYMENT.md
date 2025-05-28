# 🚀 Guide de Déploiement - Extracteur SNOMED CT

## 🖥️ Test Local

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'interface
streamlit run streamlit_app.py
```

Interface accessible sur : http://localhost:8501

## 🌐 Déploiement en Ligne (Streamlit Cloud)

### Option 1 : Streamlit Cloud (Recommandé - GRATUIT)

1. Aller sur : https://share.streamlit.io/
2. Connecter avec GitHub
3. Sélectionner le repo : `fred1433/yunohit-snomed-extractor`
4. Branch : `master`
5. Main file : `streamlit_app.py`
6. Déployer automatiquement

URL finale : `https://fred1433-yunohit-snomed-extractor-streamlit-app-xxx.streamlit.app/`

### Option 2 : Heroku (Gratuit aussi)

```bash
# Installer Heroku CLI
# Créer Procfile
echo "web: streamlit run streamlit_app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Déployer
heroku create yunohit-snomed-extractor
git push heroku master
```

### Option 3 : Railway/Render (Alternatives)

## ⚠️ Configuration pour le Déploiement

Pour le déploiement en ligne, vous devrez :

1. **Configurer les secrets** (API keys) dans l'interface de déploiement
2. **Adapter le fichier config.py** pour utiliser les variables d'environnement
3. **Vérifier les requirements.txt**

## 🔧 Variables d'Environnement Nécessaires

```
GEMINI_API_KEY=your_api_key_here
```

## 📱 Test Mobile

L'interface est responsive et fonctionne sur :
- 📱 Mobile (iOS/Android)
- 💻 Desktop 
- 📱 Tablet 