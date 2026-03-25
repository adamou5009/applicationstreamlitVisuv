import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

from fonction import est_connecte, charger_utilisateurs

# ═══════════════════════════════════════════════════════════════
# Helpers — délèguent TOUT à file_attente.py (SQL + .lock)
# ═══════════════════════════════════════════════════════════════
from file_attente import (
    lire_file        as _lire_file,
    lire_historique  as _lire_historique,
    est_worker_actif as _est_worker_actif,
)

def lire_file():
    """Requêtes en_attente / en_cours depuis la BDD SQL."""
    try:
        return _lire_file() or []
    except Exception:
        return []

def lire_historique():
    """50 dernières requêtes terminées/échouées depuis la BDD SQL."""
    try:
        return _lire_historique() or []
    except Exception:
        return []

def est_worker_actif(worker_id: int) -> bool:
    """
    Lit worker_N.lock (contient le PID du process), vérifie que
    ce PID existe encore — identique à file_attente.est_worker_actif().
    """
    try:
        return _est_worker_actif(worker_id)
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════════
# CSS — Light Luxury Theme
# ═══════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f9f9f9 !important;
    color: #1e293b !important;
}
.stApp { background-color: #f9f9f9 !important; }

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #1e293b !important;
    letter-spacing: 0.01em;
}
h1 { font-size: 2rem !important; }
h2 { font-size: 1.2rem !important; color: #64748b !important;
     text-transform: uppercase; letter-spacing: 0.1em; }

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

/* ── Cartes ── */
.lux-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px 26px;
    margin: 8px 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.lux-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #f59e0b, #d97706);
    border-radius: 14px 0 0 14px;
}
.card-indigo  { background:linear-gradient(135deg,#eef2ff,#e0e7ff); border:1px solid #c7d2fe; }
.card-indigo::before  { background:linear-gradient(180deg,#6366f1,#4f46e5); }
.card-violet  { background:linear-gradient(135deg,#faf5ff,#f3e8ff); border:1px solid #d8b4fe; }
.card-violet::before  { background:linear-gradient(180deg,#a855f7,#9333ea); }
.card-emerald { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border:1px solid #6ee7b7; }
.card-emerald::before { background:linear-gradient(180deg,#10b981,#059669); }
.card-rose    { background:linear-gradient(135deg,#fff1f2,#ffe4e6); border:1px solid #fecdd3; }
.card-rose::before    { background:linear-gradient(180deg,#f43f5e,#e11d48); }
.card-amber   { background:linear-gradient(135deg,#fffbeb,#fef3c7); border:1px solid #fde68a; }
.card-amber::before   { background:linear-gradient(180deg,#f59e0b,#d97706); }
.card-cyan    { background:linear-gradient(135deg,#ecfeff,#cffafe); border:1px solid #a5f3fc; }
.card-cyan::before    { background:linear-gradient(180deg,#06b6d4,#0891b2); }

.card-label {
    font-size: 0.7rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 6px;
}
.card-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem; font-weight: 700; color: #1e293b; line-height: 1.1; margin-bottom: 4px;
}
.card-value-indigo  { color: #4f46e5; }
.card-value-violet  { color: #9333ea; }
.card-value-emerald { color: #059669; }
.card-value-rose    { color: #e11d48; }
.card-value-amber   { color: #d97706; }
.card-value-cyan    { color: #0891b2; }

.card-badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
}
.badge-green  { background:#d1fae5; color:#065f46; }
.badge-red    { background:#ffe4e6; color:#9f1239; }
.badge-amber  { background:#fef3c7; color:#92400e; }
.badge-purple { background:#f3e8ff; color:#6b21a8; }
.badge-blue   { background:#dbeafe; color:#1e40af; }

/* ── Chips ── */
.metric-row { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0; }
.metric-chip {
    border-radius: 12px; padding: 16px 18px; flex: 1;
    min-width: 110px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.chip-indigo  { background:linear-gradient(135deg,#eef2ff,#e0e7ff); border:1px solid #c7d2fe; }
.chip-violet  { background:linear-gradient(135deg,#faf5ff,#f3e8ff); border:1px solid #d8b4fe; }
.chip-emerald { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border:1px solid #6ee7b7; }
.chip-rose    { background:linear-gradient(135deg,#fff1f2,#ffe4e6); border:1px solid #fecdd3; }
.chip-amber   { background:linear-gradient(135deg,#fffbeb,#fef3c7); border:1px solid #fde68a; }
.chip-cyan    { background:linear-gradient(135deg,#ecfeff,#cffafe); border:1px solid #a5f3fc; }
.chip-sky     { background:linear-gradient(135deg,#f0f9ff,#e0f2fe); border:1px solid #bae6fd; }

.metric-chip .chip-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem; font-weight: 700; color: #1e293b; display: block; line-height: 1.2;
}
.metric-chip .chip-lbl {
    font-size: 0.65rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.1em;
}

/* ── Worker rows ── */
.worker-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 9px 0; border-bottom: 1px solid #f1f5f9;
}
.worker-row:last-child { border-bottom: none; }
.worker-name { font-size: 0.85rem; color: #475569; font-weight: 500; }
.worker-dot-on  {
    width:8px; height:8px; border-radius:50%; background:#10b981;
    box-shadow:0 0 5px #10b98188; display:inline-block; margin-right:7px;
}
.worker-dot-off { width:8px; height:8px; border-radius:50%; background:#cbd5e1;
                  display:inline-block; margin-right:7px; }

/* ── Séparateurs ── */
.section-divider {
    height:1px; background:linear-gradient(90deg,transparent,#cbd5e1,transparent);
    margin:32px 0; border:none;
}
.section-header { display:flex; align-items:center; gap:12px; margin:28px 0 18px; }
.section-header .sh-line { flex:1; height:1px; background:linear-gradient(90deg,#94a3b8,transparent); }
.section-header .sh-title {
    font-size:0.7rem; font-weight:700; color:#475569;
    text-transform:uppercase; letter-spacing:0.2em; white-space:nowrap;
}

/* ── Tableaux ── */
[data-testid="stDataFrame"] {
    border:1px solid #e2e8f0 !important; border-radius:10px !important;
    box-shadow:0 1px 4px rgba(0,0,0,0.04) !important;
}

/* ── Download ── */
.stDownloadButton > button {
    background:linear-gradient(135deg,#6366f1,#4f46e5) !important;
    color:#ffffff !important; font-weight:600 !important;
    border:none !important; border-radius:8px !important;
    letter-spacing:0.04em; font-size:0.8rem !important; padding:8px 18px !important;
}

/* ── Bannière ── */
.welcome-banner {
    background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#a855f7 100%);
    border-radius:16px; padding:30px 38px; margin-bottom:28px;
    position:relative; overflow:hidden;
    box-shadow:0 8px 24px rgba(99,102,241,0.25);
}
.welcome-banner::after {
    content:'CGA'; position:absolute; right:32px; top:50%;
    transform:translateY(-50%);
    font-family:'Playfair Display',serif; font-size:5rem; font-weight:700;
    color:rgba(255,255,255,0.08); letter-spacing:0.2em; user-select:none;
}
.welcome-banner h1 {
    margin:0 0 6px !important; border:none !important; padding:0 !important;
    color:#ffffff !important; font-size:1.9rem !important;
}
.welcome-banner p { color:rgba(255,255,255,0.75); font-size:0.9rem; margin:0; }
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Helpers Plotly
# ═══════════════════════════════════════════════════════════════
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#64748b", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(font=dict(color="#475569", size=10)),
)

def pie_chart(labels, values, colors, title, height=240):
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color="#f9f9f9", width=2)),
        textinfo="percent", textfont=dict(color="#1e293b", size=11),
    )])
    fig.update_layout(
        title=dict(text=title, font=dict(color="#475569", size=12), x=0.5, xanchor="center"),
        height=height, showlegend=True, **PLOTLY_BASE
    )
    return fig


def afficher_stats_workers():
    try:
        file_attente = lire_file()
        historique   = lire_historique()

        stats = {
            "en_attente":  len([r for r in file_attente if r.get("statut") == "en_attente"]),
            "en_cours":    len([r for r in file_attente if r.get("statut") == "en_cours"]),
            "terminees":   len([r for r in historique   if r.get("statut") == "terminee"]),
            "echouees":    len([r for r in historique   if r.get("statut") == "echouee"]),
            "abandonnees": len([r for r in historique   if r.get("statut") == "abandonné"]),
        }
        stats["total_file"]       = len(file_attente)
        stats["total_historique"] = len(historique)

        w1 = est_worker_actif(1)
        w2 = est_worker_actif(2)
        nb = sum([w1, w2])

        total_traite  = stats["terminees"] + stats["echouees"] + stats["abandonnees"]
        total_general = total_traite + stats["total_file"]
        progression   = (total_traite / total_general * 100) if total_general > 0 else 0
        base_taux     = stats["terminees"] + stats["echouees"]
        taux          = (stats["terminees"] / max(base_taux, 1)) * 100
        mode_label    = "Parallèle" if nb == 2 else ("Simple" if nb == 1 else "Arrêté")

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.markdown(f"""
            <div class="lux-card card-indigo">
                <div class="card-label">Moteurs de traitement</div>
                <div style="display:flex;align-items:baseline;gap:12px;margin:8px 0 14px;">
                    <div class="card-value card-value-indigo">{nb}<span style="font-size:1rem;color:#94a3b8;">/2</span></div>
                    <span class="card-badge {'badge-green' if nb > 0 else 'badge-red'}">{mode_label}</span>
                </div>
                <div class="worker-row">
                    <span class="worker-name">
                        <span class="{'worker-dot-on' if w1 else 'worker-dot-off'}"></span>Worker 1
                    </span>
                    <span class="card-badge {'badge-green' if w1 else 'badge-red'}">{'Actif' if w1 else 'Inactif'}</span>
                </div>
                <div class="worker-row">
                    <span class="worker-name">
                        <span class="{'worker-dot-on' if w2 else 'worker-dot-off'}"></span>Worker 2
                    </span>
                    <span class="card-badge {'badge-green' if w2 else 'badge-red'}">{'Actif' if w2 else 'Inactif'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="lux-card card-violet">
                <div class="card-label">File d'attente</div>
                <div style="display:flex;align-items:baseline;gap:12px;margin:8px 0 14px;">
                    <div class="card-value card-value-violet">{stats["en_attente"]}</div>
                    <span class="card-badge badge-purple">en attente</span>
                </div>
                <div class="worker-row">
                    <span class="worker-name">⚙️ En traitement</span>
                    <span style="color:#9333ea;font-weight:600;">{stats["en_cours"]}</span>
                </div>
                <div class="worker-row">
                    <span class="worker-name">📊 Progression globale</span>
                    <span style="color:#d97706;font-weight:600;">{progression:.1f} %</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-chip chip-violet">
                <span class="chip-val" style="color:#9333ea;">{stats["en_attente"]}</span>
                <span class="chip-lbl">En attente</span>
            </div>
            <div class="metric-chip chip-indigo">
                <span class="chip-val" style="color:#4f46e5;">{stats["en_cours"]}</span>
                <span class="chip-lbl">En cours</span>
            </div>
            <div class="metric-chip chip-emerald">
                <span class="chip-val" style="color:#059669;">{stats["terminees"]}</span>
                <span class="chip-lbl">Terminées</span>
            </div>
            <div class="metric-chip chip-rose">
                <span class="chip-val" style="color:#e11d48;">{stats["echouees"]}</span>
                <span class="chip-lbl">Échouées</span>
            </div>
            <div class="metric-chip chip-amber">
                <span class="chip-val" style="color:#d97706;">{stats["abandonnees"]}</span>
                <span class="chip-lbl">Abandonnées</span>
            </div>
            <div class="metric-chip chip-sky">
                <span class="chip-val" style="color:#0284c7;">{taux:.1f}%</span>
                <span class="chip-lbl">Taux réussite</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            if stats["total_file"] > 0:
                st.plotly_chart(
                    pie_chart(["En attente", "En cours"],
                              [stats["en_attente"], stats["en_cours"]],
                              ["#a855f7", "#6366f1"], "État de la file"),
                    use_container_width=True, config={"displayModeBar": False}
                )
            else:
                st.markdown(
                    '<div class="lux-card" style="text-align:center;color:#94a3b8;padding:40px;">📭 File vide</div>',
                    unsafe_allow_html=True
                )

        with col2:
            if stats["total_historique"] > 0:
                st.plotly_chart(
                    pie_chart(
                        ["Terminées", "Échouées", "Abandonnées"],
                        [stats["terminees"], stats["echouees"], stats["abandonnees"]],
                        ["#10b981", "#f43f5e", "#f59e0b"],
                        "Résultats historiques"
                    ),
                    use_container_width=True, config={"displayModeBar": False}
                )
            else:
                st.markdown(
                    '<div class="lux-card" style="text-align:center;color:#94a3b8;padding:40px;">Aucun historique</div>',
                    unsafe_allow_html=True
                )

        # ── Contrôle manuel des workers ──────────────────────
        st.markdown("""
        <div class="section-header" style="margin-top:24px;">
            <span class="sh-title">
                <i class="fa-solid fa-sliders" style="margin-right:6px;"></i>
                Contrôle manuel des workers
            </span>
            <div class="sh-line"></div>
        </div>
        """, unsafe_allow_html=True)

        # CSS boutons relance
        st.markdown("""
        <style>
        .btn-relance-on  > div > button {
            background: linear-gradient(135deg,#d1fae5,#a7f3d0) !important;
            color: #065f46 !important;
            border: 1.5px solid #6ee7b7 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            height: 52px !important;
            cursor: default !important;
            box-shadow: none !important;
        }
        .btn-relance-off > div > button {
            background: linear-gradient(135deg,#6366f1,#4f46e5) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
            height: 52px !important;
            box-shadow: 0 4px 12px rgba(99,102,241,0.35) !important;
            letter-spacing: 0.03em !important;
        }
        .btn-relance-off > div > button:hover {
            background: linear-gradient(135deg,#4f46e5,#4338ca) !important;
            box-shadow: 0 6px 16px rgba(99,102,241,0.45) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col_w1, col_w2, col_info = st.columns([1, 1, 2], gap="medium")

        # ── Worker 1 ──────────────────────────────────────────
        with col_w1:
            if w1:
                st.markdown('<div class="btn-relance-on">', unsafe_allow_html=True)
                st.button(
                    "✅  Worker 1 — Actif",
                    key="btn_relance_w1",
                    use_container_width=True,
                    disabled=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#fff1f2,#ffe4e6);
                            border:1px solid #fecdd3;border-radius:10px;
                            padding:10px 14px;margin-bottom:8px;
                            display:flex;align-items:center;gap:8px;">
                    <i class="fa-solid fa-circle-xmark" style="color:#e11d48;font-size:1rem;"></i>
                    <span style="font-size:0.8rem;font-weight:600;color:#9f1239;">Worker 1 inactif</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div class="btn-relance-off">', unsafe_allow_html=True)
                if st.button(
                    "▶  Relancer Worker 1",
                    key="btn_relance_w1",
                    use_container_width=True
                ):
                    try:
                        from file_attente import (
                            supprimer_verrou_worker, creer_verrou_worker,
                            traiter_file_automatique, _workers, _worker_lock
                        )
                        import threading
                        with _worker_lock:
                            supprimer_verrou_worker(1)
                            if creer_verrou_worker(1):
                                t = threading.Thread(
                                    target=traiter_file_automatique,
                                    args=(1,),
                                    daemon=True,
                                    name="Worker-1"
                                )
                                t.start()
                                _workers[1] = t
                        st.success("✅ Worker 1 relancé avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur relance Worker 1 : {e}")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Worker 2 ──────────────────────────────────────────
        with col_w2:
            if w2:
                st.markdown('<div class="btn-relance-on">', unsafe_allow_html=True)
                st.button(
                    "✅  Worker 2 — Actif",
                    key="btn_relance_w2",
                    use_container_width=True,
                    disabled=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#fff1f2,#ffe4e6);
                            border:1px solid #fecdd3;border-radius:10px;
                            padding:10px 14px;margin-bottom:8px;
                            display:flex;align-items:center;gap:8px;">
                    <i class="fa-solid fa-circle-xmark" style="color:#e11d48;font-size:1rem;"></i>
                    <span style="font-size:0.8rem;font-weight:600;color:#9f1239;">Worker 2 inactif</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div class="btn-relance-off">', unsafe_allow_html=True)
                if st.button(
                    "▶  Relancer Worker 2",
                    key="btn_relance_w2",
                    use_container_width=True
                ):
                    try:
                        from file_attente import (
                            supprimer_verrou_worker, creer_verrou_worker,
                            traiter_file_automatique, _workers, _worker_lock
                        )
                        import threading
                        with _worker_lock:
                            supprimer_verrou_worker(2)
                            if creer_verrou_worker(2):
                                t = threading.Thread(
                                    target=traiter_file_automatique,
                                    args=(2,),
                                    daemon=True,
                                    name="Worker-2"
                                )
                                t.start()
                                _workers[2] = t
                        st.success("✅ Worker 2 relancé avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur relance Worker 2 : {e}")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Info card ─────────────────────────────────────────
        with col_info:
            st.markdown(f"""
            <div class="lux-card card-amber" style="padding:18px 22px;">
                <div class="card-label">
                    <i class="fa-solid fa-triangle-exclamation"
                       style="margin-right:5px;color:#d97706;"></i>
                    Pourquoi un worker s'arrête ?
                </div>
                <div style="margin-top:10px;display:flex;flex-direction:column;gap:8px;">
                    <div style="display:flex;align-items:flex-start;gap:8px;">
                        <i class="fa-solid fa-xmark-circle"
                           style="color:#e11d48;margin-top:2px;font-size:0.85rem;flex-shrink:0;"></i>
                        <span style="font-size:0.8rem;color:#78350f;line-height:1.5;">
                            <strong>2 tentatives CGAWEB échouées</strong> — identifiants invalides ou site inaccessible.
                        </span>
                    </div>
                    <div style="display:flex;align-items:flex-start;gap:8px;">
                        <i class="fa-solid fa-gear"
                           style="color:#d97706;margin-top:2px;font-size:0.85rem;flex-shrink:0;"></i>
                        <span style="font-size:0.8rem;color:#78350f;line-height:1.5;">
                            Vérifiez le <strong>compte CGAWEB actif</strong> avant de relancer.
                        </span>
                    </div>
                    <div style="display:flex;align-items:flex-start;gap:8px;">
                        <i class="fa-solid fa-shield-halved"
                           style="color:#059669;margin-top:2px;font-size:0.85rem;flex-shrink:0;"></i>
                        <span style="font-size:0.8rem;color:#78350f;line-height:1.5;">
                            Le <strong>Watchdog</strong> surveille et relance automatiquement toutes les
                            <strong>30 secondes</strong>.
                        </span>
                    </div>
                    <div style="margin-top:6px;padding-top:8px;border-top:1px solid #fde68a;
                                display:flex;align-items:center;gap:8px;">
                        <i class="fa-solid fa-circle{'  worker-dot-on' if (w1 or w2) else ''}"
                           style="color:{'#10b981' if (w1 or w2) else '#cbd5e1'};font-size:0.7rem;"></i>
                        <span style="font-size:0.75rem;font-weight:600;
                                     color:{'#065f46' if (w1 or w2) else '#64748b'};">
                            Système {'opérationnel' if (w1 or w2) else 'arrêté — relance requise'}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Requêtes en cours ───────────────────────────────
        en_cours_list = [r for r in file_attente if r.get("statut") == "en_cours"]
        if en_cours_list:
            with st.expander(f"🔍  {len(en_cours_list)} requête(s) en cours"):
                for req in en_cours_list:
                    cols = st.columns([1, 1, 2, 2])
                    cols[0].markdown(f"**`{req.get('id','?')}`**")
                    cols[1].markdown(f"W{req.get('worker_id','?')}")
                    cols[2].markdown(f"`{req.get('utilisateur','?')}`")
                    cols[3].markdown(f"{req.get('valeur','?')}")

        # ── Historique récent ───────────────────────────────
        if stats["total_historique"] > 0:
            with st.expander("🕓  20 dernières requêtes"):
                df = pd.DataFrame(historique[-20:][::-1])
                if not df.empty:
                    cols_want = ["id", "utilisateur", "type_recherche", "valeur", "statut"]
                    df = df[[c for c in cols_want if c in df.columns]]

                    def color_st(v):
                        if v == "terminee":  return "background-color:#d1fae5;color:#065f46"
                        if v == "echouee":   return "background-color:#ffe4e6;color:#9f1239"
                        if v == "abandonné": return "background-color:#fef3c7;color:#92400e"
                        return ""

                    styled = df.style.map(color_st, subset=["statut"]) if "statut" in df.columns else df
                    st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Performance par utilisateur ─────────────────────
        if stats["total_historique"] > 0:
            with st.expander("👥  Performance par utilisateur"):
                df_h = pd.DataFrame(historique)
                if "utilisateur" in df_h.columns:
                    su = df_h.groupby("utilisateur").agg(
                        Total       =("id",     "count"),
                        Reussies    =("statut", lambda x: (x == "terminee").sum()),
                        Abandonnees =("statut", lambda x: (x == "abandonné").sum()),
                    ).reset_index()
                    su.columns     = ["Utilisateur", "Total", "Réussies", "Abandonnées"]
                    su["Échouées"] = su["Total"] - su["Réussies"] - su["Abandonnées"]
                    su["Taux (%)"] = (su["Réussies"] / su["Total"] * 100).round(1)
                    st.dataframe(
                        su.sort_values("Total", ascending=False),
                        use_container_width=True, hide_index=True
                    )

    except Exception as e:
        st.warning(f"⚠️ Données workers indisponibles : {e}")


# ═══════════════════════════════════════════════════════════════
# Section 2 : Journal utilisateurs
# ═══════════════════════════════════════════════════════════════
def afficher_stats_utilisateurs():
    try:
        df_u     = charger_utilisateurs()
        nb_total = df_u["username"].nunique() if not df_u.empty else 0
    except Exception:
        nb_total = 0

    FICHIER_LOG = "journal_actions.csv"
    if not os.path.exists(FICHIER_LOG):
        st.markdown('<div class="lux-card" style="color:#6b7a8d;">⚠️ Fichier journal introuvable.</div>', unsafe_allow_html=True)
        return

    try:
        data = pd.read_csv(FICHIER_LOG)
    except Exception as e:

        print(f"❌ Lecture du journal impossible : {e}")
        return

    if data.empty:
        st.info("Le journal est vide.")
        return

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data          = data.dropna(subset=["date"])

    col1, col2, col3 = st.columns([1, 1, 2], gap="medium")
    with col1:
        utilisateurs = sorted(data["utilisateur"].dropna().unique().tolist())
        user_sel     = st.selectbox("Utilisateur", utilisateurs)
    with col2:
        d_min, d_max = data["date"].min().date(), data["date"].max().date()
        date_range   = st.date_input("Période", [d_min, d_max])
    with col3:
        actions = sorted(data["action"].dropna().unique().tolist())
        with st.expander("Filtrer les actions"):
            act_sel = st.multiselect("", actions, default=actions,
                                     key="actions_ms", label_visibility="collapsed")

    f_date = (data["date"].dt.date >= date_range[0]) & (data["date"].dt.date <= date_range[1])
    f_act  = data["action"].isin(act_sel)
    f_user = data["utilisateur"] == user_sel
    df_f   = data[f_user & f_date & f_act]

    seuil   = pd.Timestamp.now() - pd.Timedelta(minutes=10)
    nb_j    = data[f_date & f_act]["utilisateur"].nunique()
    conn    = data[f_date & f_act & (data["date"] > seuil)]["utilisateur"].nunique()
    nb_ok   = int((df_f["action"] == "recherche").sum())
    nb_ko   = int((df_f["action"] == "recherche non aboutie").sum())
    nb_reac = int((df_f["action"] == "reactivation").sum())
    nb_suiv = int((df_f["action"] == "suivi abonne").sum())

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-chip chip-amber">
            <span class="chip-val" style="color:#d97706;">{nb_total}</span>
            <span class="chip-lbl">Utilisateurs total</span>
        </div>
        <div class="metric-chip chip-indigo">
            <span class="chip-val" style="color:#4f46e5;">{nb_j}</span>
            <span class="chip-lbl">Dans le journal</span>
        </div>
        <div class="metric-chip chip-emerald">
            <span class="chip-val" style="color:#059669;">{conn}</span>
            <span class="chip-lbl">Actifs 10 min</span>
        </div>
        <div class="metric-chip chip-cyan">
            <span class="chip-val" style="color:#0891b2;">{nb_ok}</span>
            <span class="chip-lbl">Recherches OK</span>
        </div>
        <div class="metric-chip chip-rose">
            <span class="chip-val" style="color:#e11d48;">{nb_ko}</span>
            <span class="chip-lbl">Recherches KO</span>
        </div>
        <div class="metric-chip chip-violet">
            <span class="chip-val" style="color:#9333ea;">{nb_reac}</span>
            <span class="chip-lbl">Réactivations</span>
        </div>
        <div class="metric-chip chip-sky">
            <span class="chip-val" style="color:#0284c7;">{nb_suiv}</span>
            <span class="chip-lbl">Suivi abonné</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not df_f.empty:
        ac         = df_f["action"].value_counts().reset_index()
        ac.columns = ["Action", "Nombre"]
        ac["Action"] = ac["Action"].str.replace("_", " ").str.capitalize()

        palette = ["#6366f1", "#a855f7", "#10b981", "#f43f5e", "#06b6d4", "#f59e0b", "#0284c7"]
        fig = px.bar(ac, x="Nombre", y="Action", orientation="h",
                     color="Action", color_discrete_sequence=palette)
        fig.update_traces(marker_line_width=0, opacity=0.85)
        fig.update_layout(
            title=dict(text="Répartition des actions", font=dict(color="#475569", size=12), x=0.5),
            height=300, showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", color="#64748b"),
            yaxis=dict(showgrid=False, color="#64748b"),
            **PLOTLY_BASE
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown('<div class="lux-card" style="text-align:center;color:#94a3b8;padding:30px;">Aucune donnée pour ces filtres</div>', unsafe_allow_html=True)

    with st.expander("📄  Journal détaillé"):
        st.dataframe(df_f.sort_values("date", ascending=False),
                     use_container_width=True, hide_index=True)

    if not df_f.empty:
        out = BytesIO()
        df_f.to_excel(out, index=False, sheet_name="Journal")
        out.seek(0)
        st.download_button(
            "📥  Exporter en Excel",
            data=out,
            file_name="journal_filtre.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ═══════════════════════════════════════════════════════════════
# Assemblage final
# ═══════════════════════════════════════════════════════════════
def afficher_tableau_de_bord():
    st.markdown(CSS, unsafe_allow_html=True)

    user = st.session_state.get("utilisateur_connecte", "")
    st.markdown(f"""
    <div class="welcome-banner">
        <h1>Tableau de Bord</h1>
        <p>Bienvenue, <strong style="color:#e6c97a;">{user}</strong>
           &nbsp;·&nbsp; Vue d'ensemble du système VISUV CGA</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <span class="sh-title">⚡ Workers &amp; File d'attente</span>
        <div class="sh-line"></div>
    </div>
    """, unsafe_allow_html=True)
    afficher_stats_workers()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <span class="sh-title">👥 Activité Utilisateurs</span>
        <div class="sh-line"></div>
    </div>
    """, unsafe_allow_html=True)
    afficher_stats_utilisateurs()


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════
def app():
    if not est_connecte():
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()
    afficher_tableau_de_bord()


if __name__ == "__main__":
    app()