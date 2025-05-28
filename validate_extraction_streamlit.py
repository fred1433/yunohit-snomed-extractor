#!/usr/bin/env python3
"""
Version Streamlit Cloud de validate_extraction.py
Sans rich, adaptée pour l'environnement cloud
"""

import sys
import time
from typing import Dict, List, Any
import json

# Imports adaptés pour Streamlit Cloud
try:
    from config_unified import GEMINI_API_KEY, MODEL_CONFIG
except ImportError:
    # Fallback direct pour Streamlit Cloud
    import os
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    MODEL_CONFIG = {
        'model_name': 'gemini-2.0-flash-exp',
        'temperature': 0.3,
        'max_output_tokens': 8192,
        'top_p': 0.8,
        'top_k': 40
    }

from snomed_extractor import SnomedExtractor
from snomed_validator import SnomedValidator

def simple_print(text: str, style: str = ""):
    """Remplace rich.print par print simple"""
    print(text)

def create_simple_table(title: str, data: List[Dict]) -> str:
    """Crée un tableau simple en texte"""
    output = f"\n=== {title} ===\n"
    if not data:
        return output + "Aucun résultat\n"
    
    for i, item in enumerate(data, 1):
        output += f"\n{i}. {item.get('terme', 'N/A')}\n"
        output += f"   Code: {item.get('code_snomed', 'N/A')}\n"
        output += f"   Catégorie: {item.get('categorie', 'N/A')}\n"
        if 'valide' in item:
            output += f"   Valide: {'✅' if item['valide'] else '❌'}\n"
        if 'raison' in item:
            output += f"   Raison: {item['raison']}\n"
    
    return output + "\n"

def main():
    """Fonction principale adaptée pour Streamlit Cloud"""
    
    if not GEMINI_API_KEY:
        print("❌ ERREUR: GEMINI_API_KEY non configurée")
        sys.exit(1)
    
    # Note par défaut si pas d'input
    if len(sys.argv) > 1:
        note_medicale = sys.argv[1]
    else:
        # Lire depuis stdin
        note_medicale = sys.stdin.read().strip()
        if not note_medicale:
            note_medicale = """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée."""

    print("🏥 EXTRACTEUR SNOMED CT - VERSION STREAMLIT CLOUD")
    print("=" * 50)
    print(f"📄 Note médicale: {note_medicale[:100]}...")
    
    # Extraction
    print("\n🔄 Extraction en cours...")
    start_time = time.time()
    
    try:
        extractor = SnomedExtractor(GEMINI_API_KEY)
        extraction_result = extractor.extract_medical_entities(note_medicale)
        extraction_time = time.time() - start_time
        
        print(f"✅ Extraction réussie en {extraction_time:.1f}s")
        
        if not extraction_result or not extraction_result.get('entites'):
            print("❌ Aucune entité extraite")
            sys.exit(1)
        
        entites = extraction_result['entites']
        print(f"📊 {len(entites)} entités extraites")
        
        # Validation
        print("\n🔍 Validation SNOMED en cours...")
        start_validation = time.time()
        
        validator = SnomedValidator()
        validation_results = []
        
        for entite in entites:
            result = validator.validate_code(entite.get('code_snomed', ''))
            validation_results.append({
                **entite,
                'valide': result['is_valid'],
                'raison': result.get('reason', ''),
                'terme_officiel': result.get('term', '')
            })
        
        validation_time = time.time() - start_validation
        
        # Statistiques
        total_codes = len(validation_results)
        valid_codes = sum(1 for r in validation_results if r['valide'])
        success_rate = (valid_codes / total_codes * 100) if total_codes > 0 else 0
        
        # Affichage des résultats
        print(f"\n📊 RÉSULTATS DE VALIDATION")
        print("=" * 30)
        print(f"Total des codes analysés : {total_codes}")
        print(f"Codes VALIDES : {valid_codes}")
        print(f"Codes INVALIDES : {total_codes - valid_codes}")
        print(f"Taux de validité : {success_rate:.1f}%")
        print(f"Temps d'extraction Gemini : {extraction_time:.1f}s")
        print(f"Temps de validation SNOMED : {validation_time:.1f}s")
        
        # Tableaux détaillés
        print(create_simple_table("Détail COMPLET de la validation", validation_results))
        
        # Tableau client (codes valides uniquement)
        valid_results = [r for r in validation_results if r['valide']]
        print(create_simple_table("Tableau CLIENT - Codes SNOMED Valides", valid_results))
        
        print("\n🎯 EXTRACTION TERMINÉE AVEC SUCCÈS")
        
    except Exception as e:
        print(f"❌ ERREUR FATALE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 