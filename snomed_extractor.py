import google.generativeai as genai
import json
import re
from typing import Dict, Any
from config import Config
from models import MedicalNote, SNOMEDExtraction, ClinicalFinding, Procedure, BodyStructure
from api_security import security_manager

class SNOMEDExtractor:
    """Extracteur d'informations SNOMED CT à partir de notes médicales"""
    
    def __init__(self):
        """Initialiser l'extracteur avec le modèle Gemini"""
        Config.validate()
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        # Modèle configurable
        self.model_name = Config.GEMINI_MODEL
        self.model = genai.GenerativeModel(self.model_name)
    
    def set_model(self, model_name: str):
        """Changer le modèle utilisé"""
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
        print(f"🔄 Modèle changé vers : {model_name}")
    
    def create_extraction_prompt(self, medical_note: str) -> str:
        """Créer un prompt éducatif optimisé pour extraction complète"""
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
        """Extraction optimisée ONE-SHOT avec codes SNOMED CT et modifieurs contextuels"""
        try:
            # 🛡️ SÉCURITÉ : Vérifier les limites avant l'appel API
            can_proceed, message = security_manager.can_make_request()
            if not can_proceed:
                print(f"🚫 EXTRACTION BLOQUÉE : {message}")
                print("⏰ Réessayez plus tard ou contactez l'administrateur")
                return self._create_empty_extraction(medical_note)
            
            print(f"🔒 Sécurité : {message}")
            print("🔍 Extraction ONE-SHOT avec modifieurs contextuels...")
            
            prompt = self.create_extraction_prompt(medical_note.content)
            
            response = self.model.generate_content(prompt)
            
            # 🛡️ SÉCURITÉ : Enregistrer l'appel API réussi
            security_manager.record_api_call(estimated_cost=0.015)  # Coût estimé pour Gemini Flash
            security_manager.print_usage_warning()
            
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
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                print("❌ Aucun JSON trouvé dans la réponse")
                return {"termes_medicaux": []}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON : {e}")
            print(f"Réponse reçue : {response_text[:500]}...")
            return {"termes_medicaux": []}
    
    def _extract_response_text(self, response) -> str:
        """Extraire le texte d'une réponse Gemini"""
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                print("❌ Réponse bloquée par filtres de sécurité")
                return ""
            
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(candidate.content, 'parts') and candidate.content.parts:
                return "".join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
        
        print("❌ Pas de texte dans la réponse")
        return ""
    
    def _create_empty_extraction(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """Créer une extraction vide en cas d'erreur"""
        return SNOMEDExtraction(
            original_note=medical_note,
            clinical_findings=[],
            procedures=[],
            body_structures=[]
        )
    
    def extract_triple_parallel(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """Extraction avec 3 appels parallèles pour améliorer la robustesse"""
        try:
            # 🛡️ SÉCURITÉ : Vérifier les limites avant les appels API
            can_proceed, message = security_manager.can_make_request()
            if not can_proceed:
                print(f"🚫 EXTRACTION BLOQUÉE : {message}")
                return self._create_empty_extraction(medical_note)
            
            print(f"🔒 Sécurité : {message}")
            print("🔍 Extraction TRIPLE PARALLÈLE commencée...")
            
            prompt = self.create_extraction_prompt(medical_note.content)
            
            # Faire 3 appels parallèles avec le même prompt
            print("📋 Lancement de 3 appels parallèles à Gemini...")
            
            responses = []
            for i in range(3):
                print(f"🔄 Appel {i+1}/3...")
                response = self.model.generate_content(prompt)
                security_manager.record_api_call(estimated_cost=0.02)
                responses.append(response)
            
            print("✅ 3 appels terminés, analyse des réponses...")
            
            # Collecter tous les termes de tous les appels
            all_terms = []
            
            for i, response in enumerate(responses):
                print(f"📊 Analyse réponse {i+1}/3...")
                response_text = self._extract_response_text(response)
                if response_text:
                    parsed_data = self.parse_gemini_response(response_text)
                    terms = parsed_data.get("termes_medicaux", [])
                    print(f"   → {len(terms)} termes extraits")
                    all_terms.extend(terms)
                else:
                    print(f"   → Échec de l'extraction")
            
            print(f"🔄 Total combiné : {len(all_terms)} termes")
            
            # Dédupliquer par terme (garder le premier trouvé)
            seen_terms = set()
            unique_terms = []
            for term_data in all_terms:
                terme = term_data.get("terme", "").lower().strip()
                if terme and terme not in seen_terms:
                    seen_terms.add(terme)
                    unique_terms.append(term_data)
            
            print(f"✅ Après déduplication : {len(unique_terms)} termes uniques")
            
            # Convertir en objets SNOMED CT
            clinical_findings = []
            procedures = []
            body_structures = []
            
            for terme_data in unique_terms:
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
                        context="Extrait par méthode triple parallèle",
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
                        context="Extrait par méthode triple parallèle",
                        snomed_code=code_snomed,
                        snomed_term_fr=terme,
                        negation=negation,
                        family=family,
                        suspicion=suspicion,
                        antecedent=antecedent
                    ))
                elif "structure" in categorie or "body_structure" in categorie:
                    body_structures.append(BodyStructure(
                        term=terme,
                        description=f"Structure corporelle : {terme}",
                        context="Extrait par méthode triple parallèle",
                        snomed_code=code_snomed,
                        snomed_term_fr=terme,
                        negation=negation,
                        family=family,
                        suspicion=suspicion,
                        antecedent=antecedent
                    ))
            
            print(f"✅ Extraction TRIPLE PARALLÈLE réussie : {len(clinical_findings)} constatations, {len(procedures)} procédures, {len(body_structures)} structures")
            security_manager.print_usage_warning()
            
            return SNOMEDExtraction(
                original_note=medical_note,
                clinical_findings=clinical_findings,
                procedures=procedures,
                body_structures=body_structures
            )
            
        except Exception as e:
            print(f"❌ Erreur extraction triple parallèle : {e}")
            return self._create_empty_extraction(medical_note)
    
    def extract_triple_with_validation_fusion(self, medical_note: MedicalNote) -> SNOMEDExtraction:
        """
        MÉTHODE ULTIME : 3 extractions + validation + fusion de TOUS les résultats validés
        Collecte et combine tous les termes validés des 3 extractions pour maximiser le résultat
        """
        try:
            # 🛡️ SÉCURITÉ : Vérifier les limites avant les appels API
            can_proceed, message = security_manager.can_make_request()
            if not can_proceed:
                print(f"🚫 EXTRACTION BLOQUÉE : {message}")
                return self._create_empty_extraction(medical_note)
            
            print(f"🔒 Sécurité : {message}")
            print("🎯 EXTRACTION TRIPLE + VALIDATION + FUSION commencée...")
            
            # Charger le validateur une seule fois pour toutes les validations
            from snomed_validator import SNOMEDValidator
            validator = SNOMEDValidator()
            print("✅ Validateur SNOMED CT chargé")
            
            # Lancer 3 extractions séquentielles avec validation immédiate
            all_valid_items = []
            extraction_stats = []
            
            for i in range(3):
                print(f"\n🔄 === EXTRACTION {i+1}/3 ===")
                
                # Extraction avec Gemini
                extraction = self.extract_snomed_info(medical_note)
                security_manager.record_api_call(estimated_cost=0.02)
                
                # Collecter tous les items extraits
                all_items = (extraction.clinical_findings + 
                           extraction.procedures + 
                           extraction.body_structures)
                
                print(f"📊 Extraction {i+1} : {len(all_items)} termes extraits")
                
                # Validation immédiate des termes de cette extraction
                valid_items_this_round = []
                for item in all_items:
                    if validator.validate_code(item.snomed_code):
                        valid_items_this_round.append(item)
                
                print(f"✅ Validation {i+1} : {len(valid_items_this_round)}/{len(all_items)} termes validés")
                
                # Ajouter à la collection globale
                all_valid_items.extend(valid_items_this_round)
                
                extraction_stats.append({
                    'total': len(all_items),
                    'valid': len(valid_items_this_round),
                    'rate': (len(valid_items_this_round) / len(all_items) * 100) if len(all_items) > 0 else 0
                })
            
            print(f"\n🔄 Total avant déduplication : {len(all_valid_items)} termes validés")
            
            # DÉDUPLICATION par code SNOMED (pas par terme)
            seen_codes = set()
            unique_valid_items = []
            
            for item in all_valid_items:
                code = item.snomed_code
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    unique_valid_items.append(item)
                    print(f"   ➕ {item.term} ({code})")
                else:
                    print(f"   🔄 Doublon ignoré : {item.term} ({code})")
            
            print(f"✨ Après déduplication : {len(unique_valid_items)} termes uniques validés")
            
            # Réorganiser par type pour créer l'objet final
            final_clinical_findings = []
            final_procedures = []
            final_body_structures = []
            
            for item in unique_valid_items:
                if hasattr(item, '__class__'):
                    class_name = item.__class__.__name__
                    if class_name == 'ClinicalFinding':
                        final_clinical_findings.append(item)
                    elif class_name == 'Procedure':
                        final_procedures.append(item)
                    elif class_name == 'BodyStructure':
                        final_body_structures.append(item)
            
            # Statistiques finales
            print(f"\n🎯 RÉSULTAT FINAL DE LA FUSION :")
            print(f"   🔍 {len(final_clinical_findings)} constatations cliniques")
            print(f"   ⚕️  {len(final_procedures)} procédures/traitements")
            print(f"   🫀 {len(final_body_structures)} structures corporelles")
            print(f"   📊 TOTAL : {len(unique_valid_items)} entités validées")
            
            # Afficher les statistiques par extraction
            print(f"\n📈 STATISTIQUES PAR EXTRACTION :")
            for i, stats in enumerate(extraction_stats, 1):
                print(f"   Extraction {i} : {stats['valid']}/{stats['total']} ({stats['rate']:.1f}%)")
            
            # Calculer le gain vs méthode simple
            total_extractions = sum(stats['total'] for stats in extraction_stats)
            total_valid_before_fusion = sum(stats['valid'] for stats in extraction_stats)
            gain = len(unique_valid_items) - max(stats['valid'] for stats in extraction_stats)
            
            print(f"\n🚀 PERFORMANCE DE LA FUSION :")
            print(f"   📊 Avant fusion : max {max(stats['valid'] for stats in extraction_stats)} entités validées")
            print(f"   ✨ Après fusion : {len(unique_valid_items)} entités uniques")
            print(f"   📈 GAIN : +{gain} entités supplémentaires !")
            
            security_manager.print_usage_warning()
            
            return SNOMEDExtraction(
                original_note=medical_note,
                clinical_findings=final_clinical_findings,
                procedures=final_procedures,
                body_structures=final_body_structures
            )
            
        except Exception as e:
            print(f"❌ Erreur extraction triple + fusion : {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_extraction(medical_note) 