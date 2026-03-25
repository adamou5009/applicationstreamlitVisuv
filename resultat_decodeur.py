"""
resultat_decodeur.py
────────────────────
Page de résultat pour une recherche par numéro de décodeur.
Même logique et affichage que resultat_abonne.py — seuls le label et
l'accent couleur diffèrent. Délègue à resultat_fiche.render_fiche().
"""
import streamlit as st
from resultat_fiche import render_fiche


def app():
    render_fiche(
        banner_title     = "Fiche Décodeur",
        banner_subtitle  = "Résultat de l'extraction CGAWEB — recherche par numéro de décodeur.",
        banner_watermark = "DEC",
        label_numero     = "Décodeur",
        avatar_fa        = "fa-solid fa-satellite-dish",
        accent_class     = "accent-cyan",
        avatar_class     = "avatar-cyan",
        progress_class   = "pb-cyan",
        empty_fa         = "fa-solid fa-satellite-dish",
    )