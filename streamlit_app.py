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

def translate_modifier_values(value):
    """Traduit les valeurs des modifieurs contextuels de l'anglais vers le français"""
    translations = {
        # Négation
        'positive': 'positif',
        'negative': 'négatif',
        'absent': 'absent',
        'present': 'présent',
        
        # Famille
        'patient': 'patient',
        'family': 'famille',
        
        # Suspicion
        'confirmed': 'confirmé',
        'suspected': 'suspecté',
        'suspicion': 'suspicion',
        
        # Antécédent
        'current': 'actuel',
        'antecedent': 'antécédent',
        'past': 'passé',
        'history': 'historique'
    }
    
    return translations.get(value.lower(), value) if isinstance(value, str) else value

def get_demo_results():
    """Retourne des résultats de démonstration fixes pour tester l'interface"""
    return [
        {
            "term": "varicelle",
            "gemini_code": "38907003",
            "official_term": "Varicelle",
            "negation": "positif",
            "family": "patient", 
            "suspicion": "confirmé",
            "antecedent": "actuel"
        },
        {
            "term": "éruption cutanée",
            "gemini_code": "271807003",
            "official_term": "Éruption cutanée",
            "negation": "positif",
            "family": "patient",
            "suspicion": "confirmé", 
            "antecedent": "actuel"
        },
        {
            "term": "prurit",
            "gemini_code": "418290006",
            "official_term": "Prurit",
            "negation": "positif",
            "family": "patient",
            "suspicion": "confirmé",
            "antecedent": "actuel"
        },
        {
            "term": "antihistaminique",
            "gemini_code": "372806008",
            "official_term": "Antihistaminique",
            "negation": "positif",
            "family": "patient",
            "suspicion": "confirmé",
            "antecedent": "actuel"
        },
        {
            "term": "vaccination",
            "gemini_code": "33879002",
            "official_term": "Vaccination",
            "negation": "positif",
            "family": "patient",
            "suspicion": "confirmé",
            "antecedent": "antécédent"
        }
    ]

def main():
    # CSS personnalisé pour un design plus moderne
    st.markdown("""
    <style>
    /* Amélioration globale de la police */
    .main {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* SUPPRIMER LES LIENS D'ANCRAGE AUTOMATIQUES */
    .element-container h1 a, 
    .element-container h2 a, 
    .element-container h3 a, 
    .element-container h4 a, 
    .element-container h5 a, 
    .element-container h6 a {
        display: none !important;
    }
    
    /* AUGMENTER TOUTES LES TAILLES DE POLICES - MINIMUM 28PX ! */
    
    /* Taille de base globale beaucoup plus grande */
    html { font-size: 28px !important; }
    
    /* Texte général de l'application */
    .main, .stApp, body {
        font-size: 28px !important;
    }
    
    /* Labels et textes des formulaires */
    .stSelectbox label, 
    .stTextArea label, 
    .stCheckbox label,
    .stRadio label,
    .stSlider label {
        font-size: 32px !important;
        font-weight: 500 !important;
    }
    
    /* Contenu des selectbox */
    .stSelectbox > div > div > div {
        font-size: 28px !important;
    }
    
    /* Zone de texte */
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e1e5fe;
        transition: border-color 0.3s ease;
        font-size: 28px !important;
        line-height: 1.5 !important;
        padding: 20px !important;
        min-height: 200px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Texte des checkboxes */
    .stCheckbox > label > div:last-child {
        font-size: 28px !important;
    }
    
    /* Métriques - valeurs et labels */
    div[data-testid="metric-container"] > div {
        font-size: 30px !important;
    }
    
    div[data-testid="metric-container"] > div > div:first-child {
        font-size: 28px !important; /* Label de la métrique */
    }
    
    div[data-testid="metric-container"] > div > div:last-child {
        font-size: 48px !important; /* Valeur de la métrique */
        font-weight: 600 !important;
    }
    
    /* Tableaux */
    .stDataFrame table {
        font-size: 28px !important;
    }
    
    .stDataFrame th {
        font-size: 30px !important;
        font-weight: 600 !important;
    }
    
    .stDataFrame td {
        font-size: 28px !important;
        padding: 16px 12px !important;
    }
    
    /* Boutons */
    .stButton > button {
        font-size: 32px !important;
        font-weight: 600 !important;
        padding: 1rem 2.5rem !important;
    }
    
    /* Messages d'alerte et de succès */
    .stAlert {
        font-size: 28px !important;
    }
    
    /* Texte dans les expanders */
    .streamlit-expanderContent {
        font-size: 28px !important;
    }
    
    /* Titres - beaucoup plus grands */
    h1 { font-size: 4rem !important; }
    h2 { font-size: 3.5rem !important; }
    h3 { font-size: 3rem !important; }
    h4 { font-size: 2.5rem !important; }
    h5 { font-size: 2rem !important; }
    h6 { font-size: 1.8rem !important; }
    
    /* Paragraphes et texte libre */
    p, div, span {
        font-size: 28px !important;
        line-height: 1.6 !important;
    }
    
    /* Help tooltips */
    .stTooltipIcon {
        font-size: 28px !important;
    }
    
    /* Sidebar si utilisé */
    .css-1d391kg {
        font-size: 28px !important;
    }
    
    /* RÈGLES CIBLÉES POUR AUGMENTER LES PETITES POLICES */
    
    /* Forcer les labels de formulaires spécifiquement */
    label[data-testid] { font-size: 16px !important; }
    
    /* Forcer le contenu des selectbox seulement */
    .stSelectbox div[data-baseweb="select"] span { font-size: 15px !important; }
    
    /* Forcer seulement le texte dans les checkboxes */
    .stCheckbox label span { font-size: 15px !important; }
    
    /* Augmenter la taille de base de l'application */
    html { font-size: 16px !important; }
    
    /* Header principal plus moderne */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    /* Amélioration des métriques */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #f8f9ff 0%, #e8ecff 100%);
        border: 1px solid #e1e5fe;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 16px rgba(103, 126, 234, 0.1);
        transition: transform 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(103, 126, 234, 0.15);
    }
    
    /* Styling des selectbox et inputs */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #e1e5fe;
        transition: border-color 0.3s ease;
        min-height: 80px !important;
        padding: 20px 16px !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Ajuster la hauteur de tous les éléments selectbox */
    .stSelectbox div[data-baseweb="select"] {
        min-height: 80px !important;
        padding: 20px 16px !important;
    }
    
    /* Ajuster la hauteur de la dropdown elle-même */
    .stSelectbox div[data-baseweb="select"] > div {
        min-height: 60px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Corriger l'alignement du selectbox */
    .stSelectbox {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    .stSelectbox > div {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Règles plus agressives pour l'alignement du selectbox */
    .stSelectbox > div > div > div {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Cibler spécifiquement les éléments BaseWeb */
    .stSelectbox div[data-baseweb="select"] {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Forcer l'alignement sur tous les containers Streamlit */
    div[data-testid="stSelectbox"] {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    div[data-testid="stSelectbox"] > div {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Reset complet des marges pour le selectbox */
    .stSelectbox * {
        margin-left: 0 !important;
    }
    
    /* Bouton principal plus attractif */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Amélioration des checkboxes */
    .stCheckbox > label {
        background: rgba(102, 126, 234, 0.05);
        padding: 0.5rem 1rem;
        border-radius: 10px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .stCheckbox > label:hover {
        background: rgba(102, 126, 234, 0.1);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    /* Tableau de résultats plus moderne */
    .stDataFrame {
        background: white;
        border-radius: 15px;
        border: 1px solid #e1e5fe;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
        overflow: hidden;
    }
    
    /* FORCER ABSOLUMENT LA TAILLE DES TABLEAUX */
    .stDataFrame table * {
        font-size: 28px !important;
    }
    
    .stDataFrame th * {
        font-size: 30px !important;
    }
    
    .stDataFrame td * {
        font-size: 28px !important;
    }
    
    /* Sélecteurs ultra-spécifiques pour les tableaux */
    div[data-testid="stDataFrame"] table {
        font-size: 28px !important;
    }
    
    div[data-testid="stDataFrame"] th {
        font-size: 30px !important;
    }
    
    div[data-testid="stDataFrame"] td {
        font-size: 28px !important;
    }
    
    /* Forcer avec des sélecteurs encore plus précis */
    div[data-testid="stDataFrame"] * {
        font-size: 28px !important;
    }
    
    /* RÈGLES ULTRA-AGRESSIVES POUR LES TABLEAUX - PHASE 2 */
    
    /* Cibler spécifiquement les cellules des tableaux Streamlit */
    .dataframe tbody tr th, .dataframe tbody tr td {
        font-size: 28px !important;
        line-height: 1.4 !important;
    }
    
    /* Cibler les headers de tableaux */
    .dataframe thead tr th {
        font-size: 30px !important;
        font-weight: 600 !important;
    }
    
    /* Forcer sur tous les éléments contenant du texte dans les tableaux */
    .stDataFrame table tbody tr td,
    .stDataFrame table thead tr th,
    .stDataFrame table tbody tr th {
        font-size: 28px !important;
        padding: 16px 12px !important;
    }
    
    /* Sélecteurs encore plus spécifiques pour Streamlit */
    div[data-testid="stDataFrame"] table tbody tr td,
    div[data-testid="stDataFrame"] table thead tr th {
        font-size: 28px !important;
        line-height: 1.5 !important;
    }
    
    /* Forcer sur les spans et divs à l'intérieur des cellules */
    .stDataFrame table tbody tr td span,
    .stDataFrame table tbody tr td div,
    .stDataFrame table thead tr th span,
    .stDataFrame table thead tr th div {
        font-size: 28px !important;
    }
    
    /* Règles pour le contenu des cellules avec data-testid */
    div[data-testid="stDataFrame"] table tbody tr td span,
    div[data-testid="stDataFrame"] table tbody tr td div,
    div[data-testid="stDataFrame"] table thead tr th span,
    div[data-testid="stDataFrame"] table thead tr th div {
        font-size: 28px !important;
    }
    
    /* Forcer absolument TOUT dans les dataframes */
    .stDataFrame, .stDataFrame *, 
    div[data-testid="stDataFrame"], div[data-testid="stDataFrame"] * {
        font-size: 28px !important;
    }
    
    /* Règles spécifiques pour le widget dataframe de Streamlit */
    .element-container .stDataFrame,
    .element-container .stDataFrame * {
        font-size: 28px !important;
    }
    
    /* Cibler les classes CSS générées par Streamlit/Pandas */
    .dataframe, .dataframe * {
        font-size: 28px !important;
    }
    
    /* CSS spécifique pour les tables HTML générées */
    table.dataframe, table.dataframe * {
        font-size: 28px !important;
    }
    
    /* Forcer sur les éléments tbody et thead spécifiquement */
    .stDataFrame tbody, .stDataFrame tbody *,
    .stDataFrame thead, .stDataFrame thead * {
        font-size: 28px !important;
    }
    
    /* Amélioration des alertes de succès */
    .stAlert > div {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.2);
    }
    
    /* Sections avec cartes */
    .result-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e1e5fe;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.08);
    }
    
    /* Dividers plus élégants */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1px;
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal redesigné
    st.markdown("""
    <div class="main-header">
        <h1>🏥 PoC Extracteur SNOMED CT Yunohit</h1>
        <p style="opacity: 0.9; font-size: 1.1rem; margin: 0.5rem 0 0 0;">
            Intelligence artificielle pour l'extraction d'entités médicales
        </p>
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
                "Exemple 1 - Pédiatrie": """Enfant Léo Martin, 8 ans. Consulte pour une éruption cutanée prurigineuse évoluant depuis 48h sur les membres et le tronc.
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
                "📋 Sélectionnez ou saisissez une Note Médicale :",
                options=list(exemples_notes.keys()),
                index=0
            )
            
            # Zone de texte qui se met à jour selon la sélection
            if choix_note == "Saisie personnalisée":
                note_content = st.text_area(
                    "✍️ Votre note médicale :",
                    value="",
                    height=150,
                    placeholder="Saisissez ici votre note médicale..."
                )
            else:
                note_content = st.text_area(
                    "📄 Note médicale sélectionnée :",
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
            
            # Mode démonstration pour tests interface instantanés
            demo_mode = st.checkbox(
                "🎭 Mode démonstration : Afficher des résultats fixes (instantané)",
                value=False,
                help="Résultats factices pour tester l'interface sans attendre ni consommer d'API"
            )
            
            # Mode fusion ultime - seulement si pas en mode Flash
            if not use_flash_model and not preview_production:
                fusion_mode = st.checkbox(
                    "🚀 MÉTHODE ULTIME : Fusion de 3 extractions + validation (recommandé)",
                    value=False,
                    help="Combine TOUS les résultats validés de 3 extractions pour maximiser les entités trouvées"
                )
                
                # Nouvelle méthode V2 avec validation sémantique
                fusion_v2_mode = st.checkbox(
                    "🧠 MÉTHODE ULTIME V2 : + Validation sémantique hybride (PREMIUM)",
                    value=True,
                    help="Version avancée avec filtrage intelligent des incohérences sémantiques via LLM hybride"
                )
            else:
                fusion_mode = False
                fusion_v2_mode = False
            
            # Afficher le warning seulement si pas en mode prévisualisation
            if use_flash_model and not preview_production:
                st.warning("⚠️ Mode développement activé - Qualité réduite")
            
            if st.button("🚀 Extraire les Entités SNOMED", type="primary"):
                try:
                    # Mode démonstration : affichage instantané de résultats fixes
                    if demo_mode:
                        st.success("🎭 Mode démonstration activé - Résultats factices affichés instantanément")
                        
                        # Résultats de démonstration
                        valid_results_with_modifiers = get_demo_results()
                        
                        # Métriques de démonstration - Seulement en mode développement
                        if not preview_production:
                            st.markdown("#### 📈 Métriques de performance (démonstration)")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "📋 Entités extraites", 
                                    len(valid_results_with_modifiers),
                                    help="Nombre total d'entités détectées par l'IA"
                                )
                            with col2:
                                st.metric(
                                    "✅ Codes valides", 
                                    len(valid_results_with_modifiers),
                                    help="Codes trouvés dans la base SNOMED CT française"
                                )
                            with col3:
                                st.metric(
                                    "🎯 Taux de réussite", 
                                    "100.0%",
                                    help="Pourcentage de codes validés"
                                )
                            with col4:
                                st.metric(
                                    "⏱️ Temps d'extraction", 
                                    "0.0s",
                                    help="Durée totale du traitement"
                                )
                        
                        # Affichage du tableau de démonstration
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                                    color: white; 
                                    padding: 1.5rem 2rem; 
                                    border-radius: 15px; 
                                    margin: 1.5rem 0; 
                                    text-align: center; 
                                    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
                                    border: 2px solid #4CAF50;">
                                <h3 style="margin: 0; font-size: 2rem; font-weight: 600;">
                                    🎯 {len(valid_results_with_modifiers)} terme(s) extraits et validés dans la base SNOMED CT française
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Créer un tableau HTML personnalisé avec contrôle total des polices
                        # En-tête du tableau
                        table_html = '<div style="background: white; border-radius: 15px; border: 1px solid #e1e5fe; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1); overflow: hidden; margin: 1rem 0;">'
                        table_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">'
                        table_html += '<thead><tr style="background: linear-gradient(145deg, #f8f9ff 0%, #e8ecff 100%);">'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Terme extrait</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Code SNOMED</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Terme officiel</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Négation</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Famille</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Suspicion</th>'
                        table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Antécédent</th>'
                        table_html += '</tr></thead><tbody>'
                        
                        # Lignes de données
                        for i, result in enumerate(valid_results_with_modifiers):
                            bg_color = "#f8f9ff" if i % 2 == 0 else "white"
                            table_html += f'<tr style="background: {bg_color};">'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["term"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0; font-family: monospace; color: #667eea;">{result["gemini_code"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["official_term"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["negation"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["family"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["suspicion"]}</td>'
                            table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["antecedent"]}</td>'
                            table_html += '</tr>'
                        
                        # Fermeture du tableau
                        table_html += '</tbody></table></div>'
                        
                        st.markdown(table_html, unsafe_allow_html=True)
                        
                        return  # Sortir ici pour le mode démonstration
                    
                    # Mode normal : appels API réels
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
                        
                        # Choix de la méthode selon le mode
                        if use_flash_model:
                            # Mode développement : méthode rapide 1-étape avec Flash
                            result = extractor.extract_snomed_info(medical_note)
                        elif fusion_v2_mode:
                            # Mode ULTIME V2 : extraction parallèle + validation SNOMED + validation sémantique
                            import asyncio
                            # Définir use_context_modifiers pour la méthode V2
                            use_context_modifiers = True
                            result_v2 = asyncio.run(extractor.extract_triple_with_validation_fusion_v2(
                                text=note_content, 
                                use_context_modifiers=use_context_modifiers
                            ))
                            
                            if "error" in result_v2:
                                st.error(f"❌ {result_v2['error']}")
                                return
                            
                            # Convertir le format V2 vers le format SNOMEDExtraction attendu
                            from models import SNOMEDExtraction, ClinicalFinding, Procedure, BodyStructure
                            
                            findings = []
                            procedures = []
                            body_structures = []
                            
                            for entity in result_v2['entities']['findings']:
                                findings.append(ClinicalFinding(
                                    term=entity['term'],
                                    description=f"Constatation clinique : {entity['term']}",
                                    context="Extrait par méthode ULTIME V2",
                                    snomed_code=entity['snomed_code'],
                                    negation=entity.get('negation', 'positive'),
                                    family=entity.get('family', 'patient'),
                                    suspicion=entity.get('suspicion', 'confirmed'),
                                    antecedent=entity.get('antecedent', 'current')
                                ))
                            
                            for entity in result_v2['entities']['procedures']:
                                procedures.append(Procedure(
                                    term=entity['term'],
                                    description=f"Procédure médicale : {entity['term']}",
                                    context="Extrait par méthode ULTIME V2",
                                    snomed_code=entity['snomed_code'],
                                    negation=entity.get('negation', 'positive'),
                                    family=entity.get('family', 'patient'),
                                    suspicion=entity.get('suspicion', 'confirmed'),
                                    antecedent=entity.get('antecedent', 'current')
                                ))
                            
                            for entity in result_v2['entities']['body_structures']:
                                body_structures.append(BodyStructure(
                                    term=entity['term'],
                                    description=f"Structure corporelle : {entity['term']}",
                                    context="Extrait par méthode ULTIME V2",
                                    snomed_code=entity['snomed_code'],
                                    negation=entity.get('negation', 'positive'),
                                    family=entity.get('family', 'patient'),
                                    suspicion=entity.get('suspicion', 'confirmed'),
                                    antecedent=entity.get('antecedent', 'current')
                                ))
                            
                            result = SNOMEDExtraction(
                                original_note=medical_note,
                                clinical_findings=findings,
                                procedures=procedures,
                                body_structures=body_structures
                            )
                        elif fusion_mode:
                            # Mode ULTIME V1 : fusion de 3 extractions + validation SNOMED
                            result = extractor.extract_triple_with_validation_fusion(medical_note)
                        else:
                            # Mode production standard : méthode 3 appels parallèles classique
                            result = extractor.extract_triple_parallel(medical_note)
                            
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
                            # Validation complète avec SNOMEDValidator
                            validator = SNOMEDValidator()
                            validation_stats = validator.validate_extraction_result(result)
                            
                            # Métriques globales - Seulement en mode développement
                            if not preview_production:
                                total_extracted = len(validation_stats.get("validation_details", []))
                                valid_count = validation_stats.get("valid_codes", 0)
                                success_rate = (valid_count / total_extracted * 100) if total_extracted > 0 else 0
                                
                                st.markdown("#### 📈 Métriques de performance")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric(
                                        "📋 Entités extraites", 
                                        total_extracted,
                                        help="Nombre total d'entités détectées par l'IA"
                                    )
                                with col2:
                                    st.metric(
                                        "✅ Codes valides", 
                                        valid_count,
                                        help="Codes trouvés dans la base SNOMED CT française"
                                    )
                                with col3:
                                    st.metric(
                                        "🎯 Taux de réussite", 
                                        f"{success_rate:.1f}%",
                                        help="Pourcentage de codes validés"
                                    )
                                with col4:
                                    st.metric(
                                        "⏱️ Temps d'extraction", 
                                        f"{extraction_time:.1f}s",
                                        help="Durée totale du traitement"
                                    )
                            
                            # Tableau des résultats valides uniquement avec modifieurs contextuels
                            valid_results_with_modifiers = []
                            
                            # Récupérer les modifieurs depuis les objets originaux
                            all_items = result.clinical_findings + result.procedures + result.body_structures
                            
                            for item in all_items:
                                # Vérifier si le code est valide
                                is_valid = validator.validate_code(item.snomed_code)
                                if is_valid:
                                    official_term = validator.get_french_term(item.snomed_code)
                                    if official_term:
                                        valid_results_with_modifiers.append({
                                            "term": item.term,
                                            "gemini_code": item.snomed_code,
                                            "official_term": official_term,
                                            "negation": translate_modifier_values(getattr(item, 'negation', 'positive')),
                                            "family": translate_modifier_values(getattr(item, 'family', 'patient')),
                                            "suspicion": translate_modifier_values(getattr(item, 'suspicion', 'confirmed')),
                                            "antecedent": translate_modifier_values(getattr(item, 'antecedent', 'current'))
                                        })
                            
                            if valid_results_with_modifiers:
                                # Titre simple comme demandé
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                                            color: white; 
                                            padding: 1.5rem 2rem; 
                                            border-radius: 15px; 
                                            margin: 1.5rem 0; 
                                            text-align: center; 
                                            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
                                            border: 2px solid #4CAF50;">
                                        <h3 style="margin: 0; font-size: 2rem; font-weight: 600;">
                                            🎯 {len(valid_results_with_modifiers)} terme(s) extraits et validés dans la base SNOMED CT française
                                        </h3>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # Créer un tableau HTML personnalisé avec contrôle total des polices
                                # En-tête du tableau
                                table_html = '<div style="background: white; border-radius: 15px; border: 1px solid #e1e5fe; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1); overflow: hidden; margin: 1rem 0;">'
                                table_html += '<table style="width: 100%; border-collapse: collapse; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">'
                                table_html += '<thead><tr style="background: linear-gradient(145deg, #f8f9ff 0%, #e8ecff 100%);">'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Terme extrait</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Code SNOMED</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Terme officiel</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Négation</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Famille</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Suspicion</th>'
                                table_html += '<th style="padding: 20px 16px; font-size: 30px; font-weight: 600; text-align: left; border-bottom: 2px solid #e1e5fe;">Antécédent</th>'
                                table_html += '</tr></thead><tbody>'
                                
                                # Lignes de données
                                for i, result in enumerate(valid_results_with_modifiers):
                                    bg_color = "#f8f9ff" if i % 2 == 0 else "white"
                                    table_html += f'<tr style="background: {bg_color};">'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["term"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0; font-family: monospace; color: #667eea;">{result["gemini_code"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["official_term"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["negation"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["family"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["suspicion"]}</td>'
                                    table_html += f'<td style="padding: 20px 16px; font-size: 28px; border-bottom: 1px solid #f0f0f0;">{result["antecedent"]}</td>'
                                    table_html += '</tr>'
                                
                                # Fermeture du tableau
                                table_html += '</tbody></table></div>'
                                
                                st.markdown(table_html, unsafe_allow_html=True)
                            
                            else:
                                st.warning("⚠️ Aucun terme n'a pu être validé dans la base SNOMED CT française")
                        
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