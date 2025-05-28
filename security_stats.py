#!/usr/bin/env python3
"""
Script pour consulter les statistiques de sécurité de l'API Gemini
Affiche l'utilisation actuelle et les coûts estimés
"""

from api_security import security_manager
import json
from datetime import datetime, timedelta

def print_security_dashboard():
    """Afficher le tableau de bord de sécurité"""
    print("🛡️" + "="*60)
    print("         TABLEAU DE BORD SÉCURITÉ API GEMINI")
    print("="*62)
    
    stats = security_manager.get_usage_stats()
    
    # Status actuel
    print(f"\n📊 UTILISATION ACTUELLE :")
    print(f"   📅 Quotidien : {stats['daily_usage']}/{stats['daily_limit']} appels ({stats['remaining_daily']} restants)")
    print(f"   ⏰ Horaire  : {stats['hourly_usage']}/{stats['hourly_limit']} appels ({stats['remaining_hourly']} restants)")
    
    # Calcul des pourcentages
    daily_percent = (stats['daily_usage'] / stats['daily_limit']) * 100
    hourly_percent = (stats['hourly_usage'] / stats['hourly_limit']) * 100
    
    # Barres de progression
    daily_bar = "🟩" * int(daily_percent // 10) + "⬜" * (10 - int(daily_percent // 10))
    hourly_bar = "🟩" * int(hourly_percent // 10) + "⬜" * (10 - int(hourly_percent // 10))
    
    print(f"   📊 Quotidien : [{daily_bar}] {daily_percent:.1f}%")
    print(f"   📊 Horaire   : [{hourly_bar}] {hourly_percent:.1f}%")
    
    # Coûts
    print(f"\n💰 COÛTS ESTIMÉS :")
    print(f"   📅 Aujourd'hui  : {stats['daily_cost']:.3f}€")
    print(f"   📊 30 derniers jours : {stats['total_cost_30d']:.2f}€")
    print(f"   📈 Projection mensuelle : {stats['daily_cost'] * 30:.2f}€")
    
    # Alertes
    print(f"\n⚠️  ALERTES :")
    if daily_percent >= 90:
        print("   🚨 LIMITE QUOTIDIENNE PRESQUE ATTEINTE !")
    elif daily_percent >= 80:
        print("   ⚠️  Attention : limite quotidienne à 80%")
    
    if hourly_percent >= 90:
        print("   🚨 LIMITE HORAIRE PRESQUE ATTEINTE !")
    elif hourly_percent >= 80:
        print("   ⚠️  Attention : limite horaire à 80%")
    
    if stats['total_cost_30d'] > 50:
        print(f"   💸 Coût élevé sur 30 jours : {stats['total_cost_30d']:.2f}€")
    
    if not any([daily_percent >= 80, hourly_percent >= 80, stats['total_cost_30d'] > 50]):
        print("   ✅ Aucune alerte - utilisation normale")
    
    # Historique récent
    print(f"\n📈 HISTORIQUE DES 7 DERNIERS JOURS :")
    show_recent_history()
    
    print("\n" + "="*62)

def show_recent_history():
    """Afficher l'historique des 7 derniers jours"""
    usage_data = security_manager.usage_data
    daily_data = usage_data.get("daily", {})
    cost_data = usage_data.get("costs", {})
    
    # Générer les 7 derniers jours
    today = datetime.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    for date_obj in dates:
        date_str = date_obj.isoformat()
        calls = daily_data.get(date_str, 0)
        cost = cost_data.get(date_str, 0.0)
        
        # Barre de progression simple
        bar_length = int(calls / 10) if calls <= 50 else 5  # Max 5 caractères
        bar = "▓" * bar_length + "░" * (5 - bar_length)
        
        day_name = date_obj.strftime("%a")
        print(f"   {day_name} {date_str} : [{bar}] {calls:2d} appels ({cost:.3f}€)")

def reset_usage_stats():
    """Réinitialiser les statistiques d'utilisation (fonction d'urgence)"""
    confirm = input("⚠️  Êtes-vous sûr de vouloir réinitialiser les stats ? (tapez 'RESET') : ")
    if confirm == "RESET":
        security_manager.usage_data = {}
        security_manager.save_usage_data()
        print("✅ Statistiques réinitialisées")
    else:
        print("❌ Réinitialisation annulée")

def main():
    """Fonction principale"""
    print_security_dashboard()
    
    while True:
        print(f"\n🔧 ACTIONS DISPONIBLES :")
        print("  1. 🔄 Actualiser le tableau de bord")
        print("  2. 📊 Voir détails complets")
        print("  3. 🗑️  Réinitialiser les statistiques")
        print("  4. 🚪 Quitter")
        
        choice = input("\nVotre choix (1-4) : ").strip()
        
        if choice == "1":
            print_security_dashboard()
        elif choice == "2":
            print(f"\n📋 DONNÉES COMPLÈTES :")
            print(json.dumps(security_manager.usage_data, indent=2, ensure_ascii=False))
        elif choice == "3":
            reset_usage_stats()
        elif choice == "4":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 