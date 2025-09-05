import streamlit as st
import pandas as pd
import threading
import time
import base64
import os
from file_attente import (
    lire_file, lire_historique, fusionner_nouvelles, traiter_file_automatique
)

# URL fixe CGAWEB
url = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"
utilisateur = os.getenv("CGAWEB_USER")
mot_de_passe = os.getenv("CGAWEB_PASS")

# --- Lancement du worker en arrière-plan ---
def lancer_traitement_en_background():
    thread = st.session_state.get("worker_thread")
    if thread is None or not thread.is_alive():
        t = threading.Thread(
            target=traiter_file_automatique,
            args=(url, utilisateur, mot_de_passe),
            kwargs={"pause": 0.1},
            daemon=True
        )
        t.start()
        st.session_state["worker_thread"] = t
        st.session_state["traitement_en_cours"] = True
        print(f"🟢 Worker CGAWEB lancé en arrière-plan pour {utilisateur}")

# --- Page principale ---
def app():
    st.title("📋 Résultats de la recherche")

    # Bouton retour
    if st.button("🏠 Retour"):
        st.session_state["page_active"] = "Accueil"
        st.session_state.pop("numero_recherche", None)
        st.rerun()

    # Récupérer le numéro recherché
    numero = st.session_state.get("numero_recherche")
    if not numero:
        st.warning("⚠️ Aucun numéro à rechercher.")
        st.stop()

    # Placeholder pour statut et logs
    statut_placeholder = st.empty()
    logs_placeholder = st.empty()

    # Fusionner les nouvelles requêtes avant lecture
    fusionner_nouvelles()
    file_actuelle = lire_file()
    requete = next((r for r in file_actuelle if r["valeur"] == numero), None)

    if not requete:
        histo = lire_historique()
        requete = next((r for r in histo if r["valeur"] == numero), None)

    if not requete:
        st.warning("⚠️ La requête n’a pas été prise en compte, veuillez réessayer.")
        st.stop()

    # --- Si la requête est en attente ou en cours ---
    if requete["statut"] in ["en_attente", "en_cours"]:
        lancer_traitement_en_background()

        # Affichage dynamique du statut et logs
        while requete["statut"] in ["en_attente", "en_cours"]:
            fusionner_nouvelles()
            file_actuelle = lire_file()
            requete = next((r for r in file_actuelle if r["valeur"] == numero), requete)

            statut_placeholder.info(f"🔄 Traitement en cours pour {numero}... Statut : {requete['statut']}")
            logs = requete.get("logs", [])
            logs_placeholder.text("\n".join(logs) if logs else "Aucune étape enregistrée pour le moment...")
            
            time.sleep(1)  # rafraîchissement toutes les secondes

    # --- Affichage du résultat ---
    res = requete.get("resultat")

    if requete["statut"] == "erreur":
        st.error(f"❌ La requête a échoué : {res}")
        return

    elif requete["statut"] == "terminee":
        colonnes = ["abonne", "c", "nom", "prenom", "pays", "code postal",
                    "ville", "adresse", "option majeure", "annule", "ret", "ci", "societe"]

        if isinstance(res, list) and all(isinstance(r, (list, tuple)) and len(r) == len(colonnes) for r in res):
            # Résultat sous forme de tableau (recherche par téléphone)
            df = pd.DataFrame(res, columns=colonnes)
            st.success(f"✅ {len(df)} résultat(s) trouvé(s) pour le numéro {numero} :")
            st.dataframe(df)

        else:
            # Résultat simplifié (recherche par décodeur)
            if isinstance(res, tuple):
                numero_abonne, fiche_abonne, *screenshot_path = res
                st.success(f"✅ Résultat pour l’abonné {numero_abonne}")
                st.write(fiche_abonne)
                if screenshot_path:
                    path = screenshot_path[0]
                    with open(path, "rb") as img_file:
                        b64 = base64.b64encode(img_file.read()).decode()
                        href = f'<a href="data:file/png;base64,{b64}" download="{path}">📥 Télécharger</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    st.image(path, caption="Fiche abonné", use_column_width=True)
            else:
                st.write(res)

    print("✅ Affichage terminé pour le numéro :", numero)
