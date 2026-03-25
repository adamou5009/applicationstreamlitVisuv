import streamlit as st
import pandas as pd
from fonction import (
    connexion_cgaweb,
    deconnexion_cgaweb,
    resultatsmart,
    arret_urgence,
    est_connecte,
    identifiants_cgaweb_rpe,
    traiter_decodeurs_rapide
)

def format_colonne(col):
    """Transforme nom_colonne en Nom Colonne pour l'affichage"""
    return " ".join([mot.capitalize() for mot in col.replace("-", "_").split("_")])

def app():
    #st.set_page_config(page_title="Extraction CGAWEB", layout="wide")

    # --- CSS Global et personnalisé ---
    st.markdown("""
    <style>
    main[data-testid="stMain"] { padding: 2rem; flex-grow: 1; }
    .css-1d391kg { background-color: #f0f2f6; }
    body-box { display: flex !important; flex-direction: column !important; min-height: 100vh !important; }
    #stMainBlockContainer { background-color: #ffffff !important; border-radius: 12px; padding: 24px; box-shadow: 2px 2px 6px rgba(0,0,0,0.08); }
    main[data-testid="stAppViewContainer"] > div:first-child { padding: 10px 20px !important; margin: 0 auto !important; }
    footer { flex-shrink: 0 !important; text-align: center; font-size: 14px; color: #666; padding: 10px 0; }
    .header-box { background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: center; box-shadow: 2px 2px 6px rgba(0,0,0,0.08); }
    .main-title { color: #222; font-weight: 700; margin: 0; }
    .separator { border: none; border-bottom: 1px solid #ddd; margin: 15px 0 25px 0; }
    .instructions-text { background-color: #fefefe; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 16px; color: #444; }
    .results-section { background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-top: 25px; box-shadow: 2px 2px 6px rgba(0,0,0,0.05); }
    .download-button-container { margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

    # --- Vérification connexion ---
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    with st.container():

        st.markdown("""
        <div class="header-box">
            <h3 class="main-title">EXTRACTION DES INFORMATIONS DES ABONNÉS</h3>
        </div>
        <hr class="separator">
        """, unsafe_allow_html=True)

        url = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"

        # --- Initialisation des états ---
        for key in ["traitement_lance", "stop_processing", "traitement_en_cours"]:
            if key not in st.session_state:
                st.session_state[key] = False

        # --- Identifiants temporaires ---
        if "rpe_user" not in st.session_state or "rpe_pass" not in st.session_state:
            with st.form("form_rpe_login"):
                st.text("Définir les identifiants CGAWEB")
                user = st.text_input("Nom d'utilisateur CGAWEB")
                pwd = st.text_input("Mot de passe CGAWEB", type="password")
                submitted = st.form_submit_button("Se connecter")
            if submitted:
                if not user or not pwd:
                    st.warning("⚠️ Veuillez remplir les deux champs.")
                else:
                    st.session_state.rpe_user = user
                    st.session_state.rpe_pass = pwd
                    st.success("✅ Identifiants enregistrés.")
                    st.rerun()
            st.stop()

        utilisateur, mot_de_passe = identifiants_cgaweb_rpe()

        # --- Instructions ---
        st.markdown("""
        <div class="instructions-text">
            <p>Importez un fichier Excel contenant la colonne : <code>numéro de décodeur</code>.</p>
            <p>Sélectionnez les informations que vous souhaitez extraire.</p>
        </div>
        """, unsafe_allow_html=True)

        # --- Upload fichier ---
        fichier = st.file_uploader("📂 Choisissez un fichier Excel", type=["xlsx"])
        if fichier:
            df = pd.read_excel(fichier)
            if "numéro de décodeur" not in df.columns:
                st.error("❌ La colonne 'numéro de décodeur' est absente.")
                return

            colonnes_possibles = [
                "nom_abonne", "numero_abonne", "date_recrutement",
                "num_distributeur", "nom_distributeur",
                "telephone", "telephone_2", "fin_abonnement",
                "statut", "detail_statut", "jours_restants"
            ]

            colonnes_a_extraire = st.multiselect(
                "Sélectionnez les informations à extraire",
                options=colonnes_possibles,
                format_func=format_colonne,
                default=["nom_abonne", "numero_abonne", "telephone", "fin_abonnement", "statut"]
            )

            # --- Vérification dépendance colonnes ---
            if ("detail_statut" in colonnes_a_extraire or "jours_restants" in colonnes_a_extraire) and "statut" not in colonnes_a_extraire:
                st.warning("⚠️ Pour extraire 'Detail statut' ou 'Jours restants', 'Statut' doit être sélectionné.")
                colonnes_a_extraire = [c for c in colonnes_a_extraire if c not in ["detail_statut", "jours_restants"]]

            # --- Bouton de lancement ---
            lancer = st.button("🚀 Lancer le traitement")
            if lancer:
                st.session_state.traitement_lance = True

            if st.session_state.traitement_lance:
                st.success("✅ Traitement lancé !")
                st.session_state.traitement_en_cours = True

                progress_bar = st.progress(0)
                statut_txt = st.empty()
                total = len(df)
                st.info(f"Nombre de décodeurs à traiter : {total}")
                resultats = []

                driver = None
                try:
                    driver, original_window, new_window = connexion_cgaweb(url, utilisateur, mot_de_passe)
                    if not driver:
                        st.error("❌ Échec de connexion à CGAWEB.")
                    else:
                        resultats = traiter_decodeurs_rapide(
                            driver, df, original_window, new_window, colonnes_a_extraire,
                            statut_txt=statut_txt, progress_bar=progress_bar
                        )
                except Exception as e:
                    st.error(f"Erreur durant le traitement : {e}")
                finally:
                    if driver:
                        try:
                            deconnexion_cgaweb(driver)
                        except Exception as e:
                            st.warning(f"Erreur lors de la déconnexion : {e}")

                # --- Affichage et téléchargement ---
                if resultats:
                    output, nom_fichier = resultatsmart(resultats, colonnes_a_extraire)
                    st.success("✅ Traitement terminé !")

                    df_resultats = pd.DataFrame(resultats).astype(str)

                    # Stylisation statut
                    colonnes_a_styler = [col for col in ["statut"] if col in df_resultats.columns]
                    def colorer_statut(val):
                        if val == "Actif": return "background-color: #d4edda; color: #155724;"
                        elif val == "Échu": return "background-color: #f8d7da; color: #721c24;"
                        elif val in ["À échoir", "Échu dans 5 jours"]: return "background-color: #fff3cd; color: #856404;"
                        return ""
                    styled_df = df_resultats.style.map(colorer_statut, subset=colonnes_a_styler) if colonnes_a_styler else df_resultats.style

                    # Renommer colonnes pour affichage
                    df_resultats_affichage = df_resultats.rename(columns=format_colonne)

                    st.markdown('<div class="results-section">', unsafe_allow_html=True)
                    st.subheader("📊 Résultats extraits :")
                    st.dataframe(df_resultats_affichage, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="download-button-container">', unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Télécharger les résultats",
                        data=output,
                        file_name=nom_fichier,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("Aucun résultat à afficher.")

                st.session_state.traitement_lance = False
                st.session_state.traitement_en_cours = False

        st.markdown("""
        <hr class="footer-separator">
        <div class="footer-text">
            &copy; 2025 by Adamou Muisse. Tous droits réservés.
        </div>
        """, unsafe_allow_html=True)
if __name__ == "__main__":
    app()