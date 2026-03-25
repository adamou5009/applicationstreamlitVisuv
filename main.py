import streamlit as st
import os
from streamlit_cookies_controller import CookieController

# =========================================================
# 1. PAGE CONFIG — DOIT ÊTRE EN PREMIER ABSOLU
# =========================================================
st.set_page_config(
    page_title="VisuV CGAWEB",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. COOKIE CONTROLLER — après set_page_config
# =========================================================
cookie = CookieController()

# =========================================================
# 3. NETTOYAGE DES VERROUS
# =========================================================
def nettoyer_vieux_verrous():
    for i in range(1, 3):
        lock_file = f"worker_{i}.lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"Vieux verrou {lock_file} supprimé.")
            except Exception as e:
                print(f"Erreur nettoyage : {e}")

if "verrous_nettoyes" not in st.session_state:
    nettoyer_vieux_verrous()
    st.session_state["verrous_nettoyes"] = True

# =========================================================
# 4. THÈME GLOBAL
# =========================================================
from theme import apply_theme
apply_theme()

# =========================================================
# 5. RESTAURATION SESSION DEPUIS COOKIE
# =========================================================
def page_defaut_par_role(role: str) -> str:
    if role == "Administrateur":
        return "Tableau de bord"
    return "Accueil"

def restaurer_session_depuis_cookie():
    if st.session_state.get("connecte"):
        return

    token = cookie.get("visuv_session")
    if not token:
        return

    try:
        from file_attente import get_db_connection
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT utilisateur, role FROM sessions_actives WHERE token = %s AND active = 1",
            (token,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            st.session_state["connecte"]             = True
            st.session_state["utilisateur_connecte"] = row["utilisateur"]
            st.session_state["role_utilisateur"]     = row["role"]
            st.session_state.setdefault("page_active",            page_defaut_par_role(row["role"]))
            st.session_state.setdefault("sous_page_tableau",      "Gestion Utilisateurs")
            st.session_state.setdefault("req_id",                 None)
            st.session_state.setdefault("requete_en_cours",       False)
            st.session_state.setdefault("type_recherche_actuel",  None)
            st.session_state.setdefault("dernier_resultat",       None)
        else:
            cookie.remove("visuv_session")

    except Exception as e:
        import logging
        logging.error(f"❌ Erreur restauration session : {e}")

restaurer_session_depuis_cookie()

# =========================================================
# 6. INITIALISATION SESSION STATE (si pas restauré)
# =========================================================
if "connecte" not in st.session_state:
    st.session_state.update({
        "connecte":               False,
        "utilisateur_connecte":   None,
        "role_utilisateur":       None,
        "page_active":            "Connexion",
        "sous_page_tableau":      "Gestion Utilisateurs",
        "req_id":                 None,
        "requete_en_cours":       False,
        "type_recherche_actuel":  None,
        "dernier_resultat":       None,
    })

# =========================================================
# 7. LANCEMENT AUTOMATIQUE DES WORKERS
# =========================================================
from file_attente import demarrage_permanent_workers
demarrage_permanent_workers()

# =========================================================
# 8. POINT D'ENTRÉE PRINCIPAL
# =========================================================
def main():

    # ── Font Awesome ──────────────────────────────────────
    st.markdown("""
    <link rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
          crossorigin="anonymous" referrerpolicy="no-referrer" />
    """, unsafe_allow_html=True)

    # ── Authentification ──────────────────────────────────
    if not st.session_state.connecte:
        import connexion
        import inscription

        st.markdown(
            """
            <div style="padding:20px;background:#fef3c7;border:1px solid #fde68a;
                        border-radius:10px;margin-bottom:16px;">
                <i class="fa-solid fa-circle-exclamation" style="color:#b45309;margin-right:8px;"></i>
                Veuillez vous connecter pour accéder aux fonctionnalités.
            </div>
            """, unsafe_allow_html=True
        )

        if st.session_state.page_active == "inscription":
            inscription.page_inscription()
        else:
            connexion.app(cookie)

        # ⚠️ Ici on **n’utilise plus st.stop()**
        # On met juste un return pour ne pas exécuter le routage des pages
        return

    # ── Chargement des modules ────────────────────────────
    import accueil
    import tableau_de_bord
    import configure_cga
    import gestionUtilisateur
    import Rpemanager
    import resultat_abonne
    import resultat_decodeur
    import resultat_telephone
    import profil
    import pageExtration

    role        = st.session_state.role_utilisateur
    est_admin   = (role == "Administrateur")
    est_manager = (role == "Manager")

    # =========================================================
    # NAVIGATION SIDEBAR
    # =========================================================
    with st.sidebar:

        st.markdown("""
        <style>
        section[data-testid="stSidebar"] button {
            border-radius: 8px !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            height: 40px !important;
            margin-bottom: 4px !important;
            box-shadow: none !important;
            text-align: left !important;
        }
        section[data-testid="stSidebar"] button:hover {
            background: #eef2ff !important;
            border-color: #c7d2fe !important;
            color: #4f46e5 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Logo / titre ──────────────────────────────────
        st.markdown("""
        <div style="padding:8px 0 16px;">
            <div style="font-family:'Playfair Display',serif;font-size:1.25rem;
                        font-weight:700;color:#4f46e5;letter-spacing:0.02em;
                        display:flex;align-items:center;gap:8px;">
                <i class="fa-solid fa-satellite-dish"
                   style="font-size:1.1rem;color:#6366f1;"></i>
                VisuV CGAWEB
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Badge couleur selon le rôle ───────────────────
        if est_admin:
            badge_bg    = "#dbeafe"
            badge_color = "#1e40af"
            badge_icon  = "fa-shield-halved"
        elif est_manager:
            badge_bg    = "#fef3c7"
            badge_color = "#92400e"
            badge_icon  = "fa-user-tie"
        else:
            badge_bg    = "#f3e8ff"
            badge_color = "#6b21a8"
            badge_icon  = "fa-user"

        # ── Bandeau utilisateur connecté ──────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#eef2ff,#e0e7ff);
                    border:1px solid #c7d2fe;border-radius:10px;
                    padding:12px 14px;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <i class="fa-solid fa-circle-user"
                   style="color:#6366f1;font-size:0.85rem;"></i>
                <span style="font-size:0.72rem;font-weight:600;color:#6366f1;
                             text-transform:uppercase;letter-spacing:0.1em;">
                    Connecté
                </span>
            </div>
            <div style="font-size:0.9rem;font-weight:600;color:#1e293b;">
                {st.session_state.utilisateur_connecte}
            </div>
            <div style="margin-top:4px;">
                <span style="background:{badge_bg};color:{badge_color};padding:2px 8px;
                             border-radius:10px;font-size:0.68rem;font-weight:600;">
                    <i class="fa-solid {badge_icon}" style="margin-right:4px;"></i>{role}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation commune ────────────────────────────
        if st.button("Mon profil", key="btn_open_profil", use_container_width=True):
            st.session_state.page_active = "Profil"
            st.rerun()

        if st.button("Accueil", key="nav_accueil", use_container_width=True):
            st.session_state.page_active      = "Accueil"
            st.session_state.req_id           = None
            st.session_state.requete_en_cours = False
            st.session_state.dernier_resultat = None
            st.session_state.screenshot_bytes = None
            st.rerun()

        # ── Section Manager ───────────────────────────────
        if est_manager:
            st.markdown("""
            <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;
                        text-transform:uppercase;letter-spacing:0.15em;
                        margin:16px 0 8px;padding-left:2px;
                        display:flex;align-items:center;gap:6px;">
                <i class="fa-solid fa-user-tie" style="font-size:0.7rem;color:#d97706;"></i>
                Manager
            </div>
            """, unsafe_allow_html=True)

            if st.button("RPE Manager", key="nav_RPEManager_mgr", use_container_width=True):
                st.session_state.page_active       = "RPEManager"
                st.session_state.sous_page_tableau = "RPE Manager"
                st.rerun()

        # ── Section Administration ────────────────────────
        if est_admin:
            st.markdown("""
            <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;
                        text-transform:uppercase;letter-spacing:0.15em;
                        margin:16px 0 8px;padding-left:2px;
                        display:flex;align-items:center;gap:6px;">
                <i class="fa-solid fa-screwdriver-wrench"
                   style="font-size:0.7rem;"></i>
                Administration
            </div>
            """, unsafe_allow_html=True)

            if st.button("Tableau de bord", key="nav_dashboard", use_container_width=True):
                st.session_state.page_active = "Tableau de bord"
                st.rerun()

            if st.button("Configuration CGAWEB", key="nav_Configuration", use_container_width=True):
                st.session_state.page_active       = "Configuration"
                st.session_state.sous_page_tableau = "Configuration CGAWEB"
                st.rerun()

            if st.button("Gestion Utilisateurs", key="nav_Utilisateurs", use_container_width=True):
                st.session_state.page_active       = "Utilisateurs"
                st.session_state.sous_page_tableau = "Gestion Utilisateurs"
                st.rerun()

            if st.button("RPE Manager", key="nav_RPEManager", use_container_width=True):
                st.session_state.page_active       = "RPEManager"
                st.session_state.sous_page_tableau = "RPE Manager"
                st.rerun()

            if st.button("Extraction Alonwa", key="nav_extraction_alonwa", use_container_width=True):
                st.session_state.page_active       = "Extraction Alonwa"
                st.session_state.sous_page_tableau = "Extraction Alonwa"
                st.rerun()

            # ── Alerte déblocage CGAWEB ───────────────────
            # Visible uniquement si le système est bloqué suite à saturation.
            # L'admin doit intervenir manuellement pour relancer les workers.
            try:
                from file_attente import get_db_connection, lancer_worker
                from file_attente import reset_saturation_cgaweb, _est_cgaweb_bloque

                if _est_cgaweb_bloque():
                    # Lire le détail du blocage (raison + horodatage)
                    conn   = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT raison, bloque_at FROM cgaweb_statut WHERE id = 1")
                    info = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    raison    = info["raison"]    if info else "Raison inconnue"
                    bloque_at = info["bloque_at"] if info else "—"

                    # Bandeau d'alerte rouge dans la sidebar
                    st.markdown(f"""
                    <div style="background:#fef2f2;border:1px solid #fca5a5;
                                border-radius:10px;padding:12px 14px;margin:12px 0 4px;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <i class="fa-solid fa-circle-exclamation"
                               style="color:#dc2626;font-size:0.85rem;"></i>
                            <span style="font-size:0.72rem;font-weight:700;color:#dc2626;
                                         text-transform:uppercase;letter-spacing:0.08em;">
                                CGAWEB bloqué
                            </span>
                        </div>
                        <div style="font-size:0.75rem;color:#7f1d1d;line-height:1.4;">
                            {raison}
                        </div>
                        <div style="font-size:0.68rem;color:#b91c1c;margin-top:4px;">
                            Depuis : {bloque_at}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        "Débloquer et relancer",
                        key="btn_debloquer_cgaweb",
                        use_container_width=True,
                        type="primary"
                    ):
                        if reset_saturation_cgaweb():
                            lancer_worker()
                            st.success("✅ Système débloqué. Workers relancés.")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors du déblocage.")

            except Exception as e:
                # Non bloquant — si la table n'existe pas encore, on ignore silencieusement
                import logging
                logging.warning(f"⚠️ Vérification statut CGAWEB échouée : {e}")

        # ── Séparateur + Déconnexion ──────────────────────
        st.markdown(
            '<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">',
            unsafe_allow_html=True,
        )

        if st.button("Deconnexion", key="nav_logout", use_container_width=True):
            from connexion import marquer_session_inactive
            marquer_session_inactive(st.session_state.utilisateur_connecte)
            cookie.remove("visuv_session")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # =========================================================
    # ROUTAGE DES PAGES
    # =========================================================
    current_page = st.session_state.page_active

    if   current_page == "resultat_abonne":    resultat_abonne.app()
    elif current_page == "resultat_decodeur":  resultat_decodeur.app()
    elif current_page == "resultat_telephone": resultat_telephone.app()
    elif current_page == "Configuration":      configure_cga.app()
    elif current_page == "Utilisateurs":       gestionUtilisateur.app()
    elif current_page == "Tableau de bord":    tableau_de_bord.app()
    elif current_page == "Extraction Alonwa":  pageExtration.app()
    elif current_page == "Profil":             profil.app()
    elif current_page == "RPEManager":
        if est_admin or est_manager:
            Rpemanager.app()
        else:
            st.session_state.page_active = "Accueil"
            st.rerun()
    else:
        accueil.app()


# =========================================================
# 9. PING SESSION
# =========================================================
def ping_session():
    if not st.session_state.get("connecte"):
        return
    try:
        from file_attente import get_db_connection
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions_actives SET updated_at = NOW() WHERE utilisateur = %s AND active = 1",
            (st.session_state.utilisateur_connecte,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    ping_session()
    main()