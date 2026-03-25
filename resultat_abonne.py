"""
resultat_abonne.py
──────────────────
Page de résultat pour une recherche par numéro d'abonné.
Délègue entièrement l'affichage à resultat_fiche.render_fiche().
"""
import streamlit as st
from resultat_fiche import render_fiche


def app():
    render_fiche(
        banner_title     = "Fiche Abonné",
        banner_subtitle  = "Résultat de l'extraction CGAWEB — recherche par numéro d'abonné.",
        banner_watermark = "ABO",
        label_numero     = "Abonné",
        avatar_fa        = "fa-solid fa-circle-user",
        accent_class     = "accent-indigo",
        avatar_class     = "avatar-indigo",
        progress_class   = "pb-indigo",
        empty_fa         = "fa-solid fa-magnifying-glass",
    )