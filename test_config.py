#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration et la connexion à Google Gemini
"""

import google.generativeai as genai
from config import Config

def test_configuration():
    """Tester la configuration et la connexion"""
    try:
        print("🔧 Test de la configuration...")
        
        # Valider la configuration
        Config.validate()
        print("✅ Configuration validée")
        
        # Configurer l'API
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        print("✅ API configurée")
        
        # Tester la connexion avec un modèle simple
        print(f"🤖 Test de connexion avec le modèle : {Config.GEMINI_MODEL}")
        
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content("Dis simplement 'test réussi' en français.")
        
        if response.text:
            print("✅ Test de connexion réussi !")
            print(f"Réponse du modèle : {response.text.strip()}")
            return True
        else:
            print("❌ Pas de réponse reçue du modèle")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        
        # Suggérer des solutions selon l'erreur
        if "API key" in str(e).lower():
            print("\n🔑 Vérifiez votre clé API dans le fichier .env")
        elif "model" in str(e).lower():
            print(f"\n🤖 Le modèle {Config.GEMINI_MODEL} n'est peut-être pas disponible.")
            print("Essayez de changer GEMINI_MODEL dans config.py vers :")
            print("- 'gemini-1.5-pro'")
            print("- 'gemini-1.5-flash'")
            print("- 'gemini-pro'")
        
        return False

if __name__ == "__main__":
    if test_configuration():
        print("\n🎉 Tout fonctionne ! Vous pouvez maintenant lancer : python main.py")
    else:
        print("\n❌ Des erreurs ont été détectées. Corrigez-les avant de continuer.") 