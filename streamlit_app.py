import streamlit as st
import time
import re
from typing import Dict, List, Any
import os

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
        <h3>Plateforme d'extraction automatisée - Yunohit</h3>
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
                
                # Interface principale
                st.markdown("## 📝 Extraction SNOMED CT")
                
                # Interface à onglets
                tab1, tab2, tab3 = st.tabs(["📄 Extraction Simple", "📊 Analyse Batch", "⚙️ Configuration"])
                
                with tab1:
                    note_content = st.text_area(
                        "Note médicale:",
                        value="""Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée.""",
                        height=150
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button("🚀 Extraire les Entités SNOMED", type="primary"):
                            try:
                                # Configuration de l'API key via environnement
                                os.environ['GOOGLE_API_KEY'] = api_key
                                
                                # Import direct ici pour éviter les problèmes de subprocess
                                from snomed_extractor import SNOMEDExtractor
                                from snomed_validator import SNOMEDValidator
                                from models import MedicalNote
                                
                                with st.spinner("🔄 Extraction en cours..."):
                                    start_time = time.time()
                                    
                                    # Extraction
                                    extractor = SNOMEDExtractor()
                                    medical_note = MedicalNote(content=note_content)
                                    result = extractor.extract_snomed_info(medical_note)
                                    extraction_time = time.time() - start_time
                                    
                                    if result and result.clinical_findings or result.procedures or result.body_structures:
                                        st.success(f"✅ Extraction réussie en {extraction_time:.1f}s")
                                        
                                        # Convertir en format pour affichage
                                        validation_results = []
                                        
                                        # Ajouter clinical findings
                                        for cf in result.clinical_findings:
                                            validation_results.append({
                                                'terme': cf.term,
                                                'code_snomed': cf.snomed_code,
                                                'categorie': 'Clinical Finding',
                                                'valide': True,  # Pour l'instant, on suppose valide
                                                'raison': ''
                                            })
                                        
                                        # Ajouter procedures
                                        for proc in result.procedures:
                                            validation_results.append({
                                                'terme': proc.term,
                                                'code_snomed': proc.snomed_code,
                                                'categorie': 'Procedure',
                                                'valide': True,
                                                'raison': ''
                                            })
                                        
                                        # Ajouter body structures
                                        for bs in result.body_structures:
                                            validation_results.append({
                                                'terme': bs.term,
                                                'code_snomed': bs.snomed_code,
                                                'categorie': 'Body Structure',
                                                'valide': True,
                                                'raison': ''
                                            })
                                        
                                        # Validation avec SNOMEDValidator
                                        validator = SNOMEDValidator()
                                        for res in validation_results:
                                            val_result = validator.validate_code(res['code_snomed'])
                                            res['valide'] = val_result['is_valid']
                                            res['raison'] = val_result.get('reason', '')
                                        
                                        # Affichage des résultats
                                        st.markdown("### 📊 Résultats de l'extraction")
                                        
                                        # Métriques
                                        valid_count = sum(1 for r in validation_results if r['valide'])
                                        total_count = len(validation_results)
                                        success_rate = (valid_count / total_count * 100) if total_count > 0 else 0
                                        
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Entités extraites", total_count)
                                        with col2:
                                            st.metric("Codes valides", valid_count)
                                        with col3:
                                            st.metric("Taux de réussite", f"{success_rate:.1f}%")
                                        with col4:
                                            st.metric("Temps d'extraction", f"{extraction_time:.1f}s")
                                        
                                        # Table des résultats
                                        for i, res in enumerate(validation_results, 1):
                                            status = "✅" if res['valide'] else "❌"
                                            with st.expander(f"{status} {res.get('terme', 'N/A')} - {res.get('code_snomed', 'N/A')}"):
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    st.write("**Terme:**", res.get('terme', 'N/A'))
                                                    st.write("**Code SNOMED:**", res.get('code_snomed', 'N/A'))
                                                    st.write("**Catégorie:**", res.get('categorie', 'N/A'))
                                                with col2:
                                                    st.write("**Statut:**", "✅ Valide" if res['valide'] else "❌ Invalide")
                                                    if not res['valide'] and res.get('raison'):
                                                        st.write("**Raison:**", res['raison'])
                                        
                                        # JSON brut optionnel
                                        with st.expander("📄 Voir les données JSON brutes"):
                                            # Convertir l'objet en dict pour l'affichage
                                            result_dict = {
                                                'clinical_findings': [{'term': cf.term, 'snomed_code': cf.snomed_code, 'description': cf.description} for cf in result.clinical_findings],
                                                'procedures': [{'term': proc.term, 'snomed_code': proc.snomed_code, 'description': proc.description} for proc in result.procedures],
                                                'body_structures': [{'term': bs.term, 'snomed_code': bs.snomed_code, 'description': bs.description} for bs in result.body_structures]
                                            }
                                            st.json(result_dict)
                                    
                                    else:
                                        st.warning("⚠️ Aucune entité extraite")
                            
                            except Exception as e:
                                st.error(f"❌ Erreur lors de l'extraction : {str(e)}")
                                import traceback
                                with st.expander("🔧 Détails de l'erreur"):
                                    st.code(traceback.format_exc())
                    
                    with col2:
                        st.info("💡 **Conseils:**\n\n- Utilisez des notes structurées\n- Incluez diagnostics et traitements\n- Plus de détails = meilleure extraction")
                
                with tab2:
                    st.markdown("### 📊 Analyse par lots")
                    st.info("🚧 Fonctionnalité en développement - Prochainement disponible")
                
                with tab3:
                    st.markdown("### ⚙️ Configuration")
                    st.write("**API Key:** ✅ Configurée")
                    st.write("**Version:** Streamlit Cloud Production")
                    
                    if st.button("🧪 Test de connectivité API"):
                        try:
                            import google.generativeai as genai
                            genai.configure(api_key=api_key)
                            
                            # Test simple
                            model = genai.GenerativeModel('gemini-pro')
                            response = model.generate_content("Test de connectivité : dites 'OK'")
                            
                            if response.text:
                                st.success("✅ API connectée et fonctionnelle")
                                st.write("Réponse de test:", response.text)
                            else:
                                st.error("❌ Pas de réponse de l'API")
                        except Exception as e:
                            st.error(f"❌ Erreur de connectivité : {e}")
            
            else:
                st.warning("⚠️ API Key non configurée dans les secrets")
                st.markdown("""
                **Pour configurer l'API Key :**
                1. Allez dans les **Settings** de l'app Streamlit
                2. Section **Secrets**
                3. Ajoutez : `GEMINI_API_KEY = "votre_clé_ici"`
                4. Sauvegardez - l'app redémarre automatiquement
                """)
                
        except Exception as e:
            st.error(f"❌ Erreur accès secrets : {e}")
    
    else:
        st.error("❌ Dépendances manquantes - Redéploiement nécessaire")
        st.markdown("""
        **Problème détecté :** Module google-generativeai non installé
        
        **Solution :** Le requirements.txt sera mis à jour automatiquement
        """)

# Sidebar avec informations
with st.sidebar:
    st.markdown("### 🏥 Yunohit - SNOMED CT")
    st.markdown("**Extracteur automatisé**")
    st.markdown("---")
    st.markdown("**Fonctionnalités :**")
    st.markdown("✅ Extraction temps réel")
    st.markdown("✅ Validation automatique")
    st.markdown("✅ Interface moderne")
    st.markdown("✅ Monitoring intégré")
    st.markdown("---")
    st.markdown("**Support :** Version Cloud")

if __name__ == "__main__":
    main() 