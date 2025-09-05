import streamlit as st
import pandas as pd
import time
from fonction import (
    connexion_cgaweb,
    deconnexion_cgaweb,
    resultat,
    traiter_decodeurs,
    arret_urgence,
    traiter_decodeurs_multi_navigateurs,
    est_connecte,
    identifiants_cgaweb_rpe
)

def extraction():
    # --- CSS GLOBAL ---
    
    st.set_page_config(page_title="Extraction CGAWEB", layout="wide")
    st.markdown("""
    <style>
    

    

    /* Conteneur principal de la page */
    main[data-testid="stMain"] {
        padding: 2rem;
        flex-grow: 1; /* Prend l'espace restant */
    }

    .css-1d391kg {
        background-color: #f0f2f6;
    }
    body-box {
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
    }

    
    /* Conteneur principal */
    #stMainBlockContainer {
        background-color: #ffffff !important; /* Fond blanc du contenu */
        border-radius: 12px;
        padding: 24px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.08);
    }
    main[data-testid="stAppViewContainer"] > div:first-child {
        padding: 10px 20px !important;
        margin: 0 auto !important;
    }
    .css-1d391kg {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    footer {
        flex-shrink: 0 !important;
        text-align: center;
        font-size: 14px;
        color: #666;
        padding: 10px 0;
    }

    .header-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.08);
    }
    .main-title {
        color: #222;
        font-weight: 700;
        margin: 0;
    }
    .separator {
        border: none;
        border-bottom: 1px solid #ddd;
        margin: 15px 0 25px 0;
    }

    .edit-button-container,
    .launch-button-container,
    .download-button-container,
    .login-button-container {
        margin: 15px 0;
        text-align: center;
    }
    

    .instructions-text {
        background-color: #fefefe;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 16px;
        color: #444;
    }

    .file-uploader-container {
        margin-bottom: 20px;
    }

    .results-section {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        margin-top: 25px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
    }

    .footer-separator {
        border: none;
        border-top: 1px solid #ccc;
        margin: 30px 0 10px 0;
    }
    .footer-text {
        font-size: 13px;
        color: #777;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    # --- VÉRIFICATION CONNEXION ---
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()
    # Configuration de la page
    st.set_page_config(page_title="Extraction CGAWEB", layout="wide")
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
    # mettre la page dans un conteneur
    with st.container():
        # --- HEADER ---
        st.markdown("""
        <div class="header-box">
            <h3 class="main-title">EXTRACTION DES INFORMATIONS DES ABONNÉS</h3>
            </div>
        <hr class="separator">
        """, unsafe_allow_html=True)

        # --- BLOC GLOBAL CONTENU ---
        st.markdown('<div class="body-box">', unsafe_allow_html=True)

        url = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"

        if "traitement_lance" not in st.session_state:
            st.session_state.traitement_lance = False

        # --- IDENTIFIANTS TEMPORAIRES ---
        if "rpe_user" not in st.session_state or "rpe_pass" not in st.session_state:
            #st.markdown('<div class="login-button-container">Définir les identifiants CGAWEB</div>', unsafe_allow_html=True)
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

        if "stop_processing" not in st.session_state:
            st.session_state.stop_processing = False
        if "traitement_en_cours" not in st.session_state:
            st.session_state.traitement_en_cours = False

        col_vide, col_arret = st.columns([6, 1])
        arret_placeholder = col_arret.empty()

        #def afficher_bouton_arret():
            #if st.session_state.get("traitement_en_cours", False):
                #clic = st.button(
                    #"🚨 Arrêt", 
                    #help="Cliquez pour arrêter immédiatement", 
                    #type="primary", 
                    #key="btn_arret"
                #)
                #if clic:
                    #st.session_state.stop_processing = True
                    #st.session_state.traitement_en_cours = False
                    #st.warning("🚨 Arrêt d'urgence demandé ! Le traitement est interrompu.")
                    #time.sleep(1)

                    #arret_urgence(
                        #driver=st.session_state.get("driver"), 
                        #resultats_en_cours=st.session_state.get("resultats_en_cours")
                    #)

                # On ne fait PAS de st.rerun()

        # --- INSTRUCTIONS ---
        st.markdown("""
        <div class="instructions-text">
            <p>Importez un fichier Excel contenant la colonne : <code>numéro de décodeur</code>.</p>
            <p>Cliquez sur le bouton pour lancer le traitement.</p>
        </div>
        """, unsafe_allow_html=True)

        # --- UPLOADER ---
        st.markdown('<div class="file-uploader-container">', unsafe_allow_html=True)
        fichier = st.file_uploader("📂 Choisissez un fichier Excel", type=["xlsx"])
        st.markdown('</div>', unsafe_allow_html=True)

        if fichier:
            df = pd.read_excel(fichier)
            if "numéro de décodeur" not in df.columns:
                st.error("❌ La colonne 'numéro de décodeur' est absente.")
                return

            st.markdown('<div class="launch-button-container">', unsafe_allow_html=True)
            if st.button("🚀 Lancer le traitement") and not st.session_state.traitement_lance:
                st.session_state.traitement_lance = True
            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.traitement_lance:
                st.success("✅ Traitement lancé !")
                st.session_state.traitement_en_cours = True
                arret = st.button("Arrêt d'urgence")
                if arret:
                    arret_urgence(driver)
                    st.rerun

                progress_bar = st.progress(0)
                statut_txt = st.empty()
                total = len(df)

                st.info(f"Nombre de décodeurs à traiter : {total}")
                resultats = []

                if total == 0:
                    st.warning("⚠️ Aucun décodeur à traiter.")
                elif total > 52000:
                    st.warning("🧪 Traitement multi-navigateurs activé.")
                    resultats = traiter_decodeurs_multi_navigateurs(
                        df, url, utilisateur, mot_de_passe, statut_txt, progress_bar, st.session_state
                    )
                else:
                    driver = None
                    try:
                        driver, original_window, new_window = connexion_cgaweb(url, utilisateur, mot_de_passe)
                        if not driver:
                            print("❌ Échec de connexion à CGAWEB.")
                        else:
                            resultats = traiter_decodeurs(
                                driver, df, original_window, new_window, statut_txt, progress_bar
                            )
                    except Exception as e:
                        st.error(f"Erreur durant le traitement : {e}")
                    finally:
                        if driver:
                            try:
                                deconnexion_cgaweb(driver)
                            except Exception as e:
                                st.warning(f"Erreur lors de la déconnexion : {e}")

                if resultats:
                    output, nom_fichier = resultat(resultats)
                    st.success("✅ Traitement terminé !")

                    df_resultats = pd.DataFrame(resultats)
                    df_resultats = df_resultats.astype(str)
                    def colorer_statut(val):
                        if val == "Actif":
                            return "background-color: #d4edda; color: #155724;"
                        elif val == "Échu":
                            return "background-color: #f8d7da; color: #721c24;"
                        elif val in ["À échoir", "Échu dans 5 jours"]:
                            return "background-color: #fff3cd; color: #856404;"
                        return ""

                    styled_df = df_resultats.style.map(colorer_statut, subset=["statut"])

                    st.markdown('<div class="results-section">', unsafe_allow_html=True)
                    st.subheader("📊 Résultats extraits :")
                    st.dataframe(styled_df, use_container_width=True)
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
                arret_placeholder.empty()

        # --- FERMETURE CONTENEUR GLOBAL ---
        st.markdown('</div>', unsafe_allow_html=True)

        # --- FOOTER ---
        st.markdown("""
        <hr class="footer-separator">
        <div class="footer-text">
            &copy; 2025 by Adamou Muisse. Tous droits réservés.
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    extraction()