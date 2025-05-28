#!/usr/bin/env python3
"""
Mode Haute Précision - Extraction SNOMED CT avec validation croisée
Lance plusieurs extractions en parallèle pour optimiser la fiabilité
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import re
from typing import List, Dict

def run_single_extraction() -> dict:
    """Lance une extraction individuelle"""
    try:
        result = subprocess.run(
            ['python', 'validate_extraction.py'], 
            capture_output=True, 
            text=True, 
            timeout=180
        )
        
        if result.returncode == 0:
            stats = parse_validation_output(result.stdout)
            return {
                'success': True,
                'output': result.stdout,
                'stats': stats,
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'output': "",
            'error': str(e)
        }

def parse_validation_output(output: str) -> dict:
    """Parser les résultats d'une extraction"""
    stats = {
        'total_codes': 0,
        'valid_codes': 0,
        'success_rate': 0.0,
        'clinical_findings': 0,
        'procedures': 0,
        'body_structures': 0
    }
    
    try:
        # Statistiques de validation
        total_match = re.search(r'Total des codes analysés : (\d+)', output)
        if total_match:
            stats['total_codes'] = int(total_match.group(1))
        
        valid_match = re.search(r'Codes VALIDES.*? : (\d+)', output)
        if valid_match:
            stats['valid_codes'] = int(valid_match.group(1))
        
        rate_match = re.search(r'Taux de validité : (\d+(?:\.\d+)?)%', output)
        if rate_match:
            stats['success_rate'] = float(rate_match.group(1))
        
        # Statistiques d'extraction
        extraction_match = re.search(r'Extraction réussie : (\d+) constatations, (\d+) procédures, (\d+) structures', output)
        if extraction_match:
            stats['clinical_findings'] = int(extraction_match.group(1))
            stats['procedures'] = int(extraction_match.group(2))
            stats['body_structures'] = int(extraction_match.group(3))
            
    except Exception as e:
        print(f"⚠️  Erreur parsing : {e}")
    
    return stats

def select_best_result(results: List[dict]) -> dict:
    """Sélectionner le meilleur résultat selon plusieurs critères"""
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        return None
    
    # Critères de sélection (par ordre de priorité)
    best_result = None
    best_score = -1
    
    for result in successful_results:
        stats = result['stats']
        
        # Score composite : privilégier le taux de validité puis le nombre d'entités
        score = (
            stats['success_rate'] * 2 +  # Priorité au taux de validité
            stats['valid_codes'] * 10 +  # Nombre de codes valides
            (stats['clinical_findings'] + stats['procedures'] + stats['body_structures']) * 1  # Nombre total d'entités
        )
        
        if score > best_score:
            best_score = score
            best_result = result
    
    return best_result

def calculate_consensus_stats(results: List[dict]) -> dict:
    """Calculer les statistiques de consensus"""
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        return None
    
    success_rates = [r['stats']['success_rate'] for r in successful_results]
    valid_codes = [r['stats']['valid_codes'] for r in successful_results]
    total_codes = [r['stats']['total_codes'] for r in successful_results]
    
    return {
        'extractions_reussies': len(successful_results),
        'taux_moyen': sum(success_rates) / len(success_rates),
        'taux_min': min(success_rates),
        'taux_max': max(success_rates),
        'codes_valides_moyen': sum(valid_codes) / len(valid_codes),
        'codes_total_moyen': sum(total_codes) / len(total_codes),
        'variabilite': max(success_rates) - min(success_rates)
    }

def main():
    """Fonction principale - Mode Haute Précision"""
    print("🎯" + "="*70)
    print("              MODE HAUTE PRÉCISION - EXTRACTION SNOMED CT")
    print("                  Validation croisée avec 3 extractions")
    print("="*72)
    
    print(f"🚀 Lancement à {datetime.now().strftime('%H:%M:%S')}")
    print("🔄 Exécution de 3 extractions en parallèle...")
    
    start_time = time.time()
    
    # Lancer 3 extractions en parallèle
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_single_extraction) for _ in range(3)]
        results = []
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)
            
            if result['success']:
                print(f"   ✅ Extraction {completed}/3 : {result['stats']['success_rate']:.1f}% de codes valides")
            else:
                print(f"   ❌ Extraction {completed}/3 : Échec")
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n⏱️  Durée totale : {total_duration:.1f}s")
    
    # Analyser les résultats
    consensus = calculate_consensus_stats(results)
    best_result = select_best_result(results)
    
    if not best_result or not consensus:
        print("\n❌ ÉCHEC : Aucune extraction réussie")
        return
    
    print("\n" + "="*72)
    print("📊 ANALYSE DE CONSENSUS")
    print("="*72)
    
    print(f"✅ Extractions réussies : {consensus['extractions_reussies']}/3")
    print(f"📈 Taux de validité SNOMED :")
    print(f"   • Moyenne : {consensus['taux_moyen']:.1f}%")
    print(f"   • Plage : {consensus['taux_min']:.1f}% - {consensus['taux_max']:.1f}%")
    print(f"   • Variabilité : ±{consensus['variabilite']:.1f} points")
    print(f"🎯 Codes valides moyens : {consensus['codes_valides_moyen']:.1f}/{consensus['codes_total_moyen']:.1f}")
    
    # Évaluation de la stabilité
    if consensus['variabilite'] < 15:
        print(f"✅ Résultats STABLES (variabilité {consensus['variabilite']:.1f} points)")
    elif consensus['variabilite'] < 25:
        print(f"⚠️  Résultats MODÉRÉMENT VARIABLES (variabilité {consensus['variabilite']:.1f} points)")
    else:
        print(f"🚨 Résultats TRÈS VARIABLES (variabilité {consensus['variabilite']:.1f} points)")
    
    print(f"\n🏆 MEILLEUR RÉSULTAT SÉLECTIONNÉ :")
    print(f"   📊 {best_result['stats']['valid_codes']}/{best_result['stats']['total_codes']} codes SNOMED valides ({best_result['stats']['success_rate']:.1f}%)")
    print(f"   🔍 {best_result['stats']['clinical_findings']} constats + {best_result['stats']['procedures']} procédures + {best_result['stats']['body_structures']} structures")
    
    print("\n" + "="*72)
    print("📋 RÉSULTAT FINAL - HAUTE PRÉCISION")
    print("="*72)
    
    # Afficher le résultat complet du meilleur
    print(best_result['output'])
    
    print(f"\n💰 COÛT ESTIMÉ : {3 * 0.015:.3f}€ (3 extractions × 0.015€)")
    print(f"🎯 FIABILITÉ : Optimisée par validation croisée")
    print(f"⏱️  EFFICACITÉ : {total_duration:.1f}s pour 3 extractions parallèles")

if __name__ == "__main__":
    main() 