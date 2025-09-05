import streamlit as st
from fonction import rechercher_par_decodeur, connexion_cgaweb, deconnexion_cgaweb
import base64
import os
from dotenv import load_dotenv

st.title("🔍 Résultat - Recherche par décodeur")
print("✅ Fonction app() de resultat_decodeur exécutée")

def app():
    from fonction import est_connecte
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        #st.stop()

    num_decodeur = st.session_state.get("num_decodeur", None)
    declenche = st.session_state.get("declenche_recherche_decodeur", False)

    if not num_decodeur or not declenche:
        st.warning("⚠️ Veuillez lancer une recherche depuis la page d'accueil.")
        if st.button("⬅️ Retour à l'accueil"):
            st.session_state.page_active = "Accueil"
            st.rerun()
        st.stop()

    st.info(f"📡 Recherche pour le décodeur : {num_decodeur}")

    load_dotenv()
    url = os.getenv("CGAWEB_URL")
    utilisateur = os.getenv("CGAWEB_USER")
    mot_de_passe = os.getenv("CGAWEB_PASS")

    screenshot_path = None  # Initialisation

    # Spinner contrôlé manuellement
    spinner_placeholder = st.empty()
    with spinner_placeholder.container():
        st.spinner("🔄 Connexion à CGAWEB et recherche en cours...")

    # Connexion
    driver, original_window, new_window = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)

    # Supprimer le spinner dès que la connexion est terminée
    spinner_placeholder.empty()

    if not driver:
        st.error("❌ Échec de la connexion à CGAWEB.")
        st.stop()

    try:
        res = rechercher_par_decodeur(driver, num_decodeur, original_window, new_window)

        if res:
            screenshot_path = f"fiche_abonne_{num_decodeur}.png"
            driver.set_window_size(1920, 1080)
            driver.save_screenshot(screenshot_path)

            st.success("✅ Résultat trouvé. Voici la fiche abonné :")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.button("⚡ Réactivation")
            with col2:
                st.button("🔐 Réinit. Code Parental")
            with col3:
                st.button("📊 Suivi Abonné")
            with col4:
                with open(screenshot_path, "rb") as img_file:
                    b64 = base64.b64encode(img_file.read()).decode()
                    href = f'<a href="data:file/png;base64,{b64}" download="{screenshot_path}">📥 Télécharger</a>'
                    st.markdown(href, unsafe_allow_html=True)

            st.image(screenshot_path, caption="Fiche abonné", use_column_width=True)
        else:
            st.error("❌ Aucun résultat trouvé pour ce numéro de décodeur.")

    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        st.error("❌ Erreur lors de la recherche.")

    finally:
        try:
            if driver:
                deconnexion_cgaweb(driver)
                driver.quit()
        except Exception as e:
            print(f"⚠️ Erreur lors de la fermeture du navigateur : {e}")

    st.session_state["declenche_recherche_decodeur"] = False

    if st.button("🏠 Retour"):
        st.session_state.page_active = "Accueil"
        st.rerun()
