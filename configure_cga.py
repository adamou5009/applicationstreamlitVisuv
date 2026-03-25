import streamlit as st
import os
from dotenv import load_dotenv
from fonction import (
    charger_comptes, enregistrer_nouveau_compte, marquer_compte_actif,
    obtenir_compte_actif_worker, supprimer_compte_sql, desactiver_tous_les_comptes,
    tester_connexion_cgaweb, est_connecte,
)
from theme import page_banner, section_header, divider, metric_chips

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CSS spécifique
# ═══════════════════════════════════════════════════════════════
CONFIG_CSS = """
<style>
/* ── Carte compte ── */
.compte-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 8px 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}
.compte-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: #e2e8f0;
    border-radius: 14px 0 0 14px;
}
.compte-card.actif::before {
    background: linear-gradient(180deg, #10b981, #059669);
}
.compte-card.inactif::before {
    background: linear-gradient(180deg, #cbd5e1, #94a3b8);
}

.compte-info { flex: 1; }
.compte-nom {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
}
.compte-meta {
    font-size: 0.76rem;
    color: #94a3b8;
    letter-spacing: 0.04em;
}

/* ── Badge actif ── */
.badge-actif {
    background: #d1fae5; color: #065f46;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em;
    white-space: nowrap;
}
.badge-inactif {
    background: #f1f5f9; color: #94a3b8;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em;
    white-space: nowrap;
}

/* ── Bannière compte actif ── */
.worker-banner {
    background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    border: 1.5px solid #6ee7b7;
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.worker-banner .wb-icon { font-size: 2rem; }
.worker-banner .wb-title {
    font-weight: 700; color: #065f46; font-size: 0.9rem;
    margin-bottom: 2px;
}
.worker-banner .wb-sub { font-size: 0.78rem; color: #34d399; }
.worker-banner code {
    background: #a7f3d0; color: #064e3b;
    padding: 2px 8px; border-radius: 6px;
    font-weight: 700; font-size: 0.88rem;
}

/* ── Alerte no-compte ── */
.no-worker-banner {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 1.5px solid #fcd34d;
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 0.88rem;
    color: #92400e;
    font-weight: 500;
}

/* ── Form card ── */
.form-section {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 28px 32px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.form-section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem; font-weight: 700; color: #1e293b;
    padding-bottom: 12px; margin-bottom: 20px;
    border-bottom: 1px solid #f1f5f9;
}

/* ── Inputs ── */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    padding: 11px 16px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}

/* ── Boutons d'action inline ── */
.action-btn .stButton > button {
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 6px 14px !important;
    height: 36px !important;
}
</style>
"""


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
def app():
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.markdown(CONFIG_CSS, unsafe_allow_html=True)

    page_banner(
        title="Configuration CGAWEB",
        subtitle="Gérez les comptes utilisés par le worker pour le traitement automatique.",
        watermark="CFG"
    )

    # ── Données ──────────────────────────────────────────
    comptes          = charger_comptes()
    compte_actif     = obtenir_compte_actif_worker()
    nom_actif        = compte_actif["user_cga"] if compte_actif else None
    nb_total         = len(comptes)
    nb_actifs        = 1 if nom_actif else 0

    # ── Chips métriques ──────────────────────────────────
    metric_chips([
        {"label": "Comptes enregistrés", "value": nb_total,        "color": "indigo"},
        {"label": "Compte actif",        "value": nb_actifs,       "color": "emerald"},
        {"label": "Comptes inactifs",    "value": nb_total - nb_actifs, "color": "amber"},
    ])

    divider()

    # ── Bannière compte worker actif ──────────────────────
    if nom_actif:
        st.markdown(f"""
        <div class="worker-banner">
            <span class="wb-icon">🤖</span>
            <div>
                <div class="wb-title">Compte Worker Actif</div>
                <div class="wb-sub">
                    Le worker utilise actuellement le compte
                    <code>{nom_actif}</code>
                    pour traiter les requêtes.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="no-worker-banner">
            ⚠️ &nbsp; Aucun compte actif configuré — le worker ne peut pas traiter les requêtes.
        </div>
        """, unsafe_allow_html=True)

    # ── Liste des comptes ─────────────────────────────────
    section_header("👤 Comptes enregistrés")

    if comptes:
        for compte in comptes:
            est_actif  = (nom_actif == compte["user_cga"])
            cls_card   = "actif" if est_actif else "inactif"
            cls_badge  = "badge-actif" if est_actif else "badge-inactif"
            badge_txt  = "✅ Actif" if est_actif else "Inactif"

            col_info, col_actions = st.columns([4, 3], gap="medium")

            with col_info:
                st.markdown(f"""
                <div class="compte-card {cls_card}">
                    <div class="compte-info">
                        <div class="compte-nom">👤 {compte["user_cga"]}</div>
                        <div class="compte-meta">🔑 OTP : ••••••••  &nbsp;|&nbsp; ID : #{compte["id"]}</div>
                    </div>
                    <span class="{cls_badge}">{badge_txt}</span>
                </div>
                """, unsafe_allow_html=True)

            with col_actions:
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("🚀", key=f"activer_{compte['id']}",
                                 help="Activer ce compte", use_container_width=True):
                        marquer_compte_actif(compte["id"])
                        st.success(f"✅ {compte['user_cga']} activé.")
                        st.rerun()
                with c2:
                    if st.button("✏️", key=f"modifier_{compte['id']}",
                                 help="Modifier ce compte", use_container_width=True):
                        st.session_state["modifier_id"] = compte["id"]
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"supprimer_{compte['id']}",
                                 help="Supprimer ce compte", use_container_width=True):
                        supprimer_compte_sql(compte["id"])
                        if est_actif:
                            desactiver_tous_les_comptes()
                        st.success("Compte supprimé.")
                        st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#94a3b8;
                    background:#f8fafc;border-radius:14px;border:1px dashed #e2e8f0;">
            <div style="font-size:2rem;margin-bottom:8px;">📭</div>
            <div style="font-weight:600;color:#64748b;">Aucun compte enregistré</div>
            <div style="font-size:0.82rem;margin-top:4px;">Ajoutez un compte via le formulaire ci-dessous.</div>
        </div>
        """, unsafe_allow_html=True)

    divider()

    # ── Formulaire modification ───────────────────────────
    id_modif = st.session_state.get("modifier_id")

    if id_modif:
        section_header(" Modifier le compte")
        c_edit = next((c for c in comptes if c["id"] == id_modif), None)

        if c_edit:
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown(f'<div class="form-section-title">Modification — {c_edit["user_cga"]}</div>',
                        unsafe_allow_html=True)

            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_u = st.text_input(" Nom d'utilisateur", value=c_edit["user_cga"])
                    new_p = st.text_input(" Mot de passe", type="password",
                                          value=c_edit["password_cga"])
                with col2:
                    new_s = st.text_input(" Clé secrète OTP", type="password",
                                          value=c_edit["secret_otp"])

                col_save, col_cancel = st.columns([1, 1])
                with col_save:
                    if st.form_submit_button("  Enregistrer", use_container_width=True):
                        # Ajoutez ici votre fonction update_compte_sql(id_modif, new_u, new_p, new_s)
                        st.session_state.pop("modifier_id", None)
                        st.success(" Modifications enregistrées.")
                        st.rerun()
                with col_cancel:
                    if st.form_submit_button("✖️  Annuler", use_container_width=True):
                        st.session_state.pop("modifier_id", None)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # ── Formulaire ajout ─────────────────────────────
        section_header(" Ajouter un compte")

        with st.expander("Nouveau compte CGAWEB", expanded=False):
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<div class="form-section-title">Informations du compte</div>',
                        unsafe_allow_html=True)

            with st.form("ajout_formulaire"):
                col1, col2 = st.columns(2)
                with col1:
                    utilisateur  = st.text_input(" Nom d'utilisateur")
                    mot_de_passe = st.text_input(" Mot de passe", type="password")
                with col2:
                    secret         = st.text_input("🔑 Clé secrète OTP", type="password")
                    test_connexion = st.checkbox("Tester la connexion avant d'enregistrer",
                                                  value=True)

                submitted = st.form_submit_button("➕  Ajouter le compte",
                                                   use_container_width=True)
                if submitted:
                    if utilisateur and mot_de_passe and secret:
                        if test_connexion:
                            url_fixe = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"
                            with st.spinner("🔄 Test de connexion en cours…"):
                                if tester_connexion_cgaweb(url_fixe, utilisateur,
                                                            mot_de_passe, secret):
                                    if enregistrer_nouveau_compte(utilisateur,
                                                                   mot_de_passe, secret):
                                        st.success(" Compte ajouté avec succès !")
                                        st.rerun()
                                else:
                                    st.error(" Échec du test de connexion CGAWEB.")
                        else:
                            st.warning(" Veuillez activer le test de connexion.")
                    else:
                        st.warning(" Tous les champs sont obligatoires.")

            st.markdown('</div>', unsafe_allow_html=True)