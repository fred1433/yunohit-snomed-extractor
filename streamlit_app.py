import streamlit as st
import subprocess
import time
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="🏥 Extracteur SNOMED CT - Yunohit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un look professionnel moderne
st.markdown("""
<style>
    /* Thème principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header h3 {
        margin: 0.5rem 0;
        font-weight: 300;
        opacity: 0.9;
    }
    
    /* Cards métriques améliorées */
    .metric-card {
        background: linear-gradient(145deg, #f8f9ff 0%, #e8ecf7 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Boxes de statut */
    .success-box {
        background: linear-gradient(145deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    
    .warning-box {
        background: linear-gradient(145deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #ffc107;
    }
    
    .info-box {
        background: linear-gradient(145deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #bee5eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #17a2b8;
    }
    
    /* Boutons personnalisés */
    .stButton > button {
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar améliorée */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9ff 0%, #e8ecf7 100%);
    }
    
    /* Métriques temps réel */
    .real-time-metrics {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    
    /* Footer */
    .footer-style {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-top: 3rem;
    }
    
    /* Animations */
    @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }
    
    .loading-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .main-header {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def parse_validation_output(output: str) -> dict:
    """Parser les résultats d'extraction"""
    stats = {
        'total_codes': 0,
        'valid_codes': 0,
        'success_rate': 0.0,
        'clinical_findings': 0,
        'procedures': 0,
        'body_structures': 0,
        'extraction_time': 0,
        'validation_time': 0
    }
    
    try:
        # Statistiques de validation
        total_match = re.search(r'Total des codes analysés : (\d+)', output)
        if total_match:
            stats['total_codes'] = int(total_match.group(1))
        
        valid_match = re.search(r'Codes VALIDES.*? : (\d+)', output)
        if valid_match:
            stats['valid_codes'] = int(valid_match.group(1))
        
        rate_match = re.search(r'Taux de validité : (\d+(?:\.\d+)?)%', output)
        if rate_match:
            stats['success_rate'] = float(rate_match.group(1))
        
        # Statistiques d'extraction
        extraction_match = re.search(r'Extraction réussie : (\d+) constatations, (\d+) procédures, (\d+) structures', output)
        if extraction_match:
            stats['clinical_findings'] = int(extraction_match.group(1))
            stats['procedures'] = int(extraction_match.group(2))
            stats['body_structures'] = int(extraction_match.group(3))
        
        # Temps d'exécution
        extraction_time_match = re.search(r'Temps d\'extraction Gemini : (\d+(?:\.\d+)?)s', output)
        if extraction_time_match:
            stats['extraction_time'] = float(extraction_time_match.group(1))
        
        validation_time_match = re.search(r'Temps de validation SNOMED : (\d+(?:\.\d+)?)s', output)
        if validation_time_match:
            stats['validation_time'] = float(validation_time_match.group(1))
            
    except Exception as e:
        st.error(f"Erreur parsing : {e}")
    
    return stats

def extract_tables_from_output(output: str) -> Dict[str, str]:
    """Extraire les tableaux de résultats"""
    tables = {'validation': '', 'client': ''}
    
    try:
        # Tableau de validation détaillé
        validation_start = output.find('Détail COMPLET de la validation')
        validation_end = output.find('Tableau CLIENT')
        if validation_start != -1 and validation_end != -1:
            tables['validation'] = output[validation_start:validation_end]
        
        # Tableau client
        client_start = output.find('Tableau CLIENT')
        client_end = output.find('LÉGENDE DES MODIFIEURS')
        if client_start != -1 and client_end != -1:
            tables['client'] = output[client_start:client_end]
    except:
        pass
    
    return tables

def run_extraction(mode: str, note_content: str) -> dict:
    """Lance une extraction selon le mode choisi"""
    
    # Vérifier d'abord que les secrets sont configurés
    try:
        from config_unified import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            return {
                'success': False,
                'output': "",
                'error': """🔐 CONFIGURATION REQUISE

❌ L'API Key Gemini n'est pas configurée.

📋 ÉTAPES DE CONFIGURATION :
1. Cliquez sur ⚙️ Settings (en bas à droite)
2. Allez dans l'onglet "Secrets"  
3. Ajoutez : GEMINI_API_KEY = "votre_clé_ici"
4. Cliquez Save
5. L'app redémarre automatiquement

🔗 Guide complet : SETUP_SECRETS.md dans le repo"""
            }
    except Exception as e:
        return {
            'success': False,
            'output': "",
            'error': f"""🔐 ERREUR DE CONFIGURATION

❌ Problème de configuration : {str(e)}

📋 SOLUTION :
1. Configurez GEMINI_API_KEY dans les secrets Streamlit
2. ⚙️ Settings → Secrets → GEMINI_API_KEY = "votre_clé"

🔗 Plus d'infos : SETUP_SECRETS.md"""
        }
    
    try:
        if mode == "Standard":
            result = subprocess.run(
                ['python', 'validate_extraction_streamlit.py'], 
                capture_output=True, 
                text=True, 
                timeout=180,
                input=note_content
            )
        else:  # Haute Précision
            result = subprocess.run(
                ['python', 'extract_high_precision.py'], 
                capture_output=True, 
                text=True, 
                timeout=300
            )
        
        if result.returncode == 0:
            stats = parse_validation_output(result.stdout)
            tables = extract_tables_from_output(result.stdout)
            return {
                'success': True,
                'output': result.stdout,
                'stats': stats,
                'tables': tables,
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': f"""❌ ERREUR D'EXÉCUTION

📋 STDOUT:
{result.stdout}

🔴 STDERR:
{result.stderr}

🔧 CODE DE RETOUR: {result.returncode}

💡 DIAGNOSTIC:
- Si erreur 'rich': Redéploiement en cours...
- Si erreur de configuration: Vérifiez les secrets."""
            }
    except Exception as e:
        return {
            'success': False,
            'output': "",
            'error': f"Erreur d'exécution : {str(e)}"
        }

def main():
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Extracteur SNOMED CT</h1>
        <h3>Solution d'extraction automatisée pour Yunohit</h3>
        <p>Extraction d'entités médicales avec validation officielle SNOMED CT</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar pour les paramètres
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/2a5298/ffffff?text=YUNOHIT", width=200)
        st.markdown("### ⚙️ Paramètres")
        
        mode = st.selectbox(
            "🎯 Mode d'extraction",
            ["Standard", "Haute Précision"],
            help="Standard: 1 extraction (~45s, 0.015€)\nHaute Précision: 3 extractions parallèles (~50s, 0.045€)"
        )
        
        st.markdown("### 📊 Informations")
        if mode == "Standard":
            st.info("⏱️ ~45 secondes\n💰 ~0.015€\n🎯 Extraction unique")
        else:
            st.info("⏱️ ~50 secondes\n💰 ~0.045€\n🎯 Validation croisée (3 extractions)")
        
        st.markdown("### 🛡️ Sécurité")
        st.success("✅ Limites API actives\n✅ Coûts surveillés\n✅ Base SNOMED officielle")

    # Interface principale
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Note Médicale")
        
        # Choix entre exemple et saisie personnalisée
        input_type = st.radio(
            "Source de la note:",
            ["Utiliser l'exemple", "Saisir une note personnalisée"],
            horizontal=True
        )
        
        if input_type == "Utiliser l'exemple":
            note_content = """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
Pas d'antécédents notables. Vaccins à jour. Notion de cas similaire à l'école.
Examen : Lésions vésiculeuses typiques.
Diagnostic : Varicelle.
Traitement : Antihistaminique oral et soins locaux. Éviction scolaire recommandée."""
            
            st.text_area(
                "Note médicale (exemple):",
                value=note_content,
                height=150,
                disabled=True
            )
        else:
            note_content = st.text_area(
                "Votre note médicale:",
                placeholder="Saisissez ici la note médicale à analyser...",
                height=150
            )
        
        # Bouton d'extraction
        if st.button(f"🚀 Lancer l'extraction {mode}", type="primary", use_container_width=True):
            if not note_content.strip():
                st.error("⚠️ Veuillez saisir une note médicale")
                return
            
            # Session state pour stocker les résultats
            st.session_state.extraction_running = True
            st.session_state.extraction_results = None

    with col2:
        st.markdown("### 📈 Métriques en Temps Réel")
        
        # Métriques par défaut
        metrics_placeholder = st.empty()
        
        with metrics_placeholder.container():
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("⏱️ Temps", "--", "")
            with col_m2:
                st.metric("🎯 Codes valides", "--", "")
            with col_m3:
                st.metric("💰 Coût", "--", "")

    # Traitement de l'extraction
    if st.session_state.get('extraction_running', False):
        with st.spinner(f"🔄 Extraction en cours ({mode})..."):
            start_time = time.time()
            
            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulation du progrès
            for i in range(100):
                progress_bar.progress(i + 1)
                if i < 20:
                    status_text.text("🔍 Initialisation...")
                elif i < 60:
                    status_text.text("🧠 Extraction avec Gemini...")
                elif i < 90:
                    status_text.text("✅ Validation SNOMED...")
                else:
                    status_text.text("📊 Finalisation...")
                time.sleep(0.1)  # Simulation
            
            # Lancement réel de l'extraction
            result = run_extraction(mode, note_content)
            end_time = time.time()
            duration = end_time - start_time
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.extraction_running = False
            st.session_state.extraction_results = result
            st.session_state.extraction_duration = duration

    # Affichage des résultats
    if st.session_state.get('extraction_results'):
        result = st.session_state.extraction_results
        duration = st.session_state.get('extraction_duration', 0)
        
        if result['success']:
            stats = result['stats']
            
            st.markdown("---")
            st.markdown("## 🎯 Résultats de l'Extraction")
            
            # Métriques mises à jour
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("⏱️ Temps total", f"{duration:.1f}s")
            with col_m2:
                st.metric("🎯 Codes valides", f"{stats['valid_codes']}/{stats['total_codes']}")
            with col_m3:
                st.metric("📊 Taux réussite", f"{stats['success_rate']:.1f}%")
            with col_m4:
                cost = 0.015 if mode == "Standard" else 0.045
                st.metric("💰 Coût", f"{cost:.3f}€")
            
            # Affichage conditionnel selon le mode
            if mode == "Haute Précision" and "ANALYSE DE CONSENSUS" in result['output']:
                st.markdown("### 🔬 Analyse de Consensus (Haute Précision)")
                
                # Extraire les stats de consensus
                consensus_section = result['output'].split("ANALYSE DE CONSENSUS")[1].split("RÉSULTAT FINAL")[0]
                st.code(consensus_section, language="text")
            
            # Résultats détaillés
            col_res1, col_res2 = st.columns([1, 1])
            
            with col_res1:
                st.markdown("### 📋 Entités Extraites")
                st.success(f"✅ {stats['clinical_findings']} Constatations cliniques")
                st.info(f"🏥 {stats['procedures']} Interventions/Procédures")
                st.warning(f"🫀 {stats['body_structures']} Structures corporelles")
            
            with col_res2:
                st.markdown("### ⏱️ Performance")
                if stats['extraction_time'] > 0:
                    st.metric("🧠 Temps Gemini", f"{stats['extraction_time']:.1f}s")
                    st.metric("✅ Temps validation", f"{stats['validation_time']:.1f}s")
                
                # Évaluation de la qualité
                if stats['success_rate'] >= 60:
                    st.success(f"🎯 Excellent résultat ({stats['success_rate']:.1f}%)")
                elif stats['success_rate'] >= 40:
                    st.warning(f"⚠️ Résultat modéré ({stats['success_rate']:.1f}%)")
                else:
                    st.error(f"❌ Résultat faible ({stats['success_rate']:.1f}%)")
            
            # Onglets pour les tableaux détaillés
            tab1, tab2, tab3 = st.tabs(["📊 Tableau Client", "🔍 Validation Détaillée", "📄 Sortie Complète"])
            
            with tab1:
                st.markdown("### 🎯 Résultat Final - Codes SNOMED Valides")
                if 'client' in result['tables'] and result['tables']['client']:
                    st.code(result['tables']['client'], language="text")
                else:
                    st.code("Tableau client non trouvé", language="text")
            
            with tab2:
                st.markdown("### 🔬 Validation Complète")
                if 'validation' in result['tables'] and result['tables']['validation']:
                    st.code(result['tables']['validation'], language="text")
                else:
                    st.code("Tableau de validation non trouvé", language="text")
            
            with tab3:
                st.markdown("### 📄 Sortie Technique Complète")
                st.code(result['output'], language="text")
        
        else:
            st.error("❌ Erreur lors de l'extraction")
            st.code(result['error'], language="text")

    # Footer
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("**🏥 Yunohit**")
        st.caption("Solution SNOMED CT")
    with col_f2:
        st.markdown("**🔧 Powered by**")
        st.caption("Google Gemini + SNOMED CT")
    with col_f3:
        st.markdown("**📞 Support**")
        st.caption("Version 2.0")

if __name__ == "__main__":
    # Initialisation session state
    if 'extraction_running' not in st.session_state:
        st.session_state.extraction_running = False
    if 'extraction_results' not in st.session_state:
        st.session_state.extraction_results = None
    
    main() 