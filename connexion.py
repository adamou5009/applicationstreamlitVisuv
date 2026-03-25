import secrets
import streamlit as st
from fonction import verifier_identifiants, get_connection
from theme import apply_theme

# ═══════════════════════════════════════════════════════════════
# CSS spécifique à la page (complète theme.py)
# ═══════════════════════════════════════════════════════════════
CONNEXION_CSS = """
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
.auth-logo { text-align: center; margin-bottom: 6px; }
.auth-logo-icon { font-size: 2.4rem; display: block; margin-bottom: 4px; }
.auth-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem; font-weight: 700;
    color: #1e293b; text-align: center; margin-bottom: 4px;
}
.auth-subtitle {
    font-size: 0.82rem; color: #94a3b8;
    text-align: center; margin-bottom: 28px;
}
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
.btn-secondary .stButton > button {
    background: #f8fafc !important;
    color: #4f46e5 !important;
    border: 1.5px solid #c7d2fe !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    height: 44px !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
}
.btn-secondary .stButton > button:hover { background: #eef2ff !important; }
.auth-footer {
    text-align: center; margin-top: 20px;
    font-size: 0.82rem; color: #64748b;
}
.role-badge {
    display: inline-block; padding: 3px 12px;
    border-radius: 20px; font-size: 0.72rem; font-weight: 600;
    background: #dbeafe; color: #1e40af;
    letter-spacing: 0.06em; text-transform: uppercase;
}
</style>
"""


# ═══════════════════════════════════════════════════════════════
# Helpers session BDD
# ═══════════════════════════════════════════════════════════════
def marquer_session_active(utilisateur: str, role: str) -> str:
    """
    Enregistre ou réactive la session en base.
    Génère un token unique et le retourne pour le stocker en cookie.
    """
    token = secrets.token_urlsafe(32)
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions_actives (utilisateur, role, active, token)
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
                active     = 1,
                role       = %s,
                token      = %s,
                updated_at = NOW()
            """,
            (utilisateur, role, token, role, token)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        import logging
        logging.error(f"❌ Erreur marquer_session_active({utilisateur}) : {e}")
    return token


def marquer_session_inactive(utilisateur: str):
    """
    Invalide la session en base (déconnexion).
    Abandonne également toutes les requêtes en cours de cet utilisateur.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE sessions_actives
               SET active = 0, token = NULL, updated_at = NOW()
               WHERE utilisateur = %s""",
            (utilisateur,)
        )
        conn.commit()

        cursor.execute(
            """UPDATE requetes
            SET statut   = 'abandonné',
                resultat = '{"erreur": "Requête abandonnée : utilisateur déconnecté."}'
            WHERE utilisateur = %s
            AND   statut IN ('en_attente', 'en_cours')""",
            (utilisateur,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        import logging
        logging.error(f"❌ Erreur marquer_session_inactive({utilisateur}) : {e}")


# ═══════════════════════════════════════════════════════════════
# Page — cookie reçu en paramètre depuis main.py
# ═══════════════════════════════════════════════════════════════
def app(cookie):   # ✅ plus de CookieController() ici
    apply_theme()
    st.markdown(CONNEXION_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("""
        <div class="auth-logo">
            <span class="auth-logo-icon">📡</span>
        </div>
        <div class="auth-title">VisuV CGAWEB</div>
        <div class="auth-subtitle">Connectez-vous pour accéder à votre espace.</div>
        """, unsafe_allow_html=True)

        with st.form("form_connexion"):
            username     = st.text_input("Nom d'utilisateur", placeholder="Votre identifiant")
            mot_de_passe = st.text_input("Mot de passe", placeholder="••••••••", type="password")
            submit       = st.form_submit_button("  Se connecter", use_container_width=True)

        if submit:
            username = username.strip()
            if not username or not mot_de_passe:
                st.error("❌ Veuillez remplir tous les champs.")
            else:
                success, role_bdd = verifier_identifiants(username, mot_de_passe)

                if success:
                    # 1. ON IDENTIFIE LE RÔLE RÉEL (sans l'écraser)
                    r_brut = str(role_bdd).strip().lower()
                    
                    if r_brut == "administrateur":
                        role_formatte = "Administrateur"
                    elif r_brut == "manager":
                        role_formatte = "Manager"
                    else:
                        role_formatte = "Utilisateur"

                    # 2. ENREGISTREMENT SESSION BDD
                    token = marquer_session_active(username, role_formatte)

                    # 3. STOCKAGE COOKIE
                    cookie.set("visuv_session", token, max_age=86400)

                    # 4. MISE À JOUR DU STATE
                    st.session_state["connecte"] = True
                    st.session_state["utilisateur_connecte"] = username
                    st.session_state["role_utilisateur"] = role_formatte

                    # 5. REDIRECTION SELON LE RÔLE
                    if role_formatte == "Administrateur":
                        st.session_state["page_active"] = "Tableau de bord"
                    elif role_formatte == "Manager":
                        st.session_state["page_active"] = "RPEManager"
                    else:
                        st.session_state["page_active"] = "Accueil"

                    # 6. VARIABLES PAR DÉFAUT
                    st.session_state.setdefault("sous_page_tableau", "Gestion Utilisateurs")
                    st.session_state.setdefault("req_id", None)
                    st.session_state.setdefault("requete_en_cours", False)
                    st.session_state.setdefault("type_recherche_actuel", None)
                    st.session_state.setdefault("dernier_resultat", None)

                    st.success(f"✅ Bienvenue, **{username}** !")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects.")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="auth-footer">Nouveau sur VisuV ?</div>', unsafe_allow_html=True)
        _, c, _ = st.columns([1, 2, 1])
        with c:
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button("Créer un compte", use_container_width=True, key="btn_vers_inscription"):
                st.session_state["page_active"] = "inscription"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    # Exécution directe (tests locaux) — cookie simulé minimal
    class _FakeCookie:
        def get(self, k):    return None
        def set(self, *a, **kw): pass
        def remove(self, k): pass
    app(_FakeCookie())