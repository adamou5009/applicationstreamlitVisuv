import streamlit as st
from fonction import rechercher_par_telephone, connexion_cgaweb, deconnexion_cgaweb
import os
from dotenv import load_dotenv
import pandas as pd

def app():
    from fonction import est_connecte
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    #st.set_page_config(page_title="🔍 Résultat téléphone", layout="centered")
    st.subheader("🔍 Résultat - Recherche par téléphone")

    num_telephone = st.session_state.get("num_telephone", None)
    declenche = st.session_state.get("declenche_recherche_tel", False)

    if not num_telephone or not declenche:
        st.warning("⚠️ Aucune recherche par téléphone n'a été déclenchée. Veuillez revenir à la page d'accueil.")
        st.stop()

    st.info(f"📡 Recherche pour le numéro : {num_telephone}")

    load_dotenv()
    url = os.getenv("CGAWEB_URL")
    utilisateur = os.getenv("CGAWEB_USER")
    mot_de_passe = os.getenv("CGAWEB_PASS")

    with st.spinner("🔄 Connexion à CGAWEB et récupération des données..."):
        driver = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)
        donnees = rechercher_par_telephone(driver, num_telephone)
        deconnexion_cgaweb(driver)

    if not donnees:
        st.error("❌ Aucun résultat trouvé pour ce numéro.")
        st.stop()

    colonnes = [
        "Abonné", "C.", "Nom", "Prénom", "Pays", "Code postal",
        "Ville", "Adresse", "Option majeure", "Annulé", "Ret. CI", "Société"
    ]

    df = pd.DataFrame(donnees, columns=colonnes)

    for i, row in df.iterrows():
        cols = st.columns(len(colonnes))
        if cols[0].button(row["Abonné"], key=f"btn_abonne_{i}"):
            st.session_state["num_abonne"] = row["Abonné"]
            st.session_state["declenche_recherche_abonne"] = True
            st.session_state.page_active = "Résultats Abonnés"
            st.rerun()
        for j, col_name in enumerate(colonnes[1:], start=1):
            cols[j].write(row[col_name])

    # Remise à False du flag de recherche pour éviter ré-exécution inutile
    st.session_state["declenche_recherche_tel"] = False
    # Bouton pour revenir à l'accueil
    if st.button("🏠 Retour"):
        st.session_state.page_active = "Accueil"
        st.rerun()