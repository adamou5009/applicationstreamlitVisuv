import streamlit as st
from fonction import rechercher_par_abonne, rechercher_par_decodeur
import os
# cette page utilise la fiche_abonne.py pour afficher les informations d'un abonné elle tutilise les identifiants de connexion cgaweb de la session en cours
from dotenv import load_dotenv
def app():
    from fonction import est_connecte
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    #st.set_page_config(page_title="📊 Suivi Abonné", layout="centered")
    st.title("📊 Suivi Abonné")
    st.markdown("---")
    #affichage du des liste des informations de l'abonné
    from fonction import extraction_suivi_abonne, afficher_suivi_abonne
    load_dotenv()
    url = os.getenv("CGAWEB_URL")
    utilisateur = os.getenv("CGAWEB_USER")
    mot_de_passe = os.getenv("CGAWEB_PASS")
    # cette page est accessible depuis la page resultat_decodeur.py et resultat_abonne.py pour afficher les informations d'un abonné extraction_suivi_abonne
    num_abonne = st.session_state.get("num_abonne", None)   
    num_decodeur = st.session_state.get("num_decodeur", None)
    if not num_abonne and not num_decodeur:
        st.warning("⚠️ Veuillez lancer une recherche depuis la page d'accueil.")
        if st.button("⬅️ Retour à l'accueil"):
            st.session_state.page_active = "Accueil"
            st.rerun()
        st.stop()
    # Vérification de la session