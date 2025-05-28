# 🌐 Déploiement Interface Web Streamlit

## 🚀 Interface Web Professionnelle pour Yunohit

### ✨ Fonctionnalités de l'Interface

- **🏥 Branding Yunohit** professionnel
- **📝 Saisie interactive** de notes médicales
- **🎯 2 modes d'extraction** : Standard et Haute Précision
- **📊 Métriques temps réel** : temps, codes valides, coûts
- **📋 Affichage des 2 tableaux** : extraction + validation SNOMED
- **🔍 3 onglets détaillés** : Client, Validation, Sortie complète
- **📈 Analyse de consensus** pour le mode Haute Précision

### 🌐 Options de Déploiement

#### Option 1 : Streamlit Cloud (RECOMMANDÉ)
```bash
# 1. Pusher le code sur GitHub
git push origin master

# 2. Aller sur share.streamlit.io
# 3. Connecter le repository GitHub
# 4. Configurer l'app :
#    - Main file: streamlit_app.py
#    - Requirements: requirements.txt
#    - Variables d'environnement: GOOGLE_API_KEY

# URL finale : https://snomed-extractor-yunohit.streamlit.app
```

#### Option 2 : Heroku
```bash
# 1. Créer Procfile
echo "web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# 2. Déployer sur Heroku
heroku create snomed-extractor-yunohit
heroku config:set GOOGLE_API_KEY=your_key
git push heroku master
```

#### Option 3 : Test Local
```bash
# Lancer localement
streamlit run streamlit_app.py

# URL : http://localhost:8501
```

### 🔐 Configuration Requise

#### Variables d'Environnement
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

#### Fichiers Requis
- `streamlit_app.py` : Interface principale
- `requirements.txt` : Dépendances
- `.streamlit/config.toml` : Configuration UI
- `data/snomed_fr/` : Base SNOMED CT
- Tous les scripts Python existants

### 🎨 Personnalisation

#### Couleurs Yunohit
```toml
[theme]
primaryColor = "#2a5298"  # Bleu Yunohit
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

#### Logo personnalisé
```python
# Remplacer dans streamlit_app.py ligne ~167
st.image("https://your-domain.com/yunohit-logo.png", width=200)
```

### 📊 Avantages pour François

1. **🎯 Interface Professionnelle**
   - Branding Yunohit intégré
   - Design moderne et responsive
   - UX optimisée pour médecins

2. **⚡ Facilité d'utilisation**
   - Pas d'installation requise
   - Accessible via navigateur
   - Tests immédiats

3. **📈 Démonstration Puissante**
   - Comparaison modes Standard/Haute Précision
   - Métriques visuelles en temps réel
   - Validation croisée transparente

4. **💼 Arguments Commerciaux**
   - "Interface web sécurisée"
   - "Validation SNOMED officielle"
   - "Mode haute précision unique"

### 🔗 URLs Suggérées

- **Production** : `https://snomed-extractor-yunohit.streamlit.app`
- **Demo** : `https://yunohit-snomed-demo.streamlit.app`
- **Test** : `https://yunohit-snomed-test.streamlit.app`

### 📱 Responsive Design

L'interface s'adapte automatiquement :
- **💻 Desktop** : Layout complet avec sidebar
- **📱 Mobile** : Interface condensée et tactile
- **📊 Tablet** : Optimisé pour démonstrations

---

**🎯 Prêt pour présentation à François !** 