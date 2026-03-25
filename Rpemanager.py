import streamlit as st
import pandas as pd
import os
import time
from fonction import (
    WebDriverManager,
    connexion_cgaweb,
    deconnexion_cgaweb,
    resultat,
    traiter_decodeurs,
    est_connecte,
    identifiants_cgaweb_rpe,
)
from theme import page_banner, section_header, divider, metric_chips

# ═══════════════════════════════════════════════════════════════
# CSS spécifique + Font Awesome
# ═══════════════════════════════════════════════════════════════
RPE_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<style>
/* ── Carte login ── */
.login-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 36px 40px;
    max-width: 460px;
    margin: 24px auto;
    box-shadow: 0 4px 20px rgba(99,102,241,0.08);
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6366f1, #a855f7, #06b6d4);
    border-radius: 18px 18px 0 0;
}
.login-card-sub {
    font-size: 0.8rem; color: #94a3b8; text-align: center; margin-bottom: 24px;
}

/* ── Bandeau identifiant actif ── */
.id-banner {
    background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    border: 1.5px solid #6ee7b7;
    border-radius: 12px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}
.id-banner .ib-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #10b981; box-shadow: 0 0 6px #10b98188;
    flex-shrink: 0;
}
.id-banner .ib-label {
    font-size: 0.72rem; font-weight: 700; color: #065f46;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.id-banner .ib-user {
    font-size: 0.9rem; font-weight: 700; color: #1e293b;
    display: flex; align-items: center; gap: 7px;
}
.id-banner .ib-user i {
    color: #10b981; font-size: 0.95rem;
}

/* ── Zone upload ── */
.upload-zone {
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    border: 2px dashed #c7d2fe;
    border-radius: 14px;
    padding: 32px;
    text-align: center;
    margin: 16px 0;
    transition: border-color 0.2s ease;
}
.upload-zone:hover { border-color: #6366f1; }
.upload-zone .uz-icon {
    font-size: 2.2rem; color: #6366f1; margin-bottom: 10px;
}
.upload-zone .uz-title {
    font-weight: 700; color: #1e293b; font-size: 0.95rem; margin-bottom: 4px;
}
.upload-zone .uz-sub { font-size: 0.78rem; color: #94a3b8; }

/* ── Info fichier chargé ── */
.file-info-card {
    background: linear-gradient(135deg, #eef2ff, #e0e7ff);
    border: 1px solid #c7d2fe;
    border-radius: 10px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0;
}
.file-info-card .fi-icon {
    font-size: 1.6rem; color: #6366f1; flex-shrink: 0;
}
.file-info-card .fi-name {
    font-weight: 700; color: #1e293b; font-size: 0.88rem;
}
.file-info-card .fi-meta { font-size: 0.75rem; color: #6366f1; }

/* ── Boutons traitement ── */
.btn-launch .stButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    height: 48px !important;
    box-shadow: 0 4px 12px rgba(16,185,129,0.3) !important;
}
.btn-stop .stButton > button {
    background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    height: 48px !important;
    box-shadow: 0 4px 12px rgba(244,63,94,0.25) !important;
}

/* ── Bandeau arrêt en cours ── */
.stopping-card {
    background: linear-gradient(135deg, #fff1f2, #ffe4e6);
    border: 1.5px solid #fda4af;
    border-radius: 12px;
    padding: 16px 24px;
    margin: 12px 0;
    display: flex;
    align-items: center;
    gap: 14px;
}
.stopping-card .sc-spinner {
    width: 20px; height: 20px;
    border: 3px solid #fda4af;
    border-top-color: #f43f5e;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.stopping-card .sc-icon {
    font-size: 1.2rem; color: #f43f5e; flex-shrink: 0;
}
.stopping-card .sc-text {
    font-weight: 700; color: #be123c; font-size: 0.9rem;
}
.stopping-card .sc-sub {
    font-size: 0.78rem; color: #e11d48; margin-top: 2px;
}

/* ── Statut traitement ── */
.processing-card {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 1.5px solid #fcd34d;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 16px 0;
    text-align: center;
}
.processing-card .pc-icon {
    font-size: 1.8rem; color: #f59e0b; margin-bottom: 8px;
}
.processing-card .pc-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; font-weight: 700; color: #92400e; margin-bottom: 6px;
}
.processing-card .pc-sub { font-size: 0.82rem; color: #b45309; }

/* ── Barre progression animée ── */
.progress-bar-anim {
    height: 5px; background: #e2e8f0; border-radius: 3px;
    margin: 14px 0 0; overflow: hidden;
}
.progress-fill-anim {
    height: 100%; border-radius: 3px;
    background: linear-gradient(90deg, #f59e0b, #f97316);
    animation: prog 1.6s ease-in-out infinite;
}
@keyframes prog {
    0%   { width:10%; margin-left:0; }
    50%  { width:40%; margin-left:30%; }
    100% { width:10%; margin-left:90%; }
}

/* ── Titres de section avec icône FA ── */
.section-title-fa {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 20px 0 10px;
}
.section-title-fa i {
    color: #6366f1;
    font-size: 1.05rem;
    width: 22px;
    text-align: center;
}

/* ── Inputs login ── */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    padding: 11px 16px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}

/* ── Label icône devant les inputs ── */
.input-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 4px;
}
.input-label i {
    color: #6366f1;
    width: 16px;
    text-align: center;
}

/* ── Footer ── */
.rpe-footer {
    text-align: center; font-size: 0.75rem; color: #cbd5e1;
    margin-top: 48px; padding-top: 16px;
    border-top: 1px solid #f1f5f9;
}
</style>
"""

URL_CGA = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"


# ═══════════════════════════════════════════════════════════════
# Helpers HTML avec icônes Font Awesome
# ═══════════════════════════════════════════════════════════════
def _section_fa(icon_class: str, label: str):
    """Titre de section avec icône Font Awesome."""
    st.markdown(
        f'<div class="section-title-fa"><i class="{icon_class}"></i>{label}</div>',
        unsafe_allow_html=True,
    )


def _input_label_fa(icon_class: str, label: str):
    """Label enrichi avec icône FA au-dessus d'un st.text_input."""
    st.markdown(
        f'<div class="input-label"><i class="{icon_class}"></i>{label}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# Utilitaire : nettoyage propre du WebDriverManager en session
# ═══════════════════════════════════════════════════════════════
def _cleanup_manager():
    wdm = st.session_state.get("wdm_instance")
    if wdm is not None:
        try:
            wdm.stop_driver()
        except Exception:
            pass
        st.session_state.wdm_instance = None


# ═══════════════════════════════════════════════════════════════
# Utilitaire : affichage des résultats (normaux, arrêt, crash)
# ═══════════════════════════════════════════════════════════════
def _afficher_resultats(final_data: list, partiel: bool = False):
    if not final_data:
        return

    output, nom_fichier = resultat(final_data)
    df_result = pd.DataFrame(final_data)

    divider()
    _section_fa("fa-solid fa-chart-bar", "Résultats")

    nb_total  = len(df_result)
    nb_ok     = (
        int(df_result["statut"].eq("ok").sum())
        if "statut" in df_result.columns else nb_total
    )
    nb_erreur = (
        int(df_result["statut"].eq("Erreur").sum())
        if "statut" in df_result.columns else 0
    )

    metric_chips([
        {"label": "Lignes traitées", "value": nb_total,  "color": "indigo"},
        {"label": "Réussies",        "value": nb_ok,     "color": "emerald"},
        {"label": "Erreurs",         "value": nb_erreur, "color": "rose"},
    ])

    if partiel:
        if st.session_state.get("stop_processing"):
            st.warning(
                f"Arrêt d'urgence confirmé — {nb_total} ligne(s) traitées. "
                "Téléchargez les résultats partiels ci-dessous."
            )
        else:
            st.warning(
                f"Interruption technique — {nb_total} ligne(s) récupérées. "
                "Téléchargez les résultats partiels ci-dessous."
            )
    else:
        st.success("Extraction terminée avec succès !")

    st.dataframe(df_result, use_container_width=True, hide_index=True)

    # Bouton téléchargement avec icône FA injectée via markdown au-dessus
    st.markdown(
        '<p style="margin:0 0 4px;font-size:0.82rem;color:#6366f1;font-weight:600;">'
        '<i class="fa-solid fa-file-arrow-down" style="margin-right:6px;"></i>'
        'Fichier Excel prêt</p>',
        unsafe_allow_html=True,
    )
    st.download_button(
        label="Télécharger le fichier Excel",
        data=output,
        file_name=nom_fichier,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
def app():
    if not est_connecte():
        st.warning("Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.markdown(RPE_CSS, unsafe_allow_html=True)

    # ── Init session ──────────────────────────────────────
    for key, default in [
        ("traitement_lance",    False),
        ("stop_processing",     False),
        ("arret_en_cours",      False),
        ("traitement_en_cours", False),
        ("resultats_en_cours",  []),
        ("wdm_instance",        None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    page_banner(
        title="RPE Manager",
        subtitle="Extraction automatique des informations abonnés via CGAWEB.",
        watermark="RPE VisuV"
    )

    # ── Étape 1 : Authentification CGAWEB ────────────────
    if "rpe_user" not in st.session_state:
        _afficher_formulaire_login()
        st.stop()

    # ── Identifiants actifs ───────────────────────────────
    u_env, p_env, s_env = identifiants_cgaweb_rpe()
    utilisateur  = st.session_state.get("rpe_user")  or u_env or ""
    mot_de_passe = st.session_state.get("rpe_pass")  or p_env or ""
    secret       = st.session_state.get("rpe_otp")   or s_env or ""

    col_info, col_btn = st.columns([4, 1], gap="medium")
    with col_info:
        st.markdown(f"""
        <div class="id-banner">
            <div class="ib-dot"></div>
            <div>
                <div class="ib-label">Compte CGAWEB actif</div>
                <div class="ib-user">
                    <i class="fa-solid fa-circle-user"></i>
                    {utilisateur}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Changer", use_container_width=True):
            _cleanup_manager()
            for k in ["rpe_user", "rpe_pass", "rpe_otp"]:
                st.session_state.pop(k, None)
            st.rerun()

    divider()

    # ── Étape 2 : Import du fichier Excel ─────────────────
    _section_fa("fa-solid fa-folder-open", "Importer le fichier Excel")

    st.markdown("""
    <div class="upload-zone">
        <div class="uz-icon"><i class="fa-solid fa-file-excel"></i></div>
        <div class="uz-title">Glissez votre fichier ou cliquez pour parcourir</div>
        <div class="uz-sub">Formats acceptés : .xlsx &nbsp;—&nbsp;
            Colonnes requises : <code>numéro de décodeur</code> ou <code>Abonne</code>
        </div>
    </div>
    """, unsafe_allow_html=True)

    fichier = st.file_uploader(
        "Fichier Excel",
        type=["xlsx"],
        label_visibility="collapsed",
    )

    if not fichier:
        st.markdown('<div class="rpe-footer">© 2026 by Adamou Muisse.</div>',
                    unsafe_allow_html=True)
        return

    # ── Lecture & validation ──────────────────────────────
    df = pd.read_excel(fichier)
    df.columns = [c.strip().lower() for c in df.columns]

    colonnes_dispo = [c for c in ["numéro de décodeur", "abonne"] if c in df.columns]
    if not colonnes_dispo:
        st.error("Colonnes introuvables. Le fichier doit contenir 'numéro de décodeur' ou 'Abonne'.")
        return

    st.markdown(f"""
    <div class="file-info-card">
        <div class="fi-icon"><i class="fa-solid fa-file-spreadsheet"></i></div>
        <div>
            <div class="fi-name">{fichier.name}</div>
            <div class="fi-meta">
                <i class="fa-solid fa-list-ol" style="margin-right:4px;"></i>
                {len(df)} lignes détectées &nbsp;·&nbsp;
                <i class="fa-solid fa-table-columns" style="margin-right:4px;"></i>
                Colonnes : {", ".join(colonnes_dispo)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    metric_chips([
        {"label": "Lignes à traiter", "value": len(df),             "color": "indigo"},
        {"label": "Colonnes source",  "value": len(colonnes_dispo), "color": "violet"},
    ])

    if len(colonnes_dispo) > 1:
        _section_fa("fa-solid fa-sliders", "Paramètres d'extraction")
        colonne_source = st.selectbox("Colonne à utiliser", colonnes_dispo)
    else:
        colonne_source = colonnes_dispo[0]

    divider()

    # ── Étape 3 : Contrôles ───────────────────────────────
    _section_fa("fa-solid fa-play-circle", "Lancer l'extraction")

    traitement_actif = st.session_state.traitement_lance
    arret_en_cours   = st.session_state.arret_en_cours

    col_run, col_stop = st.columns(2, gap="medium")

    with col_run:
        st.markdown('<div class="btn-launch">', unsafe_allow_html=True)
        launch = st.button(
            "Lancer l'extraction",
            disabled=traitement_actif or arret_en_cours,
            use_container_width=True,
            key="btn_launch",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if launch:
            _cleanup_manager()
            st.session_state.traitement_lance   = True
            st.session_state.stop_processing    = False
            st.session_state.arret_en_cours     = False
            st.session_state.resultats_en_cours = []
            st.rerun()

    with col_stop:
        if traitement_actif:
            st.markdown('<div class="btn-stop">', unsafe_allow_html=True)
            stop_clicked = st.button(
                "Arrêt en cours…" if arret_en_cours else "Arrêt d'urgence",
                disabled=arret_en_cours,
                use_container_width=True,
                key="btn_stop",
            )
            st.markdown('</div>', unsafe_allow_html=True)

            if stop_clicked and not arret_en_cours:
                st.session_state.stop_processing = True
                st.session_state.arret_en_cours  = True
                st.rerun()

    # ── Bandeau arrêt en cours ────────────────────────────
    if arret_en_cours and traitement_actif:
        st.markdown("""
        <div class="stopping-card">
            <div class="sc-spinner"></div>
            <div>
                <div class="sc-text">
                    <i class="fa-solid fa-triangle-exclamation"
                       style="margin-right:6px; color:#f43f5e;"></i>
                    Arrêt d'urgence demandé
                </div>
                <div class="sc-sub">
                    Fin du décodeur en cours… Veuillez patienter.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Étape 4 : Traitement ──────────────────────────────
    if traitement_actif:

        if not arret_en_cours:
            st.markdown("""
            <div class="processing-card">
                <div class="pc-icon">
                    <i class="fa-solid fa-gears"></i>
                </div>
                <div class="pc-title">Extraction en cours…</div>
                <div class="pc-sub">
                    <i class="fa-solid fa-satellite-dish"
                       style="margin-right:5px;"></i>
                    Connexion CGAWEB, récupération des données abonnés.
                </div>
                <div class="progress-bar-anim">
                    <div class="progress-fill-anim"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        progress_bar = st.progress(0)
        statut_txt   = st.empty()
        driver       = None

        try:
            manager = WebDriverManager()
            st.session_state.wdm_instance = manager

            res_connexion = connexion_cgaweb(
                manager=manager,
                url=URL_CGA,
                utilisateur=utilisateur,
                mot_de_passe=mot_de_passe,
                secret=secret,
                headless=True,
            )

            if res_connexion and res_connexion[0] is not None:
                driver, original_window, new_window = res_connexion

                resultats = traiter_decodeurs(
                    driver,
                    df,
                    colonne_source,
                    original_window,
                    new_window,
                    statut_txt,
                    progress_bar,
                )

                final_data    = resultats or st.session_state.resultats_en_cours
                arret_demande = st.session_state.get("stop_processing", False)
                st.session_state.resultats_en_cours = final_data
                _afficher_resultats(final_data, partiel=arret_demande)

            else:
                st.error("Échec de connexion CGAWEB. Vérifiez vos identifiants.")
                st.session_state.traitement_lance = False

        except Exception as e:
            st.error(f"Erreur technique : {e}")
            resultats_partiels = st.session_state.get("resultats_en_cours", [])
            if resultats_partiels:
                _afficher_resultats(resultats_partiels, partiel=True)

        finally:
            try:
                if driver:
                    deconnexion_cgaweb(driver)
            except Exception:
                pass

            _cleanup_manager()

            st.session_state.traitement_lance    = False
            st.session_state.traitement_en_cours = False
            st.session_state.arret_en_cours      = False

    st.markdown('<div class="rpe-footer">© 2026 by Adamou Muisse.</div>',
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Formulaire de connexion CGAWEB
# ═══════════════════════════════════════════════════════════════
def _afficher_formulaire_login():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown(
            "<div class=\"login-card-sub\">"
            "<i class='fa-solid fa-shield-halved' style='margin-right:6px;color:#6366f1;'></i>"
            "Configurez vos accès pour cette session d'extraction."
            "</div>",
            unsafe_allow_html=True,
        )

        with st.form("form_rpe_login", clear_on_submit=False):

            _input_label_fa("fa-solid fa-user", "Nom d'utilisateur CGAWEB")
            user_input = st.text_input(
                "user", label_visibility="collapsed", placeholder="ex : +237000000"
            )

            _input_label_fa("fa-solid fa-lock", "Mot de passe")
            pwd_input = st.text_input(
                "pass", label_visibility="collapsed",
                type="password", placeholder="••••••••"
            )

            _input_label_fa("fa-solid fa-key", "Clé secrète OTP (Optionnel)")
            otp_input = st.text_input(
                "otp", label_visibility="collapsed",
                type="password", placeholder="JBSWY3DPEHPK3PXP…"
            )

            submitted = st.form_submit_button(
                "Valider et continuer",
                use_container_width=True,
            )
            if submitted:
                if user_input and pwd_input:
                    st.session_state.rpe_user = user_input.strip()
                    st.session_state.rpe_pass = pwd_input.strip()
                    st.session_state.rpe_otp  = otp_input.strip().replace(" ", "")
                    st.success("Identifiants configurés !")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur et mot de passe obligatoires.")

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    app()