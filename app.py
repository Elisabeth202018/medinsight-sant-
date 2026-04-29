"""
app.py — MedInsight Health Data Platform
=========================================
Couche interface : Streamlit UI uniquement.
Toute la logique métier est dans backend.py.

Lancer avec : streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Import du backend ─────────────────────────────────────────────────────────
from backend import (
    db, engine,
    REGIONS, NIVEAUX_RISQUE_ORDRE, CATEGORIES_TA_ORDRE,
    COLUMNS,
)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DE LA PAGE
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MedInsight — Données de Santé",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CORRECTION 3 — Cache du chargement des données
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def load_cached() -> pd.DataFrame:
    """Charge les données avec cache 30s — évite les lectures répétées."""
    return db.load()

def invalidate_cache():
    """Vide le cache après chaque écriture."""
    load_cached.clear()

# ══════════════════════════════════════════════════════════════════════════════
# THÈME — Dark Luxury Medical
# ══════════════════════════════════════════════════════════════════════════════

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(14,26,36,0.5)",
    font=dict(family="Outfit, sans-serif", color="#a8c0d0", size=11),
    margin=dict(t=44, b=16, l=16, r=16),
    xaxis=dict(gridcolor="rgba(0,200,150,0.07)", zerolinecolor="rgba(0,200,150,0.1)"),
    yaxis=dict(gridcolor="rgba(0,200,150,0.07)", zerolinecolor="rgba(0,200,150,0.1)"),
    colorway=["#00c896", "#c8a84b", "#a8d8ea", "#ff5a5a", "#f0a500", "#7eb8f7"],
)
EMERALD_SEQ = ["#004d38", "#006b50", "#009070", "#00c896", "#40e0b0", "#80f0cc"]
GOLD_SEQ    = ["#5a3c00", "#8a5e00", "#b88000", "#c8a84b", "#e8c97a", "#f8e8a8"]

# ── CSS complet ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600&display=swap');

:root {
    --bg-deep:    #080d12;
    --bg-card:    #0e1a24;
    --bg-glass:   rgba(14,26,36,0.72);
    --emerald:    #00c896;
    --emerald-dim:#007a5c;
    --gold:       #c8a84b;
    --gold-light: #e8c97a;
    --ice:        #a8d8ea;
    --danger:     #ff5a5a;
    --warn:       #f0a500;
    --text-main:  #e8edf2;
    --text-muted: #6b8099;
    --border:     rgba(0,200,150,0.14);
    --glow:       rgba(0,200,150,0.22);
}
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-deep) !important;
    color: var(--text-main) !important;
}
.stApp {
    background: var(--bg-deep) !important;
    background-image:
        radial-gradient(ellipse 60% 40% at 10% 15%, rgba(0,200,150,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 50% 60% at 90% 85%, rgba(200,168,75,0.05) 0%, transparent 70%);
}
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(0,200,150,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,200,150,0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none; z-index: 0;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060c11 0%, #0a1520 60%, #060c11 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-main) !important; }
[data-testid="stSidebar"] hr { border-color: var(--border); }
.sidebar-logo { text-align:center; padding:1.5rem 0 1rem; }
.sidebar-logo .cross { font-size:2.4rem; filter:drop-shadow(0 0 14px var(--emerald)); }
.sidebar-logo .brand {
    font-family:'Cormorant Garamond',serif; font-size:1.6rem; font-weight:700; letter-spacing:1px;
    background:linear-gradient(90deg,var(--emerald),var(--gold-light));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.sidebar-logo .tagline {
    font-size:0.7rem; letter-spacing:3px; text-transform:uppercase; color:var(--text-muted) !important;
}
.nav-stat {
    background:rgba(0,200,150,0.06); border:1px solid var(--border);
    border-radius:12px; padding:0.9rem 1.1rem; margin:0.3rem 0; font-size:0.82rem;
}
.nav-stat strong { color:var(--emerald) !important; }
.hero {
    position:relative; border-radius:20px; overflow:hidden;
    padding:2.8rem 3.2rem; margin-bottom:2rem;
    background:linear-gradient(120deg,#0a1f18 0%,#0d1a2e 60%,#0a1520 100%);
    border:1px solid var(--border);
    box-shadow:0 0 60px rgba(0,200,150,0.07),0 20px 40px rgba(0,0,0,0.4);
}
.hero::before {
    content:''; position:absolute; top:-60px; right:-60px; width:320px; height:320px;
    background:radial-gradient(circle,rgba(0,200,150,0.12) 0%,transparent 70%); pointer-events:none;
}
.hero::after {
    content:''; position:absolute; bottom:-40px; left:30%; width:200px; height:200px;
    background:radial-gradient(circle,rgba(200,168,75,0.07) 0%,transparent 70%); pointer-events:none;
}
.hero-eyebrow { font-size:0.7rem; letter-spacing:4px; text-transform:uppercase; color:var(--emerald); margin-bottom:0.6rem; font-weight:500; }
.hero h1 { font-family:'Cormorant Garamond',serif; font-size:3rem; font-weight:700; color:var(--text-main); margin:0 0 0.5rem; line-height:1.1; }
.hero h1 span { color:var(--emerald); }
.hero p { font-size:1rem; color:var(--text-muted); margin:0; font-weight:300; max-width:520px; }
.hero-badge {
    position:absolute; top:2rem; right:2.5rem;
    background:rgba(0,200,150,0.1); border:1px solid var(--emerald-dim); border-radius:50px;
    padding:0.35rem 1rem; font-size:0.73rem; color:var(--emerald); letter-spacing:1.5px; text-transform:uppercase;
}
.kpi-card {
    background:var(--bg-card); border:1px solid var(--border); border-radius:16px;
    padding:1.4rem 1.6rem; position:relative; overflow:hidden; transition:border-color 0.3s,box-shadow 0.3s;
}
.kpi-card:hover { border-color:var(--emerald-dim); box-shadow:0 0 24px var(--glow); }
.kpi-card::after {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,var(--emerald),transparent);
}
.kpi-icon { font-size:1.5rem; margin-bottom:0.5rem; }
.kpi-val { font-family:'Cormorant Garamond',serif; font-size:2.4rem; font-weight:700; color:var(--emerald); line-height:1; }
.kpi-lbl { font-size:0.73rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px; margin-top:0.3rem; }
.sec-title {
    font-family:'Cormorant Garamond',serif; font-size:1.6rem; font-weight:600; color:var(--text-main);
    margin:2rem 0 1rem; display:flex; align-items:center; gap:0.6rem;
}
.sec-title::after { content:''; flex:1; height:1px; background:linear-gradient(90deg,var(--border),transparent); margin-left:0.5rem; }
.sec-dot { width:8px; height:8px; background:var(--emerald); border-radius:50%; box-shadow:0 0 8px var(--emerald); display:inline-block; }
.glass-card {
    background:var(--bg-glass); backdrop-filter:blur(20px);
    border:1px solid var(--border); border-radius:18px; padding:1.8rem;
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
}
.alert-danger { background:rgba(255,90,90,0.09); border:1px solid rgba(255,90,90,0.3); border-left:4px solid var(--danger); border-radius:10px; padding:0.85rem 1.1rem; color:#ffaaaa; margin:0.4rem 0; font-size:0.88rem; }
.alert-warn   { background:rgba(240,165,0,0.09);  border:1px solid rgba(240,165,0,0.3);  border-left:4px solid var(--warn);   border-radius:10px; padding:0.85rem 1.1rem; color:#ffd580; margin:0.4rem 0; font-size:0.88rem; }
.alert-ok     { background:rgba(0,200,150,0.08);  border:1px solid rgba(0,200,150,0.25); border-left:4px solid var(--emerald); border-radius:10px; padding:0.85rem 1.1rem; color:#80ffcc; margin:0.4rem 0; font-size:0.88rem; }
.risk-badge   { display:inline-block; padding:0.3rem 1rem; border-radius:50px; font-weight:600; font-size:0.85rem; letter-spacing:0.5px; }
.risk-low     { background:rgba(0,200,150,0.15);  color:var(--emerald); border:1px solid var(--emerald-dim); }
.risk-medium  { background:rgba(240,165,0,0.15);  color:var(--warn);    border:1px solid rgba(240,165,0,0.4); }
.risk-high    { background:rgba(255,90,90,0.15);  color:var(--danger);  border:1px solid rgba(255,90,90,0.4); }
div[data-testid="stForm"] {
    background:var(--bg-card) !important; border:1px solid var(--border) !important;
    border-radius:18px !important; padding:2rem !important; box-shadow:0 8px 32px rgba(0,0,0,0.3) !important;
}
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div,
.stTextArea textarea {
    background:rgba(8,13,18,0.7) !important; border:1px solid var(--border) !important;
    border-radius:10px !important; color:var(--text-main) !important; font-family:'Outfit',sans-serif !important;
}
.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus {
    border-color:var(--emerald) !important; box-shadow:0 0 0 3px rgba(0,200,150,0.15) !important;
}
label { color:var(--text-muted) !important; font-size:0.83rem !important; }
.stButton>button {
    background:linear-gradient(135deg,var(--emerald-dim),#004d38) !important; color:#e0fff5 !important;
    border:1px solid var(--emerald-dim) !important; border-radius:10px !important;
    font-family:'Outfit',sans-serif !important; font-weight:600 !important;
    transition:all 0.25s !important; box-shadow:0 4px 16px rgba(0,200,150,0.18) !important;
}
.stButton>button:hover { background:linear-gradient(135deg,var(--emerald),var(--emerald-dim)) !important; box-shadow:0 6px 24px rgba(0,200,150,0.35) !important; transform:translateY(-1px) !important; }
.stDownloadButton>button { background:transparent !important; color:var(--gold-light) !important; border:1px solid rgba(200,168,75,0.4) !important; box-shadow:none !important; }
.stDownloadButton>button:hover { background:rgba(200,168,75,0.1) !important; box-shadow:0 4px 14px rgba(200,168,75,0.2) !important; }
.stTabs [data-baseweb="tab-list"] { background:var(--bg-card); border-radius:12px; padding:4px; gap:4px; border:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius:8px; color:var(--text-muted) !important; font-family:'Outfit',sans-serif; font-size:0.85rem; padding:0.4rem 1rem; }
.stTabs [aria-selected="true"] { background:rgba(0,200,150,0.12) !important; color:var(--emerald) !important; border-bottom:none !important; }
[data-testid="stSidebar"] .stRadio>div { gap:0.3rem !important; }
[data-testid="stSidebar"] .stRadio label { padding:0.55rem 0.8rem !important; border-radius:8px !important; transition:background 0.2s !important; font-size:0.88rem !important; }
[data-testid="stSidebar"] .stRadio label:hover { background:rgba(0,200,150,0.08) !important; }
.footer { text-align:center; color:var(--text-muted); font-size:0.73rem; margin-top:3rem; padding:1.2rem 0; border-top:1px solid var(--border); letter-spacing:0.5px; }
.footer span { color:var(--emerald); }
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:var(--bg-deep); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:var(--emerald-dim); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSANTS UI RÉUTILISABLES
# ══════════════════════════════════════════════════════════════════════════════

def render_hero(eyebrow: str, title: str, highlight: str, subtitle: str, badge: str = ""):
    badge_html = f'<div class="hero-badge">{badge}</div>' if badge else ""
    st.markdown(f"""
    <div class="hero">
        {badge_html}
        <div class="hero-eyebrow">{eyebrow}</div>
        <h1>{title} <span>{highlight}</span></h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi(icon: str, value: str, label: str):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-val">{value}</div>
        <div class="kpi-lbl">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(title: str):
    st.markdown(f'<div class="sec-title"><span class="sec-dot"></span>{title}</div>', unsafe_allow_html=True)


def render_alerts(alerts: list):
    for kind, msg in alerts:
        st.markdown(f"<div class='alert-{kind}'>{msg}</div>", unsafe_allow_html=True)


def render_glass_card(html_content: str, extra_style: str = ""):
    st.markdown(f'<div class="glass-card" style="{extra_style}">{html_content}</div>', unsafe_allow_html=True)


def render_vital_card(icon: str, label: str, value: str, category: str):
    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:0.8rem">
        <div style="font-size:1.3rem;margin-bottom:0.2rem">{icon}</div>
        <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.7px">{label}</div>
        <div style="font-size:1.5rem;font-weight:700;color:var(--emerald)">{value}</div>
        <div style="font-size:0.78rem;color:var(--text-muted)">{category}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="cross">⚕️</div>
        <div class="brand">MedInsight</div>
        <div class="tagline">Health Data Platform</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color:var(--border);margin:0.5rem 0'>", unsafe_allow_html=True)

    page = st.radio("", [
        "🏛️  Tableau de bord",
        "➕  Nouveau patient",
        "📊  Analyse descriptive",
        "🔍  Profil patient",
        "📁  Base de données",
    ], label_visibility="collapsed")

    st.markdown("<hr style='border-color:var(--border);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="nav-stat">
        <strong>{db.count()}</strong> patient(s) enregistré(s)<br>
        <span style="color:var(--danger)">{db.high_risk_count()}</span> profil(s) à risque élevé
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <hr style='border-color:var(--border);'>
    <div style='font-size:0.68rem;color:var(--text-muted);text-align:center;line-height:1.7;'>
        INF 232 EC2 — TP №1<br>Université de Yaoundé I<br>
        <span style='color:var(--emerald)'>MedInsight v2.0</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — TABLEAU DE BORD
# ══════════════════════════════════════════════════════════════════════════════

if page == "🏛️  Tableau de bord":
    render_hero("Plateforme de surveillance clinique", "Med", "Insight",
                "Collecte intelligente et analyse descriptive des données de santé", "⚕ Système actif")

    df = load_cached()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_kpi("👤", str(len(df)), "Patients enregistrés")
    with col2: render_kpi("🎂", f"{df['age'].mean():.0f} ans" if len(df) > 0 and "age" in df else "—", "Âge moyen")
    with col3: render_kpi("⚖️",  f"{df['imc'].mean():.1f}"   if len(df) > 0 and "imc" in df else "—", "IMC moyen")
    with col4: render_kpi("⚡", str(db.high_risk_count()), "Profils à risque")

    if len(df) == 0:
        st.info("Aucune donnée. Commencez par **➕ Nouveau patient**.")
        st.stop()

    render_section_title("Panorama clinique")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if "sexe" in df.columns:
            fig = px.pie(df, names="sexe", hole=0.55,
                         color_discrete_sequence=["#00c896","#c8a84b","#a8d8ea"],
                         title="Répartition par sexe")
            fig.update_traces(textfont_color="white")
            fig.update_layout(**PLOTLY_LAYOUT, height=280, title_font_color="#e8edf2")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "niveau_risque" in df.columns:
            rc = df["niveau_risque"].value_counts().reindex(NIVEAUX_RISQUE_ORDRE).dropna()
            fig = px.bar(rc, orientation="h", color=rc.index,
                         color_discrete_map={"Faible":"#00c896","Modéré":"#f0a500","Élevé":"#ff7043","Très élevé":"#ff5a5a"},
                         title="Niveaux de risque CV")
            fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
                              title_font_color="#e8edf2", yaxis_title="", xaxis_title="Patients")
            st.plotly_chart(fig, use_container_width=True)

    with col_c:
        if "categorie_ta" in df.columns:
            ta_c = df["categorie_ta"].value_counts().reindex(CATEGORIES_TA_ORDRE).dropna()
            fig = px.bar(ta_c, color=ta_c.index,
                         color_discrete_sequence=EMERALD_SEQ, title="Profil tensionnel")
            fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False, title_font_color="#e8edf2")
            st.plotly_chart(fig, use_container_width=True)

    render_section_title("Distribution démographique")
    col_d, col_e = st.columns(2)

    with col_d:
        if "age" in df.columns:
            fig = px.histogram(df, x="age", nbins=12, color_discrete_sequence=["#00c896"],
                               title="Distribution des âges", marginal="rug")
            fig.update_layout(**PLOTLY_LAYOUT, height=300, title_font_color="#e8edf2",
                              xaxis_title="Âge (ans)", yaxis_title="Effectif")
            st.plotly_chart(fig, use_container_width=True)

    with col_e:
        if "region" in df.columns:
            r_c = df["region"].value_counts().head(8)
            fig = px.bar(r_c, color=r_c.index, color_discrete_sequence=GOLD_SEQ,
                         title="Patients par région")
            fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False,
                              title_font_color="#e8edf2", xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — NOUVEAU PATIENT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "➕  Nouveau patient":
    render_hero("Enregistrement clinique", "Nouveau", "Patient",
                "Saisie complète des paramètres cliniques et calcul automatique du score de risque cardiovasculaire")

    with st.form("form_nouveau_patient", clear_on_submit=True):

        st.markdown("#### 👤 Identité")
        c1, c2, c3, c4 = st.columns(4)
        with c1: nom     = st.text_input("Nom / ID patient *", placeholder="P-0042")
        with c2: age     = st.number_input("Âge (ans)", 0, 120, 35)
        with c3: sexe    = st.selectbox("Sexe", ["Masculin", "Féminin", "Autre"])
        with c4: region  = st.selectbox("Région", REGIONS)

        st.markdown("---")
        st.markdown("#### 📏 Anthropométrie")
        c1, c2, c3 = st.columns(3)
        with c1: 
            poids  = st.number_input("Poids (kg)", 10.0, 300.0, 70.0, 0.1)
        with c2: 
            taille = st.number_input("Taille (cm)", 50.0, 250.0, 170.0, 0.5)
        imc_preview = engine.compute_imc(poids, taille)
        with c3:
            st.markdown(f"<br><div class='alert-ok' style='margin-top:0.5rem'>IMC : <b>{imc_preview}</b> — {engine.imc_category(imc_preview)}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🩸 Paramètres vitaux")
        c1, c2, c3, c4, c5 = st.columns(5)
    with c1: 
        t_sys = st.number_input("Tension sys. (mmHg)", 50, 300, 120)
        with c2: 
            t_dia = st.number_input("Tension dia. (mmHg)", 30, 200, 80)
        with c3: 
            glyc  = st.number_input("Glycémie (mmol/L)", 1.0, 40.0, 5.0, 0.1)
        with c4: 
            temp  = st.number_input("Température (°C)", 33.0, 43.0, 37.0, 0.1)
        with c5: 
            spo2  = st.number_input("SpO₂ (%)", 50, 100, 98)
        fc = st.number_input("Fréquence cardiaque (bpm)", 20, 250, 72)

        st.markdown("---")
        st.markdown("#### 🚬 Mode de vie")
        c1, c2, c3 = st.columns(3)
        with c1: fumeur   = st.selectbox("Tabagisme",       ["Non-fumeur", "Ex-fumeur", "Fumeur actif"])
        with c2: alcool   = st.selectbox("Alcool",          ["Jamais", "Occasionnel", "Régulier", "Quotidien"])
        with c3: activite = st.selectbox("Activité physique",["Sédentaire", "Légère", "Modérée", "Intense"])

        st.markdown("---")
        st.markdown("#### 🏥 Clinique")
        c1, c2 = st.columns(2)
        with c1:
            antecedents = st.text_input("Antécédents médicaux", placeholder="Diabète, HTA, infarctus…")
            diagnostic  = st.text_input("Diagnostic principal", placeholder="HTA stade 2, Diabète type 2…")
        with c2:
            traitement = st.text_input("Traitement en cours", placeholder="Médicaments, posologie…")
            notes      = st.text_area("Notes cliniques", height=90, placeholder="Observations complémentaires…")

        submitted = st.form_submit_button("⚕️ Enregistrer & calculer le score de risque", use_container_width=True)

    if submitted: 
        if not nom.strip():
            st.error("Le champ **Nom / ID** est obligatoire.")
        else:
            # ── CORRECTION 1 : Validation clinique avant enregistrement ──
            errors = engine.validate(
                age=age, poids_kg=poids, taille_cm=taille,
                tension_sys=t_sys, tension_dia=t_dia,
                glycemie=glyc, temperature=temp,
                frequence_cardiaque=fc, spo2=spo2,
            )
            if errors:
                for e in errors:
                    st.error(f"⛔ {e}")
                st.stop()

            # ── Délègue la construction du record au backend ──
            record = engine.build_patient_record(
                nom=nom, age=age, sexe=sexe, region=region,
                poids=poids, taille=taille,
                t_sys=t_sys, t_dia=t_dia, glyc=glyc,
                temp=temp, spo2=spo2, fc=fc,
                fumeur=fumeur, alcool=alcool, activite=activite,
                antecedents=antecedents, diagnostic=diagnostic,
                traitement=traitement, notes=notes,
                existing_count=db.count(),
            )
            db.add_patient(record)
            invalidate_cache()  # CORRECTION 3 : vide le cache après écriture

            st.success(f"✅ Patient **{nom}** enregistré — ID : **{record['id']}**")
            render_section_title("Résumé clinique automatique")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_glass_card(f"<div style='font-size:0.72rem;color:var(--text-muted)'>IMC</div><div style='font-size:1.6rem;font-weight:700;color:var(--emerald)'>{record['imc']}</div><div style='font-size:0.8rem'>{record['categorie_imc']}</div>")
            with col2:
                render_glass_card(f"<div style='font-size:0.72rem;color:var(--text-muted)'>Tension</div><div style='font-size:1.6rem;font-weight:700;color:var(--emerald)'>{t_sys}/{t_dia}</div><div style='font-size:0.8rem'>{record['categorie_ta']}</div>")
            with col3:
                render_glass_card(f"<div style='font-size:0.72rem;color:var(--text-muted)'>Glycémie</div><div style='font-size:1.6rem;font-weight:700;color:var(--emerald)'>{glyc} mmol/L</div><div style='font-size:0.8rem'>{record['categorie_glycemie']}</div>")
            with col4:
                css = engine.risk_css_class(record['niveau_risque'])
                render_glass_card(f"<div style='font-size:0.72rem;color:var(--text-muted)'>Score risque CV</div><div style='font-size:1.6rem;font-weight:700;color:var(--gold)'>{record['score_risque']}/100</div><span class='risk-badge {css}'>{record['niveau_risque']}</span>")

            st.markdown("**Alertes cliniques :**")
            render_alerts(engine.clinical_alerts(record))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — ANALYSE DESCRIPTIVE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📊  Analyse descriptive":
    render_hero("Statistiques & Visualisations", "Analyse", "Descriptive",
                "Exploration statistique complète — distributions, corrélations, profils de risque")

    df = load_cached()
    if len(df) == 0:
        st.warning("Aucune donnée. Enregistrez des patients d'abord.")
        st.stop()

    avail     = db.get_numeric_columns(df)
    cat_avail = db.get_categorical_columns(df)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Statistiques", "📉 Distributions", "🔗 Corrélations", "🩸 Risque CV", "🗺️ Régions"
    ])

    with tab1:
        render_section_title("Statistiques résumées")
        st.dataframe(db.summary_stats(df), use_container_width=True)

        render_section_title("Comparaison par sexe")
        if "sexe" in df.columns:
            var_box = st.selectbox("Variable", avail, key="bx")
            fig = px.violin(df, x="sexe", y=var_box, color="sexe", box=True, points="all",
                            color_discrete_map={"Masculin":"#00c896","Féminin":"#c8a84b","Autre":"#a8d8ea"})
            fig.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        render_section_title("Distributions")
        var_d = st.selectbox("Variable", avail, key="dist")
        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.histogram(df, x=var_d, nbins=14, color_discrete_sequence=["#00c896"],
                               marginal="box", title=f"Distribution — {var_d.replace('_',' ').title()}")
            fig.update_layout(**PLOTLY_LAYOUT, height=340, title_font_color="#e8edf2")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig = px.ecdf(df, x=var_d, color_discrete_sequence=["#c8a84b"],
                          title="Fonction de répartition empirique (ECDF)")
            fig.update_layout(**PLOTLY_LAYOUT, height=340, title_font_color="#e8edf2")
            st.plotly_chart(fig, use_container_width=True)

        render_section_title("Variables catégorielles")
        tabs_cat = st.tabs([c.replace("_", " ").title() for c in cat_avail])
        for i, c in enumerate(cat_avail):
            with tabs_cat[i]:
                vc = df[c].value_counts().reset_index()
                vc.columns = [c, "count"]
                fig = px.bar(vc, x=c, y="count", color=c,
                             color_discrete_sequence=EMERALD_SEQ,
                             title=f"Répartition — {c.replace('_',' ').title()}")
                fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, title_font_color="#e8edf2")
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        render_section_title("Matrice de corrélation")
        corr = df[avail].corr().round(2)
        labels = [c.replace("_", " ").title() for c in avail]
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=labels, y=labels,
            colorscale=[[0,"#005ea8"],[0.5,"#0e1a24"],[1,"#00c896"]],
            zmin=-1, zmax=1, text=corr.values.round(2), texttemplate="%{text}",
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=480)
        st.plotly_chart(fig, use_container_width=True)

        render_section_title("Nuage de points")
        c1, c2 = st.columns(2)
        with c1: xv = st.selectbox("Axe X", avail, index=0, key="sx2")
        with c2: yv = st.selectbox("Axe Y", avail, index=min(3, len(avail)-1), key="sy2")
        color_v = "niveau_risque" if "niveau_risque" in df.columns else None
        fig = px.scatter(df, x=xv, y=yv, color=color_v,
                         size="score_risque" if "score_risque" in df.columns else None,
                         trendline="ols",
                         color_discrete_map={"Faible":"#00c896","Modéré":"#f0a500","Élevé":"#ff7043","Très élevé":"#ff5a5a"},
                         opacity=0.8,
                         hover_data=["nom_patient"] if "nom_patient" in df.columns else None,
                         title=f"{xv.replace('_',' ').title()} vs {yv.replace('_',' ').title()}")
        fig.update_layout(**PLOTLY_LAYOUT, height=400, title_font_color="#e8edf2")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        render_section_title("Profil de risque cardiovasculaire")
        if "score_risque" in df.columns:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.histogram(df, x="score_risque", nbins=12,
                                   color_discrete_sequence=["#c8a84b"],
                                   title="Distribution des scores", marginal="rug")
                fig.update_layout(**PLOTLY_LAYOUT, height=320, title_font_color="#e8edf2",
                                  xaxis_title="Score (0–100)", yaxis_title="Patients")
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                rc = df["niveau_risque"].value_counts().reindex(NIVEAUX_RISQUE_ORDRE).dropna()
                fig = px.pie(rc, names=rc.index, values=rc.values, hole=0.5, color=rc.index,
                             color_discrete_map={"Faible":"#00c896","Modéré":"#f0a500","Élevé":"#ff7043","Très élevé":"#ff5a5a"},
                             title="Répartition niveaux de risque")
                fig.update_traces(textfont_color="white")
                fig.update_layout(**PLOTLY_LAYOUT, height=320, title_font_color="#e8edf2")
                st.plotly_chart(fig, use_container_width=True)

            risk_means = db.risk_means_by_level(df)
            if not risk_means.empty:
                st.dataframe(risk_means, use_container_width=True)

    with tab5:
        render_section_title("Analyse par région")
        region_stats = db.region_stats(df)
        if not region_stats.empty:
            st.dataframe(region_stats, use_container_width=True)
            fig = px.bar(region_stats.reset_index(), x="region", y="Score_risque",
                         color="Score_risque",
                         color_continuous_scale=["#00c896","#f0a500","#ff5a5a"],
                         title="Score de risque moyen par région")
            fig.update_layout(**PLOTLY_LAYOUT, height=360, title_font_color="#e8edf2", xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.download_button("⬇️ Exporter toutes les données (CSV)",
                       data=db.export_csv(df),
                       file_name=f"medinsight_{datetime.now().strftime('%Y%m%d')}.csv",
                       mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PROFIL PATIENT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🔍  Profil patient":
    render_hero("Fiche individuelle", "Profil", "Patient",
                "Vue détaillée des paramètres cliniques et score de risque individuel")

    df = load_cached()
    if len(df) == 0:
        st.warning("Aucun patient enregistré.")
        st.stop()

    patient_id = st.selectbox(
        "Sélectionner un patient",
        df["id"].tolist() if "id" in df.columns else [],
        format_func=lambda x: f"{x} — {df[df['id']==x]['nom_patient'].values[0]}"
        if len(df[df["id"] == x]) > 0 else x,
    )

    # ── Récupère le patient depuis le backend ──
    row = db.get_patient(patient_id)
    score  = float(row.get("score_risque", 0))
    niveau = row.get("niveau_risque", "—")
    css    = engine.risk_css_class(niveau)

    # Header
    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
        <div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:700">{row.get('nom_patient','—')}</div>
            <div style="color:var(--text-muted);font-size:0.85rem">{row.get('id','—')} &nbsp;·&nbsp; {row.get('age','—')} ans &nbsp;·&nbsp; {row.get('sexe','—')} &nbsp;·&nbsp; {row.get('region','—')}</div>
            <div style="margin-top:0.4rem;font-size:0.82rem;color:var(--text-muted)">Enregistré le {row.get('date_collecte','—')}</div>
        </div>
        <div style="text-align:right">
            <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:0.2rem">Score de risque CV</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:3rem;font-weight:700;color:var(--gold);line-height:1">{score:.0f}<span style="font-size:1rem">/100</span></div>
            <span class="risk-badge {css}">{niveau}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        domain={"x":[0,1],"y":[0,1]},
        title={"text":"Score de Risque Cardiovasculaire","font":{"size":14,"color":"#a8c0d0"}},
        gauge={
            "axis":{"range":[0,100],"tickcolor":"#a8c0d0"},
            "bar":{"color":"#c8a84b"}, "bgcolor":"#0e1a24",
            "bordercolor":"rgba(0,200,150,0.2)",
            "steps":[
                {"range":[0,25],   "color":"rgba(0,200,150,0.15)"},
                {"range":[25,50],  "color":"rgba(240,165,0,0.15)"},
                {"range":[50,70],  "color":"rgba(255,112,67,0.15)"},
                {"range":[70,100], "color":"rgba(255,90,90,0.2)"},
            ],
            "threshold":{"line":{"color":"#ff5a5a","width":3},"value":70},
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#a8c0d0",
                      height=280, margin=dict(t=40,b=10,l=30,r=30))
    st.plotly_chart(fig, use_container_width=True)

    # Paramètres vitaux
    render_section_title("Paramètres vitaux")
    vitals = [
        ("⚖️", "IMC",       f"{row.get('imc','—')}",                              row.get("categorie_imc","—")),
        ("🩸", "Tension",   f"{row.get('tension_sys','—')}/{row.get('tension_dia','—')} mmHg", row.get("categorie_ta","—")),
        ("🔬", "Glycémie",  f"{row.get('glycemie','—')} mmol/L",                  row.get("categorie_glycemie","—")),
        ("🌡️","Temp.",      f"{row.get('temperature','—')}°C",                    "Normal" if 36.5<=float(row.get('temperature',37))<=37.5 else "Anormal"),
        ("💓", "FC",        f"{row.get('frequence_cardiaque','—')} bpm",           "Normal" if 60<=float(row.get('frequence_cardiaque',72))<=100 else "Anormal"),
        ("💨", "SpO₂",      f"{row.get('spo2','—')}%",                            "Normal" if float(row.get('spo2',98))>=95 else "Bas"),
    ]
    cols = st.columns(3)
    for i, (icon, label, val, cat) in enumerate(vitals):
        with cols[i % 3]:
            render_vital_card(icon, label, val, cat)

    render_section_title("Alertes cliniques")
    render_alerts(engine.clinical_alerts(row))

    render_section_title("Anamnèse")
    c1, c2 = st.columns(2)
    with c1:
        render_glass_card(f"""
        <div style='font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;margin-bottom:0.8rem;letter-spacing:1px'>Mode de vie</div>
        <div style='margin-bottom:0.5rem'>🚬 Tabac : <b>{row.get('fumeur','—')}</b></div>
        <div style='margin-bottom:0.5rem'>🍺 Alcool : <b>{row.get('alcool','—')}</b></div>
        <div>🏃 Activité : <b>{row.get('activite','—')}</b></div>
        """)
    with c2:
        render_glass_card(f"""
        <div style='font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;margin-bottom:0.8rem;letter-spacing:1px'>Clinique</div>
        <div style='margin-bottom:0.5rem'>📋 Antécédents : <b>{row.get('antecedents','—') or '—'}</b></div>
        <div style='margin-bottom:0.5rem'>🏥 Diagnostic : <b>{row.get('diagnostic','—') or '—'}</b></div>
        <div>💊 Traitement : <b>{row.get('traitement','—') or '—'}</b></div>
        """)

    if row.get("notes"):
        render_glass_card(f"<span style='font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px'>Notes</span><br>{row['notes']}", "margin-top:0.8rem")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁  Base de données":
    render_hero("Gestion des données", "Base de", "Données",
                "Consultation, filtrage et export des enregistrements patients")

    df = load_cached()
    if len(df) == 0:
        st.info("Aucune donnée disponible.")
        st.stop()

    render_section_title("Filtres")
    c1, c2, c3 = st.columns(3)
    with c1:
        sexe_f = st.multiselect("Sexe", df["sexe"].dropna().unique().tolist() if "sexe" in df else [],
                                default=df["sexe"].dropna().unique().tolist() if "sexe" in df else [])
    with c2:
        risk_f = []
        if "niveau_risque" in df.columns:
            risk_f = st.multiselect("Niveau de risque", df["niveau_risque"].dropna().unique().tolist(),
                                    default=df["niveau_risque"].dropna().unique().tolist())
    with c3:
        age_r = (int(df["age"].min()), int(df["age"].max())) if "age" in df.columns and df["age"].notna().sum() > 0 else (0, 100)
        if "age" in df.columns and df["age"].notna().sum() > 0:
            age_r = st.slider("Âge", int(df["age"].min()), int(df["age"].max()), age_r)

    # ── Délègue le filtrage au backend ──
    df_filtered = db.filter(df, sexe_list=sexe_f, risk_list=risk_f, age_range=age_r)
    st.markdown(f"**{len(df_filtered)}** patient(s) affiché(s) sur {len(df)}")
    st.dataframe(df_filtered, use_container_width=True, height=420)

    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        st.download_button("⬇️ Exporter la sélection (CSV)",
                           data=db.export_csv(df_filtered),
                           file_name=f"medinsight_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           mime="text/csv")
    with col_b:
        st.download_button("⬇️ Exporter (JSON)",
                           data=db.export_json(df_filtered),
                           file_name=f"medinsight_export_{datetime.now().strftime('%Y%m%d')}.json",
                           mime="application/json")
    with col_c:
        if st.button("🗑️ Vider la base", type="secondary"):
            db.clear()
            invalidate_cache()  # CORRECTION 3
            st.warning("Base vidée.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="footer">
    <span>MedInsight</span> Health Data Platform &nbsp;·&nbsp;
    INF 232 EC2 — TP №1 &nbsp;·&nbsp;
    Université de Yaoundé I &nbsp;·&nbsp; 2026
</div>
""", unsafe_allow_html=True)