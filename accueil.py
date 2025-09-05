import streamlit as st
from file_attente import ajouter_requete
from resultatPages import app as resultatPages

def app():
    st.set_page_config(page_title="Accueil", layout="wide")

    # --- CSS personnalisé ---
    st.markdown("""
    <style>
        div[data-testid="stAppViewContainer"] { background: #E9ECF0; font-family: Arial, sans-serif; min-height: 100vh; }
        main[data-testid="stMain"] { background-color: #E9ECF0; padding: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; }
        .block-container { padding: 25px !important; margin: auto; background-color: #ffffff; border-radius: 12px; max-width: 900px; }
        h1, h2, h3, h4 { color: #333; }
        div[data-testid="stTextInput"] input { width: 100%; padding: 15px 20px; box-sizing: border-box; border: none; border-radius: 50px; outline: none; font-size: 16px; color: #333; box-shadow: inset 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 25px; }
        
    </style>
    """, unsafe_allow_html=True)

    if "utilisateur" in st.session_state:
        st.success(f"Bienvenue, {st.session_state['utilisateur']} !")

    st.title("🏠 Accueil")
    st.write("Choisissez un critère pour rechercher un abonné.")
    st.markdown("---")

    choix = st.selectbox("🔎 Rechercher par :", ["Numéro de décodeur", "Numéro d'abonné", "Numéro de téléphone"])

    # Champs selon le choix
    num_decodeur = num_abonne = suffixe =  prefixe = ""
    if choix == "Numéro de décodeur":
        num_decodeur = st.text_input("Entrez le numéro de décodeur (14 chiffres)", max_chars=14)
    elif choix == "Numéro d'abonné":
        num_abonne = st.text_input("Entrez le numéro d'abonné (8 chiffres)", max_chars=8)
    else:
        col1, col2 = st.columns([1,3])
        with col1:
            prefixe = st.text_input("Préfixe", value="00237", disabled=True)
        with col2:
            suffixe = st.text_input("Numéro (9 chiffres)", max_chars=9)

    if st.button("Rechercher"):
        print("🔹 Bouton recherche cliqué")
        valeur = None
        if choix == "Numéro de décodeur" and num_decodeur.isdigit() and len(num_decodeur) == 14:
            valeur = num_decodeur
        elif choix == "Numéro d'abonné" and num_abonne.isdigit() and len(num_abonne) == 8:
            valeur = num_abonne
        elif choix == "Numéro de téléphone" and suffixe.isdigit() and len(suffixe) == 9:
            valeur = f"{prefixe}{suffixe}"

        if valeur:
            print(f"✅ Valeur valide pour {choix} : {valeur}")

            # Stocker le numéro recherché dans le session_state
            st.session_state["numero_recherche"] = valeur

            # Ajouter la requête à la file
            try:
                print("🔹 Appel de ajouter_requete")
                nouvelle_req = ajouter_requete(
                    utilisateur=st.session_state.get("utilisateur_connecte", "inconnu"),
                    type_recherche=choix.lower().replace(" ", "_"),
                    valeur=valeur
                )
                print("🔹 Après ajout de la requête :", nouvelle_req)
            except Exception as e:
                print("❌ Erreur lors de l'ajout de la requête :", e)
                nouvelle_req = None

            # Stocker l'ID de la requête
            if nouvelle_req and "id" in nouvelle_req:
                st.session_state["requete_id"] = nouvelle_req["id"]
                print(f"📝 Nouvelle requête ajoutée - ID {nouvelle_req['id']}")
            else:
                print("⚠️ Aucune ID retournée par ajouter_requete")

            # Changer la page active et relancer Streamlit
            st.session_state["page_active"] = "ResultatPages"
            resultatPages()
            print("🔄 Redirection vers la page Résultats...")
            st.rerun()
            
        else:
            st.error("❌ Numéro invalide selon le critère choisi.")
