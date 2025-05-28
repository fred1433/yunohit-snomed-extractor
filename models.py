from dataclasses import dataclass
from typing import List, Optional
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class ClinicalFinding:
    """Constatation clinique (symptôme, signe, diagnostic)"""
    term: str  # Le terme médical trouvé
    description: str  # Description de la constatation
    context: str  # Contexte dans la note médicale
    severity: Optional[str] = None  # Sévérité si mentionnée
    snomed_code: Optional[str] = None  # Code SCTID SNOMED CT
    snomed_term_fr: Optional[str] = None  # Terme officiel SNOMED CT français
    # Nouveaux modifieurs contextuels
    negation: Optional[str] = None  # "positive" ou "negative"
    family: Optional[str] = None    # "patient" ou "family"
    suspicion: Optional[str] = None # "confirmed" ou "suspected"
    antecedent: Optional[str] = None # "current" ou "history"

@dataclass_json
@dataclass
class Procedure:
    """Intervention/Procédure médicale"""
    term: str
    description: str
    context: str
    method: Optional[str] = None
    snomed_code: Optional[str] = None
    snomed_term_fr: Optional[str] = None
    # Nouveaux modifieurs contextuels
    negation: Optional[str] = None  # "positive" ou "negative"
    family: Optional[str] = None    # "patient" ou "family"
    suspicion: Optional[str] = None # "confirmed" ou "suspected"
    antecedent: Optional[str] = None # "current" ou "history"

@dataclass
class BodyStructure:
    """Structure corporelle (anatomie)"""
    term: str
    description: str
    context: str
    laterality: Optional[str] = None  # droite/gauche
    snomed_code: Optional[str] = None
    snomed_term_fr: Optional[str] = None
    # Nouveaux modifieurs contextuels
    negation: Optional[str] = None  # "positive" ou "negative"
    family: Optional[str] = None    # "patient" ou "family"
    suspicion: Optional[str] = None # "confirmed" ou "suspected"
    antecedent: Optional[str] = None # "current" ou "history"

@dataclass_json
@dataclass
class MedicalNote:
    """Note médicale complète"""
    patient_id: str
    patient_name: str
    date: str
    doctor: str
    content: str
    specialty: str

@dataclass_json
@dataclass
class SNOMEDExtraction:
    """Résultat de l'extraction SNOMED CT"""
    original_note: MedicalNote
    clinical_findings: List[ClinicalFinding]
    procedures: List[Procedure]
    body_structures: List[BodyStructure]
    
    def to_summary(self) -> str:
        """Créer un résumé textuel de l'extraction"""
        summary = f"=== Extraction SNOMED CT ===\n\n"
        summary += f"Patient: {self.original_note.patient_name} ({self.original_note.patient_id})\n"
        summary += f"Date: {self.original_note.date}\n"
        summary += f"Médecin: {self.original_note.doctor}\n"
        summary += f"Spécialité: {self.original_note.specialty}\n\n"
        
        summary += f"📋 CONSTATATIONS CLINIQUES ({len(self.clinical_findings)}):\n"
        for i, finding in enumerate(self.clinical_findings, 1):
            summary += f"  {i}. {finding.term}\n"
            summary += f"     Description: {finding.description}\n"
            summary += f"     Contexte: {finding.context}\n"
            if finding.snomed_code:
                summary += f"     🏷️  Code SNOMED CT: {finding.snomed_code}\n"
            if finding.snomed_term_fr:
                summary += f"     🇫🇷 Terme SNOMED FR: {finding.snomed_term_fr}\n"
            
            # Afficher les modifieurs contextuels
            modifiers = []
            if finding.negation == "negative":
                modifiers.append("❌ Négatif")
            elif finding.negation == "positive":
                modifiers.append("✅ Positif")
            
            if finding.family == "family":
                modifiers.append("👨‍👩‍👧‍👦 Familial")
            elif finding.family == "patient":
                modifiers.append("🧑 Patient")
            
            if finding.suspicion == "suspected":
                modifiers.append("❓ Suspecté")
            elif finding.suspicion == "confirmed":
                modifiers.append("✓ Confirmé")
            
            if finding.antecedent == "history":
                modifiers.append("📅 Antécédent")
            elif finding.antecedent == "current":
                modifiers.append("⏰ Actuel")
            
            if modifiers:
                summary += f"     📊 Modifieurs: {' | '.join(modifiers)}\n"
            
            if finding.severity:
                summary += f"     Sévérité: {finding.severity}\n"
            summary += "\n"
        
        summary += f"🏥 INTERVENTIONS/PROCÉDURES ({len(self.procedures)}):\n"
        for i, procedure in enumerate(self.procedures, 1):
            summary += f"  {i}. {procedure.term}\n"
            summary += f"     Description: {procedure.description}\n"
            summary += f"     Contexte: {procedure.context}\n"
            if procedure.snomed_code:
                summary += f"     🏷️  Code SNOMED CT: {procedure.snomed_code}\n"
            if procedure.snomed_term_fr:
                summary += f"     🇫🇷 Terme SNOMED FR: {procedure.snomed_term_fr}\n"
            
            # Afficher les modifieurs contextuels
            modifiers = []
            if procedure.negation == "negative":
                modifiers.append("❌ Négatif")
            elif procedure.negation == "positive":
                modifiers.append("✅ Positif")
            
            if procedure.family == "family":
                modifiers.append("👨‍👩‍👧‍👦 Familial")
            elif procedure.family == "patient":
                modifiers.append("🧑 Patient")
            
            if procedure.suspicion == "suspected":
                modifiers.append("❓ Suspecté")
            elif procedure.suspicion == "confirmed":
                modifiers.append("✓ Confirmé")
            
            if procedure.antecedent == "history":
                modifiers.append("📅 Antécédent")
            elif procedure.antecedent == "current":
                modifiers.append("⏰ Actuel")
            
            if modifiers:
                summary += f"     📊 Modifieurs: {' | '.join(modifiers)}\n"
            
            if procedure.method:
                summary += f"     Méthode: {procedure.method}\n"
            summary += "\n"
        
        summary += f"🫀 STRUCTURES CORPORELLES ({len(self.body_structures)}):\n"
        for i, structure in enumerate(self.body_structures, 1):
            summary += f"  {i}. {structure.term}\n"
            summary += f"     Description: {structure.description}\n"
            summary += f"     Contexte: {structure.context}\n"
            if structure.snomed_code:
                summary += f"     🏷️  Code SNOMED CT: {structure.snomed_code}\n"
            if structure.snomed_term_fr:
                summary += f"     🇫🇷 Terme SNOMED FR: {structure.snomed_term_fr}\n"
            
            # Afficher les modifieurs contextuels
            modifiers = []
            if structure.negation == "negative":
                modifiers.append("❌ Négatif")
            elif structure.negation == "positive":
                modifiers.append("✅ Positif")
            
            if structure.family == "family":
                modifiers.append("👨‍👩‍👧‍👦 Familial")
            elif structure.family == "patient":
                modifiers.append("🧑 Patient")
            
            if structure.suspicion == "suspected":
                modifiers.append("❓ Suspecté")
            elif structure.suspicion == "confirmed":
                modifiers.append("✓ Confirmé")
            
            if structure.antecedent == "history":
                modifiers.append("📅 Antécédent")
            elif structure.antecedent == "current":
                modifiers.append("⏰ Actuel")
            
            if modifiers:
                summary += f"     📊 Modifieurs: {' | '.join(modifiers)}\n"
            
            if structure.laterality:
                summary += f"     Latéralité: {structure.laterality}\n"
            summary += "\n"
        
        return summary 