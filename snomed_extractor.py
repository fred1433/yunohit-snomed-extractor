import google.generativeai as genai
import json
import re
from typing import Dict, Any
from config import Config
from models import MedicalNote, SNOMEDExtraction, ClinicalFinding, Procedure, BodyStructure

class SNOMEDExtractor:
    """Extracteur d'informations SNOMED CT à partir de notes médicales"""
    
    def __init__(self):
        """Initialiser l'extracteur avec le modèle Gemini"""
        Config.validate()
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        # Modèle sans config pour éviter les blocages de sécurité
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def create_extraction_prompt(self, medical_note: str) -> str:
        """Créer un prompt éducatif simple pour extraction complète"""
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
    
    def create_terms_extraction_prompt(self, medical_note: str) -> str:
        """Créer un prompt pour extraire SEULEMENT les termes médicaux et modifieurs (SANS codes SNOMED)"""
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
      "negation": "positive/negative",
      "famille": "patient/family", 
      "suspicion": "confirmed/suspected",
      "antecedent": "current/history"
    }}
  ]
}}

RÈGLES pour les modifieurs :
- négation : "positive" si présent, "negative" si absent/nié
- famille : "patient" pour le patient, "family" pour antécédent familial
- suspicion : "confirmed" si certain, "suspected" si suspecté
- antecedent : "current" si actuel, "history" si antécédent médical

Retourne uniquement le JSON avec les termes des 3 hiérarchies ciblées (SANS codes SNOMED)."""
        return prompt

    def create_codes_search_prompt(self, terms_list: list) -> str:
        """Créer un prompt spécialisé pour rechercher SEULEMENT les codes SNOMED CT"""
        terms_text = "\n".join([f"- {term['terme']} ({term['categorie']})" for term in terms_list])
        
        prompt = f"""Tu es un expert en terminologie SNOMED CT. 

Voici une liste de termes médicaux déjà classifiés par hiérarchie :

{terms_text}

Ta SEULE mission : Trouve le code SNOMED CT le plus précis et approprié pour chaque terme.

🎯 **CONSIGNES CRITIQUES** :
- Concentre-toi UNIQUEMENT sur la précision des codes SNOMED CT
- Utilise tes connaissances approfondies de la terminologie SNOMED CT
- Privilégie les codes les plus spécifiques possibles
- Assure-toi que chaque code correspond exactement au terme médical

Format JSON requis :
{{
  "codes_snomed": [
    {{
      "terme": "terme médical exact",
      "code_snomed": "code numérique SNOMED CT précis"
    }}
  ]
}}

Exemples de codes de référence :
- Varicelle: 38907003
- Éruption cutanée: 271807003  
- Antihistaminique: 432102000
- Membres: 445662006
- Prurit: 418363000
- Lésions vésiculeuses: 247464001

Retourne uniquement le JSON avec les codes SNOMED CT optimaux."""
        return prompt
    
    def extract_snomed_info(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """Extraction ONE-SHOT avec codes SNOMED CT et modifieurs contextuels"""
        try:
            print("🔍 Extraction simple avec modifieurs contextuels...")
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
    
    def extract_two_step(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """🆕 MÉTHODE EXPÉRIMENTALE : Extraction en 2 étapes séparées"""
        try:
            print("🔬 Extraction expérimentale en 2 étapes...")
            
            # ÉTAPE 1 : Extraction des termes et modifieurs (SANS codes)
            print("📋 Étape 1 : Extraction des termes médicaux...")
            terms_prompt = self.create_terms_extraction_prompt(medical_note.content)
            terms_response = self.model.generate_content(terms_prompt)
            
            if not self._is_valid_response(terms_response):
                print("❌ Échec étape 1")
                return self._create_empty_extraction(medical_note)
            
            terms_text = self._extract_response_text(terms_response)
            terms_data = self.parse_gemini_response(terms_text)
            termes_medicaux = terms_data.get("termes_medicaux", [])
            
            if not termes_medicaux:
                print("❌ Aucun terme médical extrait")
                return self._create_empty_extraction(medical_note)
            
            print(f"✅ {len(termes_medicaux)} termes extraits")
            
            # ÉTAPE 2 : Recherche spécialisée des codes SNOMED
            print("🎯 Étape 2 : Recherche des codes SNOMED CT...")
            codes_prompt = self.create_codes_search_prompt(termes_medicaux)
            codes_response = self.model.generate_content(codes_prompt)
            
            if not self._is_valid_response(codes_response):
                print("❌ Échec étape 2")
                return self._create_empty_extraction(medical_note)
            
            codes_text = self._extract_response_text(codes_response)
            codes_data = self.parse_gemini_response(codes_text)
            codes_snomed = codes_data.get("codes_snomed", [])
            
            # Fusionner les résultats
            print("🔗 Fusion des résultats...")
            for terme in termes_medicaux:
                # Trouver le code correspondant
                code_found = None
                for code_item in codes_snomed:
                    if code_item.get("terme") == terme.get("terme"):
                        code_found = code_item.get("code_snomed", "UNKNOWN")
                        break
                
                terme["code_classification"] = code_found or "UNKNOWN"
            
            # Convertir en objets SNOMED CT (même logique que méthode originale)
            clinical_findings = []
            procedures = []
            body_structures = []
            
            for terme_data in termes_medicaux:
                terme = terme_data.get("terme", "")
                categorie = terme_data.get("categorie", "").lower()
                code_snomed = terme_data.get("code_classification", "UNKNOWN")
                
                # Extraire les modifieurs contextuels
                negation = terme_data.get("negation", "positive")
                family = terme_data.get("famille", "patient")
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
            
            print(f"✅ Extraction 2-étapes réussie : {len(clinical_findings)} constatations, {len(procedures)} procédures, {len(body_structures)} structures")
            return SNOMEDExtraction(
                original_note=medical_note,
                clinical_findings=clinical_findings,
                procedures=procedures,
                body_structures=body_structures
            )
            
        except Exception as e:
            print(f"❌ Erreur extraction 2-étapes : {e}")
            return self._create_empty_extraction(medical_note)
    
    def _is_valid_response(self, response) -> bool:
        """Vérifier si la réponse Gemini est valide"""
        if not hasattr(response, 'candidates') or not response.candidates:
            return False
        
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
            return False
        
        return True
    
    def _extract_response_text(self, response) -> str:
        """Extraire le texte de la réponse Gemini"""
        if hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                return "".join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
        return "" 