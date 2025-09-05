import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

from fonction import (
    charger_utilisateurs,
    enregistrer_utilisateur,
    modifier_utilisateur,
    supprimer_utilisateur,
    est_connecte
)

def app():
    # Configuration de la page doit être en premier
    st.set_page_config(page_title="Gestion des utilisateurs", layout="wide")
#
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
    # --- Initialisation des clés session_state ---
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None
    if "action_en_cours" not in st.session_state:
        st.session_state.action_en_cours = None
    if "ajout_expander_open" not in st.session_state:
        st.session_state.ajout_expander_open = False

    # Vérification connexion
    if not est_connecte():
        st.warning(" Vous devez être connecté pour accéder à cette page.")
        st.stop()
    #mettre la page dans un conteneur
    with st.container():
        st.title("👥 Gestion des utilisateurs")

        # Chargement utilisateurs
        df = charger_utilisateurs()

        # Nom utilisateur admin connecté
        admin_connecte = st.session_state.get("utilisateur_connecte", "")

        # Configuration AgGrid avec sélection unique par checkbox
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection("single", use_checkbox=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            height=300,
            width='100%',
            theme="streamlit",
            key="aggrid_utilisateurs"
        )

        # Gestion sécurisée selected_rows (peut être DataFrame ou liste)
        selected_rows = grid_response.get("selected_rows", [])

        if selected_rows is None:
            selected_rows = []
        elif isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient="records")

        if len(selected_rows) > 0:
            selected_username = selected_rows[0].get("username")
            if selected_username and selected_username in df["username"].values:
                idx = df[df["username"] == selected_username].index[0]
                st.session_state.selected_index = idx
            else:
                st.session_state.selected_index = None
        else:
            st.session_state.selected_index = None

        # Affichage boutons modifier / supprimer si un utilisateur est sélectionné
        if st.session_state.selected_index is not None:
            username_sel = df.at[st.session_state.selected_index, "username"]
            st.info(f"👤 Utilisateur sélectionné : **{username_sel}**")

            # Bloquer modification/suppression pour admin connecté sur son propre compte
            if username_sel == admin_connecte:
                role_sel = df.at[st.session_state.selected_index, "role"].lower()
                if role_sel == "admin":
                    st.warning("🔒 Vous ne pouvez pas modifier ou supprimer votre propre compte administrateur.")
                else:
                    col1, col2 = st.columns(2)
                    if col1.button(" Modifier"):
                        st.session_state.action_en_cours = "modifier"
                    if col2.button(" Supprimer"):
                        st.session_state.action_en_cours = "supprimer"
            else:
                col1, col2 = st.columns(2)
                if col1.button(" Modifier"):
                    st.session_state.action_en_cours = "modifier"
                if col2.button(" Supprimer"):
                    st.session_state.action_en_cours = "supprimer"

        # Formulaire modification utilisateur
        if st.session_state.action_en_cours == "modifier" and st.session_state.selected_index is not None:
            idx = st.session_state.selected_index
            st.subheader("🛠️ Modification de l'utilisateur")
            with st.form("form_modification", clear_on_submit=True):
                nom = st.text_input("Nom complet", value=df.at[idx, "nom"])
                username = df.at[idx, "username"]
                st.text_input("Nom d'utilisateur", value=username, disabled=True)
                code = st.text_input("Code", value=df.at[idx, "code"])
                telephone = st.text_input("Téléphone", value=df.at[idx, "telephone"])
                email = st.text_input("Email", value=df.at[idx, "email"])
                mot_de_passe = st.text_input("Nouveau mot de passe (laisser vide si inchangé)", type="password")
                role = st.selectbox("Rôle", ["Utilisateur", "Admin"], index=0 if df.at[idx, "role"] == "Utilisateur" else 1)
                confirmer = st.checkbox(" Confirmer la modification")

                col_form1, col_form2 = st.columns(2)
                enregistrer = col_form1.form_submit_button("💾 Enregistrer")
                annuler_modif = col_form2.form_submit_button("❌ Annuler")

                if annuler_modif:
                    st.session_state.action_en_cours = None
                    st.session_state.selected_index = None
                    st.rerun()

                if enregistrer:
                    if not confirmer:
                        st.warning("Veuillez confirmer la modification.")
                    else:
                        autres = df.drop(index=idx)
                        if (code in autres["code"].values or
                            telephone in autres["telephone"].values or
                            email in autres["email"].values):
                            st.error("📛 Téléphone, code ou email déjà utilisé.")
                        else:
                            modifier_utilisateur(idx, {
                                "nom": nom,
                                "code": code,
                                "telephone": telephone,
                                "email": email,
                                "mot_de_passe": mot_de_passe,
                                "role": role
                            })
                            st.success("✅ Utilisateur modifié avec succès.")
                            st.session_state.action_en_cours = None
                            st.session_state.selected_index = None
                            st.rerun()

        # Confirmation suppression utilisateur
        if st.session_state.action_en_cours == "supprimer" and st.session_state.selected_index is not None:
            idx = st.session_state.selected_index
            username = df.at[idx, "username"]
            st.warning(f"⚠️ Supprimer l'utilisateur **{username}** ?")
            col_yes, col_no = st.columns(2)
            if col_yes.button("✅ Oui, supprimer"):
                supprimer_utilisateur(idx)
                st.success(f"✅ Utilisateur **{username}** supprimé.")
                st.session_state.action_en_cours = None
                st.session_state.selected_index = None
                st.rerun()
            if col_no.button("❌ Non, annuler"):
                st.session_state.action_en_cours = None
                st.session_state.selected_index = None
                st.rerun()

        # Formulaire ajout utilisateur (expander)
        with st.expander("➕ Ajouter un utilisateur", expanded=st.session_state.ajout_expander_open):
            with st.form("ajout_formulaire"):
                nom = st.text_input("Nom complet")
                username = st.text_input("Nom d'utilisateur")
                code = st.text_input("Code")
                telephone = st.text_input("Téléphone")
                email = st.text_input("Email")
                mot_de_passe = st.text_input("Mot de passe", type="password")
                role = st.selectbox("Rôle", ["Utilisateur", "Admin"])
                confirmer_ajout = st.checkbox(" Confirmer l'ajout")

                if st.form_submit_button("➕ Ajouter"):
                    if not confirmer_ajout:
                        st.warning("Veuillez confirmer l'ajout.")
                    elif not all([nom, username, code, telephone, email, mot_de_passe]):
                        st.error("❌ Tous les champs sont obligatoires.")
                    elif username in df["telephone"].values:
                        st.error("❌ Le numéro de téléphone est déjà utilisé.")
                    elif code in df["code"].values or telephone in df["telephone"].values or email in df["email"].values:
                        st.error("❌ Téléphone, code ou email déjà utilisé.")
                    else:
                        ok, msg = enregistrer_utilisateur(nom, username, code, telephone, email, mot_de_passe, role)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.session_state.ajout_expander_open = False
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

if __name__ == "__main__":
    app()
