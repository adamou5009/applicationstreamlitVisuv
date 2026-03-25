import streamlit as st
from file_attente import ajouter_requete, lancer_worker
from theme import page_banner, divider

# ═══════════════════════════════════════════════════════════════
# CSS + Font Awesome
# ═══════════════════════════════════════════════════════════════
ACCUEIL_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<style>
.search-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 36px 40px;
    box-shadow: 0 4px 20px rgba(99,102,241,0.08);
    position: relative;
    overflow: hidden;
}
.search-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6366f1, #a855f7, #06b6d4);
    border-radius: 18px 18px 0 0;
}

/* ── Titre section avec icône FA ── */
.section-title-fa {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 14px;
}
.section-title-fa i {
    color: #6366f1;
    font-size: 1.05rem;
    width: 22px;
    text-align: center;
}

/* ── Inputs ── */
div[data-testid="stTextInput"] input {
    border-radius: 12px !important;
    padding: 12px 18px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: #f8fafc !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s ease;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}
div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
}

/* ── Bouton recherche ── */
.search-btn > div > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    width: 100% !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    height: 52px !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    transition: all 0.2s ease !important;
}
.search-btn > div > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Hint méthode ── */
.method-hint {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.method-hint i { color: #6366f1; flex-shrink: 0; }

/* ── Préfixe téléphone ── */
.prefix-box {
    background: #eef2ff;
    border: 1.5px solid #c7d2fe;
    border-radius: 12px;
    text-align: center;
    padding: 12px;
    font-weight: 700;
    color: #4f46e5;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}
.prefix-box i { font-size: 0.85rem; }

/* ── Label input avec icône ── */
.input-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 4px;
}
.input-label i {
    color: #6366f1;
    width: 16px;
    text-align: center;
}
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Mapping type → page résultat
# ═══════════════════════════════════════════════════════════════
PAGE_PAR_TYPE = {
    "Numéro de décodeur":   "resultat_decodeur",
    "Numéro d'abonné":      "resultat_abonne",
    "Numéro de téléphone":  "resultat_telephone",
}

METHODES = list(PAGE_PAR_TYPE.keys())


# ═══════════════════════════════════════════════════════════════
# Helpers HTML
# ═══════════════════════════════════════════════════════════════
def _section_fa(icon_class: str, label: str):
    st.markdown(
        f'<div class="section-title-fa"><i class="{icon_class}"></i>{label}</div>',
        unsafe_allow_html=True,
    )

def _input_label(icon_class: str, texte: str):
    st.markdown(
        f'<div class="input-label"><i class="{icon_class}"></i>{texte}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
def app():
    st.markdown(ACCUEIL_CSS, unsafe_allow_html=True)

    page_banner(
        title="Recherche CGAWEB",
        subtitle=f"Bienvenue, {st.session_state.get('utilisateur_connecte', '')} — lancez une extraction.",
        watermark="CGA"
    )

    _afficher_formulaire()


# ═══════════════════════════════════════════════════════════════
# Formulaire
# ═══════════════════════════════════════════════════════════════
def _afficher_formulaire():
    _, col, _ = st.columns([1, 3, 1])
    with col:
        st.markdown('<div class="search-card">', unsafe_allow_html=True)

        _section_fa("fa-solid fa-magnifying-glass", "Méthode de recherche")

        choix = st.selectbox(
            "Type",
            METHODES,
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        valeur_input = ""

        if choix == "Numéro de décodeur":
            _input_label("fa-solid fa-tv", "Numéro de décodeur")
            valeur_input = st.text_input(
                "Décodeur",
                placeholder="14 chiffres — ex : 22345678901234",
                max_chars=14,
                label_visibility="collapsed",
            )
            st.markdown("""
            <div class="method-hint">
                <i class="fa-solid fa-circle-info"></i>
                Numéro sous votre boîtier ou sur l'emballage.
            </div>""", unsafe_allow_html=True)

        elif choix == "Numéro d'abonné":
            _input_label("fa-solid fa-id-card", "Numéro d'abonné")
            valeur_input = st.text_input(
                "Abonné",
                placeholder="8 chiffres — ex : 22345678",
                max_chars=8,
                label_visibility="collapsed",
            )
            st.markdown("""
            <div class="method-hint">
                <i class="fa-solid fa-circle-info"></i>
                Figure sur votre facture ou contrat CANAL.
            </div>""", unsafe_allow_html=True)

        else:  # Numéro de téléphone
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown("""
                <div class="prefix-box">
                    <i class="fa-solid fa-earth-africa"></i>
                    +237
                </div><br>
                """, unsafe_allow_html=True)
            with c2:
                _input_label("fa-solid fa-mobile-screen", "Numéro de téléphone")
                valeur_input = st.text_input(
                    "Téléphone",
                    placeholder="9 chiffres — ex : 655123456",
                    max_chars=9,
                    label_visibility="collapsed",
                )
            st.markdown("""
            <div class="method-hint">
                <i class="fa-solid fa-circle-info"></i>
                Sans le préfixe pays (237 déjà inclus).
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="search-btn">', unsafe_allow_html=True)
        if st.button("Lancer la recherche", use_container_width=True, key="btn_recherche"):
            _valider_et_envoyer(choix, valeur_input)
        st.markdown('</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Validation, envoi et redirection immédiate
# ═══════════════════════════════════════════════════════════════
def _valider_et_envoyer(type_choisi: str, valeur: str):
    longueurs = {
        "Numéro de décodeur":   14,
        "Numéro d'abonné":       8,
        "Numéro de téléphone":   9,
    }
    min_len = longueurs.get(type_choisi, 8)

    if not valeur or len(valeur.strip()) < min_len:
        st.error(f"Numéro invalide — {min_len} chiffres requis.")
        return

    user_nom = st.session_state.get("utilisateur_connecte", "Utilisateur")
    nouvelle_req = ajouter_requete(
        utilisateur=user_nom,
        type_recherche=type_choisi,
        valeur=valeur.strip(),
    )

    if not nouvelle_req:
        st.error("Erreur lors de l'envoi. Vérifiez votre connexion SQL.")
        return

    # ── Enregistre l'ID et s'assure qu'un worker tourne ──
    st.session_state["req_id"]                = nouvelle_req["id"]
    st.session_state["type_recherche_actuel"] = type_choisi
    st.session_state["requete_en_cours"]      = False  # polling géré par la page résultat
    lancer_worker()

    # ── Redirection immédiate vers la page résultat ───────
    # à resultat_abonne / resultat_decodeur / resultat_telephone.
    st.session_state["page_active"] = PAGE_PAR_TYPE[type_choisi]
    st.rerun()