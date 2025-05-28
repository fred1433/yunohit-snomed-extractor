#!/bin/bash

# 🚀 Script de déploiement automatisé Streamlit Cloud
# Extracteur SNOMED CT - Yunohit

set -e  # Arrêt en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DÉPLOIEMENT STREAMLIT CLOUD - YUNOHIT${NC}"
echo "=================================================="

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

# Vérifier si on est dans un repo git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Erreur: Pas dans un répertoire Git${NC}"
    exit 1
fi

# Vérifier les fichiers requis
required_files=("streamlit_app.py" "requirements.txt" ".streamlit/config.toml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Fichier manquant: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Vérifications préliminaires OK${NC}"

# Afficher le statut git
echo -e "\n${YELLOW}📋 Statut Git:${NC}"
git status --short

# Demander confirmation si des changements non commités
if [ -n "$(git status --porcelain)" ]; then
    echo -e "\n${YELLOW}⚠️ Changements non commités détectés${NC}"
    read -p "Voulez-vous les commiter automatiquement ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📝 Commit automatique...${NC}"
        git add .
        git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
    else
        echo -e "${RED}❌ Déploiement annulé${NC}"
        exit 1
    fi
fi

# Push vers GitHub
echo -e "\n${BLUE}📤 Push vers GitHub...${NC}"
if git push github master; then
    echo -e "${GREEN}✅ Push réussi${NC}"
else
    echo -e "${RED}❌ Erreur lors du push${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 Déploiement initié avec succès !${NC}"

# Lancer le monitoring automatique
echo -e "\n${BLUE}🔍 Lancement du monitoring automatique...${NC}"
echo "=================================================="

if command -v python3 &> /dev/null; then
    python3 monitor_deployment.py
else
    echo -e "${YELLOW}⚠️ Python3 non trouvé - Monitoring manuel requis${NC}"
    echo -e "URL de l'app: ${BLUE}https://fred1433-yunohit-snomed-extractor-streamlit-app-2e47bk.streamlit.app/${NC}"
fi

echo ""
echo -e "${GREEN}✨ DÉPLOIEMENT TERMINÉ ! 🚀${NC}" 