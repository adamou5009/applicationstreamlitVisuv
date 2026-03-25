import streamlit as st
import pandas as pd

from fonction import (
    charger_utilisateurs,
    enregistrer_utilisateur,
    modifier_utilisateur,
    supprimer_utilisateur,
    est_connecte,
)
from file_attente import lire_file, lire_historique
from theme import page_banner, section_header, divider, metric_chips


# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════
def _inject_css():
    st.markdown("""
<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');

/* ── Labels boutons FA ── */
.fa-btn-label {
    display: flex; align-items: center; gap: 7px;
    font-size: 0.82rem; font-weight: 600; color: #475569;
    margin-bottom: 4px; padding-left: 2px;
}
.fa-btn-label i { color: #6366f1; font-size: 0.9rem; }
.fa-btn-label.danger  i, .fa-btn-label.danger  { color: #e11d48; }
.fa-btn-label.success i, .fa-btn-label.success { color: #16a34a; }

/* ── Tableau interactif ── */
.user-table-wrapper {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-top: 8px;
}
.user-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
}
.user-table thead th {
    background: #f1f5f9;
    color: #475569;
    font-size: 0.70rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    padding: 11px 16px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}
.user-table tbody tr {
    cursor: pointer;
    transition: background 0.15s;
    border-bottom: 1px solid #f1f5f9;
}
.user-table tbody tr:last-child { border-bottom: none; }
.user-table tbody tr:hover { background: #f8fafc; }
.user-table tbody tr.selected-row { background: #eef2ff !important; }
.user-table tbody td {
    padding: 11px 16px;
    color: #1e293b;
    vertical-align: middle;
}

/* Checkbox custom */
.row-checkbox {
    width: 16px; height: 16px;
    accent-color: #6366f1;
    cursor: pointer;
}

/* Badge rôle */
.role-badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 9px; border-radius: 10px;
    font-size: 0.68rem; font-weight: 700;
}
.role-admin { background: #dbeafe; color: #1e40af; }
.role-user  { background: #dcfce7; color: #166534; }

/* Barre de recherche/filtre */
.table-toolbar {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 16px;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}

/* Compteur sélection */
.sel-counter {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eef2ff; color: #4f46e5;
    border: 1px solid #c7d2fe; border-radius: 20px;
    padding: 3px 12px; font-size: 0.75rem; font-weight: 700;
}

/* ── Chips stats ── */
.top-user-chip {
    background: linear-gradient(135deg, #eef2ff, #e0e7ff);
    border: 1px solid #c7d2fe; border-radius: 12px;
    padding: 14px 12px; text-align: center;
    box-shadow: 0 1px 4px rgba(99,102,241,0.08);
}
.top-user-chip .tuc-rank {
    font-size: 0.65rem; font-weight: 700; color: #818cf8;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;
}
.top-user-chip .tuc-name {
    font-size: 0.95rem; font-weight: 700; color: #1e293b;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.top-user-chip .tuc-count { font-size: 0.75rem; color: #6366f1; font-weight: 600; margin-top: 2px; }

/* ── Progress bar utilisateur ── */
.user-progress {
    background: #f1f5f9; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 14px 18px; margin-top: 8px;
}
.user-progress .up-label {
    font-size: 0.72rem; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;
}
.progress-track { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.progress-fill-green {
    height: 100%; border-radius: 4px;
    background: linear-gradient(90deg, #10b981, #34d399);
}

/* ── Carte utilisateur sélectionné ── */
.selected-user-card {
    background: linear-gradient(135deg, #eef2ff, #e0e7ff);
    border: 1.5px solid #c7d2fe; border-radius: 12px;
    padding: 14px 20px; display: flex; align-items: center;
    gap: 14px; margin: 12px 0;
}
.selected-user-card .su-avatar {
    width: 42px; height: 42px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 700; color: white; flex-shrink: 0;
}
.selected-user-card .su-name { font-weight: 700; color: #1e293b; font-size: 0.95rem; }
.selected-user-card .su-sub  { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

.date-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #f0fdf4; color: #166534; border: 1px solid #86efac;
    padding: 2px 10px; border-radius: 10px; font-size: 0.68rem; font-weight: 600;
}

/* ── Alerte suppression ── */
.delete-alert {
    background: linear-gradient(135deg, #fff1f2, #ffe4e6);
    border: 1.5px solid #fda4af; border-radius: 12px;
    padding: 18px 22px; margin: 12px 0;
}
.delete-alert .da-title { font-weight: 700; color: #9f1239; font-size: 0.9rem; margin-bottom: 4px; }
.delete-alert .da-sub   { font-size: 0.82rem; color: #e11d48; }

/* ── Formulaire card ── */
.form-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 26px 30px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-top: 8px;
}
.form-card-title {
    font-size: 1.05rem; font-weight: 700; color: #1e293b;
    padding-bottom: 12px; margin-bottom: 18px; border-bottom: 1px solid #f1f5f9;
}
div[data-testid="stTextInput"] input {
    border-radius: 10px !important; padding: 11px 16px !important;
    border: 1.5px solid #e2e8f0 !important; background: #f8fafc !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important; background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />
""", unsafe_allow_html=True)


# ── Helper : label FA + bouton ────────────────────────────────
def _fa_button(icon, label, key, container_width=True, disabled=False, style="default"):
    css_class = "fa-btn-label"
    if style == "danger":  css_class += " danger"
    if style == "success": css_class += " success"
    st.markdown(
        f'<div class="{css_class}">'
        f'<i class="fa-solid {icon}"></i> {label}'
        f'</div>',
        unsafe_allow_html=True
    )
    return st.button(label, key=key,
                     use_container_width=container_width,
                     disabled=disabled)



from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def _afficher_tableau(df: pd.DataFrame) -> dict | None:

    if df.empty:
        st.info("Aucun utilisateur trouvé.")
        return None

    # 🔍 Barre de recherche
    # ────────────── CSS Personnalisé ──────────────
    st.markdown("""
    <style>
    /* Barre de recherche */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        padding: 10px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 14px !important;
    }

    /* Colonnes (les colonnes Streamlit st.columns) */
    .css-1d391kg {
        gap: 1rem !important;  /* espace entre colonnes */
    }
    .css-1d391kg > div {
        padding: 0 !important;
    }

    /* Caption / compteur */
    .stCaption {
        font-weight: 600;
        color: #1e40af;
    }

    /* AgGrid table */
    .ag-theme-balham .ag-header {
        background-color: #f1f5f9 !important;
        color: #1f2937 !important;
        font-weight: 600 !important;
    }

    .ag-theme-balham .ag-cell {
        border-bottom: 1px solid #e2e8f0 !important;
        padding: 6px 8px !important;
        font-size: 13px !important;
    }

    .ag-theme-balham .ag-row-selected {
        background-color: #eef2ff !important;
    }

    .ag-theme-balham .ag-header-cell-label {
        justify-content: flex-start !important;
    }

    .ag-theme-balham .ag-checkbox-input-wrapper input[type="checkbox"] {
        width: 16px !important;
        height: 16px !important;
    }

    /* Rôle badges (si tu ajoutes des badges plus tard) */
    .role-badge-admin {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 3px 8px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 11px;
    }
    .role-badge-user {
        background-color: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 11px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    search = st.text_input(
        "🔍 Rechercher un utilisateur",
        placeholder="Nom, email, téléphone...",
    )

    # ── Filtrage global
    dff = df.copy()

    if search:
        mask = dff.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)

        dff = dff[mask]

    if dff.empty:
        st.warning("Aucun résultat.")
        return None

    # ── Config AgGrid
    gb = GridOptionsBuilder.from_dataframe(dff)

    gb.configure_column("username", header_name="Utilisateur")
    gb.configure_column("nom", header_name="Nom complet")
    gb.configure_column("email", header_name="Email")
    gb.configure_column("telephone", header_name="Téléphone")
    gb.configure_column("role", header_name="Rôle")
    gb.configure_column("date_creation", header_name="Membre depuis")

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=True
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    grid_options = gb.build()

    response = AgGrid(
        dff,  # ✅ corrigé
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="balham",
        height=400,
        fit_columns_on_grid_load=True,
    )

    selected = response.get("selected_rows", [])

    if isinstance(selected, pd.DataFrame):
        if not selected.empty:
            return selected.iloc[0].to_dict()

    elif isinstance(selected, list):
        if len(selected) > 0:
            return selected[0]

    return None

# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
# ───────────── Top 5 utilisateurs et tableau propre ─────────────
def app():
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    _inject_css()

    # Initialisation session_state
    for key, default in [
        ("selected_user_id",    None),
        ("action_en_cours",     None),
        ("ajout_expander_open", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    page_banner(
        title="Gestion des Utilisateurs",
        subtitle="Consultez, modifiez et gérez tous les comptes de l'application.",
        watermark="USER"
    )

    df             = charger_utilisateurs()
    admin_connecte = st.session_state.get("utilisateur_connecte", "")

    # ── Top 5 seulement ─────────────
    try:
        toutes = lire_file() + lire_historique()
        if toutes:
            df_req = pd.DataFrame(toutes)
            top = (df_req.groupby("utilisateur").size()
                   .reset_index(name="Total")
                   .sort_values("Total", ascending=False)
                   .head(5))

            medals = ["1", "2", "3", "4", "5"]
            cols   = st.columns(5)
            for idx, (_, row) in enumerate(top.iterrows()):
                with cols[idx]:
                    st.markdown(f"""
<div class="top-user-chip">
    <div class="tuc-rank">
        <i class="fa-solid fa-trophy" style="margin-right:4px;"></i>
        Rang {medals[idx]}
    </div>
    <div class="tuc-name">{row["utilisateur"]}</div>
    <div class="tuc-count">{row["Total"]} requêtes</div>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur affichage Top 5 : {e}")

    divider()
    section_header("Liste des utilisateurs")
    
    # ── Tableau interactif propre
    user_data = _afficher_tableau(df)
    username_sel = user_data.get("username") if user_data else None

    # Synchronisation session_state
    if user_data:
        st.session_state.selected_user_id = user_data.get("id")
    elif st.session_state.action_en_cours is None:
        st.session_state.selected_user_id = None

    # ── Panneau utilisateur sélectionné (affiché seulement si sélectionné)
    if st.session_state.selected_user_id and user_data:
        divider()
        initiale      = username_sel[0].upper() if username_sel else "?"
        role_sel      = user_data.get("role", "—")
        date_creation = user_data.get("date_creation", "")

        st.markdown(f"""
        <div class="selected-user-card">
            <div class="su-avatar">{initiale}</div>
            <div>
                <div class="su-name">
                    <i class="fa-solid fa-circle-user" style="color:#6366f1;margin-right:6px;"></i>
                    {username_sel}
                </div>
                <div class="su-sub">
                    <i class="fa-solid fa-user" style="margin-right:4px;color:#a5b4fc;"></i>
                    {user_data.get("nom","—")} &nbsp;·&nbsp;
                    <i class="fa-solid fa-envelope" style="margin-right:4px;color:#a5b4fc;"></i>
                    {user_data.get("email","—")} &nbsp;·&nbsp;
                    <span style="background:#dbeafe;color:#1e40af;padding:2px 8px;
                                border-radius:10px;font-size:0.68rem;font-weight:600;">
                        <i class="fa-solid fa-shield-halved" style="margin-right:4px;"></i>
                        {role_sel}
                    </span>
                    &nbsp;·&nbsp;
                    <span class="date-badge">
                        <i class="fa-solid fa-calendar-days"></i>{date_creation}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        est_soi_meme = (username_sel == admin_connecte)
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if _fa_button("fa-pen-to-square", "Modifier", key="btn_modifier"):
                st.session_state.action_en_cours = "modifier"
        with col2:
            if _fa_button("fa-trash", "Supprimer", key="btn_supprimer",
                          disabled=est_soi_meme, style="danger"):
                st.session_state.action_en_cours = "supprimer"
        if est_soi_meme:
            st.caption("Vous ne pouvez pas supprimer votre propre compte administrateur.")

   
    # ── Formulaire modification ──────────────────────────
    if st.session_state.action_en_cours == "modifier" and user_data:
        divider()
        section_header(f"Modifier — {username_sel}")

        date_creation = user_data.get("date_creation", "Non renseignée")
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="form-card-title">'
            '<i class="fa-solid fa-pen-to-square" style="margin-right:8px;color:#6366f1;"></i>'
            'Informations du compte</div>',
            unsafe_allow_html=True
        )

        st.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
            padding:10px 16px;margin-bottom:16px;
            display:flex;align-items:center;gap:10px;">
    <i class="fa-solid fa-calendar-days" style="color:#16a34a;font-size:1.1rem;"></i>
    <div>
        <div style="font-size:0.68rem;font-weight:700;color:#166534;
                    text-transform:uppercase;letter-spacing:0.08em;">Membre depuis</div>
        <div style="font-size:0.9rem;font-weight:600;color:#15803d;">{date_creation}</div>
    </div>
    <span style="margin-left:auto;font-size:0.68rem;color:#86efac;font-style:italic;">
        <i class="fa-solid fa-lock" style="margin-right:4px;"></i>non modifiable
    </span>
</div>
""", unsafe_allow_html=True)

        with st.form("form_modification"):
            col1, col2 = st.columns(2)
            with col1:
                new_nom = st.text_input("Nom complet",  value=user_data.get("nom", ""))
                new_tel = st.text_input("Téléphone",    value=user_data.get("telephone", ""))
            with col2:
                new_email = st.text_input("Email",      value=user_data.get("email", ""))
                new_role  = st.selectbox(
                    "Rôle", ["Utilisateur", "Administrateur"],
                    index=0 if user_data.get("role") == "Utilisateur" else 1
                )
            new_pwd   = st.text_input("Nouveau mot de passe (vide = inchangé)", type="password")
            confirmer = st.checkbox("Je confirme les modifications")

            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Enregistrer", use_container_width=True):
                    if not confirmer:
                        st.warning("Cochez la case de confirmation.")
                    else:
                        autres = df[df["id"] != st.session_state.selected_user_id]
                        if (new_tel in autres["telephone"].values or
                                new_email in autres["email"].values):
                            st.error("Téléphone ou email déjà utilisé.")
                        else:
                            ok = modifier_utilisateur(st.session_state.selected_user_id, {
                                "nom": new_nom, "telephone": new_tel,
                                "email": new_email, "mot_de_passe": new_pwd, "role": new_role,
                            })
                            if ok:
                                st.success("Utilisateur mis à jour !")
                                st.session_state.action_en_cours = None
                                st.rerun()
            with c2:
                if st.form_submit_button("Annuler", use_container_width=True):
                    st.session_state.action_en_cours = None
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Confirmation suppression ─────────────────────────
    if st.session_state.action_en_cours == "supprimer" and user_data:
        divider()
        st.markdown(f"""
<div class="delete-alert">
    <div class="da-title">
        <i class="fa-solid fa-triangle-exclamation" style="margin-right:6px;"></i>
        Confirmer la suppression
    </div>
    <div class="da-sub">
        L'utilisateur <strong>{username_sel}</strong> sera supprimé définitivement.
        Cette action est irréversible.
    </div>
</div>
""", unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="small")
        with c1:
            if _fa_button("fa-check", "Oui, supprimer", key="confirm_suppr", style="danger"):
                supprimer_utilisateur(st.session_state.selected_user_id)
                st.success("Utilisateur supprimé.")
                st.session_state.action_en_cours  = None
                st.session_state.selected_user_id = None
                st.session_state.tbl_sel_id       = None
                st.rerun()
        with c2:
            if _fa_button("fa-arrow-left", "Annuler", key="cancel_suppr"):
                st.session_state.action_en_cours = None
                st.rerun()

    # ── Ajout utilisateur ────────────────────────────────
    divider()
    section_header("Ajouter un utilisateur")

    with st.expander("Nouveau compte", expanded=st.session_state.ajout_expander_open):
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="form-card-title">'
            '<i class="fa-solid fa-user-plus" style="margin-right:8px;color:#6366f1;"></i>'
            'Créer un compte</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
            padding:10px 16px;margin-bottom:16px;
            display:flex;align-items:center;gap:8px;">
    <i class="fa-solid fa-calendar-days" style="color:#3b82f6;"></i>
    <span style="font-size:0.82rem;color:#1e40af;font-weight:500;">
        La date de création sera enregistrée automatiquement.
    </span>
</div>
""", unsafe_allow_html=True)

        with st.form("ajout_formulaire"):
            col1, col2 = st.columns(2)
            with col1:
                a_nom  = st.text_input("Nom complet")
                a_user = st.text_input("Nom d'utilisateur")
                a_tel  = st.text_input("Téléphone")
            with col2:
                a_mail = st.text_input("Email")
                a_pwd  = st.text_input("Mot de passe", type="password")
                a_role = st.selectbox("Rôle", ["Utilisateur", "Administrateur"])

            if st.form_submit_button("Créer le compte", use_container_width=True):
                if not all([a_nom, a_user, a_tel, a_mail, a_pwd]):
                    st.error("Tous les champs sont obligatoires.")
                else:
                    ok, msg = enregistrer_utilisateur(a_nom, a_user, a_tel, a_mail, a_pwd, a_role)
                    if ok:
                        st.success(msg)
                        st.session_state.ajout_expander_open = False
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Statistiques globales
# ═══════════════════════════════════════════════════════════════
def _afficher_stats_globales(df):
    try:
        toutes = lire_file() + lire_historique()

        if not toutes:
            metric_chips([
                {"label": "Utilisateurs",  "value": len(df), "color": "indigo"},
                {"label": "Requêtes",      "value": 0,       "color": "sky"},
                {"label": "Réussies",      "value": 0,       "color": "emerald"},
                {"label": "Échouées",      "value": 0,       "color": "rose"},
            ])
            return

        df_req    = pd.DataFrame(toutes)
        nb_actifs = df_req["utilisateur"].nunique()
        nb_total  = len(df_req)
        nb_term   = len(df_req[df_req["statut"] == "terminee"])
        nb_echou  = len(df_req[df_req["statut"] == "echouee"])

        metric_chips([
            {"label": "Utilisateurs total",  "value": len(df),                 "color": "indigo"},
            {"label": "Utilisateurs actifs", "value": f"{nb_actifs}/{len(df)}", "color": "violet"},
            {"label": "Total requêtes",      "value": nb_total,                 "color": "sky"},
            {"label": "Réussies",            "value": nb_term,                  "color": "emerald"},
            {"label": "Échouées",            "value": nb_echou,                 "color": "rose"},
        ])

        section_header("Top 5 utilisateurs")
        top = (df_req.groupby("utilisateur").size()
               .reset_index(name="Total")
               .sort_values("Total", ascending=False)
               .head(5))

        medals = ["1", "2", "3", "4", "5"]
        cols   = st.columns(5)
        for idx, (_, row) in enumerate(top.iterrows()):
            with cols[idx]:
                st.markdown(f"""
<div class="top-user-chip">
    <div class="tuc-rank">
        <i class="fa-solid fa-trophy" style="margin-right:4px;"></i>
        Rang {medals[idx]}
    </div>
    <div class="tuc-name">{row["utilisateur"]}</div>
    <div class="tuc-count">{row["Total"]} requêtes</div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur stats globales : {e}")


# ═══════════════════════════════════════════════════════════════
# Statistiques individuelles
# ═══════════════════════════════════════════════════════════════
def _afficher_stats_individuelles(username: str):
    try:
        data  = lire_file() + lire_historique()
        u_req = [r for r in data if r.get("utilisateur") == username]

        if not u_req:
            st.caption("Aucune activité enregistrée pour cet utilisateur.")
            return

        total = len(u_req)
        term  = len([r for r in u_req if r.get("statut") == "terminee"])
        echou = len([r for r in u_req if r.get("statut") == "echouee"])
        taux  = (term / total * 100) if total > 0 else 0

        metric_chips([
            {"label": "Total",         "value": total,          "color": "indigo"},
            {"label": "Réussies",      "value": term,           "color": "emerald"},
            {"label": "Échouées",      "value": echou,          "color": "rose"},
            {"label": "Taux réussite", "value": f"{taux:.1f}%", "color": "amber"},
        ])

        st.markdown(f"""
<div class="user-progress">
    <div class="up-label">
        <i class="fa-solid fa-chart-line" style="margin-right:6px;"></i>
        Taux de réussite — {username}
    </div>
    <div class="progress-track">
        <div class="progress-fill-green" style="width:{taux:.1f}%;"></div>
    </div>
    <div style="text-align:right;font-size:0.72rem;color:#64748b;margin-top:4px;">
        {term} / {total} requêtes réussies
    </div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur stats individuelles : {e}")


if __name__ == "__main__":
    app()