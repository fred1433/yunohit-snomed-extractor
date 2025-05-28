import streamlit as st
import time
import re
from typing import Dict, List, Any

# Configuration de la page
st.set_page_config(
    page_title="🏥 Extracteur SNOMED CT - Yunohit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

def test_imports():
    """Teste les imports pour diagnostic"""
    try:
        import google.generativeai as genai
        st.success("✅ google-generativeai importé avec succès")
        return True
    except ImportError as e:
        st.error(f"❌ Erreur import google-generativeai: {e}")
        return False

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>🏥 Extracteur SNOMED CT</h1>
        <h3>Version de diagnostic - Yunohit</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Test des imports
    st.markdown("## 🔍 Diagnostic des dépendances")
    
    if test_imports():
        st.success("✅ Toutes les dépendances sont disponibles")
        
        # Test API Key
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                st.success(f"✅ API Key configurée : {api_key[:20]}...")
                
                # Interface simplifiée
                st.markdown("## 📝 Test d'extraction")
                
                note_content = st.text_area(
                    "Note médicale:",
                    value="""Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée.""",
                    height=150
                )
                
                if st.button("🚀 Test Extraction Directe"):
                    try:
                        # Import direct ici pour tester
                        from snomed_extractor import SnomedExtractor
                        from snomed_validator import SnomedValidator
                        
                        st.success("✅ Modules locaux importés avec succès")
                        
                        with st.spinner("🔄 Extraction en cours..."):
                            start_time = time.time()
                            
                            # Test extraction
                            extractor = SnomedExtractor(api_key)
                            result = extractor.extract_medical_entities(note_content)
                            extraction_time = time.time() - start_time
                            
                            st.success(f"✅ Extraction réussie en {extraction_time:.1f}s")
                            st.json(result)
                            
                            # Test validation
                            if result and 'entites' in result:
                                validator = SnomedValidator()
                                
                                validation_results = []
                                for entite in result['entites']:
                                    val_result = validator.validate_code(entite.get('code_snomed', ''))
                                    validation_results.append({
                                        **entite,
                                        'valide': val_result['is_valid'],
                                        'raison': val_result.get('reason', '')
                                    })
                                
                                st.markdown("### 📊 Résultats de validation")
                                for i, res in enumerate(validation_results, 1):
                                    status = "✅" if res['valide'] else "❌"
                                    st.write(f"{i}. {status} {res.get('terme', 'N/A')} - {res.get('code_snomed', 'N/A')}")
                                
                                valid_count = sum(1 for r in validation_results if r['valide'])
                                total_count = len(validation_results)
                                success_rate = (valid_count / total_count * 100) if total_count > 0 else 0
                                
                                st.metric("Taux de réussite", f"{success_rate:.1f}%")
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'extraction : {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
            else:
                st.warning("⚠️ API Key non configurée dans les secrets")
        except Exception as e:
            st.error(f"❌ Erreur accès secrets : {e}")
    
    else:
        st.error("❌ Dépendances manquantes - Redéploiement nécessaire")

if __name__ == "__main__":
    main() 