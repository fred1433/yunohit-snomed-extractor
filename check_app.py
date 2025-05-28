#!/usr/bin/env python3
"""
Vérification rapide du statut de l'app Streamlit
"""

import requests
import time
import sys

def check_app_quick(url: str) -> dict:
    """Vérification rapide de l'app"""
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start
        
        return {
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'response_time': response_time,
            'error': None
        }
    except Exception as e:
        return {
            'accessible': False,
            'status_code': None,
            'response_time': None,
            'error': str(e)
        }

def main():
    app_url = "https://fred1433-yunohit-snomed-extractor-streamlit-app-2e47bk.streamlit.app/"
    
    if len(sys.argv) > 1:
        app_url = sys.argv[1]
    
    print(f"🔍 Vérification de l'app...")
    print(f"📱 URL: {app_url}")
    print("-" * 50)
    
    result = check_app_quick(app_url)
    
    if result['accessible']:
        print(f"✅ App ACCESSIBLE")
        print(f"⚡ Temps de réponse: {result['response_time']:.2f}s")
        print(f"🌐 Status: HTTP {result['status_code']}")
        print(f"\n🚀 Prêt à tester !")
    else:
        print(f"❌ App NON ACCESSIBLE")
        if result['status_code']:
            print(f"🌐 Status: HTTP {result['status_code']}")
        if result['error']:
            print(f"❌ Erreur: {result['error']}")
        print(f"\n⏳ Réessayez dans quelques minutes...")

if __name__ == "__main__":
    main() 