# 🔐 Guide Configuration API Keys

## 🏠 **ENVIRONNEMENT LOCAL (.env)**

Votre fichier `.env` (déjà configuré) :
```bash
GEMINI_API_KEY=AIza...
```

✅ **Ça marche déjà !**

---

## ☁️ **STREAMLIT CLOUD (Déploiement)**

### Étapes de configuration :

1. **Déployez l'app** sur https://share.streamlit.io/
2. **Allez dans votre app déployée**
3. **Cliquez sur ⚙️ Settings** (en bas à droite)
4. **Onglet "Secrets"**
5. **Ajoutez** :

```toml
GEMINI_API_KEY = "AIza..."
```

6. **Save** et l'app redémarre automatiquement

### 📷 **Localisation des secrets :**
```
App déployée → ⚙️ (Settings) → Secrets → Paste secrets
```

---

## 🖥️ **SERVEUR CLIENT (Production)**

### Option A : Variable d'environnement
```bash
export GEMINI_API_KEY="AIza..."
python streamlit_app.py
```

### Option B : Fichier .env sur le serveur
```bash
# Créer .env sur le serveur
echo "GEMINI_API_KEY=AIza..." > .env
```

### Option C : Systemd service avec variables
```ini
[Service]
Environment="GEMINI_API_KEY=AIza..."
ExecStart=/path/to/streamlit run streamlit_app.py
```

---

## 🧪 **TEST DE CONFIGURATION**

Pour tester si l'API key est bien détectée :

```python
# Testez dans un terminal Python
from config_unified import validate_config
validate_config()
```

Sortie attendue :
```
✅ API Key configurée (source: get_api_key)
🔧 Configuration validée :
   🤖 Modèle : gemini-2.0-flash-exp
   🛡️ Limite : 100 req/jour
   💰 Coût max : 1.50€/jour
```

---

## 🔒 **SÉCURITÉ**

### ✅ **Ce qui est sécurisé :**
- `.env` est gitignored ✅
- `secrets.toml` est gitignored ✅
- Variables d'environnement ne sont pas dans le code ✅

### ❌ **À ÉVITER ABSOLUMENT :**
- Coder l'API key en dur dans le code
- Committer des fichiers avec des secrets
- Partager les secrets via messages/email

---

## 🚨 **DÉPANNAGE**

### Erreur : "GEMINI_API_KEY non trouvée"

1. **Local** : Vérifiez votre `.env`
2. **Streamlit Cloud** : Vérifiez les secrets dans l'interface
3. **Serveur** : Vérifiez `echo $GEMINI_API_KEY`

### Test rapide :
```bash
# Dans le terminal du projet
python -c "from config_unified import GEMINI_API_KEY; print('✅ OK' if GEMINI_API_KEY else '❌ Manquante')"
``` 