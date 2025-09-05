import streamlit as st
import os
import time
from dotenv import load_dotenv
from fonction import charger_comptes, sauvegarder_comptes, CompteCGA
from fonction import tester_connexion_cgaweb  # importe ta fonction de test de connexion

# Charger les variables d'environnement du fichier .env
load_dotenv()

def app():
    from fonction import est_connecte
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.set_page_config(page_title="Configuration CGAWEB", layout="centered")

    # === CSS personnalisé ===
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"] {
            background: #E9ECF0;
            font-family: Arial, sans-serif;
            min-height: 100vh;
        }
        main[data-testid="stMain"] {
            background-color: #E9ECF0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .block-container {
            padding: 25px !important;
            margin: auto;
            background-color: #ffffff;
            border-radius: 12px;
            max-width: 900px;
        }
        h1, h2, h3, h4 { color: #333; }
        div[data-testid="stTextInput"] input {
            width: 100%;
            padding: 15px 20px;
            box-sizing: border-box;
            border: none;
            border-radius: 50px;
            outline: none;
            font-size: 16px;
            color: #333;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }
        [data-testid="stForm"] [data-testid="stButton"] {
            width: 100%;
        }
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
            background-color: rgba(0,0,0,0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    #mettre le formulaire dans le conteneur
    with st.container():
        st.subheader("⚙️ Configuration CGAWEB")
        st.write("Cette page permet de gérer les comptes CGAWEB pour la connexion automatique.")
        st.write("Vous pouvez ajouter, modifier ou supprimer des comptes CGAWEB.")
        st.markdown("---")

        comptes = charger_comptes()  # liste d'objets CompteCGA
        compte_actif_user = st.session_state.get("cgaweb_user", None)

        if comptes:
            options = [f"{i+1}. {c.user}" for i, c in enumerate(comptes)]
            selected_option = st.selectbox("Choisissez un compte :", options)
            selected_index = options.index(selected_option)
            compte_selectionne = comptes[selected_index]

            st.markdown(f"**👤 Compte sélectionné :** `{compte_selectionne.user}`")

            col1, col2, col3 = st.columns(3)

            if col1.button(" Activer ce compte"):
                st.session_state["cgaweb_user"] = compte_selectionne.user
                st.session_state["cgaweb_pass"] = compte_selectionne.password
                st.success(f"Compte {compte_selectionne.user} activé.")

                # Mettre à jour les variables d'environnement pour que os.getenv() retourne ces valeurs
                os.environ["CGAWEB_USER"] = compte_selectionne.user
                os.environ["CGAWEB_PASS"] = compte_selectionne.password

                # Si tu veux vraiment que l'autre code continue à utiliser os.getenv()
                utilisateur = os.getenv("CGAWEB_USER")
                mot_de_passe = os.getenv("CGAWEB_PASS")
                
                st.rerun()

            if col2.button("✏️ Modifier ce compte"):
                st.session_state["modifier_index"] = selected_index
                st.rerun()

            if col3.button("🗑️ Supprimer ce compte"):
                comptes.pop(selected_index)
                sauvegarder_comptes(comptes)
                st.success("Compte supprimé.")
                st.rerun()
        else:
            st.info("Aucun compte CGAWEB enregistré pour le moment.")

        st.divider()

        index_modif = st.session_state.get("modifier_index", None)
        if index_modif is not None:
            st.subheader("✏️ Modifier un compte")
            compte = comptes[index_modif]
            utilisateur = st.text_input("👤 Nom d'utilisateur", value=compte.user)
            mot_de_passe = st.text_input("🔒 Mot de passe", type="password")
            if not mot_de_passe:
                mot_de_passe = compte.password
            test_connexion = st.checkbox("🧪 Tester la connexion", value=False)

            if st.button("Enregistrer"):
                if test_connexion:
                    url_fixe = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"
                    with st.spinner(f"Test de connexion pour l'utilisateur `{utilisateur}`..."):
                        if tester_connexion_cgaweb(url_fixe, utilisateur, mot_de_passe):
                            comptes[index_modif] = CompteCGA(utilisateur, mot_de_passe)
                            sauvegarder_comptes(comptes)
                            del st.session_state["modifier_index"]
                            st.success("Modifications enregistrées.")
                            st.rerun()
                        else:
                            st.error("❌ Échec de la connexion, vérifiez vos identifiants.")
                else:
                    # Si pas de test demandé, enregistrer quand même
                    comptes[index_modif] = CompteCGA(utilisateur, mot_de_passe)
                    sauvegarder_comptes(comptes)
                    del st.session_state["modifier_index"]
                    st.success("Modifications enregistrées.")
                    st.rerun()

        else:
            if "ajout_expander_open" not in st.session_state:
                st.session_state.ajout_expander_open = False

            with st.expander("➕ Ajouter un nouveau compte", expanded=st.session_state.ajout_expander_open):
                with st.form("ajout_formulaire"):
                    utilisateur = st.text_input("👤 Nom d'utilisateur")
                    mot_de_passe = st.text_input("🔒 Mot de passe", type="password")
                    test_connexion = st.checkbox("🧪 Tester la connexion")
                    submitted = st.form_submit_button("Ajouter")

                    if submitted:
                        if utilisateur and mot_de_passe:
                            if test_connexion:
                                url_fixe = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"
                                with st.spinner(f"Connexion en cours pour l'utilisateur `{utilisateur}`..."):
                                    if tester_connexion_cgaweb(url_fixe, utilisateur, mot_de_passe):
                                        comptes.append(CompteCGA(utilisateur, mot_de_passe))
                                        sauvegarder_comptes(comptes)
                                        st.success("Compte ajouté avec succès.")
                                        st.rerun()
                                    else:
                                        print("❌ Échec de la connexion, vérifiez vos identifiants.")
                            else:
                                # Pas de test demandé, mais on bloque quand même l'ajout pour éviter erreur
                                st.warning("⚠️ Vous devez cocher 'Tester la connexion' pour ajouter un compte.")
                        else:
                            st.warning("Veuillez remplir tous les champs.")
