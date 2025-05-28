#!/usr/bin/env python3
"""
Monitoring professionnel du déploiement Streamlit Cloud
Notifie précisément quand l'app est prête à tester
"""

import requests
import time
import sys
import subprocess
from datetime import datetime
import json

class StreamlitMonitor:
    def __init__(self, app_url: str):
        self.app_url = app_url
        self.start_time = time.time()
        self.deploy_log = []
    
    def check_app_status(self) -> dict:
        """Vérifie le statut de l'app"""
        try:
            response = requests.get(self.app_url, timeout=10)
            return {
                'status': response.status_code,
                'accessible': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'error': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': None,
                'accessible': False,
                'response_time': None,
                'error': str(e)
            }
    
    def log_status(self, status: dict):
        """Log le statut avec timestamp"""
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'elapsed': f"{elapsed:.1f}s",
            'status': status
        }
        self.deploy_log.append(log_entry)
        
        # Affichage en temps réel
        if status['accessible']:
            print(f"✅ {timestamp} [{elapsed:.1f}s] App ACCESSIBLE ({status['response_time']:.2f}s response)")
        else:
            error_msg = status['error'] or f"HTTP {status['status']}"
            print(f"⏳ {timestamp} [{elapsed:.1f}s] En cours... ({error_msg})")
    
    def notify_ready(self, final_status: dict):
        """Notification quand l'app est prête"""
        total_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print(f"🎉 APP PRÊTE À TESTER !")
        print(f"🕐 Temps de déploiement : {total_time:.1f} secondes")
        print(f"🌐 URL : {self.app_url}")
        print(f"⚡ Temps de réponse : {final_status['response_time']:.2f}s")
        print("="*60)
        
        # Notification sonore (macOS)
        try:
            subprocess.run(['osascript', '-e', 'beep 3'], check=False)
        except:
            pass
        
        # Notification système (macOS)
        try:
            subprocess.run([
                'osascript', '-e', 
                f'display notification "App déployée en {total_time:.1f}s" with title "Streamlit Cloud" sound name "Glass"'
            ], check=False)
        except:
            pass
    
    def monitor(self, max_wait: int = 300, check_interval: int = 5):
        """Lance le monitoring"""
        print(f"🔄 MONITORING DÉPLOIEMENT STREAMLIT CLOUD")
        print(f"📱 App: {self.app_url}")
        print(f"⏱️ Vérification toutes les {check_interval}s (max {max_wait}s)")
        print(f"🕐 Démarrage: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        while time.time() - self.start_time < max_wait:
            status = self.check_app_status()
            self.log_status(status)
            
            if status['accessible']:
                # App accessible - attendre stabilisation
                time.sleep(2)
                
                # Double vérification
                confirmation = self.check_app_status()
                if confirmation['accessible']:
                    self.notify_ready(confirmation)
                    return True
            
            time.sleep(check_interval)
        
        # Timeout
        print(f"\n⏰ TIMEOUT après {max_wait}s")
        print("L'app n'est pas encore accessible")
        return False

def main():
    """Fonction principale"""
    app_url = "https://fred1433-yunohit-snomed-extractor-streamlit-app-2e47bk.streamlit.app/"
    
    if len(sys.argv) > 1:
        app_url = sys.argv[1]
    
    monitor = StreamlitMonitor(app_url)
    success = monitor.monitor(max_wait=300, check_interval=5)
    
    if success:
        print(f"\n🚀 L'app est prête ! Vous pouvez tester maintenant.")
        
        # Optionnel : ouvrir automatiquement
        try:
            subprocess.run(['open', app_url], check=False)
            print(f"🌐 Ouverture automatique du navigateur...")
        except:
            print(f"📋 Copiez l'URL : {app_url}")
    else:
        print(f"\n❌ L'app n'est pas encore prête. Essayez manuellement : {app_url}")

if __name__ == "__main__":
    main() 