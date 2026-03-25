import os
import time
import json
import base64
import streamlit as st
from file_attente import ajouter_requete, lire_requete_par_id
from theme import page_banner, section_header, divider

FICHE_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<style>
/* ── Carte principale ── */
.result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 28px 34px;
    box-shadow: 0 4px 20px rgba(99,102,241,0.07);
    position: relative;
    overflow: hidden;
    margin-bottom: 20px;
}
.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 16px 16px 0 0;
}
.accent-indigo::before { background: linear-gradient(90deg,#6366f1,#a855f7,#06b6d4); }
.accent-cyan::before   { background: linear-gradient(90deg,#06b6d4,#6366f1,#a855f7); }

.fiche-header {
    display: flex; align-items: center; gap: 16px;
    padding-bottom: 14px; border-bottom: 1px solid #f1f5f9; margin-bottom: 4px;
}
.fiche-avatar {
    width: 52px; height: 52px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; color: #ffffff; flex-shrink: 0;
}
.avatar-indigo { background: linear-gradient(135deg,#6366f1,#a855f7); }
.avatar-cyan   { background: linear-gradient(135deg,#06b6d4,#6366f1); }

.fiche-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem; font-weight: 700; color: #1e293b; margin-bottom: 2px;
}
.fiche-sub { font-size: 0.78rem; color: #94a3b8; }

/* ── Titres de section ── */
.section-title-fa {
    display: flex; align-items: center; gap: 10px;
    font-size: 1rem; font-weight: 700; color: #1e293b;
    margin: 20px 0 10px;
}
.section-title-fa i {
    color: #6366f1; font-size: 1.05rem;
    width: 22px; text-align: center;
}

/* ── Statuts ── */
.status-card {
    border-radius: 14px; padding: 28px 32px;
    margin: 16px 0; border: 1.5px dashed; text-align: center;
}
.status-waiting    { background:linear-gradient(135deg,#f0f9ff,#e0f2fe); border-color:#7dd3fc; }
.status-processing { background:linear-gradient(135deg,#fffbeb,#fef3c7); border-color:#fcd34d; }

.status-icon-wrap {
    width: 56px; height: 56px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 14px; font-size: 1.4rem;
}
.si-waiting    { background:#e0f2fe; color:#0369a1; }
.si-processing { background:#fef3c7; color:#d97706; }
.si-processing i { animation: fa-spin 1.4s linear infinite; }

.status-title-s {
    font-family:'Playfair Display',serif;
    font-size:1.2rem; font-weight:700; color:#1e293b; margin-bottom:6px;
}
.status-desc { font-size:0.85rem; color:#64748b; line-height:1.5; }

/* ── Barres de progression ── */
.progress-bar { height:4px; background:#e2e8f0; border-radius:2px; margin:16px 0 0; overflow:hidden; }
.pb-indigo, .pb-amber, .pb-cyan { height:100%; border-radius:2px; animation:pb-anim 1.6s ease-in-out infinite; }
.pb-indigo { background:linear-gradient(90deg,#6366f1,#a855f7); }
.pb-amber  { background:linear-gradient(90deg,#f59e0b,#f97316); }
.pb-cyan   { background:linear-gradient(90deg,#06b6d4,#6366f1); }

@keyframes pb-anim {
    0%  { width:10%; margin-left:0; }
    50% { width:40%; margin-left:30%; }
    100%{ width:10%; margin-left:90%; }
}

/* ── Boutons d'action ── */
.action-btn-reac .stButton > button {
    background:linear-gradient(135deg,#f59e0b,#d97706) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    font-weight:700 !important; height:46px !important; font-size:0.82rem !important;
}
.action-btn-code .stButton > button {
    background:linear-gradient(135deg,#6366f1,#4f46e5) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    font-weight:700 !important; height:46px !important; font-size:0.82rem !important;
}
.action-btn-suivi .stButton > button {
    background:linear-gradient(135deg,#10b981,#059669) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    font-weight:700 !important; height:46px !important; font-size:0.82rem !important;
}
.action-btn-home .stButton > button {
    background:#f8fafc !important; color:#475569 !important;
    border:1.5px solid #e2e8f0 !important; border-radius:10px !important;
    font-weight:600 !important; height:46px !important;
}

.action-confirm {
    background:linear-gradient(135deg,#ecfdf5,#d1fae5);
    border:1px solid #6ee7b7; border-radius:10px;
    padding:10px 16px; font-size:0.82rem; color:#065f46;
    font-weight:600; margin:8px 0; text-align:center;
    display:flex; align-items:center; justify-content:center; gap:8px;
}

/* ── Screenshot ── */
.screenshot-wrapper {
    background:#f8fafc; border:1px solid #e2e8f0;
    border-radius:12px; padding:16px; margin:16px 0;
}
.screenshot-label {
    font-size:0.72rem; font-weight:700; color:#64748b;
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:10px;
    display:flex; align-items:center; gap:7px;
}

/* ── Erreur ── */
.error-card {
    background:linear-gradient(135deg,#fff1f2,#ffe4e6);
    border:1.5px solid #fda4af; border-radius:12px;
    padding:20px 24px; margin:16px 0;
    display:flex; align-items:flex-start; gap:14px;
}
.error-card .ec-icon { font-size:1.4rem; color:#e11d48; }
.error-card .ec-title { font-weight:700; color:#9f1239; margin-bottom:4px; }
.error-card .ec-msg   { font-size:0.82rem; color:#e11d48; }

/* ── Empty & No Screenshot ── */
.empty-state, .no-screenshot {
    text-align:center; padding:48px 32px;
    background:#f8fafc; border:1px dashed #e2e8f0; border-radius:14px; margin:24px 0;
}
.es-icon-wrap {
    width:64px; height:64px; border-radius:50%; background:#eef2ff;
    display:flex; align-items:center; justify-content:center; margin:0 auto 14px;
    font-size:1.6rem; color:#6366f1;
}
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Helpers internes
# ═══════════════════════════════════════════════════════════════
def _section_fa(icon_class: str, label: str):
    st.markdown(f'<div class="section-title-fa"><i class="{icon_class}"></i>{label}</div>', unsafe_allow_html=True)

def _confirm(icon_class: str, msg: str):
    st.markdown(f'<div class="action-confirm"><i class="{icon_class}"></i>{msg}</div>', unsafe_allow_html=True)

def _to_dict(val):
    if isinstance(val, dict): return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
        except: return {}
    return {}

# ═══════════════════════════════════════════════════════════════
# Fonction principale
# ═══════════════════════════════════════════════════════════════
def render_fiche(
    banner_title, banner_subtitle, banner_watermark,
    label_numero, avatar_fa, accent_class, avatar_class,
    progress_class, empty_fa
):
    st.markdown(FICHE_CSS, unsafe_allow_html=True)

    req_id      = st.session_state.get("req_id")
    utilisateur = st.session_state.get("utilisateur_connecte", "inconnu")

    page_banner(title=banner_title, subtitle=banner_subtitle, watermark=banner_watermark)

    if not req_id:
        st.markdown(f"""<div class="empty-state"><div class="es-icon-wrap"><i class="{empty_fa}"></i></div>
        <div class="es-title">Aucune recherche active</div></div>""", unsafe_allow_html=True)
        _btn_accueil()
        return

    requete = lire_requete_par_id(req_id)
    if not requete:
        st.error("Requête introuvable.")
        _btn_accueil()
        return

    statut     = requete.get("statut")
    valeur_req = requete.get("valeur", "—")
    color_statut = {"terminee":"#059669","en_attente":"#d97706","en_cours":"#d97706","echouee":"#e11d48"}.get(statut, "#64748b")

    st.markdown(f"""
    <div class="result-card {accent_class}">
        <div class="fiche-header">
            <div class="fiche-avatar {avatar_class}"><i class="{avatar_fa}"></i></div>
            <div>
                <div class="fiche-title">{label_numero} : {valeur_req}</div>
                <div class="fiche-sub">Requête #{req_id} &nbsp;·&nbsp; Statut : 
                <strong style="color:{color_statut}">{statut.replace('_',' ').capitalize()}</strong></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if statut == "en_attente":
        st.markdown(f"""<div class="status-card status-waiting"><div class="status-icon-wrap si-waiting"><i class="fa-solid fa-clock"></i></div>
        <div class="status-title-s">En file d'attente</div><div class="progress-bar"><div class="{progress_class}"></div></div></div>""", unsafe_allow_html=True)
        time.sleep(3); st.rerun()

    elif statut == "en_cours":
        worker_id = requete.get("worker_id", "—")
        st.markdown(f"""<div class="status-card status-processing"><div class="status-icon-wrap si-processing"><i class="fa-solid fa-gears"></i></div>
        <div class="status-title-s">Extraction en cours...</div><div class="status-desc">Worker {worker_id} actif.</div>
        <div class="progress-bar"><div class="pb-amber"></div></div></div>""", unsafe_allow_html=True)
        time.sleep(3); st.rerun()

    elif statut == "terminee":
        res = _to_dict(requete.get("resultat"))
        
        # --- Gestion Screenshot (Base64) ---
        img_b64 = res.get("screenshot_base64")
        img_bytes = base64.b64decode(img_b64) if img_b64 else None

        _section_fa("fa-solid fa-bolt", "Actions rapides")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="action-btn-reac">', unsafe_allow_html=True)
            if st.button("Réactivation", use_container_width=True):
                ajouter_requete(utilisateur, "réactivation", valeur_req)
                _confirm("fa-solid fa-check", "Demandée !")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="action-btn-code">', unsafe_allow_html=True)
            if st.button("Code Parental", use_container_width=True):
                ajouter_requete(utilisateur, "réinitialisation", valeur_req)
                _confirm("fa-solid fa-check", "Demandée !")
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="action-btn-suivi">', unsafe_allow_html=True)
            if st.button("Suivi abonné", use_container_width=True):
                ajouter_requete(utilisateur, "suivi_abonne", valeur_req)
                _confirm("fa-solid fa-check", "Enregistré !")
            st.markdown('</div>', unsafe_allow_html=True)

        divider()
        _section_fa("fa-solid fa-camera", "Capture CGAWEB")

        if img_bytes:
            st.markdown('<div class="screenshot-wrapper">', unsafe_allow_html=True)
            st.image(img_bytes, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("Télécharger la capture", data=img_bytes, file_name=f"{valeur_req}.png", mime="image/png", use_container_width=True)
        else:
            st.markdown('<div class="no-screenshot"><i class="fa-solid fa-image-slash"></i><br>Aucune capture.</div>', unsafe_allow_html=True)

    elif statut == "echouee":
        res = _to_dict(requete.get("resultat"))
        msg = res.get("erreur", "Erreur inconnue")
        st.markdown(f"""<div class="error-card"><div class="ec-icon"><i class="fa-solid fa-circle-xmark"></i></div>
        <div><div class="ec-title">Échec</div><div class="ec-msg">{msg}</div></div></div>""", unsafe_allow_html=True)

    divider(); _btn_accueil()

def _btn_accueil():
    st.markdown('<div class="action-btn-home">', unsafe_allow_html=True)
    if st.button("Retour à l'accueil", use_container_width=True):
        st.session_state.page_active = "Accueil"
        st.session_state.requete_en_cours = False
        st.session_state.req_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)