import streamlit as st
import re
from fonction import init_fichier_utilisateurs, enregistrer_utilisateur

# Constantes de validation
REGEX_PASSWORD = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).{8,12}$"
REGEX_TELEPHONE = r"^[0-9]{9}$"
REGEX_EMAIL = r"^[a-zA-Z0-9_.+-]+@gmail\.com$"

# Fonction de validation du mot de passe
def mot_de_passe_valide(mdp):
    erreurs = []
    if not (8 <= len(mdp) <= 12):
        erreurs.append("Le mot de passe doit contenir entre 8 et 12 caractères.")
    if not re.search(r"[A-Z]", mdp):
        erreurs.append("Le mot de passe doit contenir au moins une lettre majuscule.")
    if not re.search(r"[a-z]", mdp):
        erreurs.append("Le mot de passe doit contenir au moins une lettre minuscule.")
    if not re.search(r"[0-9]", mdp):
        erreurs.append("Le mot de passe doit contenir au moins un chiffre.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", mdp):
        erreurs.append("Le mot de passe doit contenir au moins un symbole spécial.")
    return not erreurs, erreurs

def page_inscription():
    st.set_page_config(page_title="Inscription", layout="wide")
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
    #formulaire d'inscription
    with st.form("formulaire_inscription"):
        st.title("Inscription")

        # Initialisation des champs
        #with st.form("formulaire_inscription"):
        #st.subheader("Informations de l'utilisateur")
        nom = st.text_input("Nom complet", key="nom_complet")
        username = st.text_input("Nom d'utilisateur", key="username")
        code = st.text_input("Code", key="code")
        telephone = st.text_input("Téléphone", key="telephone", max_chars=9)
        email = st.text_input("Email", key="email")
        mot_de_passe = st.text_input("Mot de passe", type="password", max_chars=12, key="mdp1")
        mot_de_passe2 = st.text_input("Confirmer le mot de passe", type="password", max_chars=12, key="mdp2")

        submit = st.form_submit_button("S'inscrire")

        # Style champs en erreur
        st.markdown("""
            <style>
                input:focus:invalid, input:invalid {
                    border: 2px solid red;
                }
            </style>
        """, unsafe_allow_html=True)

        # Validation à la soumission
        if submit:
            nom, username, code, telephone, email = nom.strip(), username.strip(), code.strip(), telephone.strip(), email.strip().lower()

            if not all([nom, username, code, telephone, email, mot_de_passe, mot_de_passe2]):
                st.error("❌ Tous les champs sont obligatoires.")
            elif mot_de_passe != mot_de_passe2:
                st.error("❌ Les mots de passe ne correspondent pas.")
            elif not re.match(REGEX_EMAIL, email):
                st.error("❌ L'email doit être une adresse valide se terminant par @gmail.com.")
            elif not re.match(REGEX_TELEPHONE, telephone):
                st.error("❌ Le numéro de téléphone doit contenir exactement 9 chiffres.")
            else:
                valid, erreurs_mdp = mot_de_passe_valide(mot_de_passe)
                if not valid:
                    st.error(f"❌ {erreurs_mdp[0]}")
                else:
                    init_fichier_utilisateurs()
                    ok, msg = enregistrer_utilisateur(nom, username, code, telephone, email, mot_de_passe, "Utilisateur")
                    if ok:
                        st.success(msg)
                        st.session_state.utilisateur_connecte = username
                        st.session_state.role = "Utilisateur"  # ou autre selon logique
                        st.session_state.page_active = "Accueil"
                        st.rerun()
                    else:
                        st.error(msg)

        # ✅ Lien vers la page de connexion
    st.write("Vous avez déjà un compte ?")
    if st.button("Se connecter"):
        st.session_state.page_active = "Connexion"
        st.rerun()

# Point d’entrée
if __name__ == "__main__":
    page_inscription()
