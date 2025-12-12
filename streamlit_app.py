import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# =============================================================================
# CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="🧬 Check-in Plateau Technique",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
CHECKINS_FILE = DATA_DIR / "checkins.json"
KUDOS_FILE = DATA_DIR / "kudos.json"
IDEAS_FILE = DATA_DIR / "ideas.json"
PROBLEMS_STATUS_FILE = DATA_DIR / "problems_status.json"

# Configuration équipe - À ADAPTER
COLLABORATEURS = ["Marie", "Thomas", "Sophie", "Lucas", "Emma", "Julie", "Pierre", "Camille"]
SITES = ["BCP Lyon Centre", "BCP Part-Dieu", "BCP Villeurbanne"]
POSTES = ["Technicien", "Biologiste", "Secrétaire", "Coursier", "Responsable"]

# Mapping humeur vers score numérique
HUMEUR_SCORES = {"😫": 1, "😟": 2, "😐": 3, "🙂": 4, "😄": 5}
EMOJIS_HUMEUR = ["😫", "😟", "😐", "🙂", "😄"]

# =============================================================================
# STYLES CSS PERSONNALISÉS
# =============================================================================
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Nunito', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #667eea;
    }
    
    .metric-card h3 {
        margin: 0;
        color: #333;
        font-size: 2rem;
    }
    
    .metric-card p {
        margin: 0.5rem 0 0 0;
        color: #666;
        font-size: 0.9rem;
    }
    
    .alert-urgent {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .kudos-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .idea-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .weather-indicator {
        font-size: 4rem;
        text-align: center;
        padding: 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    div[data-testid="stForm"] {
        background: #fafbfc;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def ensure_data_dir():
    """Crée le répertoire data si nécessaire"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(filepath):
    """Charge un fichier JSON"""
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filepath, data):
    """Sauvegarde dans un fichier JSON"""
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checkins():
    return load_json(CHECKINS_FILE)

def save_checkin(checkin):
    checkins = load_checkins()
    checkins.append(checkin)
    save_json(CHECKINS_FILE, checkins)

def load_kudos():
    return load_json(KUDOS_FILE)

def save_kudos(kudo):
    kudos = load_kudos()
    kudos.append(kudo)
    save_json(KUDOS_FILE, kudos)

def load_ideas():
    return load_json(IDEAS_FILE)

def save_idea(idea):
    ideas = load_ideas()
    ideas.append(idea)
    save_json(IDEAS_FILE, ideas)

def load_problems_status():
    return load_json(PROBLEMS_STATUS_FILE)

def update_problem_status(problem_id, new_status, resolution_note=""):
    statuses = load_problems_status()
    statuses.append({
        "problem_id": problem_id,
        "status": new_status,
        "resolution_note": resolution_note,
        "updated_at": datetime.now().isoformat()
    })
    save_json(PROBLEMS_STATUS_FILE, statuses)

def get_problem_current_status(problem_id):
    statuses = load_problems_status()
    problem_statuses = [s for s in statuses if s["problem_id"] == problem_id]
    if problem_statuses:
        return problem_statuses[-1]["status"]
    return "🟡 En attente"

def calculate_team_weather(df_recent):
    """Calcule la météo globale de l'équipe"""
    if df_recent.empty:
        return "❓", "Pas de données"
    
    # Score basé sur humeur et énergie
    humeur_scores = df_recent["humeur"].map(HUMEUR_SCORES)
    energie_scores = df_recent["energie"]
    
    avg_humeur = humeur_scores.mean()
    avg_energie = energie_scores.mean()
    nb_problemes = df_recent["a_probleme"].sum()
    
    # Score global (0-100)
    score = ((avg_humeur / 5) * 40 + (avg_energie / 5) * 40 - (nb_problemes / len(df_recent)) * 20)
    score = max(0, min(100, score * 100 / 80))
    
    if score >= 80:
        return "☀️", f"Excellent ({score:.0f}/100)"
    elif score >= 60:
        return "🌤️", f"Bon ({score:.0f}/100)"
    elif score >= 40:
        return "⛅", f"Moyen ({score:.0f}/100)"
    elif score >= 20:
        return "🌧️", f"Tendu ({score:.0f}/100)"
    else:
        return "⛈️", f"Critique ({score:.0f}/100)"

def export_to_excel(df, filename="export_checkins.xlsx"):
    """Exporte les données en Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Check-ins')
    return output.getvalue()

# =============================================================================
# SIDEBAR - IDENTIFICATION & MÉTÉO GLOBALE
# =============================================================================

with st.sidebar:
    st.markdown("### 👤 Identification")
    
    utilisateur_actuel = st.selectbox(
        "Qui es-tu ?",
        ["-- Sélectionne ton nom --"] + COLLABORATEURS,
        key="user_select"
    )
    
    if utilisateur_actuel != "-- Sélectionne ton nom --":
        st.success(f"Bienvenue {utilisateur_actuel} ! 👋")
    
    st.markdown("---")
    
    # Météo globale de l'équipe
    st.markdown("### 🌡️ Météo de l'équipe")
    
    checkins = load_checkins()
    if checkins:
        df_all = pd.DataFrame(checkins)
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_recent = df_all[df_all["date"] >= (datetime.now() - timedelta(days=7))]
        
        weather_emoji, weather_text = calculate_team_weather(df_recent)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <div style="font-size: 4rem;">{weather_emoji}</div>
            <div style="font-weight: bold; color: #333;">{weather_text}</div>
            <div style="font-size: 0.8rem; color: #666;">7 derniers jours</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Alertes urgentes
        problemes_urgents = df_recent[
            (df_recent["a_probleme"] == True) & 
            (df_recent["urgence"] == "🔴 Urgent")
        ]
        
        # Vérifier le statut actuel des problèmes
        problemes_non_resolus = []
        for _, row in problemes_urgents.iterrows():
            status = get_problem_current_status(row["id"])
            if status != "✅ Résolu":
                problemes_non_resolus.append(row)
        
        if problemes_non_resolus:
            st.markdown("---")
            st.markdown("### ⚠️ Alertes actives")
            st.error(f"**{len(problemes_non_resolus)}** problème(s) urgent(s) non résolu(s)")
    else:
        st.info("Aucun check-in enregistré")
    
    st.markdown("---")
    
    # Raccourcis
    st.markdown("### ⚡ Actions rapides")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Export", use_container_width=True):
            st.session_state["show_export"] = True
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

# =============================================================================
# HEADER PRINCIPAL
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🧬 Check-in Flash Meeting</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Plateau Technique de Biologie • Eurofins</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ONGLETS PRINCIPAUX
# =============================================================================

tab_checkin, tab_kudos, tab_ideas, tab_historique, tab_stats, tab_suivi = st.tabs([
    "📝 Mon check-in",
    "🌟 Kudos",
    "💡 Boîte à idées",
    "📋 Historique",
    "📊 Tableau de bord",
    "🔧 Suivi problèmes"
])

# =============================================================================
# TAB 1 : SAISIE DU CHECK-IN
# =============================================================================
with tab_checkin:
    
    if utilisateur_actuel == "-- Sélectionne ton nom --":
        st.warning("👈 Sélectionne ton nom dans la barre latérale pour commencer")
    else:
        st.subheader(f"Comment ça va aujourd'hui, {utilisateur_actuel} ?")
        
        # Container stylisé pour le formulaire
        with st.container():
            st.markdown("""
            <div style="background: #fafbfc; padding: 0.5rem; border-radius: 15px; border: 1px solid #e0e0e0;">
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                site = st.selectbox("📍 Ton site", SITES, key="checkin_site")
            with col2:
                poste = st.selectbox("💼 Ton poste", POSTES, key="checkin_poste")
            with col3:
                date_checkin = st.date_input("📅 Date", value=datetime.now(), key="checkin_date")
            
            st.markdown("---")
            
            # Section humeur et énergie
            col_humeur, col_energie, col_charge = st.columns(3)
            
            with col_humeur:
                st.markdown("#### 🌡️ Ta météo du jour")
                humeur = st.select_slider(
                    "Comment te sens-tu ?",
                    options=EMOJIS_HUMEUR,
                    value="🙂",
                    help="Sélectionne l'emoji qui correspond à ton état d'esprit",
                    key="checkin_humeur"
                )
            
            with col_energie:
                st.markdown("#### ⚡ Niveau d'énergie")
                energie = st.slider(
                    "De 1 (épuisé) à 5 (pleine forme)",
                    1, 5, 3,
                    help="Comment te sens-tu physiquement ?",
                    key="checkin_energie"
                )
            
            with col_charge:
                st.markdown("#### 📊 Charge de travail perçue")
                charge = st.select_slider(
                    "Ta charge aujourd'hui",
                    options=["😌 Calme", "🙂 Normal", "😓 Chargé", "🔥 Débordé"],
                    value="🙂 Normal",
                    help="Comment perçois-tu ta charge de travail ?",
                    key="checkin_charge"
                )
            
            st.markdown("---")
            
            # Section problèmes - EN DEHORS DU FORM pour réactivité
            st.markdown("#### ⚠️ Problèmes ou alertes à remonter")
            
            a_probleme = st.checkbox("J'ai un problème à signaler", key="checkin_a_probleme")
            
            # Variables par défaut
            type_probleme = None
            description_probleme = None
            urgence = None
            impact_patient = False
            
            if a_probleme:
                col_p1, col_p2 = st.columns(2)
                
                with col_p1:
                    type_probleme = st.selectbox(
                        "Type de problème",
                        [
                            "🔧 Technique / Matériel / Automate",
                            "📦 Manque de réactifs / Stock",
                            "💻 Informatique / SIL",
                            "📋 Organisation / Process",
                            "😤 Client / Prescripteur mécontent",
                            "👥 RH / Équipe / Planning",
                            "🚗 Logistique / Coursier",
                            "📞 Communication interne",
                            "🔬 Qualité / Non-conformité",
                            "❓ Autre"
                        ],
                        key="checkin_type_probleme"
                    )
                
                with col_p2:
                    urgence = st.radio(
                        "Niveau d'urgence",
                        ["🟢 Faible", "🟠 Moyen", "🔴 Urgent"],
                        horizontal=True,
                        key="checkin_urgence"
                    )
                
                description_probleme = st.text_area(
                    "Décris le problème",
                    placeholder="Explique brièvement le problème rencontré...",
                    height=100,
                    key="checkin_desc_probleme"
                )
                
                impact_patient = st.checkbox(
                    "⚠️ Impact potentiel sur les patients / délais de rendu",
                    key="checkin_impact_patient"
                )
            
            st.markdown("---")
            
            # Section positive
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.markdown("#### 🎉 Une victoire ou quelque chose de positif ?")
                victoire = st.text_area(
                    "Partage une bonne nouvelle (optionnel)",
                    placeholder="Un dossier débloqué, un patient satisfait, une bonne collaboration...",
                    height=80,
                    key="checkin_victoire"
                )
            
            with col_v2:
                st.markdown("#### 🆘 Besoin d'aide sur quelque chose ?")
                besoin_aide = st.text_area(
                    "Décris ton besoin (optionnel)",
                    placeholder="Une tâche où tu as besoin d'un coup de main...",
                    height=80,
                    key="checkin_aide"
                )
            
            st.markdown("---")
            
            # Commentaire libre
            commentaire = st.text_area(
                "💬 Autre chose à partager pour le flash meeting ?",
                placeholder="Information, suggestion, question...",
                height=60,
                key="checkin_commentaire"
            )
            
            st.markdown("---")
            
            # Bouton de soumission
            if st.button(
                "✅ Envoyer mon check-in",
                use_container_width=True,
                type="primary",
                key="checkin_submit"
            ):
                # Validation
                if a_probleme and not description_probleme:
                    st.error("⚠️ Merci de décrire le problème rencontré.")
                else:
                    checkin = {
                        "id": f"{utilisateur_actuel}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "collaborateur": utilisateur_actuel,
                        "site": site,
                        "poste": poste,
                        "date": date_checkin.strftime("%Y-%m-%d"),
                        "humeur": humeur,
                        "energie": energie,
                        "charge": charge,
                        "a_probleme": a_probleme,
                        "type_probleme": type_probleme,
                        "description_probleme": description_probleme,
                        "urgence": urgence,
                        "impact_patient": impact_patient,
                        "victoire": victoire if victoire else None,
                        "besoin_aide": besoin_aide if besoin_aide else None,
                        "commentaire": commentaire if commentaire else None,
                        "cree_le": datetime.now().isoformat()
                    }
                    
                    save_checkin(checkin)
                    st.success("✅ Check-in enregistré ! Merci pour ta contribution 🙏")
                    st.balloons()
                    
                    # Réinitialiser après soumission
                    st.toast("Check-in envoyé ! 🎉", icon="✅")

# =============================================================================
# TAB 2 : KUDOS / RECONNAISSANCE
# =============================================================================
with tab_kudos:
    
    st.subheader("🌟 Kudos - Reconnaissance entre collègues")
    st.markdown("*Remercie un collègue pour son aide, sa bonne humeur ou son travail !*")
    
    col_form, col_list = st.columns([1, 1])
    
    with col_form:
        st.markdown("#### Envoyer un Kudos")
        
        with st.form("kudos_form"):
            if utilisateur_actuel != "-- Sélectionne ton nom --":
                destinataire = st.selectbox(
                    "👤 À qui veux-tu envoyer un kudos ?",
                    [c for c in COLLABORATEURS if c != utilisateur_actuel]
                )
            else:
                destinataire = st.selectbox("👤 Destinataire", COLLABORATEURS)
            
            categorie_kudos = st.selectbox(
                "🏷️ Catégorie",
                ["🤝 Entraide", "😊 Bonne humeur", "⭐ Travail remarquable", 
                 "💪 Persévérance", "🎯 Efficacité", "💡 Bonne idée", "❤️ Autre"]
            )
            
            message_kudos = st.text_area(
                "💬 Ton message",
                placeholder="Merci pour...",
                height=100
            )
            
            send_kudos = st.form_submit_button("🌟 Envoyer le Kudos", use_container_width=True)
            
            if send_kudos:
                if utilisateur_actuel == "-- Sélectionne ton nom --":
                    st.error("Identifie-toi d'abord dans la barre latérale")
                elif not message_kudos:
                    st.warning("Écris un petit message !")
                else:
                    kudo = {
                        "id": f"kudos_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "de": utilisateur_actuel,
                        "pour": destinataire,
                        "categorie": categorie_kudos,
                        "message": message_kudos,
                        "date": datetime.now().isoformat()
                    }
                    save_kudos(kudo)
                    st.success(f"🌟 Kudos envoyé à {destinataire} !")
                    st.balloons()
    
    with col_list:
        st.markdown("#### Derniers Kudos")
        
        kudos_list = load_kudos()
        
        if not kudos_list:
            st.info("Aucun kudos pour le moment. Sois le premier ! 🌟")
        else:
            # Afficher les 10 derniers kudos
            for kudo in reversed(kudos_list[-10:]):
                st.markdown(f"""
                <div class="kudos-card">
                    <strong>{kudo['categorie']}</strong><br>
                    <span style="font-size: 1.1rem;"><b>{kudo['de']}</b> → <b>{kudo['pour']}</b></span><br>
                    <em>"{kudo['message']}"</em><br>
                    <small style="color: #666;">{kudo['date'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 3 : BOÎTE À IDÉES
# =============================================================================
with tab_ideas:
    
    st.subheader("💡 Boîte à idées - Suggestions d'amélioration")
    st.markdown("*Une idée pour améliorer notre quotidien au labo ? Partage-la ici !*")
    
    col_idea_form, col_idea_list = st.columns([1, 1])
    
    with col_idea_form:
        st.markdown("#### Proposer une idée")
        
        with st.form("idea_form"):
            categorie_idee = st.selectbox(
                "🏷️ Catégorie",
                ["🔧 Organisation", "💻 Outils / Informatique", "📋 Process / Qualité",
                 "👥 Vie d'équipe", "📦 Matériel / Stock", "🌱 Environnement de travail", "❓ Autre"]
            )
            
            titre_idee = st.text_input(
                "📌 Titre de ton idée",
                placeholder="En quelques mots..."
            )
            
            description_idee = st.text_area(
                "📝 Décris ton idée",
                placeholder="Explique ton idée et ses bénéfices potentiels...",
                height=150
            )
            
            submit_idea = st.form_submit_button("💡 Soumettre mon idée", use_container_width=True)
            
            if submit_idea:
                if utilisateur_actuel == "-- Sélectionne ton nom --":
                    st.error("Identifie-toi d'abord dans la barre latérale")
                elif not titre_idee or not description_idee:
                    st.warning("Remplis le titre et la description")
                else:
                    idea = {
                        "id": f"idea_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "auteur": utilisateur_actuel,
                        "categorie": categorie_idee,
                        "titre": titre_idee,
                        "description": description_idee,
                        "date": datetime.now().isoformat(),
                        "votes": 0,
                        "statut": "🆕 Nouvelle"
                    }
                    save_idea(idea)
                    st.success("💡 Idée soumise ! Merci pour ta contribution !")
    
    with col_idea_list:
        st.markdown("#### Idées proposées")
        
        ideas_list = load_ideas()
        
        if not ideas_list:
            st.info("Aucune idée pour le moment. Lance-toi ! 💡")
        else:
            for idea in reversed(ideas_list[-10:]):
                st.markdown(f"""
                <div class="idea-card">
                    <strong>{idea['categorie']}</strong> • <small>{idea['statut']}</small><br>
                    <span style="font-size: 1.1rem; font-weight: bold;">{idea['titre']}</span><br>
                    <p style="margin: 0.5rem 0;">{idea['description'][:200]}{'...' if len(idea['description']) > 200 else ''}</p>
                    <small style="color: #666;">Par {idea['auteur']} • {idea['date'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 4 : HISTORIQUE
# =============================================================================
with tab_historique:
    
    st.subheader("📋 Historique des check-ins")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Aucun check-in enregistré pour le moment.")
    else:
        # Filtres
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtre_collab = st.multiselect("👤 Collaborateur", COLLABORATEURS, default=[])
        with col2:
            filtre_site = st.multiselect("📍 Site", SITES, default=[])
        with col3:
            filtre_problemes = st.checkbox("⚠️ Avec problèmes uniquement")
        with col4:
            filtre_jours = st.slider("📅 Derniers jours", 1, 30, 7)
        
        # Filtrage
        df = pd.DataFrame(checkins)
        df["date"] = pd.to_datetime(df["date"])
        
        # Filtre temporel
        df = df[df["date"] >= (datetime.now() - timedelta(days=filtre_jours))]
        
        if filtre_collab:
            df = df[df["collaborateur"].isin(filtre_collab)]
        if filtre_site:
            df = df[df["site"].isin(filtre_site)]
        if filtre_problemes:
            df = df[df["a_probleme"] == True]
        
        # Export
        if not df.empty:
            col_export1, col_export2 = st.columns([3, 1])
            with col_export2:
                excel_data = export_to_excel(df)
                st.download_button(
                    "📥 Exporter Excel",
                    data=excel_data,
                    file_name=f"checkins_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        st.markdown("---")
        
        # Affichage
        df_sorted = df.sort_values("date", ascending=False)
        
        if df_sorted.empty:
            st.info("Aucun check-in ne correspond aux filtres sélectionnés.")
        else:
            for _, row in df_sorted.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        poste_display = row.get('poste', '')
                        st.markdown(f"**{row['collaborateur']}** ({poste_display})")
                        st.caption(f"📍 {row['site']}")
                    
                    with col2:
                        st.caption(f"📅 {row['date'].strftime('%d/%m/%Y')}")
                        charge_display = row.get('charge', 'N/A')
                        st.caption(f"📊 {charge_display}")
                    
                    with col3:
                        st.markdown(f"<div style='text-align:center; font-size: 2rem;'>{row['humeur']}</div>", 
                                   unsafe_allow_html=True)
                    
                    with col4:
                        energie_bars = "🔋" * row['energie'] + "⬜" * (5 - row['energie'])
                        st.markdown(f"<div style='text-align:center;'>{energie_bars}</div>", 
                                   unsafe_allow_html=True)
                    
                    # Problème
                    if row.get("a_probleme"):
                        impact_text = " • ⚠️ Impact patient" if row.get("impact_patient") else ""
                        st.error(f"⚠️ **{row['type_probleme']}** ({row['urgence']}){impact_text}")
                        st.write(row["description_probleme"])
                    
                    # Besoin d'aide
                    if row.get("besoin_aide"):
                        st.warning(f"🆘 **Besoin d'aide :** {row['besoin_aide']}")
                    
                    # Victoire
                    if row.get("victoire"):
                        st.success(f"🎉 {row['victoire']}")
                    
                    # Commentaire
                    if row.get("commentaire"):
                        st.info(f"💬 {row['commentaire']}")
                    
                    st.markdown("---")

# =============================================================================
# TAB 5 : TABLEAU DE BORD / STATISTIQUES
# =============================================================================
with tab_stats:
    
    st.subheader("📊 Tableau de bord de l'équipe")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Pas assez de données pour afficher les statistiques.")
    else:
        df = pd.DataFrame(checkins)
        df["date"] = pd.to_datetime(df["date"])
        
        # Sélection de la période
        periode = st.radio(
            "Période d'analyse",
            ["7 derniers jours", "14 derniers jours", "30 derniers jours", "Tout"],
            horizontal=True
        )
        
        if periode == "7 derniers jours":
            df_period = df[df["date"] >= (datetime.now() - timedelta(days=7))]
        elif periode == "14 derniers jours":
            df_period = df[df["date"] >= (datetime.now() - timedelta(days=14))]
        elif periode == "30 derniers jours":
            df_period = df[df["date"] >= (datetime.now() - timedelta(days=30))]
        else:
            df_period = df
        
        if df_period.empty:
            st.warning("Pas de check-ins sur cette période.")
        else:
            # Métriques principales
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📝 Check-ins", len(df_period))
            
            with col2:
                humeur_scores = df_period["humeur"].map(HUMEUR_SCORES)
                avg_humeur = humeur_scores.mean()
                st.metric("😊 Humeur moy.", f"{avg_humeur:.1f}/5")
            
            with col3:
                avg_energie = df_period["energie"].mean()
                st.metric("⚡ Énergie moy.", f"{avg_energie:.1f}/5")
            
            with col4:
                nb_problemes = df_period["a_probleme"].sum()
                st.metric("⚠️ Problèmes", int(nb_problemes))
            
            with col5:
                nb_victoires = df_period["victoire"].notna().sum()
                st.metric("🎉 Victoires", int(nb_victoires))
            
            st.markdown("---")
            
            # Graphiques
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                st.markdown("#### 📈 Évolution de l'humeur")
                
                df_daily = df_period.copy()
                df_daily["humeur_score"] = df_daily["humeur"].map(HUMEUR_SCORES)
                df_daily_agg = df_daily.groupby("date").agg({
                    "humeur_score": "mean",
                    "energie": "mean"
                }).reset_index()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_daily_agg["date"],
                    y=df_daily_agg["humeur_score"],
                    mode="lines+markers",
                    name="Humeur",
                    line=dict(color="#667eea", width=3),
                    marker=dict(size=8)
                ))
                fig.add_trace(go.Scatter(
                    x=df_daily_agg["date"],
                    y=df_daily_agg["energie"],
                    mode="lines+markers",
                    name="Énergie",
                    line=dict(color="#764ba2", width=3),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    yaxis=dict(range=[1, 5], title="Score"),
                    xaxis=dict(title=""),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_graph2:
                st.markdown("#### 🌡️ Distribution des humeurs")
                
                humeur_counts = df_period["humeur"].value_counts()
                
                # Assurer l'ordre des emojis
                humeur_order = pd.DataFrame({
                    "humeur": EMOJIS_HUMEUR,
                    "count": [humeur_counts.get(e, 0) for e in EMOJIS_HUMEUR]
                })
                
                fig_bar = px.bar(
                    humeur_order,
                    x="humeur",
                    y="count",
                    color="count",
                    color_continuous_scale=["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd"]
                )
                fig_bar.update_layout(
                    showlegend=False,
                    xaxis=dict(title=""),
                    yaxis=dict(title="Nombre"),
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=300,
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            st.markdown("---")
            
            # Analyse par site
            col_site, col_type = st.columns(2)
            
            with col_site:
                st.markdown("#### 📍 Humeur par site")
                
                df_site = df_period.copy()
                df_site["humeur_score"] = df_site["humeur"].map(HUMEUR_SCORES)
                site_agg = df_site.groupby("site").agg({
                    "humeur_score": "mean",
                    "energie": "mean",
                    "id": "count"
                }).reset_index()
                site_agg.columns = ["Site", "Humeur", "Énergie", "Nb check-ins"]
                
                st.dataframe(
                    site_agg.style.format({"Humeur": "{:.1f}", "Énergie": "{:.1f}"}),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col_type:
                st.markdown("#### ⚠️ Types de problèmes")
                
                problemes = df_period[df_period["a_probleme"] == True]
                
                if problemes.empty:
                    st.success("✅ Aucun problème sur cette période !")
                else:
                    type_counts = problemes["type_probleme"].value_counts()
                    
                    fig_pie = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        hole=0.4
                    )
                    fig_pie.update_layout(
                        margin=dict(l=20, r=20, t=30, b=20),
                        height=250,
                        showlegend=True,
                        legend=dict(font=dict(size=10))
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            
            # Charge de travail
            if "charge" in df_period.columns:
                st.markdown("#### 📊 Répartition de la charge de travail")
                
                charge_counts = df_period["charge"].value_counts()
                
                cols_charge = st.columns(4)
                charges = ["😌 Calme", "🙂 Normal", "😓 Chargé", "🔥 Débordé"]
                colors = ["#1dd1a1", "#48dbfb", "#feca57", "#ff6b6b"]
                
                for i, (charge_val, color) in enumerate(zip(charges, colors)):
                    with cols_charge[i]:
                        count = charge_counts.get(charge_val, 0)
                        pct = (count / len(df_period) * 100) if len(df_period) > 0 else 0
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: {color}20; 
                                    border-radius: 10px; border-left: 4px solid {color};">
                            <div style="font-size: 1.5rem;">{charge_val.split()[0]}</div>
                            <div style="font-size: 1.5rem; font-weight: bold;">{count}</div>
                            <div style="font-size: 0.9rem; color: #666;">{pct:.0f}%</div>
                        </div>
                        """, unsafe_allow_html=True)

# =============================================================================
# TAB 6 : SUIVI DES PROBLÈMES
# =============================================================================
with tab_suivi:
    
    st.subheader("🔧 Suivi des problèmes remontés")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Aucun check-in enregistré.")
    else:
        df = pd.DataFrame(checkins)
        problemes = df[df["a_probleme"] == True].copy()
        
        if problemes.empty:
            st.success("✅ Aucun problème remonté pour le moment !")
        else:
            # Ajouter le statut actuel
            problemes["statut_actuel"] = problemes["id"].apply(get_problem_current_status)
            
            # Filtres
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filtre_statut = st.multiselect(
                    "Statut",
                    ["🟡 En attente", "🔵 En cours", "✅ Résolu"],
                    default=["🟡 En attente", "🔵 En cours"]
                )
            
            with col_f2:
                filtre_urgence_pb = st.multiselect(
                    "Urgence",
                    ["🟢 Faible", "🟠 Moyen", "🔴 Urgent"],
                    default=[]
                )
            
            if filtre_statut:
                problemes = problemes[problemes["statut_actuel"].isin(filtre_statut)]
            if filtre_urgence_pb:
                problemes = problemes[problemes["urgence"].isin(filtre_urgence_pb)]
            
            # Trier par urgence et date
            urgence_order = {"🔴 Urgent": 0, "🟠 Moyen": 1, "🟢 Faible": 2}
            problemes["urgence_order"] = problemes["urgence"].map(urgence_order)
            problemes = problemes.sort_values(["urgence_order", "date"], ascending=[True, False])
            
            st.markdown("---")
            
            # Affichage des problèmes
            for _, row in problemes.iterrows():
                
                with st.expander(
                    f"{row['urgence']} | {row['type_probleme']} - {row['collaborateur']} ({row['date'][:10]})",
                    expanded=(row["urgence"] == "🔴 Urgent" and row["statut_actuel"] != "✅ Résolu")
                ):
                    
                    col_info, col_action = st.columns([2, 1])
                    
                    with col_info:
                        st.markdown(f"**Déclaré par :** {row['collaborateur']} ({row['site']})")
                        st.markdown(f"**Date :** {row['date']}")
                        st.markdown(f"**Description :** {row['description_probleme']}")
                        
                        if row.get("impact_patient"):
                            st.warning("⚠️ Impact potentiel sur les patients signalé")
                        
                        st.markdown(f"**Statut actuel :** {row['statut_actuel']}")
                    
                    with col_action:
                        st.markdown("**Mettre à jour le statut :**")
                        
                        new_status = st.selectbox(
                            "Nouveau statut",
                            ["🟡 En attente", "🔵 En cours", "✅ Résolu"],
                            key=f"status_{row['id']}",
                            label_visibility="collapsed"
                        )
                        
                        if new_status == "✅ Résolu":
                            resolution_note = st.text_input(
                                "Note de résolution",
                                key=f"note_{row['id']}",
                                placeholder="Comment le problème a été résolu..."
                            )
                        else:
                            resolution_note = ""
                        
                        if st.button("💾 Mettre à jour", key=f"btn_{row['id']}"):
                            update_problem_status(row["id"], new_status, resolution_note)
                            st.success("Statut mis à jour !")
                            st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>🧬 Check-in Flash Meeting • Plateau Technique Eurofins • 
    Fait avec ❤️ pour améliorer notre quotidien</small>
</div>
""", unsafe_allow_html=True)
