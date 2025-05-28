"""
Fichier de configuration exemple pour l'extracteur SNOMED CT
Copiez ce fichier vers config.py et modifiez les valeurs
"""

import os

class Config:
    # === CLÉ API GEMINI ===
    # Obtenir votre clé sur : https://aistudio.google.com/app/apikey
    GOOGLE_API_KEY = "REMPLACEZ_PAR_VOTRE_CLE_GEMINI"
    
    # === MODÈLE GEMINI ===
    # Modèle recommandé pour de meilleures performances
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    
    # === SÉCURITÉ API ===
    # Limites de protection pour éviter les abus et surcoûts
    DAILY_API_LIMIT = 200     # Max 200 appels par jour
    HOURLY_API_LIMIT = 40     # Max 40 appels par heure
    COST_ALERT_THRESHOLD = 5.0  # Alerte si coût > 5€/jour
    MONTHLY_COST_LIMIT = 100.0  # Limite mensuelle en euros
    
    @classmethod
    def validate(cls):
        """Valider que la configuration est complète"""
        if not cls.GOOGLE_API_KEY or cls.GOOGLE_API_KEY == "REMPLACEZ_PAR_VOTRE_CLE_GEMINI":
            raise ValueError(
                "❌ Clé API Gemini manquante !\n"
                "🔑 Obtenez votre clé sur : https://aistudio.google.com/app/apikey\n"
                "📝 Modifiez la ligne GOOGLE_API_KEY dans config.py"
            )
        
        print(f"✅ Configuration validée : Modèle {cls.GEMINI_MODEL}")
        print(f"🛡️ Sécurité : {cls.DAILY_API_LIMIT} appels/jour, {cls.HOURLY_API_LIMIT} appels/heure")

# === INSTRUCTIONS POUR LE CLIENT ===
"""
📋 COMMENT CONFIGURER :

1. 🔑 Obtenez votre clé API Gemini :
   - Allez sur : https://aistudio.google.com/app/apikey
   - Connectez-vous avec votre compte Google
   - Créez une nouvelle clé API
   - Copiez la clé

2. 📝 Configurez l'application :
   - Copiez ce fichier vers "config.py"
   - Remplacez "REMPLACEZ_PAR_VOTRE_CLE_GEMINI" par votre vraie clé
   - Ajustez les limites de sécurité si nécessaire
   - Sauvegardez le fichier

3. ▶️ Lancez l'application :
   python main.py

4. 🛡️ Surveillez l'utilisation :
   python security_stats.py

💰 COÛT ESTIMÉ :
   - ~0.015€ par extraction (très économique)
   - Modèle Gemini Flash = rapide et pas cher
   - Limites par défaut = ~200€/mois maximum

🛡️ SÉCURITÉS INTÉGRÉES :
   - Limite quotidienne : 200 appels/jour
   - Limite horaire : 40 appels/heure  
   - Tracking des coûts automatique
   - Alertes de dépassement
   - Tableau de bord de surveillance
""" 