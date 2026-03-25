"""
profil.py
─────────
Page de profil utilisateur — consultation + édition.
"""

import streamlit as st
from theme import page_banner, divider

# Tentative d'importation des fonctions de gestion BDD
try:
    from fonction import get_user_by_username, modifier_utilisateur
except ImportError:
    st.error("Impossible de charger le module 'fonction.py'. Vérifiez sa présence.")

PROFIL_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
.profil-card {
    background:#ffffff; border:1px solid #e2e8f0;
    border-radius:18px; padding:40px 44px;
    box-shadow:0 4px 24px rgba(99,102,241,0.09);
    position:relative; overflow:hidden;
}
.profil-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background:linear-gradient(90deg,#6366f1,#a855f7,#06b6d4);
    border-radius:18px 18px 0 0;
}
.profil-header {
    display:flex; align-items:center; gap:28px;
    padding-bottom:28px; border-bottom:1px solid #f1f5f9; margin-bottom:28px;
}
.profil-avatar {
    width:88px; height:88px; border-radius:50%;
    background:linear-gradient(135deg,#6366f1,#a855f7);
    display:flex; align-items:center; justify-content:center;
    font-size:2.2rem; color:#ffffff; flex-shrink:0;
    border:4px solid #e0e7ff;
    box-shadow:0 4px 14px rgba(99,102,241,0.25);
}
.profil-name {
    font-family:'Playfair Display',serif;
    font-size:1.5rem; font-weight:700; color:#1e293b; margin-bottom:4px;
}
.profil-username { font-size:0.82rem; color:#94a3b8; margin-bottom:8px; }
.profil-role {
    display:inline-flex; align-items:center; gap:6px;
    background:linear-gradient(135deg,#eef2ff,#e0e7ff);
    border:1px solid #c7d2fe; color:#4f46e5;
    padding:4px 12px; border-radius:20px;
    font-size:0.75rem; font-weight:700;
}
.info-grid {
    display:grid; grid-template-columns:1fr 1fr; gap:16px;
}
.info-grid-full {
    grid-column: 1 / -1;
}
.info-item {
    background:#f8fafc; border:1px solid #e2e8f0;
    border-radius:12px; padding:16px 20px;
    display:flex; align-items:flex-start; gap:14px;
}
.info-icon {
    width:38px; height:38px; border-radius:10px;
    background:linear-gradient(135deg,#eef2ff,#e0e7ff);
    display:flex; align-items:center; justify-content:center;
    font-size:0.95rem; color:#6366f1; flex-shrink:0;
}
.info-label {
    font-size:0.7rem; font-weight:700; color:#94a3b8;
    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:3px;
}
.info-value { font-size:0.92rem; font-weight:600; color:#1e293b; }
.info-empty { font-size:0.88rem; color:#cbd5e1; font-style:italic; }
.badge-actif {
    display:inline-flex; align-items:center; gap:5px;
    background:#dcfce7; color:#166534; border:1px solid #86efac;
    padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:700;
}
.badge-actif::before {
    content:''; width:6px; height:6px;
    background:#22c55e; border-radius:50%; display:inline-block;
}
.section-edition {
    background:#f8fafc; border:1px solid #e2e8f0;
    border-radius:14px; padding:24px 28px; margin-top:4px;
}
.section-mdp {
    background:#fefce8; border:1px solid #fde68a;
    border-radius:14px; padding:24px 28px; margin-top:16px;
}
.section-title {
    font-size:0.78rem; font-weight:700; color:#64748b;
    text-transform:uppercase; letter-spacing:0.08em;
    margin-bottom:16px;
    display:flex; align-items:center; gap:8px;
}
</style>
"""

def app():
    st.markdown(PROFIL_CSS, unsafe_allow_html=True)

    page_banner(
        title="Mon Profil",
        subtitle="Informations de votre compte VisuV.",
        watermark="PRO"
    )

    utilisateur = st.session_state.get("utilisateur_connecte", "—")
    role        = st.session_state.get("role_utilisateur", "—")

    # ── Chargement depuis la BDD ──────────────────────────
    user_data = {}
    try:
        result = get_user_by_username(utilisateur)
        if result:
            user_data = result
    except Exception as e:
        st.error(f" Erreur chargement profil : {e}")

    user_id       = user_data.get("id", None)
    nom           = user_data.get("nom", "") or ""
    telephone     = user_data.get("telephone", "") or ""
    email         = user_data.get("email", "") or ""
    date_creation = user_data.get("date_creation", "") or ""
    display_name  = nom or utilisateur

    # ── Mode édition ──────────────────────────────────────
    if "mode_edition_profil" not in st.session_state:
        st.session_state.mode_edition_profil = False

    # ── Helper champ HTML ─────────────────────────────────
    def _champ(icon, label, valeur, full=False):
        val_html = (
            f'<span class="info-value">{valeur}</span>'
            if valeur else
            '<span class="info-empty">Non renseigné</span>'
        )
        full_class = ' info-grid-full' if full else ''
        return f"""
        <div class="info-item{full_class}">
            <div class="info-icon"><i class="{icon}"></i></div>
            <div>
                <div class="info-label">{label}</div>
                {val_html}
            </div>
        </div>"""

    _, col, _ = st.columns([1, 4, 1])
    with col:
        # RÉACTIVATION DE LA DIV DE CARTE
        st.markdown('<div class="profil-card">', unsafe_allow_html=True)

        # ── En-tête ───────────────────────────────────────
        st.markdown(f"""
        <div class="profil-header">
            <div class="profil-avatar">
                <i class="fa-solid fa-circle-user"></i>
            </div>
            <div>
                <div class="profil-name">{display_name}</div>
                <div class="profil-username">
                    <i class="fa-solid fa-at"
                       style="margin-right:4px;color:#a5b4fc;"></i>{utilisateur}
                </div>
                <div style="display:flex;align-items:center;gap:10px;
                            flex-wrap:wrap;margin-top:6px;">
                    <span class="profil-role">
                        <i class="fa-solid fa-shield-halved"></i>&nbsp;{role}
                    </span>
                    <span class="badge-actif">Actif</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ══════════════════════════════════════════════════
        #  MODE CONSULTATION
        # ══════════════════════════════════════════════════
        if not st.session_state.mode_edition_profil:

            st.markdown(f"""
            <div class="info-grid">
                {_champ("fa-solid fa-user",          "Nom complet",    nom)}
                {_champ("fa-solid fa-id-badge",      "Identifiant",    utilisateur)}
                {_champ("fa-solid fa-envelope",      "Adresse e-mail", email)}
                {_champ("fa-solid fa-phone",         "Téléphone",      telephone)}
                {_champ("fa-solid fa-shield-halved", "Rôle",           role)}
                {_champ("fa-solid fa-calendar-days", "Membre depuis",  date_creation)}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(" Modifier ", use_container_width=True, key="btn_ouvrir_edition"):
                st.session_state.mode_edition_profil = True
                st.rerun()

        # ══════════════════════════════════════════════════
        #  MODE ÉDITION
        # ══════════════════════════════════════════════════
        else:
            st.markdown("""
            <div class="section-title">
                <i class="fa-solid fa-pen-to-square" style="color:#6366f1;"></i>
                Informations personnelles
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-edition">', unsafe_allow_html=True)
            nouveau_nom = st.text_input(label="Nom complet", value=nom, key="edit_nom")
            
            c_email, c_tel = st.columns(2)
            with c_email:
                nouveau_email = st.text_input(label="Adresse e-mail", value=email, key="edit_email")
            with c_tel:
                nouveau_telephone = st.text_input(label="Téléphone", value=telephone, key="edit_telephone")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="section-title" style="margin-top:20px;">
                <i class="fa-solid fa-lock" style="color:#d97706;"></i>
                Changer le mot de passe
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-mdp">', unsafe_allow_html=True)
            c_mdp1, c_mdp2 = st.columns(2)
            with c_mdp1:
                nouveau_mdp = st.text_input(label="Nouveau mot de passe", type="password", key="edit_mdp1")
            with c_mdp2:
                confirm_mdp = st.text_input(label="Confirmer le mot de passe", type="password", key="edit_mdp2")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)

            with c1:
                if st.button(" Enregistrer", use_container_width=True, type="primary", key="btn_enregistrer"):
                    erreur = None
                    if not nouveau_nom.strip():
                        erreur = "Le nom ne peut pas être vide."
                    elif nouveau_email and "@" not in nouveau_email:
                        erreur = "Adresse e-mail invalide."
                    elif nouveau_mdp and nouveau_mdp != confirm_mdp:
                        erreur = "Les mots de passe ne correspondent pas."

                    if erreur:
                        st.error(f" {erreur}")
                    else:
                        infos = {
                            "nom": nouveau_nom.strip(),
                            "telephone": nouveau_telephone.strip(),
                            "email": nouveau_email.strip(),
                            "role": role,
                            "mot_de_passe": nouveau_mdp
                        }
                        try:
                            if modifier_utilisateur(user_id, infos):
                                st.success(" Profil mis à jour !")
                                st.session_state.mode_edition_profil = False
                                st.rerun()
                        except Exception as e:
                            st.error(f" Erreur : {e}")

            with c2:
                if st.button(" Annuler", use_container_width=True, key="btn_annuler_edition"):
                    st.session_state.mode_edition_profil = False
                    st.rerun()

        # FERMETURE CORRECTE DE LA DIV PROFIL-CARD
        st.markdown('</div>', unsafe_allow_html=True)

    divider()

    if st.button("← Retour à l'accueil", use_container_width=True, key="btn_retour_profil"):
        st.session_state.page_active = "Accueil"
        st.rerun()