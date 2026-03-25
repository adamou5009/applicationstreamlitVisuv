import streamlit as st
from datetime import date
import time
from selenium.webdriver.support.ui import WebDriverWait

from theme import apply_theme, page_banner
from fonction import (
    connexion_savant,
    naviguer_page_intervention,
    activer_et_selectionner_dates,
    selectionner_statuts,
    selectionner_statut_temporaire,
    extraire_tableau,
    extraire_interventions_temporaire,
    generer_excel_multi_feuilles,
    est_statut_temporaire,
    demander_arret,
    reset_arret,
    arret_demande
    

)
  
import os
import shutil
import tempfile
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options


class WebDriverManager:
    def __init__(self):
        self.driver = None
        self.temp_dir = None

    def _is_streamlit_cloud(self):
        """Détecte si on tourne sur Streamlit Cloud (Linux sans display)."""
        return os.path.exists("/usr/bin/chromium-browser") or \
               os.path.exists("/usr/bin/chromium")

    def _get_chrome_binary(self):
        """Retourne le bon chemin binaire Chrome/Chromium selon l'environnement."""
        candidates = [
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _get_chromedriver_path(self):
        """Retourne le bon chromedriver selon l'environnement."""
        candidates = [
            "/usr/lib/chromium-browser/chromedriver",
            "/usr/bin/chromedriver",
            "/usr/lib/chromium/chromedriver",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def start_driver(self, headless=True):
        """Lance Chrome/Chromium automatiquement selon l'environnement."""

        # Vérifie session existante
        if self.driver:
            try:
                _ = self.driver.title
                return self.driver
            except Exception:
                print("⚠️ Session expirée. Redémarrage...")
                self.stop_driver()

        options = Options()

        # Profil isolé unique
        unique_id = str(uuid.uuid4())
        self.temp_dir = os.path.join(
            tempfile.gettempdir(),
            f"chrome_session_{os.getpid()}_{unique_id}"
        )
        options.add_argument(f"--user-data-dir={self.temp_dir}")

        # Options communes
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        if headless:
            options.add_argument("--headless=new")

        try:
            binary = self._get_chrome_binary()
            driver_path = self._get_chromedriver_path()

            if binary:
                options.binary_location = binary
                print(f"🌐 Binaire détecté : {binary}")

            if driver_path:
                # Streamlit Cloud : driver système
                print(f"🔧 Chromedriver détecté : {driver_path}")
                service = ChromeService(executable_path=driver_path)
            else:
                # Fallback local : webdriver-manager télécharge automatiquement
                print("📦 Téléchargement automatique du chromedriver...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = ChromeService(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)

            print("✅ Chrome démarré avec succès")
            return self.driver

        except Exception as e:
            print(f"❌ Échec démarrage navigateur : {e}")
            self.cleanup_temp()
            raise e

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
                self.cleanup_temp()
                print("🛑 Navigateur fermé")

    def cleanup_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            finally:
                self.temp_dir = None



TIMEOUT = 120

# =====================================================
# PAGE EXTRACTION
# =====================================================
def app():

    # ── Thème global VISUV ────────────────────────────
    apply_theme()

    # ── Bannière de page ──────────────────────────────
    page_banner(
        title="Extraction des interventions Alonwa",
        subtitle="Sélectionnez vos filtres et lancez l'extraction automatisée",
        watermark="EXT"
    )

    # =====================================================
    # CONNEXION
    # =====================================================
    with st.expander("👤 Connexion Alonwa", expanded=True):
        col1, col2 = st.columns(2)
        username = col1.text_input("Identifiant")
        password = col2.text_input("Mot de passe", type="password")

    # =====================================================
    # FILTRES
    # =====================================================
    with st.expander("🔎 Filtres d'extraction", expanded=True):
        col3, col4 = st.columns(2)
        date_debut = col3.date_input("Date début", value=date.today().replace(day=1))
        date_fin   = col4.date_input("Date fin",   value=date.today())

        statuts_disponibles = [
            "Acceptée", "Annulée", "A planifier", "A qualifier",
            "A réconcilier", "Planifiée", "Temporaire",
            "Terminée KO Canal", "Terminée KO Client",
            "Terminée OK", "Validée",
        ]

        statuts_choisis = st.multiselect(
            "Statuts à extraire",
            statuts_disponibles,
            default=["Terminée OK"],
        )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # =====================================================
    # BOUTONS
    # =====================================================
    col_run, col_stop = st.columns(2)
    lancer = col_run.button("▶️ Extraire",  use_container_width=True)
    stop   = col_stop.button("⛔ Arrêter", use_container_width=True)

    if stop:
        demander_arret()
        st.warning("⛔ Arrêt demandé… récupération des données en cours")

    # =====================================================
    # LANCEMENT
    # =====================================================
    data_temporaire = []
    data_autres     = []
    excel_buffer    = None

    if lancer:
        if not username or not password or not statuts_choisis:
            st.error("❌ Tous les champs sont obligatoires")
            return

        reset_arret()
        progress = st.progress(0)
        info     = st.empty()

        driver = WebDriverManager().start_driver()   # headless=True par défaut
        wait   = WebDriverWait(driver, TIMEOUT)

        try:
            # CONNEXION
            info.info("🔐 Connexion à SAVANT…")
            ok, driver, wait = connexion_savant(
                driver,
                "https://serviceplus.canal-plus.com/index.php?action=GET_LOGIN",
                username,
                password,
            )
            if not ok or arret_demande():
                return
            progress.progress(10)

            # NAVIGATION
            info.info("🗂️ Accès à la page Intervention…")
            if not naviguer_page_intervention(driver, wait) or arret_demande():
                return
            progress.progress(20)
            time.sleep(1)

            # DATES
            info.info("📅 Application de la période…")
            activer_et_selectionner_dates(
                driver, wait,
                date_debut.strftime("%d/%m/%Y"),
                date_fin.strftime("%d/%m/%Y"),
            )
            progress.progress(30)

            # PIPELINE TEMPORAIRE
            if est_statut_temporaire(statuts_choisis) and not arret_demande():
                info.info("⏳ Extraction des interventions TEMPORAIRE…")
                selectionner_statut_temporaire(driver, wait)
                progress.progress(45)
                data_temporaire = extraire_interventions_temporaire(driver, wait)
                progress.progress(60)

            # PIPELINE AUTRES STATUTS
            autres_statuts = [s for s in statuts_choisis if s != "Temporaire"]
            if autres_statuts and not arret_demande():
                info.info("📋 Extraction des autres statuts…")
                selectionner_statuts(driver, wait, autres_statuts)
                time.sleep(1)
                progress.progress(70)
                data_autres = extraire_tableau(driver, wait, autres_statuts)
                progress.progress(85)

        except Exception as e:
            st.error("❌ Erreur critique pendant l'extraction")
            st.exception(e)

        finally:
            if driver is not None:   # ✅ Vérifie avant de quitter
                try:
                    driver.quit()
                except Exception:
                    pass
            st.info("🛑 Navigateur fermé")

        # =============================================
        # EXPORT EXCEL
        # =============================================
        excel_buffer = generer_excel_multi_feuilles(data_temporaire, data_autres)
        progress.progress(100)

        if arret_demande():
            info.warning("⚠️ Extraction arrêtée – données partielles disponibles")
        else:
            info.success("✅ Extraction terminée avec succès")

    # =====================================================
    # TÉLÉCHARGEMENT + RÉSUMÉ
    # =====================================================
    if excel_buffer and (data_temporaire or data_autres):

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=excel_buffer,
            file_name="extraction_interventions_savant.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # Résumé avec les chips du thème
        st.markdown(f"""
        <div class="metric-row">
            <div class="chip chip-amber">
                <span class="chip-val val-amber">{len(data_temporaire)}</span>
                <span class="chip-lbl">Temporaire</span>
            </div>
            <div class="chip chip-emerald">
                <span class="chip-val val-emerald">{len(data_autres)}</span>
                <span class="chip-lbl">Autres statuts</span>
            </div>
            <div class="chip chip-indigo">
                <span class="chip-val val-indigo">{len(data_temporaire) + len(data_autres)}</span>
                <span class="chip-lbl">Total extrait</span>
            </div>
        </div>
        """, unsafe_allow_html=True)