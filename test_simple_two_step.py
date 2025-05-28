#!/usr/bin/env python3
"""
Test simple de la méthode 2-étapes
Validation que l'extraction expérimentale fonctionne correctement
"""

import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models import MedicalNote
from snomed_extractor import SNOMEDExtractor
from snomed_validator import SNOMEDValidator

def test_two_step_method():
    """Test simple de la méthode 2-étapes"""
    console = Console()
    
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
    
    console.print(Panel("🔬 TEST SIMPLE : Méthode 2-étapes", style="blue"))
    console.print(f"📋 Patient : {medical_note.patient_name}")
    console.print(f"📝 Note : {note_content[:100]}...")
    
    try:
        # Test de la méthode 2-étapes
        console.print("\n⏰ Lancement du test...")
        start_time = time.time()
        
        extractor = SNOMEDExtractor()
        extraction = extractor.extract_two_step(medical_note)
        
        extraction_time = time.time() - start_time
        
        # Validation
        console.print("\n🔍 Validation des codes SNOMED...")
        start_validation = time.time()
        validator = SNOMEDValidator()
        validation_stats = validator.validate_extraction_result(extraction)
        validation_time = time.time() - start_validation
        
        # Affichage des résultats
        console.print(f"\n⏱️  Temps d'extraction : {extraction_time:.1f}s")
        console.print(f"⏱️  Temps de validation : {validation_time:.1f}s")
        console.print(f"⏱️  Temps total : {extraction_time + validation_time:.1f}s")
        
        # Tableau des résultats
        table = Table(title="Résultats de l'extraction 2-étapes")
        table.add_column("Catégorie", style="cyan")
        table.add_column("Terme", style="green")
        table.add_column("Code SNOMED", style="yellow")
        table.add_column("Modifieurs", style="magenta")
        
        # Constatations cliniques
        for finding in extraction.clinical_findings:
            modifiers = f"Nég:{finding.negation} | Fam:{finding.family} | Sus:{finding.suspicion} | Ant:{finding.antecedent}"
            table.add_row("FINDING", finding.term, finding.snomed_code, modifiers)
        
        # Procédures
        for procedure in extraction.procedures:
            modifiers = f"Nég:{procedure.negation} | Fam:{procedure.family} | Sus:{procedure.suspicion} | Ant:{procedure.antecedent}"
            table.add_row("PROCEDURE", procedure.term, procedure.snomed_code, modifiers)
        
        # Structures corporelles
        for structure in extraction.body_structures:
            modifiers = f"Nég:{structure.negation} | Fam:{structure.family} | Sus:{structure.suspicion} | Ant:{structure.antecedent}"
            table.add_row("STRUCTURE", structure.term, structure.snomed_code, modifiers)
        
        console.print(table)
        
        # Statistiques de validation
        total_codes = validation_stats.get("total_codes", 0)
        valid_codes = validation_stats.get("valid_codes", 0)
        invalid_codes = validation_stats.get("invalid_codes", 0)
        success_rate = (valid_codes / total_codes * 100) if total_codes > 0 else 0
        
        stats_text = f"""
📊 STATISTIQUES DE VALIDATION :

🎯 Codes extraits : {total_codes}
✅ Codes valides : {valid_codes}
❌ Codes invalides : {invalid_codes}
📈 Taux de réussite : {success_rate:.1f}%

🔗 Détails :
• Constatations : {len(extraction.clinical_findings)}
• Procédures : {len(extraction.procedures)}
• Structures : {len(extraction.body_structures)}
"""
        
        console.print(Panel(stats_text, title="Validation", border_style="green"))
        
        # Évaluation du résultat
        if total_codes == 0:
            console.print("❌ [red]ÉCHEC : Aucun code extrait[/red]")
        elif success_rate >= 70:
            console.print("🏆 [green]EXCELLENT : Méthode 2-étapes fonctionne bien ![/green]")
        elif success_rate >= 50:
            console.print("✅ [yellow]BON : Méthode 2-étapes fonctionne correctement[/yellow]")
        elif success_rate >= 30:
            console.print("⚠️  [orange]MOYEN : Méthode 2-étapes fonctionne mais peut être améliorée[/orange]")
        else:
            console.print("🔴 [red]FAIBLE : Méthode 2-étapes a des problèmes[/red]")
            
        return True
        
    except Exception as e:
        console.print(f"\n❌ [red]ERREUR lors du test : {e}[/red]")
        return False

def main():
    """Fonction principale"""
    console = Console()
    
    console.print("🔬 Validation de la méthode expérimentale 2-étapes")
    console.print("🎯 Objectif : S'assurer que l'implémentation fonctionne correctement\n")
    
    success = test_two_step_method()
    
    if success:
        console.print("\n✅ [green]Test terminé avec succès ![/green]")
        console.print("💡 [cyan]Prêt pour les tests comparatifs[/cyan]")
    else:
        console.print("\n❌ [red]Test échoué - Vérifier l'implémentation[/red]")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 