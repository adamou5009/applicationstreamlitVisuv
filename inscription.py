import streamlit as st
import re
from fonction import enregistrer_utilisateur
from theme import apply_theme

REGEX_TELEPHONE = r"^[0-9]{9}$"
REGEX_EMAIL     = r"^[a-zA-Z0-9_.+-]+@gmail\.com$"

# ═══════════════════════════════════════════════════════════════
# CSS spécifique à la page (complète theme.py)
# ═══════════════════════════════════════════════════════════════
INSCRIPTION_CSS = """
<style>
/* ── Carte formulaire centrée ── */
.auth-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 40px 44px;
    box-shadow: 0 8px 32px rgba(99,102,241,0.10);
    position: relative;
    overflow: hidden;
}
.auth-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6366f1, #a855f7, #06b6d4);
    border-radius: 20px 20px 0 0;
}

/* ── Titre ── */
.auth-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #1e293b;
    text-align: center;
    margin-bottom: 6px;
}
.auth-subtitle {
    font-size: 0.82rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 28px;
}

/* ── Inputs arrondis ── */
div[data-testid="stTextInput"] input {
    border-radius: 12px !important;
    padding: 12px 16px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ── Bouton principal ── */
button[kind="secondaryFormSubmit"],
button[kind="primaryFormSubmit"] {
    width: 100% !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    height: 50px !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    letter-spacing: 0.04em !important;
}

/* ── Lien bas de page ── */
.auth-footer {
    text-align: center;
    margin-top: 20px;
    font-size: 0.82rem;
    color: #64748b;
}

/* ── Règles mot de passe ── */
.pwd-rules {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.76rem;
    color: #64748b;
    margin: 4px 0 12px;
    line-height: 1.7;
}
.pwd-rules span { font-weight: 600; color: #475569; }
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════════
def mot_de_passe_valide(mdp):
    erreurs = []
    if not (8 <= len(mdp) <= 12):
        erreurs.append("Entre 8 et 12 caractères requis.")
    if not re.search(r"[A-Z]", mdp):
        erreurs.append("Au moins une majuscule requise.")
    if not re.search(r"[0-9]", mdp):
        erreurs.append("Au moins un chiffre requis.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", mdp):
        erreurs.append("Au moins un symbole requis.")
    return not erreurs, erreurs


# ═══════════════════════════════════════════════════════════════
# Page
# ═══════════════════════════════════════════════════════════════
def page_inscription():
    apply_theme()
    st.markdown(INSCRIPTION_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        #st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Créer un compte</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Remplissez les informations ci-dessous pour vous inscrire.</div>', unsafe_allow_html=True)

        with st.form("formulaire_inscription"):
            nom          = st.text_input("Nom complet",              placeholder="Ex : Jean Dupont")
            username     = st.text_input("Nom d'utilisateur",        placeholder="Ex : jean.dupont")
            telephone    = st.text_input("Téléphone",                placeholder="9 chiffres ex: 655123456", max_chars=9)
            email        = st.text_input("Email",                    placeholder="exemple@gmail.com")
            mot_de_passe = st.text_input("Mot de passe",             type="password", placeholder="••••••••")

            st.markdown("""
            <div class="pwd-rules">
                <span>Règles :</span> 8–12 caractères · 1 majuscule · 1 chiffre · 1 symbole (!@#…)
            </div>
            """, unsafe_allow_html=True)

            mot_de_passe2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="••••••••")

            submit = st.form_submit_button("  S'inscrire", use_container_width=True)

        if submit:
            nom       = nom.strip()
            username  = username.strip()
            telephone = telephone.strip()
            email     = email.strip().lower()

            if not all([nom, username, telephone, email, mot_de_passe, mot_de_passe2]):
                st.error("❌ Tous les champs sont obligatoires.")
            elif mot_de_passe != mot_de_passe2:
                st.error("❌ Les mots de passe ne correspondent pas.")
            elif not re.match(REGEX_EMAIL, email):
                st.error("❌ Utilisez une adresse @gmail.com valide.")
            elif not re.match(REGEX_TELEPHONE, telephone):
                st.error("❌ Le téléphone doit contenir exactement 9 chiffres.")
            else:
                is_valid, erreurs_mdp = mot_de_passe_valide(mot_de_passe)
                if not is_valid:
                    st.error(f"❌ {erreurs_mdp[0]}")
                else:
                    ok, msg = enregistrer_utilisateur(
                        nom, username, telephone, email, mot_de_passe, "Utilisateur"
                    )
                    if ok:
                        st.success(msg)
                        st.session_state["utilisateur_connecte"] = username
                        st.session_state["role_utilisateur"]     = "Utilisateur"
                        st.session_state["connecte"]             = True
                        st.session_state["page_active"]          = "Accueil"
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)  # /auth-card

        # ── Lien vers connexion ──────────────────────────
        st.markdown('<div class="auth-footer">Vous avez déjà un compte ?</div>', unsafe_allow_html=True)
        _, c, _ = st.columns([1, 1, 1])
        with c:
            if st.button("Se connecter", use_container_width=True, key="btn_vers_connexion"):
                st.session_state["page_active"] = "Connexion"
                st.rerun()


if __name__ == "__main__":
    page_inscription()