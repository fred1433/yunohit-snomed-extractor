#!/usr/bin/env python3
"""
Script de test comparatif automatisé
Compare les performances entre prompt simple et prompt avec self-verification
"""

import time
import json
import subprocess
import concurrent.futures
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models import MedicalNote
from snomed_extractor import SNOMEDExtractor
from snomed_validator import SNOMEDValidator

@dataclass
class TestResult:
    """Résultat d'un test individuel"""
    test_id: int
    version: str  # "simple" ou "verification"
    extraction_time: float
    validation_time: float
    total_time: float
    total_codes: int
    valid_codes: int
    invalid_codes: int
    success_rate: float

def run_single_test(test_id: int, version: str, note: MedicalNote) -> TestResult:
    """Exécuter un test individuel"""
    start_total = time.time()
    
    # Extraction
    start_extraction = time.time()
    extractor = SNOMEDExtractor()
    extraction = extractor.extract_snomed_info(note)
    end_extraction = time.time()
    extraction_time = end_extraction - start_extraction
    
    # Validation
    start_validation = time.time()
    validator = SNOMEDValidator()
    validation_stats = validator.validate_extraction_result(extraction)
    end_validation = time.time()
    validation_time = end_validation - start_validation
    
    end_total = time.time()
    total_time = end_total - start_total
    
    # Statistiques
    total_codes = validation_stats.get("total_codes", 0)
    valid_codes = validation_stats.get("valid_codes", 0)
    invalid_codes = validation_stats.get("invalid_codes", 0)
    success_rate = (valid_codes / total_codes * 100) if total_codes > 0 else 0
    
    return TestResult(
        test_id=test_id,
        version=version,
        extraction_time=extraction_time,
        validation_time=validation_time,
        total_time=total_time,
        total_codes=total_codes,
        valid_codes=valid_codes,
        invalid_codes=invalid_codes,
        success_rate=success_rate
    )

def run_parallel_tests(version: str, num_tests: int, note: MedicalNote) -> List[TestResult]:
    """Lancer plusieurs tests en parallèle pour une version"""
    console = Console()
    console.print(f"🚀 Lancement de {num_tests} tests en parallèle pour version '{version}'...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(run_single_test, i+1, version, note) 
            for i in range(num_tests)
        ]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                console.print(f"✅ Test {result.test_id} ({version}) terminé: {result.success_rate:.1f}% en {result.total_time:.1f}s")
            except Exception as e:
                console.print(f"❌ Erreur dans un test {version}: {e}")
    
    return sorted(results, key=lambda x: x.test_id)

def analyze_results(simple_results: List[TestResult], verification_results: List[TestResult]) -> None:
    """Analyser et afficher les résultats comparatifs"""
    console = Console()
    
    # Statistiques simple
    simple_success_rates = [r.success_rate for r in simple_results]
    simple_times = [r.total_time for r in simple_results]
    simple_avg_success = sum(simple_success_rates) / len(simple_success_rates)
    simple_avg_time = sum(simple_times) / len(simple_times)
    
    # Statistiques verification
    verif_success_rates = [r.success_rate for r in verification_results]
    verif_times = [r.total_time for r in verification_results]
    verif_avg_success = sum(verif_success_rates) / len(verif_success_rates)
    verif_avg_time = sum(verif_times) / len(verif_times)
    
    # Affichage des résultats
    console.print("\n" + "="*80)
    console.print("📊 ANALYSE COMPARATIVE DES RÉSULTATS")
    console.print("="*80)
    
    # Tableau détaillé
    table = Table(title="Résultats détaillés par test")
    table.add_column("Version", style="cyan")
    table.add_column("Test", style="magenta")
    table.add_column("Codes valides", style="green")
    table.add_column("Total codes", style="blue")
    table.add_column("Taux réussite", style="yellow")
    table.add_column("Temps total", style="red")
    
    for result in simple_results:
        table.add_row(
            "Simple",
            str(result.test_id),
            str(result.valid_codes),
            str(result.total_codes),
            f"{result.success_rate:.1f}%",
            f"{result.total_time:.1f}s"
        )
    
    for result in verification_results:
        table.add_row(
            "Verification",
            str(result.test_id),
            str(result.valid_codes),
            str(result.total_codes),
            f"{result.success_rate:.1f}%",
            f"{result.total_time:.1f}s"
        )
    
    console.print(table)
    
    # Résumé statistique
    summary_text = f"""
📈 RÉSUMÉ STATISTIQUE :

🔵 VERSION SIMPLE (sans self-verification) :
   • Taux de réussite moyen : {simple_avg_success:.1f}%
   • Temps moyen : {simple_avg_time:.1f}s
   • Écart-type réussite : {(sum((x - simple_avg_success)**2 for x in simple_success_rates) / len(simple_success_rates))**0.5:.1f}%
   • Meilleur résultat : {max(simple_success_rates):.1f}%
   • Pire résultat : {min(simple_success_rates):.1f}%

🟡 VERSION VERIFICATION (avec self-verification) :
   • Taux de réussite moyen : {verif_avg_success:.1f}%
   • Temps moyen : {verif_avg_time:.1f}s
   • Écart-type réussite : {(sum((x - verif_avg_success)**2 for x in verif_success_rates) / len(verif_success_rates))**0.5:.1f}%
   • Meilleur résultat : {max(verif_success_rates):.1f}%
   • Pire résultat : {min(verif_success_rates):.1f}%

🎯 CONCLUSION :
   • Différence de réussite : {verif_avg_success - simple_avg_success:+.1f} points
   • Différence de temps : {verif_avg_time - simple_avg_time:+.1f}s
"""
    
    if verif_avg_success > simple_avg_success:
        summary_text += "   • 🏆 GAGNANT : Version avec self-verification"
    elif simple_avg_success > verif_avg_success:
        summary_text += "   • 🏆 GAGNANT : Version simple"
    else:
        summary_text += "   • 🤝 ÉGALITÉ entre les deux versions"
    
    console.print(Panel(summary_text, title="Analyse comparative", border_style="green"))

def main():
    """Fonction principale de test comparatif"""
    console = Console()
    
    # Titre
    title = Text("🧪 Test comparatif : Simple vs Self-verification", style="bold blue")
    console.print(Panel(title, expand=False))
    
    # Note médicale de test
    note_content = """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée."""
    
    medical_note = MedicalNote(
        patient_id="PAT-001",
        patient_name="Léo Martin",
        date=datetime.now().strftime("%Y-%m-%d"),
        doctor="Dr. Exemple",
        content=note_content,
        specialty="Pédiatrie"
    )
    
    num_tests = 5
    console.print(f"\n📋 Configuration : {num_tests} tests par version")
    console.print(f"🎯 Note médicale : {medical_note.patient_name}")
    
    start_global = time.time()
    
    try:
        # Tests version simple
        console.print(f"\n🔵 Phase 1 : Tests version SIMPLE")
        simple_results = run_parallel_tests("simple", num_tests, medical_note)
        
        # Tests version verification  
        console.print(f"\n🟡 Phase 2 : Tests version VERIFICATION")
        verification_results = run_parallel_tests("verification", num_tests, medical_note)
        
        end_global = time.time()
        console.print(f"\n⏱️  Temps total des tests : {end_global - start_global:.1f}s")
        
        # Analyse comparative
        analyze_results(simple_results, verification_results)
        
    except Exception as e:
        console.print(f"\n❌ [red]Erreur : {e}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 