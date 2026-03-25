"""
theme.py — Thème global VISUV CGAWEB
Importez apply_theme() au début de chaque page ou appelez-le une fois dans main.py
"""
import streamlit as st

# ═══════════════════════════════════════════════════════════════
# CSS GLOBAL — Light Professional Theme
# ═══════════════════════════════════════════════════════════════
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #f9f9f9 !important;
    color: #1e293b !important;
}
.stApp { background-color: #f9f9f9 !important; }

/* ── Titres ── */
h1, h2, h3, h4 {
    font-family: 'Playfair Display', serif !important;
    color: #1e293b !important;
}
h1 { font-size: 1.9rem !important; font-weight: 700 !important; }
h2 { font-size: 1.3rem !important; color: #475569 !important;
     text-transform: uppercase; letter-spacing: 0.1em; }
h3 { font-size: 1.1rem !important; color: #334155 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.3rem !important;
    color: #6366f1 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #f8fafc !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    text-align: left !important;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #eef2ff !important;
    color: #4f46e5 !important;
    border-color: #c7d2fe !important;
}

/* ── Boutons principaux ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.83rem !important;
    padding: 8px 18px !important;
    transition: opacity 0.15s ease;
}
.stButton > button:hover { opacity: 0.88; }

/* ── Bouton download ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
}

/* ── Inputs & Selects ── */
input, textarea, [data-baseweb="input"] input {
    background-color: #ffffff !important;
    border-color: #cbd5e1 !important;
    color: #1e293b !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: #cbd5e1 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
}
label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── Tableaux ── */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    overflow: hidden !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #334155 !important;
    font-size: 0.85rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: #64748b !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #4f46e5 !important;
    border-bottom-color: #4f46e5 !important;
}

/* ── Alertes & Messages ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Metrics Streamlit natifs ── */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.8rem !important;
    color: #1e293b !important;
}

/* ════════════════════════════════
   COMPOSANTS RÉUTILISABLES
════════════════════════════════ */

/* ── Cartes colorées ── */
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px 26px;
    margin: 8px 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    border-radius: 14px 0 0 14px;
}
.card-indigo  { background:linear-gradient(135deg,#eef2ff,#e0e7ff); border:1px solid #c7d2fe; }
.card-indigo::before  { background:linear-gradient(180deg,#6366f1,#4f46e5); }
.card-violet  { background:linear-gradient(135deg,#faf5ff,#f3e8ff); border:1px solid #d8b4fe; }
.card-violet::before  { background:linear-gradient(180deg,#a855f7,#9333ea); }
.card-emerald { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border:1px solid #6ee7b7; }
.card-emerald::before { background:linear-gradient(180deg,#10b981,#059669); }
.card-rose    { background:linear-gradient(135deg,#fff1f2,#ffe4e6); border:1px solid #fecdd3; }
.card-rose::before    { background:linear-gradient(180deg,#f43f5e,#e11d48); }
.card-amber   { background:linear-gradient(135deg,#fffbeb,#fef3c7); border:1px solid #fde68a; }
.card-amber::before   { background:linear-gradient(180deg,#f59e0b,#d97706); }
.card-cyan    { background:linear-gradient(135deg,#ecfeff,#cffafe); border:1px solid #a5f3fc; }
.card-cyan::before    { background:linear-gradient(180deg,#06b6d4,#0891b2); }
.card-sky     { background:linear-gradient(135deg,#f0f9ff,#e0f2fe); border:1px solid #bae6fd; }
.card-sky::before     { background:linear-gradient(180deg,#38bdf8,#0284c7); }
.card-white   { background:#ffffff; border:1px solid #e2e8f0; }
.card-white::before   { background:linear-gradient(180deg,#6366f1,#4f46e5); }

/* ── Textes dans les cartes ── */
.card-label {
    font-size: 0.7rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 6px;
}
.card-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem; font-weight: 700; color: #1e293b;
    line-height: 1.1; margin-bottom: 4px;
}
.val-indigo  { color: #4f46e5 !important; }
.val-violet  { color: #9333ea !important; }
.val-emerald { color: #059669 !important; }
.val-rose    { color: #e11d48 !important; }
.val-amber   { color: #d97706 !important; }
.val-cyan    { color: #0891b2 !important; }
.val-sky     { color: #0284c7 !important; }

/* ── Badges ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
}
.badge-green  { background:#d1fae5; color:#065f46; }
.badge-red    { background:#ffe4e6; color:#9f1239; }
.badge-amber  { background:#fef3c7; color:#92400e; }
.badge-purple { background:#f3e8ff; color:#6b21a8; }
.badge-blue   { background:#dbeafe; color:#1e40af; }
.badge-cyan   { background:#cffafe; color:#164e63; }
.badge-gray   { background:#f1f5f9; color:#475569; }

/* ── Chips métriques ── */
.metric-row { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0; }
.chip {
    border-radius: 12px; padding: 16px 18px;
    flex: 1; min-width: 110px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.chip-indigo  { background:linear-gradient(135deg,#eef2ff,#e0e7ff); border:1px solid #c7d2fe; }
.chip-violet  { background:linear-gradient(135deg,#faf5ff,#f3e8ff); border:1px solid #d8b4fe; }
.chip-emerald { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border:1px solid #6ee7b7; }
.chip-rose    { background:linear-gradient(135deg,#fff1f2,#ffe4e6); border:1px solid #fecdd3; }
.chip-amber   { background:linear-gradient(135deg,#fffbeb,#fef3c7); border:1px solid #fde68a; }
.chip-cyan    { background:linear-gradient(135deg,#ecfeff,#cffafe); border:1px solid #a5f3fc; }
.chip-sky     { background:linear-gradient(135deg,#f0f9ff,#e0f2fe); border:1px solid #bae6fd; }
.chip-white   { background:#ffffff; border:1px solid #e2e8f0; }

.chip .chip-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem; font-weight: 700; color: #1e293b; display: block; line-height: 1.2;
}
.chip .chip-lbl {
    font-size: 0.65rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.1em;
}

/* ── Worker dot ── */
.dot-on  { width:8px; height:8px; border-radius:50%; background:#10b981;
           box-shadow:0 0 5px #10b98188; display:inline-block; margin-right:7px; }
.dot-off { width:8px; height:8px; border-radius:50%; background:#cbd5e1;
           display:inline-block; margin-right:7px; }

/* ── Row utilitaire ── */
.row-between {
    display:flex; align-items:center; justify-content:space-between;
    padding:9px 0; border-bottom:1px solid #f1f5f9;
}
.row-between:last-child { border-bottom:none; }
.row-label { font-size:0.85rem; color:#475569; font-weight:500; }

/* ── Section header ── */
.section-header {
    display:flex; align-items:center; gap:12px; margin:28px 0 18px;
}
.section-header .sh-line {
    flex:1; height:1px; background:linear-gradient(90deg,#94a3b8,transparent);
}
.section-header .sh-title {
    font-size:0.7rem; font-weight:700; color:#475569;
    text-transform:uppercase; letter-spacing:0.2em; white-space:nowrap;
}

/* ── Séparateur ── */
.divider {
    height:1px; background:linear-gradient(90deg,transparent,#cbd5e1,transparent);
    margin:28px 0; border:none;
}

/* ── Page header (bannière) ── */
.page-banner {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 28px;
    position: relative; overflow: hidden;
    box-shadow: 0 8px 24px rgba(99,102,241,0.22);
}
.page-banner::after {
    content: attr(data-watermark);
    position:absolute; right:32px; top:50%; transform:translateY(-50%);
    font-family:'Playfair Display',serif; font-size:4.5rem; font-weight:700;
    color:rgba(255,255,255,0.07); letter-spacing:0.15em; user-select:none;
    pointer-events:none;
}
.page-banner h1 {
    margin:0 0 4px !important; border:none !important; padding:0 !important;
    color:#ffffff !important; font-size:1.8rem !important;
}
.page-banner .banner-sub { color:rgba(255,255,255,0.72); font-size:0.88rem; margin:0; }

/* ── Form card (pour les formulaires) ── */
.form-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 28px 32px; margin: 12px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.form-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; font-weight: 600; color: #1e293b;
    margin-bottom: 18px; padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}

/* ── Table striped override ── */
.stDataFrame tbody tr:nth-child(even) { background-color: #f8fafc !important; }
.stDataFrame th { background-color: #f1f5f9 !important; color:#475569 !important;
                  font-size:0.72rem !important; text-transform:uppercase; letter-spacing:0.08em; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#f1f5f9; }
::-webkit-scrollbar-thumb { background:#c7d2fe; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#818cf8; }
</style>
"""


def apply_theme():
    """Injecte le CSS global. À appeler en haut de chaque page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_banner(title: str, subtitle: str = "", watermark: str = ""):
    """
    Affiche la bannière violette en haut de page.
    Usage :
        from theme import page_banner
        page_banner("Gestion Utilisateurs", "Ajoutez et gérez les comptes", "USR")
    """
    wm = watermark or title[:3].upper()
    st.markdown(f"""
    <div class="page-banner" data-watermark="{wm}">
        <h1>{title}</h1>
        <p class="banner-sub">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    """
    Affiche un séparateur de section élégant.
    Usage :
        from theme import section_header
        section_header("📋 Liste des utilisateurs")
    """
    st.markdown(f"""
    <div class="section-header">
        <span class="sh-title">{title}</span>
        <div class="sh-line"></div>
    </div>
    """, unsafe_allow_html=True)


def divider():
    """Ligne séparatrice subtile."""
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


def metric_chips(chips: list):
    """
    Affiche une rangée de chips métriques colorés.

    chips = liste de dicts :
      { "label": "Total", "value": 42, "color": "indigo", "prefix": "", "suffix": "" }

    Couleurs disponibles : indigo, violet, emerald, rose, amber, cyan, sky, white
    Couleurs des valeurs  : val-indigo, val-violet, val-emerald, val-rose, val-amber, val-cyan, val-sky
    """
    color_map = {
        "indigo":  "val-indigo",
        "violet":  "val-violet",
        "emerald": "val-emerald",
        "rose":    "val-rose",
        "amber":   "val-amber",
        "cyan":    "val-cyan",
        "sky":     "val-sky",
        "white":   "",
    }
    html = '<div class="metric-row">'
    for c in chips:
        col   = c.get("color", "white")
        vcol  = color_map.get(col, "")
        val   = f"{c.get('prefix','')}{c['value']}{c.get('suffix','')}"
        html += f"""
        <div class="chip chip-{col}">
            <span class="chip-val {vcol}">{val}</span>
            <span class="chip-lbl">{c['label']}</span>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def card(content_html: str, color: str = "white"):
    """
    Affiche une carte colorée avec du HTML personnalisé à l'intérieur.
    color : indigo | violet | emerald | rose | amber | cyan | sky | white
    """
    st.markdown(f'<div class="card card-{color}">{content_html}</div>',
                unsafe_allow_html=True)