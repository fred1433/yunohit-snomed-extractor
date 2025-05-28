#!/usr/bin/env python3
"""
Script de validation des extractions SNOMED CT
Valide tous les codes générés par Gemini contre la base officielle française
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models import MedicalNote
from snomed_extractor import SNOMEDExtractor
from snomed_validator import SNOMEDValidator

def format_modifiers(item) -> str:
    """Formater les modifieurs contextuels pour affichage"""
    modifiers = []
    
    if hasattr(item, 'negation') and item.negation == "negative":
        modifiers.append("❌")
    elif hasattr(item, 'negation') and item.negation == "positive":
        modifiers.append("✅")
    
    if hasattr(item, 'family') and item.family == "family":
        modifiers.append("👨‍👩‍👧‍👦")
    elif hasattr(item, 'family') and item.family == "patient":
        modifiers.append("🧑")
    
    if hasattr(item, 'suspicion') and item.suspicion == "suspected":
        modifiers.append("❓")
    elif hasattr(item, 'suspicion') and item.suspicion == "confirmed":
        modifiers.append("✓")
    
    if hasattr(item, 'antecedent') and item.antecedent == "history":
        modifiers.append("📅")
    elif hasattr(item, 'antecedent') and item.antecedent == "current":
        modifiers.append("⏰")
    
    return " ".join(modifiers) if modifiers else "—"

def main():
    """Fonction principale de validation"""
    console = Console()
    
    # Affichage du titre
    title = Text("🔬 Validation des codes SNOMED CT contre la base officielle", style="bold blue")
    console.print(Panel(title, expand=False))
    
    # Note médicale d'exemple
    note_content = """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée."""
    
    # Créer l'objet MedicalNote
    medical_note = MedicalNote(
        patient_id="PAT-001",
        patient_name="Léo Martin",
        date=datetime.now().strftime("%Y-%m-%d"),
        doctor="Dr. Exemple",
        content=note_content,
        specialty="Pédiatrie"
    )
    
    try:
        # Étape 1 : Extraction avec Gemini
        console.print("\n🔄 ÉTAPE 1 : Extraction avec Google Gemini...")
        extractor = SNOMEDExtractor()
        extraction = extractor.extract_snomed_info(medical_note)
        
        # Étape 2 : Validation avec base officielle
        console.print("\n🔄 ÉTAPE 2 : Validation avec base SNOMED CT officielle...")
        validator = SNOMEDValidator()
        validation_stats = validator.validate_extraction_result(extraction)
        
        if "error" in validation_stats:
            console.print(f"❌ [red]Erreur de validation : {validation_stats['error']}[/red]")
            return 1
        
        # Affichage des résultats de validation
        console.print("\n" + "="*80)
        console.print("🎯 RÉSULTATS DE VALIDATION")
        console.print("="*80)
        
        # Statistiques globales
        total = validation_stats["total_codes"]
        valid = validation_stats["valid_codes"]
        invalid = validation_stats["invalid_codes"]
        unknown = validation_stats["unknown_codes"]
        success_rate = (valid/total*100) if total > 0 else 0
        
        stats_text = f"""
📊 STATISTIQUES GLOBALES :
   • Total des codes analysés : {total}
   • ✅ Codes VALIDES (base officielle) : {valid}
   • ❌ Codes INVALIDES : {invalid}  
   • ❓ Codes UNKNOWN : {unknown}
   •  Taux de validité : {success_rate:.1f}%
"""
        console.print(Panel(stats_text, title="Résumé de validation", border_style="blue"))
        
        # Tableau détaillé COMPLET (pour débogage)
        table_complet = Table(title="Détail COMPLET de la validation (pour analyse)")
        table_complet.add_column("Terme Gemini", style="cyan", no_wrap=True)
        table_complet.add_column("Code Gemini", style="magenta")
        table_complet.add_column("Statut", style="bold")
        table_complet.add_column("Terme Officiel SNOMED CT", style="green")
        
        for detail in validation_stats["validation_details"]:
            status_emoji = "✅" if detail["status"] == "VALID" else "❌" if detail["status"] == "INVALID" else "❓"
            status_text = f"{status_emoji} {detail['status']}"
            
            current_official_term = detail.get("official_term", "") or ""
            if not current_official_term and detail["status"] == "VALID":
                current_official_term = "(terme non trouvé)"
            
            table_complet.add_row(
                detail["term"][:30] + "..." if len(detail["term"]) > 30 else detail["term"],
                detail["gemini_code"],
                status_text,
                current_official_term[:40] + "..." if len(current_official_term) > 40 else current_official_term
            )
        
        console.print(table_complet)
        console.print("\n" + "-"*80 + "\n") # Séparateur

        # Tableau filtré (pour le client) - AVEC MODIFIEURS CONTEXTUELS
        table_filtre = Table(title="Tableau CLIENT : Correspondances SNOMED CT valides avec modifieurs contextuels")
        table_filtre.add_column("Terme Gemini", style="cyan", no_wrap=True)
        table_filtre.add_column("Code Gemini", style="magenta")
        table_filtre.add_column("Terme Officiel SNOMED CT", style="green")
        table_filtre.add_column("Modifieurs", style="yellow", justify="center")
        
        # Créer un dictionnaire pour retrouver les objets originaux
        all_items = {}
        for finding in extraction.clinical_findings:
            all_items[finding.term.lower()] = finding
        for procedure in extraction.procedures:
            all_items[procedure.term.lower()] = procedure
        for structure in extraction.body_structures:
            all_items[structure.term.lower()] = structure
        
        filtered_rows_count = 0
        for detail in validation_stats["validation_details"]:
            official_term_pour_filtre = detail.get("official_term", "") or ""
            
            if detail["status"] == "VALID" and official_term_pour_filtre and official_term_pour_filtre != "(terme non trouvé)":
                filtered_rows_count += 1
                
                # Récupérer l'objet original pour les modifieurs
                original_item = all_items.get(detail["term"].lower())
                modifiers_text = format_modifiers(original_item) if original_item else "—"
                
                table_filtre.add_row(
                    detail["term"][:30] + "..." if len(detail["term"]) > 30 else detail["term"],
                    detail["gemini_code"],
                    official_term_pour_filtre[:40] + "..." if len(official_term_pour_filtre) > 40 else official_term_pour_filtre,
                    modifiers_text
                )
        
        console.print(table_filtre)
        
        if filtered_rows_count == 0 and total > 0:
            console.print("\nℹ️ [yellow]CLIENT : Aucun code Gemini n'a correspondu à un code SNOMED CT valide avec un terme officiel identifiable.[/yellow]")

        # Légende des modifieurs
        legend_text = """
🔗 LÉGENDE DES MODIFIEURS :
   ✅ Positif / ❌ Négatif  |  🧑 Patient / 👨‍👩‍👧‍👦 Familial  |  ✓ Confirmé / ❓ Suspecté  |  ⏰ Actuel / 📅 Antécédent
"""
        console.print(Panel(legend_text, title="Légende", border_style="cyan"))

        # Conclusion
        if total > 0:
            success_rate = (valid / total) * 100
            if success_rate >= 80:
                console.print(f"\n🎉 [bold green]EXCELLENT ! {success_rate:.1f}% de codes valides - Gemini génère des codes SNOMED CT officiels ![/bold green]")
            elif success_rate >= 60:
                console.print(f"\n👍 [yellow]BON ! {success_rate:.1f}% de codes valides - Performance correcte[/yellow]")
            else:
                console.print(f"\n⚠️  [red]ATTENTION ! {success_rate:.1f}% de codes valides - Amélioration nécessaire[/red]")
        else:
            console.print("\n❌ [red]Aucun code à valider[/red]")
        
    except Exception as e:
        console.print(f"\n❌ [red]Erreur : {e}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 