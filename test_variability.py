#!/usr/bin/env python3
"""
Script pour tester la variabilité des résultats avec validation SNOMED officielle
Lance plusieurs extractions en parallèle pour observer les variations
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import re

def run_single_test(test_id: int) -> dict:
    """Lancer un test d'extraction avec validation"""
    print(f"🔄 Test {test_id} : Démarrage...")
    start_time = time.time()
    
    try:
        # Lancer validate_extraction.py et capturer la sortie
        result = subprocess.run(
            ['python', 'validate_extraction.py'], 
            capture_output=True, 
            text=True, 
            timeout=180  # 3 minutes max
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            # Parser les résultats de la sortie
            output = result.stdout
            stats = parse_validation_output(output)
            
            print(f"✅ Test {test_id} : Terminé en {duration:.1f}s - {stats['valid_codes']}/{stats['total_codes']} codes valides ({stats['success_rate']:.1f}%)")
            
            return {
                'test_id': test_id,
                'success': True,
                'duration': duration,
                'output': output,
                'stats': stats,
                'error': None
            }
        else:
            print(f"❌ Test {test_id} : Erreur - {result.stderr}")
            return {
                'test_id': test_id,
                'success': False,
                'duration': duration,
                'output': result.stdout,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Test {test_id} : Timeout après 3 minutes")
        return {
            'test_id': test_id,
            'success': False,
            'duration': 180.0,
            'error': "Timeout",
            'output': ""
        }
    except Exception as e:
        print(f"💥 Test {test_id} : Exception - {str(e)}")
        return {
            'test_id': test_id,
            'success': False,
            'duration': 0,
            'error': str(e),
            'output': ""
        }

def parse_validation_output(output: str) -> dict:
    """Parser la sortie de validate_extraction.py pour extraire les statistiques"""
    stats = {
        'total_codes': 0,
        'valid_codes': 0,
        'success_rate': 0.0,
        'clinical_findings': 0,
        'procedures': 0,
        'body_structures': 0,
        'extraction_time': 0,
        'validation_time': 0
    }
    
    try:
        # Chercher le résumé de validation avec les bonnes regex
        total_match = re.search(r'Total des codes analysés : (\d+)', output)
        if total_match:
            stats['total_codes'] = int(total_match.group(1))
        
        valid_match = re.search(r'Codes VALIDES.*? : (\d+)', output)
        if valid_match:
            stats['valid_codes'] = int(valid_match.group(1))
        
        rate_match = re.search(r'Taux de validité : (\d+(?:\.\d+)?)%', output)
        if rate_match:
            stats['success_rate'] = float(rate_match.group(1))
        
        # Chercher les statistiques d'extraction dans les messages de début
        extraction_match = re.search(r'Extraction réussie : (\d+) constatations, (\d+) procédures, (\d+) structures', output)
        if extraction_match:
            stats['clinical_findings'] = int(extraction_match.group(1))
            stats['procedures'] = int(extraction_match.group(2))
            stats['body_structures'] = int(extraction_match.group(3))
        
        # Chercher les temps d'exécution
        extraction_time_match = re.search(r'Temps d\'extraction Gemini : (\d+(?:\.\d+)?)s', output)
        if extraction_time_match:
            stats['extraction_time'] = float(extraction_time_match.group(1))
        
        validation_time_match = re.search(r'Temps de validation SNOMED : (\d+(?:\.\d+)?)s', output)
        if validation_time_match:
            stats['validation_time'] = float(validation_time_match.group(1))
            
    except Exception as e:
        print(f"⚠️  Erreur parsing : {e}")
    
    return stats

def analyze_results(results: list) -> dict:
    """Analyser les résultats pour calculer statistiques et variabilité"""
    successful_tests = [r for r in results if r['success']]
    
    if not successful_tests:
        return {"error": "Aucun test réussi"}
    
    # Calcul des moyennes et variabilité
    success_rates = [r['stats']['success_rate'] for r in successful_tests]
    durations = [r['duration'] for r in successful_tests]
    valid_codes = [r['stats']['valid_codes'] for r in successful_tests]
    total_codes = [r['stats']['total_codes'] for r in successful_tests]
    
    analysis = {
        'total_tests': len(results),
        'successful_tests': len(successful_tests),
        'failed_tests': len(results) - len(successful_tests),
        'success_rate': {
            'mean': sum(success_rates) / len(success_rates),
            'min': min(success_rates),
            'max': max(success_rates),
            'std': calculate_std(success_rates)
        },
        'duration': {
            'mean': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations)
        },
        'codes': {
            'valid_mean': sum(valid_codes) / len(valid_codes),
            'total_mean': sum(total_codes) / len(total_codes)
        }
    }
    
    return analysis

def calculate_std(values: list) -> float:
    """Calculer l'écart-type"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5

def main():
    """Fonction principale"""
    print("🧪" + "="*60)
    print("    TEST DE VARIABILITÉ - EXTRACTION + VALIDATION SNOMED")
    print("="*62)
    print(f"⏰ Début des tests : {datetime.now().strftime('%H:%M:%S')}")
    print("🔄 Lancement de 3 tests en parallèle...")
    
    start_time = time.time()
    
    # Lancer les tests en parallèle
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_single_test, i+1) for i in range(3)]
        results = []
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Trier par test_id pour l'affichage
    results.sort(key=lambda x: x['test_id'])
    
    print(f"\n⏱️  Durée totale : {total_duration:.1f}s")
    print("\n" + "="*62)
    print("📊 RÉSULTATS DÉTAILLÉS")
    print("="*62)
    
    # Afficher chaque test
    for result in results:
        print(f"\n🧪 TEST {result['test_id']} :")
        if result['success']:
            stats = result['stats']
            print(f"   ✅ Succès en {result['duration']:.1f}s")
            print(f"   📊 Codes SNOMED : {stats['valid_codes']}/{stats['total_codes']} valides ({stats['success_rate']:.1f}%)")
            print(f"   🔍 Entités : {stats['clinical_findings']} constats, {stats['procedures']} procédures, {stats['body_structures']} structures")
            if stats['extraction_time'] > 0:
                print(f"   ⏱️  Temps : {stats['extraction_time']:.1f}s extraction, {stats['validation_time']:.1f}s validation")
        else:
            print(f"   ❌ Échec : {result['error']}")
    
    # Analyser la variabilité
    analysis = analyze_results(results)
    
    print(f"\n📈 ANALYSE DE VARIABILITÉ")
    print("="*62)
    
    if 'error' not in analysis:
        print(f"📊 Tests réussis : {analysis['successful_tests']}/{analysis['total_tests']}")
        print(f"🎯 Taux de réussite SNOMED :")
        print(f"   • Moyenne : {analysis['success_rate']['mean']:.1f}%")
        print(f"   • Min-Max : {analysis['success_rate']['min']:.1f}% - {analysis['success_rate']['max']:.1f}%")
        print(f"   • Écart-type : {analysis['success_rate']['std']:.1f}%")
        print(f"⏱️  Temps d'exécution :")
        print(f"   • Moyenne : {analysis['duration']['mean']:.1f}s")
        print(f"   • Min-Max : {analysis['duration']['min']:.1f}s - {analysis['duration']['max']:.1f}s")
        print(f"📈 Codes moyens : {analysis['codes']['valid_mean']:.1f}/{analysis['codes']['total_mean']:.1f}")
        
        # Évaluation de la variabilité
        variability = analysis['success_rate']['std']
        if variability < 10:
            print(f"✅ Variabilité faible ({variability:.1f}%) - Résultats consistants")
        elif variability < 20:
            print(f"⚠️  Variabilité modérée ({variability:.1f}%) - Quelques variations")
        else:
            print(f"🚨 Variabilité élevée ({variability:.1f}%) - Résultats très variables")
    else:
        print(f"❌ {analysis['error']}")
    
    print("\n" + "="*62)
    print("✅ Tests terminés !")

if __name__ == "__main__":
    main() 