#!/usr/bin/env python3
"""
Validation sémantique HYBRIDE des correspondances SNOMED CT
Combine filtrage mathématique rapide + LLM Gemini Flash pour les cas ambigus
"""

import os
import google.generativeai as genai
from difflib import SequenceMatcher
import re
import time

def setup_gemini():
    """Configuration Gemini identique aux autres scripts"""
    
    # Essayer plusieurs sources pour l'API key
    api_key = None
    
    # 1. Variable d'environnement
    api_key = os.getenv('GEMINI_API_KEY')
    
    # 2. Fichier .env local
    if not api_key:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"')
                        break
        except FileNotFoundError:
            pass
    
    # 3. Secrets streamlit (si disponible)
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets['GEMINI_API_KEY']
        except:
            pass
    
    if api_key:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    else:
        print("⚠️ GEMINI_API_KEY non trouvée - LLM désactivé")
        return None

flash_model = setup_gemini()

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
    math_score = (levenshtein * 0.3 + word_overlap * 0.4 + contains * 0.3)
    
    return math_score

def llm_validate_medical_terms_batch(term_pairs: list) -> dict:
    """Validation par LLM Gemini Flash pour plusieurs paires à la fois"""
    
    if not flash_model:
        return {pair_id: {"valid": False, "reason": "LLM non disponible", "confidence": 0.0} for pair_id in range(len(term_pairs))}
    
    if not term_pairs:
        return {}
    
    # Construire le prompt groupé
    pairs_text = ""
    for i, (gemini_term, official_term) in enumerate(term_pairs):
        pairs_text += f'{i+1}. "{gemini_term}" ↔ "{official_term}"\n'
    
    prompt = f"""Tu es un expert médical. Analyse si chaque paire de termes médicaux désigne le MÊME concept clinique :

{pairs_text}

Réponds EXACTEMENT par ce format JSON :
{{
    "validations": [
        {{"paire": 1, "synonymes": true/false, "confiance": 0.0-1.0, "explication": "courte explication"}},
        {{"paire": 2, "synonymes": true/false, "confiance": 0.0-1.0, "explication": "courte explication"}},
        etc.
    ]
}}

Règles :
- true = synonymes médicaux ou même concept clinique
- false = concepts différents
- confiance entre 0.0 et 1.0
- explication courte et claire"""

    try:
        start_time = time.time()
        response = flash_model.generate_content(prompt)
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
                    pair_num = validation.get("paire", 0) - 1  # Convertir en index 0-based
                    if 0 <= pair_num < len(term_pairs):
                        batch_results[pair_num] = {
                            "valid": validation.get("synonymes", False),
                            "confidence": validation.get("confiance", 0.5),
                            "reason": validation.get("explication", "Analyse LLM"),
                            "duration": llm_duration / len(term_pairs)  # Temps divisé par paire
                        }
                
                # Compléter les paires manquantes
                for i in range(len(term_pairs)):
                    if i not in batch_results:
                        batch_results[i] = {
                            "valid": False,
                            "confidence": 0.5,
                            "reason": "Paire non trouvée dans la réponse",
                            "duration": llm_duration / len(term_pairs)
                        }
                
                return batch_results
            else:
                # Fallback en cas d'échec de parsing
                return {i: {"valid": False, "confidence": 0.3, "reason": "Échec parsing JSON", "duration": llm_duration / len(term_pairs)} for i in range(len(term_pairs))}
                    
        except json.JSONDecodeError as e:
            # Fallback simple en cas d'erreur JSON
            return {i: {"valid": False, "confidence": 0.3, "reason": f"Erreur JSON: {str(e)}", "duration": llm_duration / len(term_pairs)} for i in range(len(term_pairs))}
            
    except Exception as e:
        return {i: {"valid": False, "reason": f"Erreur LLM: {str(e)}", "confidence": 0.0, "duration": 0} for i in range(len(term_pairs))}

def validate_term_hybrid(gemini_term: str, official_term: str, code: str) -> dict:
    """Validation HYBRIDE : Math rapide + LLM pour les cas ambigus"""
    
    # Étape 1 : Score mathématique rapide
    math_score = calculate_math_score(gemini_term, official_term)
    
    validation_method = "mathematical"
    llm_result = None
    final_valid = False
    final_confidence = math_score
    decision_reason = ""
    
    # Étape 2 : Décision selon le score
    if math_score >= 0.5:  # Seuil abaissé pour capturer plus de cas évidents
        # Cas évident : ACCEPTER directement
        final_valid = True
        decision_reason = f"Score math élevé ({math_score:.3f}) → Accepté directement"
        
    elif math_score <= 0.01:
        # Cas très évident : REJETER directement (seuil très bas pour laisser place au LLM)
        final_valid = False
        decision_reason = f"Score math extrêmement bas ({math_score:.3f}) → Rejeté directement"
        
    else:
        # Zone ambiguë ÉLARGIE : Validation LLM (de 0.01 à 0.6)
        validation_method = "hybrid"
        decision_reason = f"Score math ambigu ({math_score:.3f}) → Validation LLM"
        
        llm_result = llm_validate_medical_terms_batch([(gemini_term, official_term)])
        final_valid = llm_result.get("valid", False)
        final_confidence = (math_score + llm_result.get("confidence", 0.5)) / 2
        decision_reason += f" → LLM: {llm_result.get('reason', 'N/A')}"
    
    return {
        'gemini_term': gemini_term,
        'official_term': official_term,
        'code': code,
        'math_score': round(math_score, 3),
        'validation_method': validation_method,
        'final_valid': final_valid,
        'final_confidence': round(final_confidence, 3),
        'decision_reason': decision_reason,
        'llm_details': llm_result
    }

def main():
    """Test de la validation hybride avec appel LLM groupé"""
    
    print("🚀 TEST DE VALIDATION HYBRIDE SNOMED CT - VERSION GROUPÉE")
    print("📊 Math rapide (0.001s) + LLM groupé intelligent pour les cas ambigus")
    print("=" * 90)
    
    # Données de test
    test_data = [
        ("éruption cutanée", "éruption", "271807003"),
        ("prurit", "démangeaison", "418290006"),  # Synonyme médical à valider
        ("Varicelle", "varicelle", "38907003"),
        ("prurit", "démangeaison de la peau", "418363000"),  # Synonyme médical étendu
        ("soins locaux", "soins", "225365006"),
        ("soins locaux", "enseignement d'une diète spéciale", "410177006")  # Erreur à rejeter
    ]
    
    # Phase 1 : Tri math rapide
    math_results = []
    llm_cases = []
    llm_indices = []
    
    print(f"\n📋 PHASE 1 : TRI MATHÉMATIQUE RAPIDE...")
    print("-" * 90)
    
    for i, (gemini_term, official_term, code) in enumerate(test_data):
        math_score = calculate_math_score(gemini_term, official_term)
        
        if math_score >= 0.5:
            # Cas évident : ACCEPTER directement
            result = {
                'gemini_term': gemini_term,
                'official_term': official_term,
                'code': code,
                'math_score': round(math_score, 3),
                'validation_method': 'mathematical',
                'final_valid': True,
                'final_confidence': round(math_score, 3),
                'decision_reason': f"Score math élevé ({math_score:.3f}) → Accepté directement",
                'llm_details': None
            }
            print(f"   ✅ {gemini_term} → {official_term} (score: {math_score:.3f}) - MATH DIRECT")
        elif math_score <= 0.01:
            # Cas très évident : REJETER directement
            result = {
                'gemini_term': gemini_term,
                'official_term': official_term,
                'code': code,
                'math_score': round(math_score, 3),
                'validation_method': 'mathematical',
                'final_valid': False,
                'final_confidence': round(math_score, 3),
                'decision_reason': f"Score math extrêmement bas ({math_score:.3f}) → Rejeté directement",
                'llm_details': None
            }
            print(f"   ❌ {gemini_term} → {official_term} (score: {math_score:.3f}) - MATH DIRECT")
        else:
            # Cas ambigu : pour LLM
            result = {
                'gemini_term': gemini_term,
                'official_term': official_term,
                'code': code,
                'math_score': round(math_score, 3),
                'validation_method': 'hybrid',
                'final_valid': False,  # Sera mis à jour après LLM
                'final_confidence': 0.0,  # Sera mis à jour après LLM
                'decision_reason': f"Score math ambigu ({math_score:.3f}) → Pour validation LLM",
                'llm_details': None  # Sera mis à jour après LLM
            }
            llm_cases.append((gemini_term, official_term))
            llm_indices.append(i)
            print(f"   🤖 {gemini_term} → {official_term} (score: {math_score:.3f}) - POUR LLM")
        
        math_results.append(result)
    
    # Phase 2 : Validation LLM groupée
    if llm_cases:
        print(f"\n📋 PHASE 2 : VALIDATION LLM GROUPÉE ({len(llm_cases)} paires)...")
        print("-" * 90)
        
        start_llm = time.time()
        llm_batch_results = llm_validate_medical_terms_batch(llm_cases)
        total_llm_time = time.time() - start_llm
        
        print(f"✅ Validation LLM groupée terminée en {total_llm_time:.2f}s")
        
        # Mettre à jour les résultats avec les validations LLM
        for batch_idx, original_idx in enumerate(llm_indices):
            if batch_idx in llm_batch_results:
                llm_result = llm_batch_results[batch_idx]
                result = math_results[original_idx]
                
                result['final_valid'] = llm_result.get('valid', False)
                result['final_confidence'] = round((result['math_score'] + llm_result.get('confidence', 0.5)) / 2, 3)
                result['decision_reason'] += f" → LLM: {llm_result.get('reason', 'N/A')}"
                result['llm_details'] = llm_result
                
                status = "✅ VALIDÉ" if result['final_valid'] else "❌ REJETÉ"
                print(f"   {status} {result['gemini_term']} → {result['official_term']}")
                print(f"      └─ {llm_result.get('reason', 'N/A')} (confiance: {llm_result.get('confidence', 0):.2f})")
    
    # Statistiques finales
    results = math_results
    valid_count = sum(1 for r in results if r['final_valid'])
    total_count = len(results)
    math_only = sum(1 for r in results if r['validation_method'] == 'mathematical')
    llm_count = len(llm_cases)
    
    print("\n" + "=" * 90)
    print("📈 RÉSULTATS DE LA VALIDATION HYBRIDE GROUPÉE :")
    print(f"   ✅ Termes VALIDÉS : {valid_count}/{total_count} ({valid_count/total_count*100:.1f}%)")
    print(f"   ❌ Termes REJETÉS : {total_count - valid_count}/{total_count}")
    print(f"   🔢 Validation math seule : {math_only}/{total_count} ({math_only/total_count*100:.1f}%)")
    print(f"   🤖 Validation LLM groupée : {llm_count}/{total_count} ({llm_count/total_count*100:.1f}%)")
    
    if llm_count > 0:
        avg_llm_time = total_llm_time / llm_count if llm_count > 0 else 0
        print(f"   ⏱️  Temps LLM total : {total_llm_time:.2f}s pour {llm_count} paires")
        print(f"   ⚡ Temps LLM par paire : {avg_llm_time:.2f}s (groupé vs ~3s individuel)")
        print(f"   💰 Coût estimé : {0.001:.4f}$ pour 1 appel groupé (vs {llm_count * 0.001:.4f}$ individuel)")
        print(f"   🚀 Gain de temps : {(3.0 * llm_count - total_llm_time):.1f}s économisés")
    
    print("\n🎯 DÉTAIL PAR VALIDATION :")
    for result in results:
        status_emoji = "✅" if result['final_valid'] else "❌"
        method_emoji = "🔢" if result['validation_method'] == 'mathematical' else "🤖"
        
        print(f"   {status_emoji} {method_emoji} '{result['gemini_term']}' → '{result['official_term']}'")
        if result['validation_method'] == 'hybrid' and result['llm_details']:
            llm_confidence = result['llm_details'].get('confidence', 0)
            llm_reason = result['llm_details'].get('reason', 'N/A')
            print(f"      └─ LLM confiance: {llm_confidence}, raison: {llm_reason}")

if __name__ == "__main__":
    main() 