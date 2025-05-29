import google.generativeai as genai
import json
import re
from typing import Dict, Any
from config import Config
from models import MedicalNote, SNOMEDExtraction, ClinicalFinding, Procedure, BodyStructure
from api_security import security_manager
import asyncio
import time
from snomed_validator import SNOMEDValidator

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

Extrais UNIQUEMENT les concepts médicaux appartenant aux 3 hiérarchies SNOMED CT ciblées :

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
  "concepts_medicaux": [
    {{
      "concept": "concept médical normalisé",
      "categorie": "clinical_finding/procedure/body_structure",
      "code_classification": "code SNOMED CT numérique unique pour ce concept",
      "negation": "positive/negative",
      "famille": "patient/family", 
      "suspicion": "confirmed/suspected",
      "antecedent": "current/history"
    }}
  ]
}}

IMPORTANT : Assigne un code SNOMED CT différent et approprié pour chaque concept médical.
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

Retourne uniquement le JSON avec les concepts des 3 hiérarchies ciblées."""
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
            for terme_data in parsed_data.get("concepts_medicaux", []):
                terme = terme_data.get("concept", "")
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
                return {"concepts_medicaux": []}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON : {e}")
            print(f"Réponse reçue : {response_text[:500]}...")
            return {"concepts_medicaux": []}
    
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
                    terms = parsed_data.get("concepts_medicaux", [])
                    print(f"   → {len(terms)} termes extraits")
                    all_terms.extend(terms)
                else:
                    print(f"   → Échec de l'extraction")
            
            print(f"🔄 Total combiné : {len(all_terms)} termes")
            
            # Dédupliquer par terme (garder le premier trouvé)
            seen_terms = set()
            unique_terms = []
            for term_data in all_terms:
                terme = term_data.get("concept", "").lower().strip()
                if terme and terme not in seen_terms:
                    seen_terms.add(terme)
                    unique_terms.append(term_data)
            
            print(f"✅ Après déduplication : {len(unique_terms)} termes uniques")
            
            # Convertir en objets SNOMED CT
            clinical_findings = []
            procedures = []
            body_structures = []
            
            for terme_data in unique_terms:
                terme = terme_data.get("concept", "")
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
    
    async def extract_triple_with_validation_fusion_v2(self, text, use_context_modifiers=True):
        """
        MÉTHODE ULTIME V2 : Triple extraction parallèle + validation SNOMED + validation sémantique finale
        
        Processus optimisé :
        1. 3 extractions Gemini Pro EN PARALLÈLE (chronométrées)
        2. Validation SNOMED de chaque extraction (chronométrée)  
        3. Fusion + déduplication par code SNOMED (chronométrée)
        4. Validation sémantique hybride SUR LE TABLEAU FINAL SEULEMENT (chronométrée)
        
        Returns:
            dict: Résultats finaux avec statistiques détaillées et temps
        """
        print("🎯 EXTRACTION ULTIME V2 : Triple extraction parallèle + validation SNOMED + validation sémantique finale")
        start_time = time.time()
        
        # Vérifications préliminaires
        if not self._security_check():
            return {"error": "Limites de sécurité dépassées"}
        
        # Initialiser le validator SNOMED
        if not hasattr(self, 'validator') or self.validator is None:
            print("✅ Validateur SNOMED CT chargé")
            self.validator = SNOMEDValidator()
        
        # === PHASE 1 : TRIPLE EXTRACTION PARALLÈLE ===
        parallel_start = time.time()
        print("🚀 Début des 3 extractions en parallèle...")
        
        async def extract_single(extraction_num):
            """Extraction individuelle avec chronométrage"""
            extraction_start = time.time()
            print(f"🔄 === EXTRACTION {extraction_num}/3 ===")
            
            # CORRECTION : Utiliser asyncio.to_thread pour vraie parallélisation
            entities = await asyncio.to_thread(
                self.extract_medical_entities, 
                text, 
                use_context_modifiers
            )
            
            extraction_time = time.time() - extraction_start
            print(f"✅ Extraction {extraction_num} terminée en ⏱️ {extraction_time:.2f}s")
            return entities, extraction_time
        
        # Exécution des 3 extractions en parallèle  
        results = await asyncio.gather(
            extract_single(1),
            extract_single(2), 
            extract_single(3)
        )
        
        parallel_time = time.time() - parallel_start
        individual_times = [result[1] for result in results]
        print(f"🎯 3 extractions parallèles terminées en ⏱️ {parallel_time:.2f}s (vs {sum(individual_times):.2f}s séquentiel = Gain: {sum(individual_times) - parallel_time:.2f}s)")
        
        # === PHASE 2 : VALIDATION SNOMED AVEC CHRONOMÉTRAGE ===
        validation_phase_start = time.time()
        print(f"\n🔍 === VALIDATION SNOMED (3 extractions) ===")
        
        all_validated_terms = []
        extraction_stats = []
        
        for i, (entities_result, _) in enumerate(results):
            extraction_num = i + 1
            all_terms = []
            
            # Correction : accès correct à la structure des données
            if entities_result and 'entities' in entities_result:
                entities = entities_result['entities']
                
                # Collecte des termes avec structure corrigée ET modifieurs contextuels
                for finding in entities.get('findings', []):
                    all_terms.append({
                        'term': finding['term'],
                        'snomed_code': finding.get('snomed_code', 'UNKNOWN'),
                        'category': finding.get('category', 'clinical_finding'),
                        'negation': finding.get('negation', 'positive'),
                        'family': finding.get('family', 'patient'),
                        'suspicion': finding.get('suspicion', 'confirmed'),
                        'antecedent': finding.get('antecedent', 'current')
                    })
                for procedure in entities.get('procedures', []):
                    all_terms.append({
                        'term': procedure['term'],
                        'snomed_code': procedure.get('snomed_code', 'UNKNOWN'),
                        'category': procedure.get('category', 'procedure'),
                        'negation': procedure.get('negation', 'positive'),
                        'family': procedure.get('family', 'patient'),
                        'suspicion': procedure.get('suspicion', 'confirmed'),
                        'antecedent': procedure.get('antecedent', 'current')
                    })
                for structure in entities.get('body_structures', []):
                    all_terms.append({
                        'term': structure['term'],
                        'snomed_code': structure.get('snomed_code', 'UNKNOWN'),
                        'category': structure.get('category', 'body_structure'),
                        'negation': structure.get('negation', 'positive'),
                        'family': structure.get('family', 'patient'),
                        'suspicion': structure.get('suspicion', 'confirmed'),
                        'antecedent': structure.get('antecedent', 'current')
                    })
                
                print(f"📊 Extraction {extraction_num} : {len(all_terms)} termes extraits")
            else:
                print(f"❌ Extraction {extraction_num} : pas de données")
                continue
            
            # Validation SNOMED avec chronométrage ET préservation des modifieurs
            validation_start = time.time()
            validated = []
            valid_count = 0
            
            for term_data in all_terms:
                term = term_data['term']
                
                # 🎯 NOUVELLE LOGIQUE PRIORITAIRE
                snomed_code = None
                snomed_term = None
                
                # 🥇 PRIORITÉ 1 : Recherche EXACTE du terme dans la base SNOMED
                exact_code = self.validator.find_exact_term_code(term)
                if exact_code:
                    snomed_code = exact_code
                    snomed_term = term 
                    print(f"   🎯 Terme EXACT trouvé : {term} → {exact_code} (UTILISE LE TERME EXACT : '{snomed_term}')")
                else:
                    # 🥈 PRIORITÉ 2 : Vérifier si le code de Gemini existe dans notre base
                    gemini_code = term_data.get('snomed_code', 'UNKNOWN')
                    if gemini_code != 'UNKNOWN' and self.validator.validate_code(gemini_code):
                        snomed_code = gemini_code
                        snomed_term = self.validator.get_french_term(gemini_code)
                        print(f"   ✅ Code Gemini validé : {term} → {gemini_code} ('{snomed_term}')")
                    else:
                        # 🥉 PRIORITÉ 3 : Fallback - chercher nous-mêmes
                        snomed_code = self.validator.find_closest_code(term)
                        if snomed_code:
                            snomed_term = self.validator.get_french_term(snomed_code)
                            print(f"   🔍 Code trouvé par recherche : {term} → {snomed_code}")
                        else:
                            print(f"   ❌ Aucun code valide trouvé pour : {term} (Gemini: {gemini_code})")
                            continue
                
                if snomed_code and snomed_term:
                    validated.append({
                        'term': term,
                        'snomed_code': snomed_code,
                        'snomed_term': snomed_term,
                        'valid': True,
                        # Préserver les modifieurs contextuels
                        'negation': term_data.get('negation', 'positive'),
                        'family': term_data.get('family', 'patient'),
                        'suspicion': term_data.get('suspicion', 'confirmed'),
                        'antecedent': term_data.get('antecedent', 'current'),
                        'category': term_data.get('category', 'clinical_finding')
                    })
                    valid_count += 1
                else:
                    print(f"   ❌ Aucun code valide trouvé pour : {term} (Gemini: {gemini_code})")
            
            validation_time = time.time() - validation_start
            print(f"✅ Validation SNOMED {extraction_num} : {valid_count}/{len(all_terms)} termes validés (⏱️ {validation_time:.2f}s)")
            
            # Collecte des termes validés
            for term_data in validated:
                if term_data['valid']:
                    all_validated_terms.append(term_data)
            
            extraction_stats.append((extraction_num, valid_count, len(all_terms)))
        
        # === PHASE 3 : FUSION ET DÉDUPLICATION ===
        fusion_start = time.time()
        print(f"\n🔄 === FUSION ET DÉDUPLICATION ===")
        print(f"Total avant déduplication : {len(all_validated_terms)} termes validés SNOMED")
        
        unique_terms = {}
        for term_data in all_validated_terms:
            code = term_data['snomed_code']
            if code not in unique_terms:
                print(f"   ➕ {term_data['term']} ({code})")
                unique_terms[code] = term_data
            else:
                print(f"   🔄 Doublon ignoré : {term_data['term']} ({code})")
        
        fusion_time = time.time() - fusion_start
        print(f"✨ Après déduplication : {len(unique_terms)} termes uniques validés SNOMED (⏱️ {fusion_time:.2f}s)")
        
        # === PHASE 4 : VALIDATION SÉMANTIQUE SUR LE TABLEAU FINAL ===
        semantic_start = time.time()
        print(f"\n🧠 === VALIDATION SÉMANTIQUE HYBRIDE ===")
        
        # Préparation des paires pour validation sémantique
        semantic_pairs = []
        for term_data in unique_terms.values():
            original_term = term_data['term']
            snomed_term = term_data['snomed_term']
            if original_term.lower() != snomed_term.lower():
                semantic_pairs.append((original_term, snomed_term))
        
        if not semantic_pairs:
            print("📊 Aucune validation sémantique nécessaire : tous les termes sont identiques")
            final_validated = []
            for term_data in unique_terms.values():
                entity = {
                    'term': term_data['term'],
                    'snomed_code': term_data['snomed_code'],
                    'snomed_term': term_data['snomed_term'],
                    'category': self._categorize_by_snomed_code(term_data['snomed_code']),
                    'negation': term_data.get('negation', 'positive'),
                    'family': term_data.get('family', 'patient'),
                    'suspicion': term_data.get('suspicion', 'confirmed'),
                    'antecedent': term_data.get('antecedent', 'current')
                }
                final_validated.append(entity)
        else:
            print(f"🔍 Validation sémantique hybride : {len(semantic_pairs)} paires à analyser")
            
            # Validation sémantique hybride
            semantic_results = await self._validate_semantic_coherence_batch(semantic_pairs)
            
            # Application des résultats de validation sémantique
            if semantic_pairs:
                print(f"📊 Validation terminée : {len([r for r in semantic_results.values() if r['valid']])}/{len(semantic_pairs)} validées")
                
                # Créer un dictionnaire pour associer les paires à leurs résultats
                validation_results = {}
                for i, (original_term, snomed_term) in enumerate(semantic_pairs):
                    if i in semantic_results:
                        validation_results[(original_term.lower(), snomed_term.lower())] = semantic_results[i]
                
                # Application des résultats
                final_validated = []
                rejected_terms = []
                
                for term_data in unique_terms.values():
                    original_term = term_data['term']
                    snomed_term = term_data['snomed_term']
                    pair_key = (original_term.lower(), snomed_term.lower())
                    
                    # Vérifier si cette paire a été validée sémantiquement
                    if pair_key in validation_results:
                        semantic_result = validation_results[pair_key]
                        if semantic_result['valid']:
                            print(f"   ✅ Conservé : {original_term} → {snomed_term}")
                            current_snomed_term = snomed_term
                            # VÉRIFICATION FINALE : Si le terme original est une correspondance exacte pour ce code,
                            # s'assurer que le snomed_term EST le terme original.
                            # Ceci est redondant si le flux de données est parfait, mais sert de garde-fou.
                            if self.validator.find_exact_term_code(original_term) == term_data['snomed_code']:
                                current_snomed_term = original_term
                                print(f"   🛡️ GARDE-FOU (Phase 5) : Pour {original_term} ({term_data['snomed_code']}), snomed_term forcé à '{current_snomed_term}'")
                            entity = {
                                'term': term_data['term'],
                                'snomed_code': term_data['snomed_code'],
                                'snomed_term': current_snomed_term,
                                'category': self._categorize_by_snomed_code(term_data['snomed_code']),
                                'negation': term_data.get('negation', 'positive'),
                                'family': term_data.get('family', 'patient'),
                                'suspicion': term_data.get('suspicion', 'confirmed'),
                                'antecedent': term_data.get('antecedent', 'current')
                            }
                            final_validated.append(entity)
                        else:
                            print(f"   ❌ Rejeté : {original_term} → {snomed_term} ({semantic_result['reason']})")
                            rejected_terms.append({
                                'term': original_term,
                                'reason': semantic_result['reason']
                            })
                    else:
                        # Terme identique (pas besoin de validation sémantique) -> conservé automatiquement
                        print(f"   ✅ Identique : {original_term} → {snomed_term}")
                        current_snomed_term = snomed_term
                        # VÉRIFICATION FINALE : Si le terme original est une correspondance exacte pour ce code,
                        # s'assurer que le snomed_term EST le terme original.
                        # Ceci est redondant si le flux de données est parfait, mais sert de garde-fou.
                        if self.validator.find_exact_term_code(original_term) == term_data['snomed_code']:
                            current_snomed_term = original_term
                            print(f"   🛡️ GARDE-FOU (Phase 5) : Pour {original_term} ({term_data['snomed_code']}), snomed_term forcé à '{current_snomed_term}'")
                        entity = {
                            'term': term_data['term'],
                            'snomed_code': term_data['snomed_code'],
                            'snomed_term': current_snomed_term,
                            'category': self._categorize_by_snomed_code(term_data['snomed_code']),
                            'negation': term_data.get('negation', 'positive'),
                            'family': term_data.get('family', 'patient'),
                            'suspicion': term_data.get('suspicion', 'confirmed'),
                            'antecedent': term_data.get('antecedent', 'current')
                        }
                        final_validated.append(entity)
            
            semantic_time = time.time() - semantic_start
            
            # === DÉDUPLICATION FINALE PAR TERME ORIGINAL ===
            # Si même terme original avec codes différents → garder le plus proche sémantiquement
            print(f"🔄 Déduplication finale par terme original...")
            final_deduplicated = []
            seen_terms = {}
            
            for entity in final_validated:
                original_term = entity['term'].lower()
                snomed_term = entity['snomed_term'].lower()
                
                if original_term not in seen_terms:
                    # Premier terme de ce type
                    seen_terms[original_term] = entity
                    final_deduplicated.append(entity)
                else:
                    # Doublon détecté - choisir le meilleur
                    existing_entity = seen_terms[original_term]
                    existing_snomed = existing_entity['snomed_term'].lower()
                    
                    # Priorité : terme identique > terme différent
                    if original_term == snomed_term and original_term != existing_snomed:
                        # Le nouveau est identique, l'ancien non → remplacer
                        print(f"   🔄 Remplacement: '{entity['term']}' → '{entity['snomed_term']}' (identique) au lieu de → '{existing_entity['snomed_term']}'")
                        final_deduplicated.remove(existing_entity)
                        final_deduplicated.append(entity)
                        seen_terms[original_term] = entity
                    elif original_term == existing_snomed and original_term != snomed_term:
                        # L'ancien est identique, le nouveau non → garder l'ancien
                        print(f"   ✅ Conservé: '{existing_entity['term']}' → '{existing_entity['snomed_term']}' (identique) au lieu de → '{entity['snomed_term']}'")
                    else:
                        # Cas ambigus → garder le premier
                        print(f"   ⚠️  Doublon gardé premier: '{existing_entity['term']}' → '{existing_entity['snomed_term']}' vs → '{entity['snomed_term']}'")
            
            final_validated = final_deduplicated
            print(f"✨ Après déduplication finale : {len(final_validated)} termes uniques")
            
            print(f"🎯 Après validation sémantique : {len(final_validated)}/{len(unique_terms)} termes conservés (⏱️ {semantic_time:.2f}s)")
            
            if rejected_terms:
                print(f"🗑️ Rejetés pour incohérence sémantique : {len(rejected_terms)}")
                for rejected in rejected_terms:
                    print(f"   • {rejected['term']} : {rejected['reason']}")
        
        total_validation_time = time.time() - validation_phase_start
        print(f"✅ Phase validation complète terminée en ⏱️ {total_validation_time:.2f}s")
        
        # === PHASE 5 : RÉSULTATS FINAUX ===
        # Catégorisation des résultats finaux
        final_findings = []
        final_procedures = []
        final_body_structures = []
        
        for term_data in final_validated:
            # Détection automatique de catégorie basée sur le code SNOMED
            category = self._categorize_by_snomed_code(term_data['snomed_code'])
            
            current_snomed_term = term_data['snomed_term']
            # VÉRIFICATION FINALE : Si le terme original est une correspondance exacte pour ce code,
            # s'assurer que le snomed_term EST le terme original.
            if self.validator.find_exact_term_code(term_data['term']) == term_data['snomed_code']:
                current_snomed_term = term_data['term']
                print(f"   🛡️ GARDE-FOU (Phase 5) : Pour {term_data['term']} ({term_data['snomed_code']}), snomed_term forcé à '{current_snomed_term}'")

            entity = {
                'term': term_data['term'],
                'snomed_code': term_data['snomed_code'],
                'snomed_term': current_snomed_term,
                'category': category,
                'negation': term_data.get('negation', 'positive'),
                'family': term_data.get('family', 'patient'),
                'suspicion': term_data.get('suspicion', 'confirmed'),
                'antecedent': term_data.get('antecedent', 'current')
            }
            
            if 'finding' in category.lower() or 'disorder' in category.lower():
                final_findings.append(entity)
            elif 'procedure' in category.lower():
                final_procedures.append(entity)
            else:
                final_body_structures.append(entity)
        
        # Calcul des statistiques de performance
        max_individual = max([stats[1] for stats in extraction_stats]) if extraction_stats else 0
        fusion_gain = len(unique_terms) - max_individual
        semantic_filtered = len(unique_terms) - len(final_validated)
        total_time = time.time() - start_time
        
        # Résultat final avec temps détaillés
        result = {
            'entities': {
                'findings': final_findings,
                'procedures': final_procedures,
                'body_structures': final_body_structures
            },
            'statistics': {
                'extractions': extraction_stats,
                'before_fusion': max_individual,
                'after_fusion': len(unique_terms),
                'after_semantic': len(final_validated),
                'fusion_gain': fusion_gain,
                'semantic_filtered': semantic_filtered,
                'times': {
                    'parallel_extractions': parallel_time,
                    'individual_times': individual_times,
                    'sequential_equivalent': sum(individual_times),
                    'parallel_gain': sum(individual_times) - parallel_time,
                    'validation_phase': total_validation_time,
                    'fusion': fusion_time,
                    'semantic_validation': semantic_time,
                    'total': total_time
                }
            }
        }
        
        # Affichage des résultats avec temps détaillés
        print(f"\n🎯 RÉSULTAT FINAL DE LA FUSION V2 :")
        print(f"   🔍 {len(final_findings)} constatations cliniques")
        print(f"   ⚕️  {len(final_procedures)} procédures/traitements")
        print(f"   🫀 {len(final_body_structures)} structures corporelles")
        print(f"   📊 TOTAL : {len(final_validated)} entités validées")
        
        print(f"\n📈 STATISTIQUES PAR EXTRACTION :")
        for extraction_num, valid_count, total_count in extraction_stats:
            percentage = (valid_count/total_count*100) if total_count > 0 else 0
            print(f"   Extraction {extraction_num} : {valid_count}/{total_count} ({percentage:.1f}%)")
        
        print(f"\n🚀 PERFORMANCE DE LA FUSION V2 :")
        print(f"   📊 Avant fusion : max {max_individual} entités validées")
        print(f"   ✨ Après fusion SNOMED : {len(unique_terms)} entités uniques")
        print(f"   🧠 Après validation sémantique : {len(final_validated)} entités cohérentes")
        print(f"   📈 GAIN fusion : +{fusion_gain} entités supplémentaires")
        print(f"   🛡️ FILTRAGE sémantique : -{semantic_filtered} incohérences éliminées")
        
        print(f"\n⏱️ CHRONOMÉTRAGE DÉTAILLÉ :")
        print(f"   🚀 Extractions parallèles : {parallel_time:.2f}s")
        print(f"   🔄 Équivalent séquentiel : {sum(individual_times):.2f}s")
        print(f"   💨 Gain parallélisme : -{sum(individual_times) - parallel_time:.2f}s")
        print(f"   🔍 Phase validation : {total_validation_time:.2f}s")
        print(f"   🧠 Validation sémantique : {semantic_time:.2f}s")
        print(f"   🎯 TEMPS TOTAL : {total_time:.2f}s")
        
        return result
    
    async def _validate_semantic_coherence_batch(self, term_pairs: list) -> dict:
        """
        Validation sémantique hybride groupée des correspondances SNOMED CT
        Combine filtrage mathématique rapide + LLM Gemini Flash pour les cas ambigus
        """
        from difflib import SequenceMatcher
        import time
        
        def calculate_math_score(gemini_term: str, official_term: str) -> float:
            """Score mathématique rapide combinant plusieurs métriques"""
            
            # 1. Similarité Levenshtein
            levenshtein = SequenceMatcher(None, gemini_term.lower(), official_term.lower()).ratio()
            
            # 2. Mots en commun
            words_a = set(gemini_term.lower().split())
            words_b = set(official_term.lower().split())
            word_overlap = len(words_a.intersection(words_b)) / max(len(words_a), len(words_b)) if words_a or words_b else 0
            
            # 3. Contenance (un terme contient l'autre)
            a_clean = gemini_term.lower().strip()
            b_clean = official_term.lower().strip()
            contains = 1.0 if (a_clean in b_clean or b_clean in a_clean) else 0.0
            
            # Score global pondéré
            return (levenshtein * 0.3 + word_overlap * 0.4 + contains * 0.3)
        
        def llm_validate_batch(llm_pairs: list) -> dict:
            """Validation LLM groupée pour les cas ambigus"""
            if not llm_pairs:
                return {}
            
            # Construire le prompt groupé
            pairs_text = ""
            for i, (gemini_term, official_term) in enumerate(llm_pairs):
                pairs_text += f'{i+1}. "{gemini_term}" ↔ "{official_term}"\n'
            
            prompt = f"""Tu es un expert médical. Analyse si chaque paire de termes médicaux désigne le MÊME concept clinique :

{pairs_text}

Réponds EXACTEMENT par ce format JSON :
{{
    "validations": [
        {{"paire": 1, "meme_concept": true}},
        {{"paire": 2, "meme_concept": false}},
        etc.
    ]
}}

Règles :
- true = même concept clinique (identique ou équivalent)
- false = concepts cliniques différents"""

            try:
                start_time = time.time()
                response = self.model.generate_content(prompt)
                llm_duration = time.time() - start_time
                
                response_text = response.text.strip()
                
                # Parser la réponse JSON groupée
                import json
                try:
                    # Extraire le JSON de la réponse
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        result = json.loads(json_str)
                        
                        # Convertir en dictionnaire indexé
                        batch_results = {}
                        validations = result.get("validations", [])
                        
                        for validation in validations:
                            paire_num = validation.get('paire')
                            meme_concept = validation.get('meme_concept')
                            
                            if paire_num is not None and meme_concept is not None:
                                paire_idx = paire_num - 1
                                if 0 <= paire_idx < len(llm_pairs):
                                    pair_dict = llm_pairs[paire_idx]
                                    if meme_concept:
                                        batch_results[paire_idx] = {
                                            "valid": True,
                                            "confidence": 1.0,
                                            "reason": "Concept identique",
                                            "duration": llm_duration / len(llm_pairs)
                                        }
                                    else:
                                        batch_results[paire_idx] = {
                                            "valid": False,
                                            "confidence": 0.0,
                                            "reason": "Concept différent",
                                            "duration": llm_duration / len(llm_pairs)
                                        }
                        
                        # Compléter les paires manquantes
                        for i in range(len(llm_pairs)):
                            if i not in batch_results:
                                batch_results[i] = {
                                    "valid": False,
                                    "confidence": 0.0,
                                    "reason": "Paire non trouvée dans la réponse",
                                    "duration": llm_duration / len(llm_pairs)
                                }
                        
                        return batch_results
                    else:
                        # Fallback en cas d'échec de parsing
                        return {i: {"valid": False, "confidence": 0.0, "reason": "Échec parsing JSON", "duration": llm_duration / len(llm_pairs)} for i in range(len(llm_pairs))}
                        
                except json.JSONDecodeError as e:
                    # Fallback simple en cas d'erreur JSON
                    return {i: {"valid": False, "confidence": 0.0, "reason": f"Erreur JSON: {str(e)}", "duration": llm_duration / len(llm_pairs)} for i in range(len(llm_pairs))}
                    
            except Exception as e:
                return {i: {"valid": False, "reason": f"Erreur LLM: {str(e)}", "confidence": 0.0, "duration": 0} for i in range(len(llm_pairs))}
        
        if not term_pairs:
            return {}
        
        # Phase 1 : Tri mathématique rapide
        math_results = []
        llm_cases = []
        llm_indices = []
        
        print(f"🔍 Validation sémantique hybride : {len(term_pairs)} paires à analyser")
        
        for i, (gemini_term, official_term) in enumerate(term_pairs):
            math_score = calculate_math_score(gemini_term, official_term)
            
            if math_score >= 0.5:
                # Cas évident : ACCEPTER directement
                result = {
                    'valid': True,
                    'confidence': math_score,
                    'method': 'mathematical',
                    'reason': f"Score math élevé ({math_score:.3f})"
                }
                print(f"   ✅ Math: '{gemini_term}' → '{official_term}' (score: {math_score:.3f})")
            elif math_score <= 0.01:
                # Cas très évident : REJETER directement
                result = {
                    'valid': False,
                    'confidence': math_score,
                    'method': 'mathematical', 
                    'reason': f"Score math très bas ({math_score:.3f})"
                }
                print(f"   ❌ Math: '{gemini_term}' → '{official_term}' (score: {math_score:.3f})")
            else:
                # Cas ambigu : pour LLM
                result = {
                    'valid': False,  # Sera mis à jour après LLM
                    'confidence': 0.0,  # Sera mis à jour après LLM
                    'method': 'hybrid',
                    'reason': f"Score math ambigu ({math_score:.3f}) → LLM"
                }
                llm_cases.append((gemini_term, official_term))
                llm_indices.append(i)
                print(f"   🤖 LLM: '{gemini_term}' → '{official_term}' (score: {math_score:.3f})")
            
            math_results.append(result)
        
        # Phase 2 : Validation LLM groupée
        if llm_cases:
            print(f"🤖 Validation LLM groupée : {len(llm_cases)} paires ambiguës")
            
            start_llm = time.time()
            llm_batch_results = llm_validate_batch(llm_cases)
            total_llm_time = time.time() - start_llm
            
            print(f"✅ LLM groupé terminé en {total_llm_time:.2f}s")
            
            # Mettre à jour les résultats avec les validations LLM
            for batch_idx, original_idx in enumerate(llm_indices):
                if batch_idx in llm_batch_results:
                    llm_result = llm_batch_results[batch_idx]
                    result = math_results[original_idx]
                    
                    result['valid'] = llm_result.get('valid', False)
                    result['confidence'] = llm_result.get('confidence', 0.0)
                    result['reason'] = llm_result.get('reason', 'Analyse LLM')
                    
                    status = "✅" if result['valid'] else "❌"
                    gemini_term, official_term = llm_cases[batch_idx]
                    print(f"   {status} LLM: '{gemini_term}' → '{official_term}' (confiance: {result['confidence']:.2f})")
                    print(f"      └─ {result['reason']}")
        
        # Convertir en dictionnaire indexé pour le retour
        final_results = {}
        for i, result in enumerate(math_results):
            final_results[i] = result
        
        # Statistiques
        valid_count = sum(1 for r in math_results if r['valid'])
        math_count = sum(1 for r in math_results if r['method'] == 'mathematical')
        llm_count = len(llm_cases)
        
        print(f"📊 Validation terminée : {valid_count}/{len(term_pairs)} validées")
        print(f"   🔢 Math : {math_count}/{len(term_pairs)} ({math_count/len(term_pairs)*100:.1f}%)")
        print(f"   🤖 LLM : {llm_count}/{len(term_pairs)} ({llm_count/len(term_pairs)*100:.1f}%)")
        
        return final_results 

    def _categorize_by_snomed_code(self, snomed_code):
        """
        Catégorise automatiquement une entité basée sur son code SNOMED
        
        Args:
            snomed_code (str): Code SNOMED CT
            
        Returns:
            str: Catégorie déterminée
        """
        # Règles de catégorisation basées sur les hiérarchies SNOMED
        # Ces codes correspondent aux grandes hiérarchies SNOMED CT
        
        # Findings/Disorders (domaine clinique)
        if snomed_code.startswith(('271', '40', '38', '41', '27', '36', '23', '25', '42')):
            return "Clinical finding"
        
        # Procedures (interventions)  
        elif snomed_code.startswith(('71', '77', '23', '18', '38', '89', '17', '18')):
            return "Procedure"
            
        # Body structures (anatomie)
        elif snomed_code.startswith(('51', '81', '15', '79', '24', '36', '12', '91')):
            return "Body structure"
            
        # Observable entity (observations)
        elif snomed_code.startswith(('36', '24', '25')):
            return "Observable entity"
            
        # Substances (médicaments, substances)
        elif snomed_code.startswith(('44', '37', '39', '41')):
            return "Substance"
            
        # Par défaut, catégoriser comme finding
        else:
            return "Clinical finding"
    
    def _security_check(self):
        """Vérification de sécurité des limites API"""
        can_proceed, message = security_manager.can_make_request()
        if not can_proceed:
            print(f"🚫 EXTRACTION BLOQUÉE : {message}")
            return False
        return True
    
    def extract_medical_entities(self, text, use_context_modifiers=True):
        """
        Extraction d'entités médicales à partir de texte brut
        Compatible avec la méthode V2 asynchrone
        """
        try:
            # Créer un objet MedicalNote temporaire
            medical_note = MedicalNote(
                patient_id="TEMP_001",
                patient_name="Patient Temporaire",
                date="2025-01-01",
                doctor="Dr. Extracteur",
                content=text,
                specialty="Extraction automatique"
            )
            
            # Utiliser la méthode d'extraction existante
            extraction = self.extract_snomed_info(medical_note)
            
            # Convertir au format attendu par la méthode V2
            findings = []
            procedures = []
            body_structures = []
            
            for finding in extraction.clinical_findings:
                findings.append({
                    'term': finding.term,
                    'snomed_code': finding.snomed_code,
                    'category': 'clinical_finding',
                    # Récupérer TOUS les modifieurs contextuels
                    'negation': getattr(finding, 'negation', 'positive'),
                    'family': getattr(finding, 'family', 'patient'),
                    'suspicion': getattr(finding, 'suspicion', 'confirmed'),
                    'antecedent': getattr(finding, 'antecedent', 'current')
                })
            
            for procedure in extraction.procedures:
                procedures.append({
                    'term': procedure.term,
                    'snomed_code': procedure.snomed_code,
                    'category': 'procedure',
                    # Récupérer TOUS les modifieurs contextuels
                    'negation': getattr(procedure, 'negation', 'positive'),
                    'family': getattr(procedure, 'family', 'patient'),
                    'suspicion': getattr(procedure, 'suspicion', 'confirmed'),
                    'antecedent': getattr(procedure, 'antecedent', 'current')
                })
            
            for structure in extraction.body_structures:
                body_structures.append({
                    'term': structure.term,
                    'snomed_code': structure.snomed_code,
                    'category': 'body_structure',
                    # Récupérer TOUS les modifieurs contextuels
                    'negation': getattr(structure, 'negation', 'positive'),
                    'family': getattr(structure, 'family', 'patient'),
                    'suspicion': getattr(structure, 'suspicion', 'confirmed'),
                    'antecedent': getattr(structure, 'antecedent', 'current')
                })
            
            return {
                'entities': {
                    'findings': findings,
                    'procedures': procedures,
                    'body_structures': body_structures
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur extraction_medical_entities: {str(e)}")
            return None 