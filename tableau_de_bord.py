from fonction import est_connecte
import streamlit as st

def app():
    # Vérifier si l'utilisateur est connecté
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.set_page_config(page_title="Tableau de bord", layout="wide")

    # === Interface et styles ===
    st.markdown("""
<style>
/* Sidebar container */
.stSidebar {
    width: 248px !important;
    background-color: #ffffff !important;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
    padding: 20px !important;
    box-sizing: border-box;
    display: flex !important;
    flex-direction: column !important;
}

/* Titre Navigation */
.stHeading h1, .stHeading h2 {
    color: rgba(49, 51, 63, 0.8) !important;
    font-size: 1.5rem !important;
    margin-bottom: 1rem !important;
}

/* Boutons secondaires */
.stButton > button[data-testid="stBaseButton-secondary"] {
    background-color: #e0e0e0 !important;
    border: none !important;
    padding: 12px 20px !important;
    margin: 3px 0 !important; /* réduit l’espace vertical */
    border-radius: 20px !important;
    color: #31333f !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    transition: background-color 0.3s ease !important;
    white-space: nowrap !important; /* empêche le texte de passer à la ligne */
    overflow: hidden !important;     /* cache débordement éventuel */
    text-overflow: ellipsis !important; /* ajoute "..." si trop long */
}

/* Hover bouton */
.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background-color: #d1d1d1 !important;
}

/* Bouton se déconnecter (dernier bouton) */
.stButton > button[data-testid="stBaseButton-secondary"].disconnect {
    background-color: #ff5c5c !important;
    color: white !important;
    margin-top: auto !important;
}

.stButton > button[data-testid="stBaseButton-secondary"].disconnect:hover {
    background-color: #218838 !important;
}

</style>
""", unsafe_allow_html=True)

    # === Barre latérale ===
    with st.sidebar:
        st.title("Navigation")
        
        # Initialiser la sous-page tableau de bord par défaut
        if "sous_page_tableau" not in st.session_state:
            st.session_state.sous_page_tableau = "Accueil"

        # Liste des sous-pages disponibles dans le tableau de bord (ordre alphabétique)
        sous_pages = [
            "Accueil",
            "Configuration CGAWEB",
            "Gestion Utilisateurs",
            "RPE Manager",
            "Statistiques"
        ]

        for page in sous_pages:
            if st.button(page, use_container_width=True):
                st.session_state.sous_page_tableau = page
                st.rerun()

        st.markdown("---")

        # Bouton déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.clear()
            st.session_state.page_active = "Connexion"  # Ou autre page de login
            st.rerun()

    # === Affichage dynamique de la sous-page choisie ===
    page = st.session_state.sous_page_tableau 
    
    # Importation et affichage de la page sélectionnée
    if page == "Accueil":
        import accueil
        accueil.app()
    elif page == "Configuration CGAWEB":
        import configure_cga
        configure_cga.app()
    elif page == "Gestion Utilisateurs":
        import gestionUtilisateur
        gestionUtilisateur.app()
    elif page == "RPE Manager":
        import Rpemanager
        Rpemanager.extraction()
    elif page == "Statistiques":
        import statistique
        statistique.app()
    else:
        st.error(f"❌ Page inconnue : {page}")
        st.stop()
    
if __name__ == "__main__":
    app()