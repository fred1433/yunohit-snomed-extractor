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
        return True 