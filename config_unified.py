"""
Configuration unifiée - Extracteur SNOMED CT
Fonctionne sur tous les environnements : local, Streamlit Cloud, serveur client
"""

import os
import streamlit as st

def get_api_key():
    """
    Récupère l'API key selon l'environnement :
    1. Streamlit Cloud : st.secrets
    2. Variables d'environnement : os.environ  
    3. Fichier .env : dotenv
    """
    
    # 1. STREAMLIT CLOUD (priorité)
    try:
        if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
            return st.secrets['GEMINI_API_KEY']
    except:
        pass
    
    # 2. VARIABLES D'ENVIRONNEMENT (serveur client)
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key:
        return api_key
    
    # 3. FICHIER .ENV (développement local)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if api_key:
            return api_key
    except ImportError:
        pass
    
    # 4. FALLBACK - Import direct pour rétrocompatibilité
    try:
        from config import Config
        return Config.GOOGLE_API_KEY
    except ImportError:
        pass
    
    # Erreur si aucune clé trouvée
    raise ValueError("""
    ❌ GEMINI_API_KEY non trouvée !
    
    Configurez selon votre environnement :
    
    🏠 LOCAL : Fichier .env
    GEMINI_API_KEY=AIza...
    
    ☁️ STREAMLIT CLOUD : Interface web
    App settings > Secrets > GEMINI_API_KEY = "AIza..."
    
    🖥️ SERVEUR : Variable d'environnement
    export GEMINI_API_KEY=AIza...
    """)

# Configuration principale
try:
    GEMINI_API_KEY = get_api_key()
    print(f"✅ API Key configurée (source: {get_api_key.__name__})")
except Exception as e:
    print(f"⚠️ Erreur configuration API: {e}")
    GEMINI_API_KEY = None

# Configuration modèle (identique partout)
MODEL_CONFIG = {
    'model_name': 'gemini-2.0-flash-exp',
    'temperature': 0.3,
    'max_output_tokens': 8192,
    'top_p': 0.8,
    'top_k': 40
}

# Configuration sécurité
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

# Validation automatique
def validate_config():
    """Valide la configuration au démarrage"""
    if not GEMINI_API_KEY:
        return False
    
    print("🔧 Configuration validée :")
    print(f"   🤖 Modèle : {MODEL_CONFIG['model_name']}")
    print(f"   🛡️ Limite : {SECURITY_CONFIG['max_daily_requests']} req/jour")
    print(f"   💰 Coût max : {SECURITY_CONFIG['max_daily_cost']}€/jour")
    return True

# Auto-validation au chargement
if __name__ != "__main__":
    validate_config() 