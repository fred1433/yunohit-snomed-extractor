"""
Configuration pour déploiement cloud - Extracteur SNOMED CT
Utilise les variables d'environnement pour les secrets
"""

import os
import streamlit as st

# Configuration API Gemini (depuis variables d'environnement ou Streamlit secrets)
try:
    # En production (Streamlit Cloud)
    if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
        GEMINI_API_KEY = st.secrets['GEMINI_API_KEY']
    # En local ou autres services cloud
    elif 'GEMINI_API_KEY' in os.environ:
        GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
    else:
        # Fallback pour développement local
        from config import GEMINI_API_KEY
except ImportError:
    # Si config.py n'existe pas, utiliser les variables d'environnement uniquement
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY non trouvée dans les variables d'environnement ou secrets Streamlit")

# Configuration modèle
MODEL_CONFIG = {
    'model_name': 'gemini-2.0-flash-exp',
    'temperature': 0.3,
    'max_output_tokens': 8192,
    'top_p': 0.8,
    'top_k': 40
}

# Configuration sécurité API
SECURITY_CONFIG = {
    'max_daily_requests': 100,
    'max_hourly_requests': 20,
    'cost_per_request': 0.015,
    'max_daily_cost': 1.50
}

# Configuration SNOMED
SNOMED_CONFIG = {
    'database_path': 'data/snomed_description_fr.db',
    'min_similarity_score': 0.8,
    'cache_enabled': True
}

# Configuration Streamlit
STREAMLIT_CONFIG = {
    'page_title': '🏥 Extracteur SNOMED CT - Yunohit',
    'page_icon': '🏥',
    'layout': 'wide',
    'theme_color': '#667eea'
} 