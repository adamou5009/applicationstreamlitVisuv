import streamlit as st
from fonction import rechercher_par_abonne, connexion_cgaweb, deconnexion_cgaweb, charger_compte_actif
import base64
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("CGAWEB_URL")

# Charger le compte admin actif (depuis JSON via configure_cga)
charger_compte_actif()

utilisateur = st.session_state.get("cgaweb_user")
mot_de_passe = st.session_state.get("cgaweb_pass")

def app():
    from fonction import est_connecte
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    if not utilisateur or not mot_de_passe:
        st.error("❌ Aucun compte CGAWEB actif configuré. Veuillez contacter l'administrateur.")
        st.stop()

    st.title("🔍 Résultat - Recherche par abonné")

    num_abonne = st.session_state.get("num_abonne", None)
    declenche = st.session_state.get("declenche_recherche_abonne", False)

    if not num_abonne or not declenche:
        st.warning("⚠️ Aucune recherche d'abonné n'a été déclenchée. Veuillez revenir à la page d'accueil.")
        st.stop()

    st.info(f"📡 Recherche pour l'abonné : {num_abonne}")

    screenshot_path = None

    with st.spinner("🔄 Connexion à CGAWEB et recherche en cours..."):
        driver = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)
        try:
            res = rechercher_par_abonne(driver, num_abonne)
            if res:
                screenshot_path = f"fiche_abonne_{num_abonne}.png"
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
                st.error("❌ Aucun résultat trouvé pour ce numéro d’abonné.")
        except Exception as e:
            print(f"❌ Erreur : {e}")
            st.error("❌ Erreur lors de la recherche.")
        finally:
            deconnexion_cgaweb(driver)
            driver.quit()

    if screenshot_path and os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        print(f"🗑️ Fichier {screenshot_path} supprimé.")

    st.session_state["declenche_recherche_abonne"] = False

    if st.button("🏠 Retour"):
        st.session_state.page_active = "Accueil"
        st.rerun()
