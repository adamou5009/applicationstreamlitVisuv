import streamlit as st
from fonction import est_connecte, verifier_identifiants

def app():
    
    # Afficher le titre uniquement si on est sur la page connexion
    if st.session_state.get("page_active", "Connexion") == "Connexion":
        st.set_page_config(page_title="Connexion", layout="centered")

        # 💄 CSS appliqué uniquement à la page connexion
        st.markdown("""
    <style>
                    
    /* Style général de l'application */
    div[data-testid="stAppViewContainer"] {
        background: #E9ECF0;
        font-family: Arial, sans-serif;
    }

    /* Zone centrale du formulaire */
    .stForm {
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
        padding: 40px;
        color: #333;
        max-width: 400px;
        margin: 50px auto;
    }

    /* Titre du formulaire */
    h1 {
        font-size: 28px;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-bottom: 25px;
    }

    /* Champs de texte et de mot de passe */
    div[data-testid="stTextInput"] input {
        width: 100%;
        padding: 15px 20px;
        box-sizing: border-box;
        border: none;
        border-radius: 50px;
        outline: none;
        font-size: 16px;
        color: #333;
        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }

    /* Bouton "Se connecter" */
    button[kind="secondaryFormSubmit"] {
        width: 100% !important;
        padding: 15px 20px !important; /* L'important a été déplacé */
        box-sizing: border-box;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        color: white;
        background: black;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    /* Effet au survol du bouton "Se connecter" */
    button[kind="secondaryFormSubmit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 20px rgba(0, 0, 0, 0.3);
    }

    /* Conteneur pour centrer le bouton secondaire */
    div[data-testid="stVerticalBlock"] > div:last-child {
        display: flex;
        justify-content: center;
    }

    /* Bouton "Créer un compte" */
    button[kind="secondary"] {
        background-color: transparent !important;
        color: #333 !important;
        border: 1px solid #333 !important;
        border-radius: 50px;
        padding: 10px 20px;
        margin-top: 15px;
        transition: all 0.3s ease;
    }

    button[kind="secondary"]:hover {
        background-color: rgba(0, 0, 0, 0.1) !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # Si déjà connecté, redirection automatique
    if est_connecte():
        role = st.session_state.get("role", "").lower()
        if role == "admin":
            st.session_state["page_active"] = "Tableau de bord"
            import tableau_de_bord
            tableau_de_bord.app()
        elif role == "utilisateur":
            st.session_state["page_active"] = "Accueil"
            import accueil
            accueil.app()
        else:
            st.error("❗ Rôle inconnu. Veuillez vous reconnecter.")
            st.session_state.clear()
            st.rerun()
        st.stop()

    # Formulaire de connexion
    #st.title("Connexion")
    with st.form("form_connexion"):
        st.title("Connexion")
        username = st.text_input("Nom d'utilisateur")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        bouton = st.form_submit_button("Se connecter", use_container_width=True)

    if bouton:
        # Accès spécial admin
        if username == "admin" and mot_de_passe == "admin":
            st.session_state["utilisateur_connecte"] = "admin"
            st.session_state["role"] = "admin"
            st.session_state["page_active"] = "Tableau de bord"
            st.success("✅ Connexion réussie en tant qu'administrateur.")
            st.rerun()

        # Vérification normale
        success, role = verifier_identifiants(username, mot_de_passe)
        if success:
            st.session_state["utilisateur_connecte"] = username
            st.session_state["role"] = role.lower()
            st.session_state["page_active"] = "Tableau de bord" if role.lower() == "admin" else "Accueil"
            st.success("✅ Connexion réussie.")
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects.")

    # Bouton vers inscription
    if st.button("Créer un compte"):
        st.session_state["page_active"] = "inscription"
        st.rerun()
    st.markdown("---")
    
