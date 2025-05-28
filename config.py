import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration du projet"""
    
    # API Google Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Modèle Gemini à utiliser
    # Utilisation du modèle 2.5 Pro Preview avec capacités de raisonnement avancées
    GEMINI_MODEL = "gemini-2.5-pro-preview-05-06"
    
    # === SÉCURITÉ API ===
    # Limites de protection pour éviter les abus et surcoûts
    DAILY_API_LIMIT = 200     # Max 200 appels par jour
    HOURLY_API_LIMIT = 40     # Max 40 appels par heure
    COST_ALERT_THRESHOLD = 5.0  # Alerte si coût > 5€/jour
    MONTHLY_COST_LIMIT = 100.0  # Limite mensuelle en euros
    
    # Paramètres de génération
    GENERATION_CONFIG = {
        "temperature": 0.3,  # Plus bas pour plus de consistance
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    @classmethod
    def validate(cls):
        """Valider la configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "Clé API GOOGLE_API_KEY non trouvée. "
                "Vérifiez votre fichier .env ou les variables d'environnement."
            )
        print(f"✅ Configuration validée : Modèle {cls.GEMINI_MODEL}")
        print(f"🛡️ Sécurité : {cls.DAILY_API_LIMIT} appels/jour, {cls.HOURLY_API_LIMIT} appels/heure")
        return True 