import streamlit as st
import uuid

import connexion
import inscription
import accueil
import tableau_de_bord
import resultatPages
import configure_cga
import statistique
import gestionUtilisateur
import Rpemanager

# Dictionnaire des pages principales
PAGES_PRINCIPALES = {
    "Accueil": accueil,
    "Tableau de bord": tableau_de_bord,
}

# Dictionnaire des sous-pages du tableau de bord (accès Admin)
SOUS_PAGES_TABLEAU = {
    "Configuration CGAWEB": configure_cga,
    "Gestion Utilisateurs": gestionUtilisateur,
    "RPE Manager": Rpemanager,
    "Statistiques": statistique,
}

def main():
    st.set_page_config(page_title="Application CGAWEB", layout="wide")

    # --- Initialisation des variables de session ---
    if "connecte" not in st.session_state:
        st.session_state.connecte = False
    if "utilisateur_connecte" not in st.session_state:
        st.session_state.utilisateur_connecte = None
    if "role_utilisateur" not in st.session_state:
        st.session_state.role_utilisateur = None
    if "page_active" not in st.session_state:
        st.session_state.page_active = "Connexion"

    # --- Gestion connexion ---
    if not st.session_state.connecte:
        if st.session_state.page_active == "inscription":
            inscription.page_inscription()
        else:
            st.session_state.page_active = "Connexion"
            connexion.app()
        return

    # --- Utilisateur connecté ---
    role = st.session_state.role_utilisateur

    # --- Navigation principale ---
    st.sidebar.title("Navigation")

    if role == "Admin":
        pages_disponibles = list(PAGES_PRINCIPALES.keys())
    elif role == "Utilisateur":
        pages_disponibles = ["Accueil"]
    else:
        st.error("⛔ Rôle non reconnu.")
        st.stop()

    for page_name in pages_disponibles:
        if st.sidebar.button(page_name):
            st.session_state.page_active = page_name
            st.rerun()

    if role == "Admin" and st.sidebar.button("⚙️ Ouvrir les outils admin"):
        st.session_state.page_active = "Tableau de bord - sous"
        st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Déconnexion"):
        st.session_state.clear()
        st.rerun()

    # --- Gestion des pages ---
    if st.session_state.page_active == "Accueil":
        accueil.app()

    elif st.session_state.page_active == "ResultatPages":
        resultatPages.app()

    elif st.session_state.page_active == "Tableau de bord - sous":
        if role != "Admin":
            st.error("⛔ Accès réservé aux administrateurs.")
            st.stop()

        if "sous_page_tableau" not in st.session_state:
            st.session_state.sous_page_tableau = list(SOUS_PAGES_TABLEAU.keys())[0]

        sous_page = st.sidebar.radio(
            "📁 Outils Admin",
            list(SOUS_PAGES_TABLEAU.keys()),
            index=list(SOUS_PAGES_TABLEAU.keys()).index(st.session_state.sous_page_tableau)
        )

        if sous_page != st.session_state.sous_page_tableau:
            st.session_state.sous_page_tableau = sous_page
            st.rerun()

        SOUS_PAGES_TABLEAU[sous_page].app()

        if st.sidebar.button("🔙 Retour au tableau de bord"):
            st.session_state.page_active = "Tableau de bord"
            st.rerun()

    elif st.session_state.page_active in PAGES_PRINCIPALES:
        if st.session_state.page_active == "Tableau de bord" and role != "Admin":
            st.error("⛔ Accès réservé aux administrateurs.")
            st.stop()
        PAGES_PRINCIPALES[st.session_state.page_active].app()

    else:
        st.error("❌ Page inconnue.")


if __name__ == "__main__":
    main()
