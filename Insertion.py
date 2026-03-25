import streamlit as st
import pandas as pd
import time
import mysql.connector
import json
from datetime import datetime
import logging

# ==========================
# 🗄️ CONFIGURATION BDD (MySQL)
# ==========================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "", 
    "database": "visuv_apk_db"
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ==========================
# 📊 LOGIQUE DE DONNÉES
# ==========================
def ajouter_a_la_file(df, nom_fichier):
    """Transforme les lignes Excel en requêtes SQL pour les workers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    utilisateur = st.session_state.get("utilisateur_connecte", "anonyme")
    nb_ajouts = 0
    
    try:
        for _, row in df.iterrows():
            # On crée une entrée pour le décodeur ou l'abonné
            valeur = str(row.get("DECODEUR", row.get("ABONNE", ""))).strip()
            if valeur and valeur != "nan":
                req_id = int(time.time() * 1000) + nb_ajouts
                sql = """INSERT INTO requetes (id, utilisateur, type_recherche, valeur, statut, fichier_source) 
                         VALUES (%s, %s, %s, %s, 'en_attente', %s)"""
                cursor.execute(sql, (req_id, utilisateur, "EXTRACTION", valeur, nom_fichier))
                nb_ajouts += 1
        conn.commit()
        return nb_ajouts
    except Exception as e:
        st.error(f"Erreur insertion : {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def lire_resultats_fichier(nom_fichier):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM requetes WHERE fichier_source = %s", (nom_fichier,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==========================
# 🎨 INTERFACE STREAMLIT
# ==========================
def app():
    st.markdown("""
    <style>
    .main { background-color: #f5f6fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004c97; color: white; }
    .status-box { padding: 20px; border-radius: 10px; border: 1px solid #ddd; background: white; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚀 Service d'Extraction CGAWEB")

    # --- Section Upload ---
    with st.container():
        st.subheader("📂 Importation des données")
        fichier = st.file_uploader("Charger le fichier Excel (DECODEUR / ABONNE)", type=["xlsx"])

        if fichier:
            df = pd.read_excel(fichier)
            df.columns = df.columns.str.strip().str.upper()
            
            if not any(col in df.columns for col in ["DECODEUR", "ABONNE"]):
                st.error("❌ Le fichier doit contenir 'DECODEUR' ou 'ABONNE'.")
            else:
                st.write(f"📄 {len(df)} lignes détectées.")
                if st.button("🚀 Envoyer à la file de traitement"):
                    nb = ajouter_a_la_file(df, fichier.name)
                    if nb > 0:
                        st.success(f"✅ {nb} lignes ajoutées à la file d'attente. Les workers vont démarrer le traitement.")
                        # Ici on pourrait appeler lancer_worker() si on est sur le même serveur
                        time.sleep(1)
                        st.rerun()

    st.divider()

    # --- Section Suivi en Temps Réel ---
    st.subheader("📊 Suivi du traitement")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Statistiques rapides
    cursor.execute("""
        SELECT statut, COUNT(*) as total 
        FROM requetes 
        WHERE date_creation > DATE_SUB(NOW(), INTERVAL 1 DAY) 
        GROUP BY statut
    """)
    stats = {row['statut']: row['total'] for row in cursor.fetchall()}
    
    col1, col2, col3 = st.columns(3)
    col1.metric("En attente", stats.get('en_attente', 0))
    col2.metric("En cours", stats.get('en_cours', 0), delta_color="normal")
    col3.metric("Terminées", stats.get('terminee', 0))

    # --- Section Résultats ---
    st.subheader("📥 Historique & Téléchargement")
    cursor.execute("SELECT DISTINCT fichier_source, MIN(date_creation) as date FROM requetes WHERE fichier_source IS NOT NULL GROUP BY fichier_source ORDER BY date DESC")
    fichiers_historique = cursor.fetchall()
    
    if fichiers_historique:
        selection = st.selectbox("Sélectionner un fichier pour voir les résultats", 
                                [f['fichier_source'] for f in fichiers_historique])
        
        if selection:
            res_rows = lire_resultats_fichier(selection)
            if res_rows:
                df_res = pd.DataFrame(res_rows)
                
                # Nettoyage pour l'affichage
                display_cols = ['valeur', 'statut', 'resultat', 'date_creation']
                st.dataframe(df_res[display_cols], use_container_width=True)
                
                # Export Excel
                from io import BytesIO
                output = BytesIO()
                df_res.to_excel(output, index=False)
                st.download_button(
                    label="📥 Télécharger les résultats (Excel)",
                    data=output.getvalue(),
                    file_name=f"resultats_{selection}.xlsx",
                    mime="application/vnd.ms-excel"
                )
                
                # Bouton de relance pour les erreurs
                if st.button(" Relancer les erreurs"):
                    cursor.execute("UPDATE requetes SET statut = 'en_attente' WHERE fichier_source = %s AND statut = 'echouee'", (selection,))
                    conn.commit()
                    st.info("Les erreurs ont été remises en file d'attente.")
                    st.rerun()
    else:
        st.info("Aucun traitement enregistré en base de données.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    app()