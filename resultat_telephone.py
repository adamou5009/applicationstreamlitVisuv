"""
resultat_telephone.py
─────────────────────
Page de résultat pour une recherche par numéro de téléphone.
Affiche une liste d'abonnés trouvés ; chaque ligne est cliquable
et redirige vers la fiche détaillée (resultat_abonne).
"""

import streamlit as st
import time
import pandas as pd
from file_attente import lire_requete_par_id
from theme import apply_theme, page_banner, section_header, divider

TEL_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<style>
/* ── Carte entête ── */
.tel-result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 28px 34px;
    box-shadow: 0 4px 20px rgba(99,102,241,0.07);
    position: relative;
    overflow: hidden;
    margin-bottom: 20px;
}
.tel-result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #06b6d4, #6366f1, #a855f7);
    border-radius: 16px 16px 0 0;
}
.tel-header {
    display: flex; align-items: center; gap: 16px;
    padding-bottom: 14px; border-bottom: 1px solid #f1f5f9;
}
.tel-avatar {
    width: 52px; height: 52px; border-radius: 14px;
    background: linear-gradient(135deg, #06b6d4, #6366f1);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; color: #ffffff; flex-shrink: 0;
}
.tel-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem; font-weight: 700; color: #1e293b; margin-bottom: 2px;
}
.tel-sub { font-size: 0.78rem; color: #94a3b8; }

/* ── Titres de section FA ── */
.section-title-fa {
    display: flex; align-items: center; gap: 10px;
    font-size: 1rem; font-weight: 700; color: #1e293b;
    margin: 20px 0 10px;
}
.section-title-fa i {
    color: #6366f1; font-size: 1.05rem;
    width: 22px; text-align: center;
}

/* ── Blocs statut ── */
.status-block {
    border-radius: 14px; padding: 28px 32px;
    margin: 16px 0; text-align: center; border: 1.5px dashed;
}
.status-waiting    { background:linear-gradient(135deg,#ecfeff,#cffafe); border-color:#67e8f9; }
.status-processing { background:linear-gradient(135deg,#fffbeb,#fef3c7); border-color:#fcd34d; }

.status-icon-wrap {
    width: 56px; height: 56px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 14px; font-size: 1.4rem;
}
.si-waiting    { background:#cffafe; color:#0e7490; }
.si-processing { background:#fef3c7; color:#d97706; }
.si-processing i { animation: fa-spin 1.4s linear infinite; }

.status-title-s {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 6px;
}
.status-desc-s { font-size: 0.85rem; color: #64748b; line-height: 1.5; }

/* ── Barres de progression ── */
.progress-bar { height:4px; background:#e2e8f0; border-radius:2px; margin:16px 0 0; overflow:hidden; }
.pb-cyan {
    height:100%; border-radius:2px;
    background:linear-gradient(90deg,#06b6d4,#6366f1);
    animation:pba 1.6s ease-in-out infinite;
}
.pb-amber {
    height:100%; border-radius:2px;
    background:linear-gradient(90deg,#f59e0b,#f97316);
    animation:pba 1.6s ease-in-out infinite;
}
@keyframes pba {
    0%  { width:10%; margin-left:0; }
    50% { width:40%; margin-left:30%; }
    100%{ width:10%; margin-left:90%; }
}

/* ── Tableau ── */
.col-header {
    font-size: 0.7rem; font-weight: 700;
    color: #64748b; text-transform: uppercase; letter-spacing: 0.08em;
}
.row-sep { border:none; border-top:1px solid #f1f5f9; margin:3px 0; }

/* ── Bouton abonné ── */
.btn-abo .stButton > button {
    background: transparent !important;
    color: #4f46e5 !important;
    border: none !important;
    padding: 2px 4px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    text-decoration: underline !important;
    height: auto !important;
    box-shadow: none !important;
    min-height: unset !important;
}
.btn-abo .stButton > button:hover {
    color: #4338ca !important;
    background: #eef2ff !important;
    border-radius: 6px !important;
    text-decoration: none !important;
}

/* ── Carte erreur ── */
.error-card {
    background: linear-gradient(135deg,#fff1f2,#ffe4e6);
    border: 1.5px solid #fda4af; border-radius: 12px;
    padding: 20px 24px; margin: 16px 0;
    display: flex; align-items: flex-start; gap: 14px;
}
.ec-icon  { font-size: 1.4rem; color: #e11d48; flex-shrink: 0; margin-top: 2px; }
.ec-title { font-weight: 700; color: #9f1239; margin-bottom: 4px; }
.ec-msg   { font-size: 0.82rem; color: #e11d48; }

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 48px 32px;
    background: #f8fafc; border: 1px dashed #e2e8f0;
    border-radius: 14px; margin: 24px 0;
}
.empty-state .es-icon-wrap {
    width: 64px; height: 64px; border-radius: 50%;
    background: #ecfeff; display: flex; align-items: center;
    justify-content: center; margin: 0 auto 14px;
    font-size: 1.6rem; color: #0e7490;
}
.es-title { font-weight: 700; color: #64748b; font-size: 0.95rem; }
.es-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; }

/* ── Bouton retour accueil ── */
.btn-home .stButton > button {
    background: #f8fafc !important; color: #475569 !important;
    border: 1.5px solid #e2e8f0 !important; border-radius: 10px !important;
    font-weight: 600 !important; height: 46px !important;
    font-size: 0.82rem !important; box-shadow: none !important;
}
.btn-home .stButton > button:hover {
    background: #eef2ff !important; color: #4f46e5 !important;
    border-color: #c7d2fe !important;
}
</style>
"""

COLS_CONFIG = [
    ("abonne",         "Abonné",  1.8),
    ("c",              "C",       0.5),
    ("nom",            "Nom",     1.8),
    ("prenom",         "Prénom",  1.8),
    ("pays",           "Pays",    0.8),
    ("code_postal",    "CP",      0.8),
    ("ville",          "Ville",   1.4),
    ("adresse",        "Adresse", 2.4),
    ("option_majeure", "Option",  1.5),
    ("annule",         "Annulé",  0.8),
    ("ret",            "Ret",     0.6),
    ("societe",        "Société", 1.5),
]


def _section_fa(icon_class: str, label: str):
    st.markdown(
        f'<div class="section-title-fa"><i class="{icon_class}"></i>{label}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
def app():
    apply_theme()
    st.markdown(TEL_CSS, unsafe_allow_html=True)

    req_id      = st.session_state.get("req_id")
    utilisateur = st.session_state.get("utilisateur_connecte", "inconnu")

    page_banner(
        title     = "Recherche par Téléphone",
        subtitle  = "Liste des abonnés associés au numéro de téléphone saisi.",
        watermark = "TEL"
    )

    # ── Aucune requête active ─────────────────────────────
    if not req_id:
        st.markdown("""
        <div class="empty-state">
            <div class="es-icon-wrap">
                <i class="fa-solid fa-mobile-screen"></i>
            </div>
            <div class="es-title">Aucune recherche active</div>
            <div class="es-sub">Lancez une recherche depuis la page d'accueil.</div>
        </div>""", unsafe_allow_html=True)
        _btn_accueil()
        return

    requete = lire_requete_par_id(req_id)
    if not requete:
        st.error("Requête introuvable en base de données.")
        _btn_accueil()
        return

    statut = requete.get("statut")
    valeur = requete.get("valeur", "—")

    color_statut = {
        "terminee":   "#059669",
        "en_attente": "#d97706",
        "en_cours":   "#d97706",
        "echouee":    "#e11d48",
    }.get(statut, "#64748b")

    # ── Carte entête ──────────────────────────────────────
    st.markdown(f"""
    <div class="tel-result-card">
        <div class="tel-header">
            <div class="tel-avatar">
                <i class="fa-solid fa-mobile-screen"></i>
            </div>
            <div>
                <div class="tel-title">Téléphone : +237&nbsp;{valeur}</div>
                <div class="tel-sub">
                    Requête #{req_id} &nbsp;·&nbsp; Statut :
                    <strong style="color:{color_statut};">
                        {statut.replace('_', ' ').capitalize()}
                    </strong>
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # États — polling
    # ══════════════════════════════════════════════════════

    if statut == "en_attente":
        st.markdown("""
        <div class="status-block status-waiting">
            <div class="status-icon-wrap si-waiting">
                <i class="fa-solid fa-clock"></i>
            </div>
            <div class="status-title-s">En file d'attente</div>
            <div class="status-desc-s">
                Un worker va rechercher les abonnés liés à ce numéro.
            </div>
            <div class="progress-bar"><div class="pb-cyan"></div></div>
        </div>""", unsafe_allow_html=True)
        time.sleep(3)
        st.rerun()

    elif statut == "en_cours":
        worker_id = requete.get("worker_id", "—")
        st.markdown(f"""
        <div class="status-block status-processing">
            <div class="status-icon-wrap si-processing">
                <i class="fa-solid fa-magnifying-glass"></i>
            </div>
            <div class="status-title-s">Recherche en cours…</div>
            <div class="status-desc-s">
                <i class="fa-solid fa-microchip"
                   style="margin-right:5px;color:#d97706;"></i>
                Worker <strong>{worker_id}</strong> connecté à CGAWEB.<br>
                Identification des abonnés, veuillez patienter.
            </div>
            <div class="progress-bar"><div class="pb-amber"></div></div>
        </div>""", unsafe_allow_html=True)
        time.sleep(3)
        st.rerun()

    elif statut == "terminee":
        resultat = requete.get("resultat") or []

        if not resultat:
            st.markdown("""
            <div class="empty-state">
                <div class="es-icon-wrap">
                    <i class="fa-solid fa-magnifying-glass"></i>
                </div>
                <div class="es-title">Aucun abonné trouvé</div>
                <div class="es-sub">
                    Ce numéro n'est associé à aucun abonné dans CGAWEB.
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            _section_fa("fa-solid fa-list-ul", f"{len(resultat)} abonné(s) trouvé(s)")

            widths  = [c[2] for c in COLS_CONFIG]
            headers = [c[1] for c in COLS_CONFIG]
            fields  = [c[0] for c in COLS_CONFIG]

            # En-têtes
            cols_h = st.columns(widths)
            for i, head in enumerate(headers):
                cols_h[i].markdown(
                    f'<span class="col-header">{head}</span>',
                    unsafe_allow_html=True
                )
            st.markdown('<hr class="row-sep">', unsafe_allow_html=True)

            # Lignes
            df = pd.DataFrame(resultat)
            for idx, row in df.iterrows():
                cols = st.columns(widths)
                id_ab = str(row.get("abonne", "N/A"))

                st.markdown('<div class="btn-abo">', unsafe_allow_html=True)
                if cols[0].button(id_ab, key=f"btn_abo_{idx}_{id_ab}", use_container_width=True):
                    from file_attente import ajouter_requete, lancer_worker
                    nouvelle = ajouter_requete(utilisateur, "Numéro d'abonné", id_ab)
                    if nouvelle:
                        st.session_state["req_id"]                = nouvelle["id"]
                        st.session_state["type_recherche_actuel"] = "Numéro d'abonné"
                        st.session_state["requete_en_cours"]      = False
                        st.session_state["page_active"]           = "resultat_abonne"
                        lancer_worker()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                for i, field in enumerate(fields[1:], start=1):
                    val = str(row.get(field, "—"))
                    if field == "adresse" and len(val) > 22:
                        val = val[:20] + "…"
                    cols[i].write(val)

                st.markdown('<hr class="row-sep">', unsafe_allow_html=True)

    elif statut == "echouee":
        msg = "Erreur inconnue"
        if requete.get("resultat"):
            msg = requete["resultat"].get("erreur", msg)
        st.markdown(f"""
        <div class="error-card">
            <div class="ec-icon"><i class="fa-solid fa-circle-xmark"></i></div>
            <div>
                <div class="ec-title">Échec de la recherche</div>
                <div class="ec-msg">
                    <i class="fa-solid fa-triangle-exclamation"
                       style="margin-right:5px;"></i>
                    <strong>Raison :</strong> {msg}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    divider()
    _btn_accueil()


def _btn_accueil():
    st.markdown('<div class="btn-home">', unsafe_allow_html=True)
    if st.button("Retour à l'accueil", use_container_width=True, key="btn_home_tel"):
        st.session_state.page_active      = "Accueil"
        st.session_state.requete_en_cours = False
        st.session_state.req_id           = None
        st.session_state.dernier_resultat = None
        st.session_state.screenshot_bytes = None  # ← libère la mémoire
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)