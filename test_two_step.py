#!/usr/bin/env python3
"""
Script de test comparatif : Méthode classique vs Méthode 2-étapes
Test de l'hypothèse : Gemini trouve-t-il de meilleurs codes SNOMED quand il se concentre exclusivement sur cette tâche ?
"""

import time
import concurrent.futures
from datetime import datetime
from dataclasses import dataclass
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models import MedicalNote
from snomed_extractor import SNOMEDExtractor
from snomed_validator import SNOMEDValidator

@dataclass
class ComparisonResult:
    """Résultat de comparaison entre les deux méthodes"""
    test_id: int
    method: str  # "classique" ou "two_step"
    extraction_time: float
    validation_time: float
    total_time: float
    total_codes: int
    valid_codes: int
    success_rate: float
    terms_found: int

def run_test_classique(test_id: int, note: MedicalNote) -> ComparisonResult:
    """Test avec la méthode classique (1 étape)"""
    start_time = time.time()
    
    start_extraction = time.time()
    extractor = SNOMEDExtractor()
    extraction = extractor.extract_snomed_info(note)
    end_extraction = time.time()
    
    start_validation = time.time()
    validator = SNOMEDValidator()
    validation_stats = validator.validate_extraction_result(extraction)
    end_validation = time.time()
    
    total_time = time.time() - start_time
    
    # Compter le nombre total de termes trouvés
    terms_found = len(extraction.clinical_findings) + len(extraction.procedures) + len(extraction.body_structures)
    
    return ComparisonResult(
        test_id=test_id,
        method="classique",
        extraction_time=end_extraction - start_extraction,
        validation_time=end_validation - start_validation,
        total_time=total_time,
        total_codes=validation_stats.get("total_codes", 0),
        valid_codes=validation_stats.get("valid_codes", 0),
        success_rate=(validation_stats.get("valid_codes", 0) / validation_stats.get("total_codes", 1) * 100) if validation_stats.get("total_codes", 0) > 0 else 0,
        terms_found=terms_found
    )

def run_test_two_step(test_id: int, note: MedicalNote) -> ComparisonResult:
    """Test avec la méthode expérimentale 2-étapes"""
    start_time = time.time()
    
    start_extraction = time.time()
    extractor = SNOMEDExtractor()
    extraction = extractor.extract_two_step(note)
    end_extraction = time.time()
    
    start_validation = time.time()
    validator = SNOMEDValidator()
    validation_stats = validator.validate_extraction_result(extraction)
    end_validation = time.time()
    
    total_time = time.time() - start_time
    
    # Compter le nombre total de termes trouvés
    terms_found = len(extraction.clinical_findings) + len(extraction.procedures) + len(extraction.body_structures)
    
    return ComparisonResult(
        test_id=test_id,
        method="two_step",
        extraction_time=end_extraction - start_extraction,
        validation_time=end_validation - start_validation,
        total_time=total_time,
        total_codes=validation_stats.get("total_codes", 0),
        valid_codes=validation_stats.get("valid_codes", 0),
        success_rate=(validation_stats.get("valid_codes", 0) / validation_stats.get("total_codes", 1) * 100) if validation_stats.get("total_codes", 0) > 0 else 0,
        terms_found=terms_found
    )

def run_parallel_comparison(num_tests: int, note: MedicalNote) -> tuple[List[ComparisonResult], List[ComparisonResult]]:
    """Lancer les tests en parallèle pour les deux méthodes"""
    console = Console()
    console.print(f"🚀 Lancement de {num_tests} tests en parallèle pour chaque méthode...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # Soumettre tous les tests
        classique_futures = [
            executor.submit(run_test_classique, i+1, note) 
            for i in range(num_tests)
        ]
        two_step_futures = [
            executor.submit(run_test_two_step, i+1, note) 
            for i in range(num_tests)
        ]
        
        # Collecter les résultats
        classique_results = []
        two_step_results = []
        
        for future in concurrent.futures.as_completed(classique_futures + two_step_futures):
            try:
                result = future.result()
                if result.method == "classique":
                    classique_results.append(result)
                else:
                    two_step_results.append(result)
                console.print(f"✅ Test {result.test_id} ({result.method}) terminé: {result.success_rate:.1f}% en {result.total_time:.1f}s")
            except Exception as e:
                console.print(f"❌ Erreur dans un test: {e}")
    
    return sorted(classique_results, key=lambda x: x.test_id), sorted(two_step_results, key=lambda x: x.test_id)

def analyze_comparison(classique_results: List[ComparisonResult], two_step_results: List[ComparisonResult]) -> None:
    """Analyser et afficher la comparaison entre les deux méthodes"""
    console = Console()
    
    # Statistiques méthode classique
    classique_success = [r.success_rate for r in classique_results]
    classique_times = [r.total_time for r in classique_results]
    classique_terms = [r.terms_found for r in classique_results]
    
    classique_avg_success = sum(classique_success) / len(classique_success)
    classique_avg_time = sum(classique_times) / len(classique_times)
    classique_avg_terms = sum(classique_terms) / len(classique_terms)
    
    # Statistiques méthode 2-étapes
    two_step_success = [r.success_rate for r in two_step_results]
    two_step_times = [r.total_time for r in two_step_results]
    two_step_terms = [r.terms_found for r in two_step_results]
    
    two_step_avg_success = sum(two_step_success) / len(two_step_success)
    two_step_avg_time = sum(two_step_times) / len(two_step_times)
    two_step_avg_terms = sum(two_step_terms) / len(two_step_terms)
    
    # Affichage des résultats
    console.print("\n" + "="*80)
    console.print("🔬 COMPARAISON : CLASSIQUE vs 2-ÉTAPES")
    console.print("="*80)
    
    # Tableau détaillé
    table = Table(title="Résultats détaillés par test")
    table.add_column("Méthode", style="cyan")
    table.add_column("Test", style="magenta")
    table.add_column("Termes", style="green")
    table.add_column("Codes valides", style="yellow")
    table.add_column("Total codes", style="blue")
    table.add_column("Taux réussite", style="red")
    table.add_column("Temps", style="white")
    
    for result in classique_results:
        table.add_row(
            "Classique",
            str(result.test_id),
            str(result.terms_found),
            str(result.valid_codes),
            str(result.total_codes),
            f"{result.success_rate:.1f}%",
            f"{result.total_time:.1f}s"
        )
    
    for result in two_step_results:
        table.add_row(
            "2-Étapes",
            str(result.test_id),
            str(result.terms_found),
            str(result.valid_codes),
            str(result.total_codes),
            f"{result.success_rate:.1f}%",
            f"{result.total_time:.1f}s"
        )
    
    console.print(table)
    
    # Analyse statistique
    success_diff = two_step_avg_success - classique_avg_success
    time_diff = two_step_avg_time - classique_avg_time
    terms_diff = two_step_avg_terms - classique_avg_terms
    
    summary_text = f"""
📊 ANALYSE COMPARATIVE :

🔵 MÉTHODE CLASSIQUE (1 étape) :
   • Taux de réussite moyen : {classique_avg_success:.1f}%
   • Temps moyen : {classique_avg_time:.1f}s
   • Termes trouvés moyens : {classique_avg_terms:.1f}
   • Meilleur résultat : {max(classique_success):.1f}%
   • Pire résultat : {min(classique_success):.1f}%

🟡 MÉTHODE 2-ÉTAPES (expérimentale) :
   • Taux de réussite moyen : {two_step_avg_success:.1f}%
   • Temps moyen : {two_step_avg_time:.1f}s
   • Termes trouvés moyens : {two_step_avg_terms:.1f}
   • Meilleur résultat : {max(two_step_success):.1f}%
   • Pire résultat : {min(two_step_success):.1f}%

🎯 DIFFÉRENCES :
   • Précision des codes : {success_diff:+.1f} points
   • Temps d'exécution : {time_diff:+.1f}s
   • Nombre de termes : {terms_diff:+.1f}
"""
    
    if success_diff > 2:
        summary_text += "\n   • 🏆 GAGNANT : Méthode 2-étapes (codes plus précis)"
    elif success_diff < -2:
        summary_text += "\n   • 🏆 GAGNANT : Méthode classique (codes plus précis)"
    else:
        summary_text += "\n   • 🤝 ÉGALITÉ : Performances similaires"
        
    if abs(time_diff) > 5:
        if time_diff > 0:
            summary_text += f"\n   • ⏱️  Méthode classique {abs(time_diff):.1f}s plus rapide"
        else:
            summary_text += f"\n   • ⏱️  Méthode 2-étapes {abs(time_diff):.1f}s plus rapide"
    
    console.print(Panel(summary_text, title="🔬 Analyse expérimentale", border_style="blue"))

def main():
    """Fonction principale de test comparatif"""
    console = Console()
    
    # Titre
    title = Text("🔬 TEST EXPÉRIMENTAL : Classique vs 2-Étapes", style="bold blue")
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
    console.print(f"\n📋 Configuration : {num_tests} tests par méthode")
    console.print(f"🎯 Hypothèse : La spécialisation des prompts améliore-t-elle la précision des codes SNOMED ?")
    
    start_global = time.time()
    
    try:
        # Tests comparatifs
        classique_results, two_step_results = run_parallel_comparison(num_tests, medical_note)
        
        end_global = time.time()
        console.print(f"\n⏱️  Temps total des tests : {end_global - start_global:.1f}s")
        
        # Analyse comparative
        analyze_comparison(classique_results, two_step_results)
        
    except Exception as e:
        console.print(f"\n❌ [red]Erreur : {e}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 