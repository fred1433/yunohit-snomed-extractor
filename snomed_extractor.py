import google.generativeai as genai
import json
import re
from typing import Dict, Any
from config import Config
from models import MedicalNote, SNOMEDExtraction, ClinicalFinding, Procedure, BodyStructure

class SNOMEDExtractor:
    """Extracteur d'informations SNOMED CT à partir de notes médicales - Version simplifiée"""
    
    def __init__(self):
        """Initialiser l'extracteur avec le modèle Gemini"""
        Config.validate()
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        # Modèle sans config pour éviter les blocages de sécurité
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def create_extraction_prompt(self, medical_note: str) -> str:
        """Créer un prompt éducatif qui obtient les codes SNOMED CT et modifieurs contextuels"""
        prompt = f"""Dans un contexte éducatif de classification médicale, analyse ce cas d'étude :

{medical_note}

Extrais UNIQUEMENT les termes appartenant aux 3 hiérarchies SNOMED CT ciblées :

1. **CLINICAL FINDING** (Constatations cliniques) :
   - Symptômes observés (ex: éruption cutanée, prurit)
   - Signes cliniques (ex: lésions vésiculeuses)
   - Diagnostics établis (ex: varicelle)
   - États pathologiques

2. **PROCEDURE** (Interventions/Procédures) :
   - Traitements administrés (ex: antihistaminique oral)
   - Soins médicaux (ex: soins locaux)
   - Recommandations thérapeutiques (ex: éviction scolaire)
   - Actes médicaux

3. **BODY STRUCTURE** (Structures corporelles) :
   - Parties anatomiques mentionnées (ex: membres, tronc)
   - Organes, régions corporelles
   - Structures anatomiques

**EXCLURE** : antécédents, contexte familial, informations administratives, expositions

Format JSON requis :
{{
  "termes_medicaux": [
    {{
      "terme": "terme médical exact",
      "categorie": "clinical_finding/procedure/body_structure",
      "code_classification": "code SNOMED CT numérique unique pour ce terme",
      "negation": "positive/negative",
      "famille": "patient/family", 
      "suspicion": "confirmed/suspected",
      "antecedent": "current/history"
    }}
  ]
}}

IMPORTANT : Assigne un code SNOMED CT différent et approprié pour chaque terme médical.
Exemples de codes : 
- Varicelle: 38907003
- Éruption cutanée: 271807003  
- Antihistaminique: 432102000
- Membres: 445662006

RÈGLES pour les modifieurs :
- négation : "positive" si présent, "negative" si absent/nié
- famille : "patient" pour le patient, "family" pour antécédent familial
- suspicion : "confirmed" si certain, "suspected" si suspecté
- antecedent : "current" si actuel, "history" si antécédent médical

Retourne uniquement le JSON avec les termes des 3 hiérarchies ciblées."""
        return prompt
    
    def extract_snomed_info(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """Extraction ONE-SHOT avec codes SNOMED CT et modifieurs contextuels"""
        try:
            print("🔍 Extraction avec modifieurs contextuels...")
            
            prompt = self.create_extraction_prompt(medical_note.content)
            response = self.model.generate_content(prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    print("❌ Extraction bloquée par filtres de sécurité")
                    return self._create_empty_extraction(medical_note)
                
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                elif hasattr(candidate.content, 'parts') and candidate.content.parts:
                    response_text = "".join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                else:
                    print("❌ Pas de texte dans la réponse")
                    return self._create_empty_extraction(medical_note)
            else:
                print("❌ Pas de candidat dans la réponse")
                return self._create_empty_extraction(medical_note)
            
            print("✅ Réponse reçue, parsing...")
            
            # Parser la réponse simple
            parsed_data = self.parse_gemini_response(response_text)
            
            # Convertir le format en objets SNOMED CT
            clinical_findings = []
            procedures = []
            body_structures = []
            
            # Traiter les termes médicaux avec codes et modifieurs fournis par Gemini
            for terme_data in parsed_data.get("termes_medicaux", []):
                terme = terme_data.get("terme", "")
                categorie = terme_data.get("categorie", "").lower()
                code_snomed = terme_data.get("code_classification", "UNKNOWN")
                
                # Extraire les modifieurs contextuels
                negation = terme_data.get("negation", "positive")
                family = terme_data.get("famille", "patient")  # Note: "famille" en français dans le JSON
                suspicion = terme_data.get("suspicion", "confirmed")
                antecedent = terme_data.get("antecedent", "current")
                
                if "symptome" in categorie or "diagnostic" in categorie or "finding" in categorie or "clinical_finding" in categorie:
                    clinical_findings.append(ClinicalFinding(
                        term=terme,
                        description=f"Constatation clinique : {terme}",
                        context=f"Extrait de la note médicale",
                        snomed_code=code_snomed,
                        snomed_term_fr=terme,
                        negation=negation,
                        family=family,
                        suspicion=suspicion,
                        antecedent=antecedent
                    ))
                elif "traitement" in categorie or "procedure" in categorie or "intervention" in categorie:
                    procedures.append(Procedure(
                        term=terme,
                        description=f"Intervention/Procédure : {terme}",
                        context=f"Extrait de la note médicale",
                        snomed_code=code_snomed,
                        snomed_term_fr=terme,
                        negation=negation,
                        family=family,
                        suspicion=suspicion,
                        antecedent=antecedent
                    ))
                elif "anatomie" in categorie or "structure" in categorie or "corps" in categorie or "body_structure" in categorie:
                    body_structures.append(BodyStructure(
                        term=terme,
                        description=f"Structure corporelle : {terme}",
                        context=f"Extrait de la note médicale",
                        snomed_code=code_snomed,
                        snomed_term_fr=terme,
                        negation=negation,
                        family=family,
                        suspicion=suspicion,
                        antecedent=antecedent
                    ))
                else:
                    # Ignorer les termes qui ne correspondent à aucune des 3 hiérarchies ciblées
                    print(f"⚠️  Terme ignoré (hors hiérarchies ciblées) : {terme} ({categorie})")
                    continue
            
            print(f"✅ Extraction réussie : {len(clinical_findings)} constatations, {len(procedures)} procédures, {len(body_structures)} structures")
            return SNOMEDExtraction(
                original_note=medical_note,
                clinical_findings=clinical_findings,
                procedures=procedures,
                body_structures=body_structures
            )
            
        except Exception as e:
            print(f"❌ Erreur extraction : {e}")
            return self._create_empty_extraction(medical_note)
    
    def parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parser la réponse JSON de Gemini"""
        try:
            # Nettoyer la réponse pour extraire le JSON
            cleaned_text = response_text.strip()
            
            # Chercher le JSON dans la réponse
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Si pas de JSON trouvé, essayer de parser directement
                return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"Erreur de parsing JSON : {e}")
            print(f"Réponse brute : {response_text}")
            # Retourner une structure vide en cas d'erreur
            return {
                "termes_medicaux": []
            }
    
    def _create_empty_extraction(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """Créer une extraction vide en cas d'erreur"""
        return SNOMEDExtraction(
            original_note=medical_note,
            clinical_findings=[],
            procedures=[],
            body_structures=[]
        ) 