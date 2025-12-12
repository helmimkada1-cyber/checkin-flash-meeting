import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json

# =============================================================================
# CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="🧬 Check-in Plateau Technique",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fichiers de données
DATA_DIR = Path("data")
CHECKINS_FILE = DATA_DIR / "checkins.json"
KUDOS_FILE = DATA_DIR / "kudos.json"
IDEAS_FILE = DATA_DIR / "ideas.json"
PROBLEMS_STATUS_FILE = DATA_DIR / "problems_status.json"

# Configuration équipe - À ADAPTER SELON TON ÉQUIPE
COLLABORATEURS = ["Marie", "Thomas", "Sophie", "Lucas", "Emma", "Julie", "Pierre", "Camille"]
SITES = ["Site A", "Site B", "Site C"]
POSTES = ["Technicien", "Biologiste", "Secrétaire", "Coursier", "Responsable"]

# Mapping humeur vers score numérique
HUMEUR_SCORES = {"😫": 1, "😟": 2, "😐": 3, "🙂": 4, "😄": 5}
EMOJIS_HUMEUR = ["😫", "😟", "😐", "🙂", "😄"]

# =============================================================================
# INITIALISATION SESSION STATE
# =============================================================================
if "checkin_submitted" not in st.session_state:
    st.session_state.checkin_submitted = False
if "kudos_submitted" not in st.session_state:
    st.session_state.kudos_submitted = False
if "idea_submitted" not in st.session_state:
    st.session_state.idea_submitted = False
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "show_success_checkin" not in st.session_state:
    st.session_state.show_success_checkin = False
if "show_success_kudos" not in st.session_state:
    st.session_state.show_success_kudos = False
if "show_success_idea" not in st.session_state:
    st.session_state.show_success_idea = False
if "kudos_destinataire" not in st.session_state:
    st.session_state.kudos_destinataire = ""

# =============================================================================
# STYLES CSS PERSONNALISÉS
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
    
    * { font-family: 'Nunito', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
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
    
    .weather-box {
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    
    .weather-emoji {
        font-size: 4rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FONCTIONS DE DONNÉES
# =============================================================================

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(filepath):
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filepath, data):
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checkins():
    return load_json(CHECKINS_FILE)

def save_checkin(checkin_data):
    checkins = load_checkins()
    checkins.append(checkin_data)
    save_json(CHECKINS_FILE, checkins)

def load_kudos():
    return load_json(KUDOS_FILE)

def save_kudos(kudo_data):
    kudos = load_kudos()
    kudos.append(kudo_data)
    save_json(KUDOS_FILE, kudos)

def load_ideas():
    return load_json(IDEAS_FILE)

def save_idea(idea_data):
    ideas = load_ideas()
    ideas.append(idea_data)
    save_json(IDEAS_FILE, ideas)

def load_problems_status():
    return load_json(PROBLEMS_STATUS_FILE)

def get_problem_status(problem_id):
    statuses = load_problems_status()
    problem_statuses = [s for s in statuses if s.get("problem_id") == problem_id]
    if problem_statuses:
        return problem_statuses[-1]["status"]
    return "🟡 En attente"

def update_problem_status(problem_id, new_status, resolution_note=""):
    statuses = load_problems_status()
    statuses.append({
        "problem_id": problem_id,
        "status": new_status,
        "resolution_note": resolution_note,
        "updated_at": datetime.now().isoformat()
    })
    save_json(PROBLEMS_STATUS_FILE, statuses)

def calculate_team_weather(df_recent):
    if df_recent.empty:
        return "❓", "Pas de données"
    
    humeur_scores = df_recent["humeur"].map(HUMEUR_SCORES)
    energie_scores = df_recent["energie"]
    
    avg_humeur = humeur_scores.mean()
    avg_energie = energie_scores.mean()
    nb_problemes = df_recent["a_probleme"].sum()
    
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

# =============================================================================
# SIDEBAR
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
    
    st.markdown("### 🌡️ Météo de l'équipe")
    
    checkins = load_checkins()
    if checkins:
        df_all = pd.DataFrame(checkins)
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_recent = df_all[df_all["date"] >= (datetime.now() - timedelta(days=7))]
        
        weather_emoji, weather_text = calculate_team_weather(df_recent)
        
        st.markdown(f"""
        <div class="weather-box">
            <div class="weather-emoji">{weather_emoji}</div>
            <div style="font-weight: bold; color: #333;">{weather_text}</div>
            <div style="font-size: 0.8rem; color: #666;">7 derniers jours</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aucun check-in enregistré")

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🧬 Check-in Flash Meeting</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Plateau Technique de Biologie</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ONGLETS
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
# TAB 1 : CHECK-IN
# =============================================================================
with tab_checkin:
    
    # Afficher le message de succès si nécessaire
    if st.session_state.show_success_checkin:
        st.success("✅ Check-in enregistré ! Merci 🙏")
        st.balloons()
        st.session_state.show_success_checkin = False
    
    if utilisateur_actuel == "-- Sélectionne ton nom --":
        st.warning("👈 Sélectionne ton nom dans la barre latérale pour commencer")
    else:
        st.subheader(f"Comment ça va aujourd'hui, {utilisateur_actuel} ?")
        
        # Utiliser une clé unique basée sur form_key pour réinitialiser les widgets
        fk = st.session_state.form_key
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            site = st.selectbox("📍 Ton site", SITES, key=f"checkin_site_{fk}")
        with col2:
            poste = st.selectbox("💼 Ton poste", POSTES, key=f"checkin_poste_{fk}")
        with col3:
            date_checkin = st.date_input("📅 Date", value=datetime.now(), key=f"checkin_date_{fk}")
        
        st.markdown("---")
        
        col_humeur, col_energie, col_charge = st.columns(3)
        
        with col_humeur:
            st.markdown("#### 🌡️ Ta météo du jour")
            humeur = st.select_slider(
                "Comment te sens-tu ?",
                options=EMOJIS_HUMEUR,
                value="🙂",
                key=f"checkin_humeur_{fk}"
            )
        
        with col_energie:
            st.markdown("#### ⚡ Niveau d'énergie")
            energie = st.slider("De 1 à 5", 1, 5, 3, key=f"checkin_energie_{fk}")
        
        with col_charge:
            st.markdown("#### 📊 Charge de travail")
            charge = st.select_slider(
                "Ta charge",
                options=["😌 Calme", "🙂 Normal", "😓 Chargé", "🔥 Débordé"],
                value="🙂 Normal",
                key=f"checkin_charge_{fk}"
            )
        
        st.markdown("---")
        
        st.markdown("#### ⚠️ Problèmes ou alertes")
        a_probleme = st.checkbox("J'ai un problème à signaler", key=f"checkin_probleme_{fk}")
        
        type_probleme = None
        description_probleme = None
        urgence = None
        impact_patient = False
        
        if a_probleme:
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                type_probleme = st.selectbox(
                    "Type de problème",
                    ["🔧 Technique / Matériel", "📦 Stock / Réactifs", "💻 Informatique",
                     "📋 Organisation", "😤 Client mécontent", "👥 RH / Équipe", "❓ Autre"],
                    key=f"type_pb_{fk}"
                )
            
            with col_p2:
                urgence = st.radio("Urgence", ["🟢 Faible", "🟠 Moyen", "🔴 Urgent"], horizontal=True, key=f"urgence_{fk}")
            
            description_probleme = st.text_area("Décris le problème", key=f"desc_pb_{fk}", height=100)
            impact_patient = st.checkbox("⚠️ Impact patient potentiel", key=f"impact_{fk}")
        
        st.markdown("---")
        
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.markdown("#### 🎉 Une victoire ?")
            victoire = st.text_area("Partage une bonne nouvelle", key=f"victoire_{fk}", height=80)
        
        with col_v2:
            st.markdown("#### 🆘 Besoin d'aide ?")
            besoin_aide = st.text_area("Décris ton besoin", key=f"aide_{fk}", height=80)
        
        commentaire = st.text_area("💬 Autre chose ?", key=f"commentaire_{fk}", height=60)
        
        if st.button("✅ Envoyer mon check-in", type="primary", use_container_width=True):
            if a_probleme and not description_probleme:
                st.error("⚠️ Décris le problème svp")
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
                
                try:
                    save_checkin(checkin)
                    # Incrémenter la clé pour réinitialiser le formulaire
                    st.session_state.form_key += 1
                    st.session_state.show_success_checkin = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

# =============================================================================
# TAB 2 : KUDOS
# =============================================================================
with tab_kudos:
    
    # Afficher le message de succès si nécessaire
    if st.session_state.show_success_kudos:
        st.success(f"🌟 Kudos envoyé à {st.session_state.kudos_destinataire} !")
        st.balloons()
        st.session_state.show_success_kudos = False
    
    st.subheader("🌟 Kudos - Reconnaissance entre collègues")
    
    col_form, col_list = st.columns([1, 1])
    
    with col_form:
        st.markdown("#### Envoyer un Kudos")
        
        fk = st.session_state.form_key
        
        if utilisateur_actuel != "-- Sélectionne ton nom --":
            destinataire = st.selectbox(
                "👤 À qui ?",
                [c for c in COLLABORATEURS if c != utilisateur_actuel],
                key=f"kudos_dest_{fk}"
            )
        else:
            destinataire = st.selectbox("👤 Destinataire", COLLABORATEURS, key=f"kudos_dest2_{fk}")
        
        categorie_kudos = st.selectbox(
            "🏷️ Catégorie",
            ["🤝 Entraide", "😊 Bonne humeur", "⭐ Travail remarquable", 
             "💪 Persévérance", "🎯 Efficacité", "💡 Bonne idée"],
            key=f"kudos_cat_{fk}"
        )
        
        message_kudos = st.text_area("💬 Ton message", key=f"kudos_msg_{fk}", height=100)
        
        if st.button("🌟 Envoyer le Kudos", use_container_width=True):
            if utilisateur_actuel == "-- Sélectionne ton nom --":
                st.error("Identifie-toi d'abord")
            elif not message_kudos:
                st.warning("Écris un message !")
            else:
                kudo = {
                    "id": f"kudos_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "de": utilisateur_actuel,
                    "pour": destinataire,
                    "categorie": categorie_kudos,
                    "message": message_kudos,
                    "date": datetime.now().isoformat()
                }
                try:
                    save_kudos(kudo)
                    st.session_state.form_key += 1
                    st.session_state.show_success_kudos = True
                    st.session_state.kudos_destinataire = destinataire
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    with col_list:
        st.markdown("#### Derniers Kudos")
        
        kudos_list = load_kudos()
        
        if not kudos_list:
            st.info("Aucun kudos pour le moment 🌟")
        else:
            for kudo in reversed(kudos_list[-10:]):
                st.markdown(f"""
                <div class="kudos-card">
                    <strong>{kudo['categorie']}</strong><br>
                    <b>{kudo['de']}</b> → <b>{kudo['pour']}</b><br>
                    <em>"{kudo['message']}"</em>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 3 : IDÉES
# =============================================================================
with tab_ideas:
    
    # Afficher le message de succès si nécessaire
    if st.session_state.show_success_idea:
        st.success("💡 Idée soumise !")
        st.balloons()
        st.session_state.show_success_idea = False
    
    st.subheader("💡 Boîte à idées")
    
    col_idea_form, col_idea_list = st.columns([1, 1])
    
    with col_idea_form:
        st.markdown("#### Proposer une idée")
        
        fk = st.session_state.form_key
        
        categorie_idee = st.selectbox(
            "🏷️ Catégorie",
            ["🔧 Organisation", "💻 Outils", "📋 Process", "👥 Vie d'équipe", "🌱 Environnement"],
            key=f"idea_cat_{fk}"
        )
        
        titre_idee = st.text_input("📌 Titre", key=f"idea_titre_{fk}")
        description_idee = st.text_area("📝 Description", key=f"idea_desc_{fk}", height=150)
        
        if st.button("💡 Soumettre mon idée", use_container_width=True):
            if utilisateur_actuel == "-- Sélectionne ton nom --":
                st.error("Identifie-toi d'abord")
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
                    "statut": "🆕 Nouvelle"
                }
                try:
                    save_idea(idea)
                    st.session_state.form_key += 1
                    st.session_state.show_success_idea = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    
    with col_idea_list:
        st.markdown("#### Idées proposées")
        
        ideas_list = load_ideas()
        
        if not ideas_list:
            st.info("Aucune idée pour le moment 💡")
        else:
            for idea in reversed(ideas_list[-10:]):
                st.markdown(f"""
                <div class="idea-card">
                    <strong>{idea['categorie']}</strong> • <small>{idea['statut']}</small><br>
                    <b>{idea['titre']}</b><br>
                    <p>{idea['description'][:150]}...</p>
                    <small>Par {idea['auteur']}</small>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 4 : HISTORIQUE
# =============================================================================
with tab_historique:
    
    st.subheader("📋 Historique des check-ins")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Aucun check-in enregistré")
    else:
        df = pd.DataFrame(checkins)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtre_collab = st.multiselect("👤 Collaborateur", COLLABORATEURS, key="hist_collab")
        with col2:
            filtre_site = st.multiselect("📍 Site", SITES, key="hist_site")
        with col3:
            filtre_jours = st.slider("📅 Derniers jours", 1, 30, 7, key="hist_jours")
        
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= (datetime.now() - timedelta(days=filtre_jours))]
        
        if filtre_collab:
            df = df[df["collaborateur"].isin(filtre_collab)]
        if filtre_site:
            df = df[df["site"].isin(filtre_site)]
        
        st.markdown("---")
        
        if df.empty:
            st.info("Aucun résultat")
        else:
            df_sorted = df.sort_values("date", ascending=False)
            
            for _, row in df_sorted.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{row['collaborateur']}** ({row['poste']})")
                        st.caption(f"📍 {row['site']}")
                    
                    with col2:
                        st.caption(f"📅 {row['date'].strftime('%d/%m/%Y')}")
                        st.caption(f"📊 {row['charge']}")
                    
                    with col3:
                        st.markdown(f"<div style='text-align:center; font-size: 2rem;'>{row['humeur']}</div>", 
                                   unsafe_allow_html=True)
                    
                    if row.get("a_probleme"):
                        st.error(f"⚠️ **{row['type_probleme']}** ({row['urgence']})")
                        st.write(row["description_probleme"])
                    
                    if row.get("victoire"):
                        st.success(f"🎉 {row['victoire']}")
                    
                    st.markdown("---")

# =============================================================================
# TAB 5 : STATISTIQUES
# =============================================================================
with tab_stats:
    
    st.subheader("📊 Tableau de bord")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Pas de données")
    else:
        df = pd.DataFrame(checkins)
        df["date"] = pd.to_datetime(df["date"])
        
        periode = st.radio("Période", ["7 jours", "14 jours", "30 jours"], horizontal=True)
        
        days = int(periode.split()[0])
        df_period = df[df["date"] >= (datetime.now() - timedelta(days=days))]
        
        if df_period.empty:
            st.warning("Pas de données sur cette période")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Check-ins", len(df_period))
            
            with col2:
                avg_humeur = df_period["humeur"].map(HUMEUR_SCORES).mean()
                st.metric("😊 Humeur", f"{avg_humeur:.1f}/5")
            
            with col3:
                avg_energie = df_period["energie"].mean()
                st.metric("⚡ Énergie", f"{avg_energie:.1f}/5")
            
            with col4:
                nb_pb = df_period["a_probleme"].sum()
                st.metric("⚠️ Problèmes", int(nb_pb))
            
            st.markdown("---")
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("#### 📈 Évolution humeur & énergie")
                
                df_daily = df_period.copy()
                df_daily["humeur_score"] = df_daily["humeur"].map(HUMEUR_SCORES)
                df_agg = df_daily.groupby("date").agg({
                    "humeur_score": "mean",
                    "energie": "mean"
                }).reset_index()
                
                df_agg = df_agg.rename(columns={
                    "humeur_score": "Humeur",
                    "energie": "Énergie"
                })
                df_agg = df_agg.set_index("date")
                
                st.line_chart(df_agg, height=300)
            
            with col_g2:
                st.markdown("#### 🌡️ Distribution des humeurs")
                
                humeur_counts = df_period["humeur"].value_counts()
                
                cols = st.columns(5)
                for i, emoji in enumerate(EMOJIS_HUMEUR):
                    with cols[i]:
                        count = humeur_counts.get(emoji, 0)
                        st.markdown(f"""
                        <div style="text-align: center; padding: 10px; background: #f0f0f0; border-radius: 10px;">
                            <div style="font-size: 2rem;">{emoji}</div>
                            <div style="font-size: 1.5rem; font-weight: bold;">{count}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("#### 📍 Humeur moyenne par site")
            
            df_site = df_period.copy()
            df_site["humeur_score"] = df_site["humeur"].map(HUMEUR_SCORES)
            site_agg = df_site.groupby("site").agg({
                "humeur_score": "mean",
                "energie": "mean"
            }).round(2)
            
            site_agg = site_agg.rename(columns={
                "humeur_score": "Humeur moy.",
                "energie": "Énergie moy."
            })
            
            st.dataframe(site_agg, use_container_width=True)

# =============================================================================
# TAB 6 : SUIVI PROBLÈMES
# =============================================================================
with tab_suivi:
    
    st.subheader("🔧 Suivi des problèmes")
    
    checkins = load_checkins()
    
    if not checkins:
        st.info("Aucun check-in")
    else:
        df = pd.DataFrame(checkins)
        problemes = df[df["a_probleme"] == True].copy()
        
        if problemes.empty:
            st.success("✅ Aucun problème remonté !")
        else:
            problemes["statut_actuel"] = problemes["id"].apply(get_problem_status)
            
            filtre_statut = st.multiselect(
                "Filtrer par statut",
                ["🟡 En attente", "🔵 En cours", "✅ Résolu"],
                default=["🟡 En attente", "🔵 En cours"],
                key="suivi_statut"
            )
            
            if filtre_statut:
                problemes = problemes[problemes["statut_actuel"].isin(filtre_statut)]
            
            st.markdown("---")
            
            for _, row in problemes.iterrows():
                with st.expander(f"{row['urgence']} | {row['type_probleme']} - {row['collaborateur']}"):
                    
                    st.markdown(f"**Déclaré par :** {row['collaborateur']} ({row['site']})")
                    st.markdown(f"**Description :** {row['description_probleme']}")
                    st.markdown(f"**Statut :** {row['statut_actuel']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_status = st.selectbox(
                            "Nouveau statut",
                            ["🟡 En attente", "🔵 En cours", "✅ Résolu"],
                            key=f"status_{row['id']}"
                        )
                    
                    with col2:
                        if new_status == "✅ Résolu":
                            note = st.text_input("Note de résolution", key=f"note_{row['id']}")
                        else:
                            note = ""
                    
                    if st.button("💾 Mettre à jour", key=f"btn_{row['id']}"):
                        update_problem_status(row["id"], new_status, note)
                        st.success("Statut mis à jour !")
                        st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>🧬 Check-in Flash Meeting • Plateau Technique</small>
</div>
""", unsafe_allow_html=True)
