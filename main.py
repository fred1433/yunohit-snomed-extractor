#!/usr/bin/env python3
"""
Script principal pour l'extraction d'informations SNOMED CT
à partir de notes médicales avec Google Gemini
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from models import MedicalNote
from snomed_extractor import SNOMEDExtractor

def main():
    """Fonction principale"""
    console = Console()
    
    # Affichage du titre
    title = Text("🏥 Extracteur SNOMED CT avec Codes", style="bold blue")
    console.print(Panel(title, expand=False))
    
    # Note médicale d'exemple fournie par l'utilisateur
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
    
    # Afficher la note originale
    console.print("\n📄 NOTE MÉDICALE ORIGINALE :")
    console.print(Panel(note_content, title="Note médicale", border_style="green"))
    
    try:
        # Initialiser l'extracteur
        console.print("\n🚀 Initialisation de l'extracteur SNOMED CT...")
        extractor = SNOMEDExtractor()
        
        # Effectuer l'extraction ONE-SHOT avec codes SNOMED CT et modifieurs contextuels
        console.print("🔄 Extraction avec modifieurs contextuels en cours...")
        extraction = extractor.extract_snomed_info(medical_note)
        
        # Afficher les résultats
        console.print("\n" + "="*80)
        console.print(extraction.to_summary())
        
        # Statistiques
        total_findings = len(extraction.clinical_findings)
        total_procedures = len(extraction.procedures)
        total_structures = len(extraction.body_structures)
        total_items = total_findings + total_procedures + total_structures
        
        # Compter les codes SNOMED CT trouvés
        codes_found = 0
        for finding in extraction.clinical_findings:
            if finding.snomed_code and finding.snomed_code != "UNKNOWN":
                codes_found += 1
        for procedure in extraction.procedures:
            if procedure.snomed_code and procedure.snomed_code != "UNKNOWN":
                codes_found += 1
        for structure in extraction.body_structures:
            if structure.snomed_code and structure.snomed_code != "UNKNOWN":
                codes_found += 1
        
        stats_text = f"""
📊 STATISTIQUES D'EXTRACTION :
   • Constatations cliniques : {total_findings}
   • Interventions/Procédures : {total_procedures}
   • Structures corporelles : {total_structures}
   • Total d'éléments extraits : {total_items}
   🏷️  Codes SNOMED CT trouvés : {codes_found}/{total_items}
"""
        console.print(Panel(stats_text, title="Résumé", border_style="blue"))
        
    except Exception as e:
        console.print(f"\n❌ [red]Erreur : {e}[/red]")
        console.print("Vérifiez votre configuration et votre connexion.")
        return 1
    
    console.print("\n✅ [green]Traitement terminé avec succès ![/green]")
    return 0

if __name__ == "__main__":
    exit(main()) 