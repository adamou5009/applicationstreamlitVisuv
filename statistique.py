import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from io import BytesIO
from fonction import est_connecte, charger_utilisateurs

def app():
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.markdown("""
    <style>
    .stVerticalBlock {
        max-width: 90vw !important;
        width: 100% !important;
    }
    .stVerticalBlock input,
    .stVerticalBlock textarea,
    .stVerticalBlock select {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.set_page_config(page_title="Statistiques", layout="wide")


    #mettre page dans un conteneur
    with st.container():
        # --- Chargement des utilisateurs ---
        try:
            df_users = charger_utilisateurs()
            nb_utilisateurs_total = df_users["username"].nunique()
        except Exception as e:
            nb_utilisateurs_total = 0
            st.error(f"❌ Impossible de charger la liste des utilisateurs : {e}")

        # --- Chargement du fichier journal ---
        FICHIER_LOG = "journal_actions.csv"
        if not os.path.exists(FICHIER_LOG):
            st.warning("⚠️ Fichier journal manquant.")
            st.stop()

        try:
            data = pd.read_csv(FICHIER_LOG)
        except Exception as e:
            st.error(f"❌ Erreur de lecture du fichier journal : {e}")
            st.stop()

        if data.empty:
            st.info("ℹ️ Le journal est vide. Aucune action à afficher.")
            st.stop()

        data["date"] = pd.to_datetime(data["date"], errors="coerce")
        data = data.dropna(subset=["date"])

        # --- Colonnes des filtres ---
        col1, col2, col3 = st.columns(3)

        # Colonne 1 : Utilisateur
        with col1:
            utilisateurs = sorted(data["utilisateur"].dropna().unique().tolist())
            utilisateur_selectionne = st.selectbox("👤 Utilisateur :", utilisateurs)

        # Colonne 2 : Période
        with col2:
            date_min, date_max = data["date"].min().date(), data["date"].max().date()
            date_range = st.date_input("📅 Période :", [date_min, date_max])

        # Colonne 3 : Actions avec expander
        with col3:
            actions = sorted(data["action"].dropna().unique().tolist())
            with st.expander("🎯 Actions", expanded=False):
                action_selectionnee = st.multiselect(
                    "Actions :", actions, default=actions, key="actions_multiselect"
                )

        # --- Filtrage des données directement ---
        filtre_date = (data["date"].dt.date >= date_range[0]) & (data["date"].dt.date <= date_range[1])
        filtre_action = data["action"].isin(action_selectionnee)
        filtre_utilisateur = data["utilisateur"] == utilisateur_selectionne

        data_filtree = data[filtre_utilisateur & filtre_date & filtre_action]

        # --- Affichage des métriques ---
        nb_utilisateurs_journal = data[filtre_date & filtre_action]["utilisateur"].nunique()
        nb_recherches = (data_filtree["action"] == "recherche").sum()
        nb_recherches_echouees = (data_filtree["action"] == "recherche non aboutie").sum()
        nb_reactivations = (data_filtree["action"] == "reactivation").sum()
        nb_suivi = (data_filtree["action"] == "suivi abonne").sum()
        connectes = data[filtre_date & filtre_action & (data["date"] > pd.Timestamp.now() - pd.Timedelta(minutes=10))]["utilisateur"].nunique()

        st.markdown("---")
        col1m, col2m, col3m, col4m = st.columns(4)
        col1m.metric("👥 Utilisateurs", nb_utilisateurs_total)
        col2m.metric("📑 Utilisateurs dans le journal", nb_utilisateurs_journal)
        col3m.metric("🟢 Actifs maintenant", connectes)
        col4m.metric("✅ Recherches réussies", nb_recherches)

        col1m2, col2m2, col3m2 = st.columns(3)
        col1m2.metric("❌ Recherches échouées", nb_recherches_echouees)
        col2m2.metric("⚡ Réactivations", nb_reactivations)
        col3m2.metric("📊 Suivi Abonné", nb_suivi)

        st.markdown("---")

        # --- Graphique ---
        if not data_filtree.empty:
            action_counts = data_filtree["action"].value_counts().reset_index()
            action_counts.columns = ["Action", "Nombre"]
            action_counts["Action"] = action_counts["Action"].str.replace("_", " ").str.capitalize()

            fig = px.pie(
                action_counts,
                names="Action",
                values="Nombre",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig.update_traces(textinfo="percent+label", pull=[0.04]*len(action_counts))
            fig.update_layout(title="Répartition des actions", height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher avec les filtres actuels.")

        # --- Tableau détaillé ---
        with st.expander("📄 Voir le journal détaillé"):
            st.dataframe(data_filtree.sort_values(by="date", ascending=False), use_container_width=True)

        # --- Bouton téléchargement ---
        if not data_filtree.empty:
            output = BytesIO()
            data_filtree.to_excel(output, index=False, sheet_name="Journal")
            output.seek(0)
            st.download_button(
                label="📥 Télécharger au format Excel",
                data=output,
                file_name="journal_actions_filtre.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
