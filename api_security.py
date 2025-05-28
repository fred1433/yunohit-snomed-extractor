"""
Module de sécurité pour protéger l'utilisation de l'API Gemini
Limite les appels, surveille la consommation et prévient les abus
"""

import json
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any

class APISecurityManager:
    """Gestionnaire de sécurité pour l'API Gemini"""
    
    def __init__(self, daily_limit: int = 50, hourly_limit: int = 10):
        """
        Initialiser le gestionnaire de sécurité
        
        Args:
            daily_limit: Nombre max d'appels par jour
            hourly_limit: Nombre max d'appels par heure
        """
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self.usage_file = Path("usage_tracking.json")
        self.load_usage_data()
    
    def load_usage_data(self):
        """Charger les données d'utilisation depuis le fichier"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            except:
                self.usage_data = {}
        else:
            self.usage_data = {}
    
    def save_usage_data(self):
        """Sauvegarder les données d'utilisation"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def get_today_key(self) -> str:
        """Obtenir la clé pour aujourd'hui"""
        return date.today().isoformat()
    
    def get_current_hour_key(self) -> str:
        """Obtenir la clé pour l'heure actuelle"""
        return datetime.now().strftime("%Y-%m-%d-%H")
    
    def get_daily_usage(self) -> int:
        """Obtenir le nombre d'appels aujourd'hui"""
        today = self.get_today_key()
        return self.usage_data.get("daily", {}).get(today, 0)
    
    def get_hourly_usage(self) -> int:
        """Obtenir le nombre d'appels cette heure"""
        current_hour = self.get_current_hour_key()
        return self.usage_data.get("hourly", {}).get(current_hour, 0)
    
    def can_make_request(self) -> tuple[bool, str]:
        """
        Vérifier si on peut faire un appel API
        
        Returns:
            (can_proceed, reason)
        """
        daily_usage = self.get_daily_usage()
        hourly_usage = self.get_hourly_usage()
        
        if daily_usage >= self.daily_limit:
            return False, f"🚫 Limite quotidienne atteinte ({daily_usage}/{self.daily_limit})"
        
        if hourly_usage >= self.hourly_limit:
            return False, f"⏰ Limite horaire atteinte ({hourly_usage}/{self.hourly_limit}). Réessayez dans 1h."
        
        return True, f"✅ OK ({daily_usage}/{self.daily_limit} quotidien, {hourly_usage}/{self.hourly_limit} horaire)"
    
    def record_api_call(self, estimated_cost: float = 0.01):
        """
        Enregistrer un appel API
        
        Args:
            estimated_cost: Coût estimé en euros
        """
        today = self.get_today_key()
        current_hour = self.get_current_hour_key()
        
        # Initialiser les structures si nécessaire
        if "daily" not in self.usage_data:
            self.usage_data["daily"] = {}
        if "hourly" not in self.usage_data:
            self.usage_data["hourly"] = {}
        if "costs" not in self.usage_data:
            self.usage_data["costs"] = {}
        
        # Incrémenter les compteurs
        self.usage_data["daily"][today] = self.usage_data["daily"].get(today, 0) + 1
        self.usage_data["hourly"][current_hour] = self.usage_data["hourly"].get(current_hour, 0) + 1
        
        # Ajouter le coût
        self.usage_data["costs"][today] = self.usage_data["costs"].get(today, 0.0) + estimated_cost
        
        # Nettoyer les anciennes données (garder 30 jours)
        self.cleanup_old_data()
        
        # Sauvegarder
        self.save_usage_data()
    
    def cleanup_old_data(self):
        """Nettoyer les données anciennes pour éviter l'accumulation"""
        cutoff_date = datetime.now().timestamp() - (30 * 24 * 3600)  # 30 jours
        
        # Nettoyer les données quotidiennes
        daily_to_remove = []
        for date_str in self.usage_data.get("daily", {}):
            try:
                date_obj = datetime.fromisoformat(date_str)
                if date_obj.timestamp() < cutoff_date:
                    daily_to_remove.append(date_str)
            except:
                daily_to_remove.append(date_str)
        
        for date_str in daily_to_remove:
            self.usage_data["daily"].pop(date_str, None)
            self.usage_data.get("costs", {}).pop(date_str, None)
        
        # Nettoyer les données horaires (garder 48h)
        hourly_cutoff = datetime.now().timestamp() - (48 * 3600)
        hourly_to_remove = []
        for hour_str in self.usage_data.get("hourly", {}):
            try:
                hour_obj = datetime.strptime(hour_str, "%Y-%m-%d-%H")
                if hour_obj.timestamp() < hourly_cutoff:
                    hourly_to_remove.append(hour_str)
            except:
                hourly_to_remove.append(hour_str)
        
        for hour_str in hourly_to_remove:
            self.usage_data["hourly"].pop(hour_str, None)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques d'utilisation"""
        today = self.get_today_key()
        daily_usage = self.get_daily_usage()
        hourly_usage = self.get_hourly_usage()
        daily_cost = self.usage_data.get("costs", {}).get(today, 0.0)
        
        # Calcul du coût total sur 30 jours
        total_cost = sum(self.usage_data.get("costs", {}).values())
        
        return {
            "daily_usage": daily_usage,
            "daily_limit": self.daily_limit,
            "hourly_usage": hourly_usage,
            "hourly_limit": self.hourly_limit,
            "daily_cost": daily_cost,
            "total_cost_30d": total_cost,
            "remaining_daily": self.daily_limit - daily_usage,
            "remaining_hourly": self.hourly_limit - hourly_usage
        }
    
    def print_usage_warning(self):
        """Afficher un avertissement sur l'utilisation"""
        stats = self.get_usage_stats()
        
        if stats["daily_usage"] > stats["daily_limit"] * 0.8:  # 80% de la limite
            print(f"⚠️  Attention : {stats['daily_usage']}/{stats['daily_limit']} appels quotidiens utilisés")
        
        if stats["hourly_usage"] > stats["hourly_limit"] * 0.8:  # 80% de la limite
            print(f"⚠️  Attention : {stats['hourly_usage']}/{stats['hourly_limit']} appels horaires utilisés")
        
        if stats["daily_cost"] > 1.0:  # Plus de 1€ par jour
            print(f"💰 Coût quotidien : {stats['daily_cost']:.2f}€")
        
        if stats["total_cost_30d"] > 20.0:  # Plus de 20€ sur 30 jours
            print(f"💰 Coût sur 30 jours : {stats['total_cost_30d']:.2f}€")

# Instance globale pour l'utilisation - utilise la config si disponible
try:
    from config import Config
    security_manager = APISecurityManager(
        daily_limit=Config.DAILY_API_LIMIT,
        hourly_limit=Config.HOURLY_API_LIMIT
    )
except ImportError:
    # Fallback si config.py n'existe pas encore
    security_manager = APISecurityManager(
        daily_limit=50,    # Max 50 appels par jour
        hourly_limit=10    # Max 10 appels par heure
    ) 