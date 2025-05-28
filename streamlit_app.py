import streamlit as st
import time
import re
from typing import Dict, List, Any
import os
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="🏥 Extracteur SNOMED CT - Yunohit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# FORCER REDÉMARRAGE STREAMLIT CLOUD - v2.1

# Imports spécifiques au projet - en tête pour éviter les problèmes Streamlit
try:
    from snomed_extractor import SNOMEDExtractor
    from snomed_validator import SNOMEDValidator
    from models import MedicalNote
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)

def main():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>PoC Extracteur SNOMED CT Yunohit</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Test des imports en arrière-plan sans affichage
    if not IMPORTS_OK:
        st.error(f"❌ Erreur d'import des modules : {IMPORT_ERROR}")
        st.markdown("""
        **Problème détecté :** Modules du projet non disponibles
        
        **Solution :** Vérifiez que tous les fichiers sont présents dans le projet
        """)
        return
    
    # Test API Key
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key:
            # Interface principale directe (sans onglets)
            
            # Exemples de notes médicales prédéfinies
            exemples_notes = {
                "Exemple 1 - Pédiatrie (Varicelle)": """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée.""",

                "Exemple 2 - Médecine du sport": """Mme. Leclerc, 35 ans, vient pour un certificat médical d'aptitude au sport.
Se plaint de lombalgies occasionnelles après un effort prolongé. Négation de traumatisme récent.
Antécédents familiaux : RAS.
Examen clinique sans particularité. TA : 120/80 mmHg. Vaccinations à jour.
Apte à la pratique sportive.""",

                "Exemple 3 - Cardiologie": """Patient : M. Dupont, 65 ans.
Motif de consultation : Douleur thoracique persistante à l'effort depuis 1 semaine, accompagnée d'une dyspnée.
Antécédents : HTA connue, diabète de type 2 traité par metformine. Tabagisme sevré il y a 5 ans. Un frère décédé d'un infarctus du myocarde à 50 ans.
Examen : Auscultation pulmonaire normale. Pas de fièvre. ECG : signes d'ischémie myocardique.
Conclusion : Suspicion d'angor instable.
Plan : Hospitalisation pour bilan cardiologique complet, incluant une coronarographie. Prescription de trinitrine sublinguale si douleur.""",

                "Saisie personnalisée": ""
            }
            
            # Sélecteur de note
            choix_note = st.selectbox(
                "Sélectionnez ou saisissez une Note Médicale :",
                options=list(exemples_notes.keys()),
                index=0
            )
            
            # Zone de texte qui se met à jour selon la sélection
            if choix_note == "Saisie personnalisée":
                note_content = st.text_area(
                    "Votre note médicale :",
                    value="",
                    height=150,
                    placeholder="Saisissez ici votre note médicale..."
                )
            else:
                note_content = st.text_area(
                    "Note médicale sélectionnée :",
                    value=exemples_notes[choix_note],
                    height=150
                )
            
            # Toggle pour mode développement (modèle rapide)
            st.markdown("---")
            
            # Toggle pour prévisualisation mode production AVANT les autres
            preview_production = st.checkbox(
                "👁️ Prévisualiser l'interface de production (masquer les éléments de développement)",
                value=False,
                help="Voir l'interface telle qu'elle apparaîtra au client final"
            )
            
            # Toggle Flash TOUJOURS visible (trop utile même en prévisualisation)
            use_flash_model = st.checkbox(
                "🚀 Mode développement : Utiliser Gemini 2.5 Flash (plus rapide, moins précis)",
                value=False,
                help="Mode Flash pour tests rapides - Ne pas utiliser pour la production client"
            )
            
            # Afficher le warning seulement si pas en mode prévisualisation
            if use_flash_model and not preview_production:
                st.warning("⚠️ Mode développement activé - Qualité réduite")
            
            if st.button("🚀 Extraire les Entités SNOMED", type="primary"):
                try:
                    # Configuration de l'API key via environnement
                    os.environ['GOOGLE_API_KEY'] = api_key
                    
                    with st.spinner("🔄 Extraction en cours..."):
                        start_time = time.time()
                        
                        # Extraction avec choix du modèle
                        extractor = SNOMEDExtractor()
                        
                        # Override du modèle si mode Flash activé
                        if use_flash_model:
                            extractor.set_model("gemini-2.5-flash-preview-05-20")
                        
                        medical_note = MedicalNote(
                            patient_id="DEMO_001",
                            patient_name="Patient Démo", 
                            date="2025-01-01",
                            doctor="Dr. Streamlit",
                            content=note_content,
                            specialty="Médecine générale"
                        )
                        result = extractor.extract_snomed_info(medical_note)
                        extraction_time = time.time() - start_time
                        
                        # Vérification du type de result pour diagnostic
                        if not result:
                            st.error("❌ Aucun résultat retourné par l'extracteur")
                            return
                        
                        # Debug: vérifier le type de result
                        if not hasattr(result, 'clinical_findings'):
                            st.error(f"❌ Erreur: result est de type {type(result)} au lieu de SNOMEDExtraction")
                            st.write("Contenu de result:", result)
                            return
                        
                        if result and (result.clinical_findings or result.procedures or result.body_structures):
                            model_info = "Gemini 2.5 Flash" if use_flash_model else "Gemini 2.5 Pro"
                            st.success(f"✅ Extraction réussie en {extraction_time:.1f}s ({model_info})")
                            
                            # Validation complète avec SNOMEDValidator
                            validator = SNOMEDValidator()
                            validation_stats = validator.validate_extraction_result(result)
                            
                            # Affichage des résultats
                            st.markdown("### 📊 Résultats de l'extraction")
                            
                            # Métriques globales
                            total_extracted = len(validation_stats.get("validation_details", []))
                            valid_count = validation_stats.get("valid_codes", 0)
                            success_rate = (valid_count / total_extracted * 100) if total_extracted > 0 else 0
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Entités extraites", total_extracted)
                            with col2:
                                st.metric("Codes valides", valid_count)
                            with col3:
                                st.metric("Taux de réussite", f"{success_rate:.1f}%")
                            with col4:
                                st.metric("Temps d'extraction", f"{extraction_time:.1f}s")
                            
                            # Tableau des résultats valides uniquement
                            valid_results = [
                                detail for detail in validation_stats.get("validation_details", [])
                                if detail["status"] == "VALID" and detail["official_term"] is not None
                            ]
                            
                            if valid_results:
                                st.markdown("### ✅ Termes SNOMED CT validés")
                                
                                # Créer le tableau
                                df_data = []
                                for result in valid_results:
                                    df_data.append({
                                        "Terme extrait (Gemini)": result["term"],
                                        "Code SNOMED": result["gemini_code"], 
                                        "Terme officiel (Base FR)": result["official_term"]
                                    })
                                
                                df = pd.DataFrame(df_data)
                                
                                # Afficher le tableau avec un style propre
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                st.success(f"🎯 {len(valid_results)} terme(s) validé(s) dans la base SNOMED CT française")
                            
                            else:
                                st.warning("⚠️ Aucun terme n'a pu être validé dans la base SNOMED CT française")
                            
                            # Section détaillée optionnelle (avec tous les résultats) - Seulement en mode développement
                            if not preview_production:
                                with st.expander("📋 Voir tous les résultats détaillés"):
                                    for detail in validation_stats.get("validation_details", []):
                                        status_icon = "✅" if detail["status"] == "VALID" else "❌"
                                        with st.container():
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write(f"{status_icon} **Terme:** {detail['term']}")
                                                st.write(f"**Code:** {detail['gemini_code']}")
                                            with col2:
                                                if detail["status"] == "VALID" and detail["official_term"]:
                                                    st.write(f"**Statut:** ✅ Validé")
                                                    st.write(f"**Terme officiel:** {detail['official_term']}")
                                                else:
                                                    st.write(f"**Statut:** ❌ Code non trouvé dans la base française")
                                            st.markdown("---")
                        
                        else:
                            st.warning("⚠️ Aucune entité extraite")
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'extraction : {str(e)}")
                    import traceback
                    with st.expander("🔧 Détails de l'erreur"):
                        st.code(traceback.format_exc())
        
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

if __name__ == "__main__":
    main() 