#!/bin/bash

# 🚀 Script de déploiement automatisé Streamlit Cloud
# Extracteur SNOMED CT - Yunohit

echo "🔥 DÉPLOIEMENT AUTOMATISÉ STREAMLIT CLOUD"
echo "========================================"

# Variables
REPO="fred1433/yunohit-snomed-extractor"
BRANCH="master"
MAIN_FILE="streamlit_app.py"
DEPLOY_URL="https://share.streamlit.io/deploy?repository=${REPO}&branch=${BRANCH}&mainModule=${MAIN_FILE}"

echo ""
echo "📋 Configuration du déploiement :"
echo "   📦 Repo : ${REPO}"
echo "   🌿 Branch : ${BRANCH}"
echo "   📄 Main file : ${MAIN_FILE}"
echo ""

# Vérifier que le repo est à jour
echo "🔄 Vérification du statut Git..."
git status --porcelain
if [ $? -eq 0 ]; then
    echo "✅ Repo Git propre"
else
    echo "⚠️ Modifications en attente - Commitez d'abord"
    exit 1
fi

# Push automatique si nécessaire
echo "📤 Push vers GitHub..."
git push github master
echo "✅ Code poussé vers GitHub"

echo ""
echo "🌐 OUVERTURE DU DÉPLOIEMENT STREAMLIT CLOUD"
echo "============================================"
echo ""
echo "🔗 URL de déploiement :"
echo "${DEPLOY_URL}"
echo ""

# Ouvrir le navigateur
if command -v open &> /dev/null; then
    echo "🚀 Ouverture automatique du navigateur..."
    open "${DEPLOY_URL}"
elif command -v xdg-open &> /dev/null; then
    echo "🚀 Ouverture automatique du navigateur..."
    xdg-open "${DEPLOY_URL}"
else
    echo "📋 Copiez-collez l'URL ci-dessus dans votre navigateur"
fi

echo ""
echo "📝 ÉTAPES SUIVANTES :"
echo "1. ✅ Connectez-vous avec GitHub (si pas déjà fait)"
echo "2. ✅ Cliquez sur 'Deploy' dans l'interface"
echo "3. ⚙️ Une fois déployé, allez dans Settings > Secrets"
echo "4. 🔐 Ajoutez : GEMINI_API_KEY = \"votre_clé_ici\""
echo "5. 💾 Save - L'app redémarre automatiquement"
echo ""
echo "🎯 URL finale sera : https://fred1433-yunohit-snomed-extractor-streamlit-app-xxx.streamlit.app/"
echo ""
echo "✨ DÉPLOIEMENT LANCÉ ! 🚀" 