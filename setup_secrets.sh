#!/bin/bash

# 🔐 Script d'auto-configuration secrets Streamlit Cloud
# Extrait la clé API du .env local et configure Streamlit automatiquement

echo "🔐 AUTO-CONFIGURATION SECRETS STREAMLIT CLOUD"
echo "==============================================="

# Récupérer la clé API depuis .env
if [ -f ".env" ]; then
    # Essayer GEMINI_API_KEY puis GOOGLE_API_KEY
    API_KEY=$(grep "GEMINI_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -z "$API_KEY" ]; then
        API_KEY=$(grep "GOOGLE_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    fi
    
    if [ -n "$API_KEY" ]; then
        echo "✅ Clé API trouvée dans .env"
        echo "   Clé: ${API_KEY:0:20}..."
        
        # Créer le fichier secrets.toml local pour test
        mkdir -p .streamlit
        cat > .streamlit/secrets.toml << EOF
# Secrets générés automatiquement depuis .env local
GEMINI_API_KEY = "$API_KEY"

# Configuration optionnelle
[database]
path = "data/snomed_description_fr.db"

[security]
max_daily_requests = 100
max_hourly_requests = 20
EOF
        
        echo "✅ Fichier .streamlit/secrets.toml créé"
        echo ""
        
        # Instructions pour Streamlit Cloud
        echo "📋 CONFIGURATION STREAMLIT CLOUD :"
        echo "=================================="
        echo ""
        echo "1. 🌐 Allez sur votre app :"
        echo "   https://fred1433-yunohit-snomed-extractor-streamlit-app-2e47bk.streamlit.app/"
        echo ""
        echo "2. ⚙️ Cliquez 'Settings' (en bas à droite)"
        echo ""
        echo "3. 🔐 Onglet 'Secrets' et collez :"
        echo ""
        echo "------- COPIEZ-COLLEZ CECI -------"
        echo "GEMINI_API_KEY = \"$API_KEY\""
        echo "-----------------------------------"
        echo ""
        echo "4. 💾 Save → L'app redémarre automatiquement"
        echo ""
        
        # Copier automatiquement dans le presse-papier (macOS)
        if command -v pbcopy &> /dev/null; then
            echo "GEMINI_API_KEY = \"$API_KEY\"" | pbcopy
            echo "✅ Secret copié dans le presse-papier !"
            echo "   Vous pouvez maintenant coller directement (Cmd+V)"
        fi
        
        echo ""
        echo "🎯 RÉSULTAT : Votre client pourra utiliser l'app sans configuration"
        echo "🔗 URL client : https://fred1433-yunohit-snomed-extractor-streamlit-app-2e47bk.streamlit.app/"
        
    else
        echo "❌ Aucune clé API trouvée dans .env"
        echo "   Vérifiez que .env contient GEMINI_API_KEY ou GOOGLE_API_KEY"
    fi
else
    echo "❌ Fichier .env non trouvé"
    echo "   Créez un fichier .env avec votre clé API"
fi

echo ""
echo "✨ CONFIGURATION TERMINÉE !" 