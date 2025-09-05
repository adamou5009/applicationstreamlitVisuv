# --------------------- IMPORTS ---------------------
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import time
import hashlib
import os     
import json
import time 


# --- Initialisation driver Edge sans affichage ---
def init_edge_driver(headless=True):  # ✅ Toujours en headless
    print("🔄 Initialisation du navigateur Edge en arrière-plan...")

    options = EdgeOptions()
    if headless:
        options.add_argument("--headless")  # Headless récent (Edge >= v109)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Réduction des traces automatisation
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    chemin_driver = os.path.join("C:\\Users\\COSTA\\MonApplication", "msedgedriver.exe")
    if not os.path.exists(chemin_driver):
        raise FileNotFoundError("❌ Le fichier msedgedriver.exe est introuvable.")

    service = EdgeService(executable_path=chemin_driver)
    driver = webdriver.Edge(service=service, options=options)
    return driver

def identifiants_cgaweb_rpe():
    """
    Priorité aux identifiants saisis via le formulaire de la page RPE.
    Sinon, utilise ceux du .env.
    """
    user = st.session_state.get("rpe_user")
    pwd = st.session_state.get("rpe_pass")

    if user and pwd:
        print("🔐 Utilisation des identifiants RPE de session.")
        return user, pwd
    else:
        # Fallback : identifiants depuis le .env
        from dotenv import load_dotenv
        load_dotenv()
        env_user = os.getenv("CGAWEB_USER_RPE")
        env_pwd = os.getenv("CGAWEB_PASS_RPE")
        print("📦 Utilisation des identifiants RPE du .env.")
        return env_user, env_pwd


    # Fallback vers les identifiants du fichier .env
    #user = os.getenv("CGAWEB_USER")
    #pwd = os.getenv("CGAWEB_PASSWORD")
    #print("🔐 Utilisation des identifiants du .env.")
    #return user, pwd

def tester_connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True):
    """
    Teste la connexion à CGAWEB avec les identifiants fournis.
    Retourne True si la connexion réussit, False sinon.
    Ferme toujours le driver Selenium proprement.
    """
    driver = None
    try:
        # Tentative de connexion
        driver, original_window, new_window = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=headless)

        # Connexion réussie, on attend un peu pour s'assurer que la page a fini de charger
        time.sleep(5)

        # Déconnexion propre
        deconnexion_cgaweb(driver)

        # Fermeture du driver Selenium
        driver.quit()

        return True

    except Exception as e:
        print(f"[ERREUR] Test connexion CGAWEB : {e}")

        # Tenter de fermer le driver même en cas d'erreur
        try:
            if driver:
                driver.quit()
        except Exception as e2:
            print(f"[ERREUR] Fermeture du driver : {e2}")

        return False



def charger_compte_actif():
    if "cgaweb_user" not in st.session_state or "cgaweb_pass" not in st.session_state:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        accounts_file = os.path.join(BASE_DIR, "cgaweb_accounts.json")
        if os.path.exists(accounts_file):
            with open(accounts_file, "r", encoding="utf-8") as f:
                comptes = json.load(f)
                if comptes:
                    # Choisir le compte activé, ou le premier par défaut
                    st.session_state["cgaweb_user"] = comptes[0]["user"]
                    st.session_state["cgaweb_pass"] = comptes[0]["pass"]


# --- Connexion CGAWEB ---
def connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True):
    print(" Début de connexion à CGAWEB...")
    driver = None
    try:
        driver = init_edge_driver(headless=headless)
        print("✅ Navigateur lancé avec succès.")
    except FileNotFoundError as e:
        print(str(e))
        return None, None, None
    except WebDriverException as e:
        st.error("❌ Edge ne démarre pas. Vérifiez que Microsoft Edge est installé et à jour.")
        print(f"❌ Erreur : {e}")
        return None, None, None

    try:
        driver.get(url)
        print("🔐 Remplissage du formulaire de connexion...")
        driver.find_element(By.ID, "cuser").send_keys(utilisateur)
        driver.find_element(By.ID, "pass").send_keys(mot_de_passe)
        print("🔄 Envoi du formulaire...")
        driver.find_element(By.NAME, "login").click()
        print("✅ Formulaire envoyé, attente de la réponse...")

        try:
            message_erreur = driver.find_element(By.XPATH, "//div[contains(@style, 'color: #CE0000')]")
            if message_erreur.is_displayed():
                message = message_erreur.text.strip()
                st.error(f"❌ Connexion échouée : {message}")
                print(f"❌ Erreur de connexion : {message}")
                driver.quit()
                return None, None, None
        except:
            print("✅ Aucun message d'erreur trouvé")

        time.sleep(2)
        print("🧭 Navigation dans les frames de CGAWEB...")

        original_window = driver.current_window_handle
        all_windows_before = driver.window_handles
        print("✅ Fenêtre principale stockée.")

        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "titleFrame")))
        driver.find_element(By.ID, "ss").click()
        print("🖱️ Clique sur le bouton 'ss'")

        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(len(all_windows_before) + 1))
        print("✅ Nouveau popup détecté.")

        new_window = None
        for handle in driver.window_handles:
            if handle != original_window:
                new_window = handle
                break

        if new_window:
            st.success("Connexion réussie à CGAWEB.")
            return driver, original_window, new_window
        else:
            raise Exception("❌ Impossible de détecter la nouvelle fenêtre popup.")

    except Exception as e:
        print(f"❌ Une erreur technique est survenue : {e}")
        st.error("❌ Une erreur technique est survenue lors de la connexion à CGAWEB.")
        try:
            if driver:
                deconnexion_cgaweb(driver)
        except Exception as ex:
            print(f"⚠️ Problème lors de la tentative de fermeture du navigateur : {ex}")
        return None, None, None

# --- Déconnexion CGAWEB ---
def deconnexion_cgaweb(driver):
    try:
        if driver:
            print("🔌 Déconnexion de CGAWEB...")

            # --- Revenir sur la fenêtre principale ---
            if len(driver.window_handles) > 1:
                # Fermer les fenêtres secondaires
                for handle in driver.window_handles[1:]:
                    driver.switch_to.window(handle)
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])

            # --- Revenir au frame principal ---
            driver.switch_to.default_content()
            driver.switch_to.frame("titleFrame")

            # --- Cliquer sur le bouton déconnexion ---
            driver.find_element(By.XPATH, "//a[contains(@href, 'DeconnexionServlet')]").click()
            print("✅ Déconnexion effectuée.")
    except Exception as e:
        print(f"❌ Problème lors de la déconnexion : {e}")
    finally:
        if driver:
            driver.quit()

# --- Recherche par décodeur ---
def rechercher_par_decodeur(driver, num_decodeur, original_window, new_window):
    try:
        driver.switch_to.window(new_window)
        print("🧭 Navigué vers la fenêtre popup de recherche.")

        champ_numdec = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "numdec"))
        )
        champ_numdec.clear()
        champ_numdec.send_keys(num_decodeur)
        print(f"🔢 Numéro de décodeur {num_decodeur} saisi.")

        driver.find_element(By.NAME, "search").click()
        print("🔍 Recherche lancée.")

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            message = alert.text
            alert.accept()
            print(f"⚠️ Alerte détectée : {message}")
            return None
        except TimeoutException:
            pass

        lien = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#subscriberDTABLE a"))
        )
        numero_abonne = lien.text.strip()
        lien.click()
        print(f"🔗 Lien vers l'abonné {numero_abonne} cliqué.")

        # Retour à la fenêtre principale
        driver.switch_to.window(original_window)
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "_right"))
        )

        fiche_abonnes = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "view-contract"))
        )
        print("📄 Fiche d'abonné chargée avec succès.")
        return numero_abonne, fiche_abonnes

    except Exception as e:
        print(f"❌ Erreur lors de la recherche par décodeur : {e}")
        if driver:
            try:
                deconnexion_cgaweb(driver)
            except Exception as ex:
                print(f"⚠️ Problème lors de la tentative de fermeture du navigateur : {ex}")
        st.error("❌ Erreur lors de la recherche par décodeur !")
        return None

# --- Extraction numéro de téléphone ---
def extraire_telephone(driver, fiche_abonnes):
    """
    Extrait le téléphone, le nom de l'abonné et la période d'abonnement
    depuis la fiche_abonnes avant de cliquer sur 'view-contract-anchor'.

    Retourne : (telephone, nom_abonne, date_debut, date_fin)
    """
    try:
        # 1️⃣ Cliquer sur le lien "Adresse"
        lien_adresse = fiche_abonnes.find_element(
            By.XPATH, "//a[contains(@href, 'modaddress.do') and contains(text(), 'Adresse')]"
        )
        lien_adresse.click()

        # 2️⃣ Extraire le téléphone dans le frame _right
        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "_right"))
        )

        WebDriverWait(driver, 20).until(
            lambda drv: len(drv.find_elements(By.NAME, "mobile1")) >= 4
        )
        inputs = driver.find_elements(By.NAME, "mobile1")
        if len(inputs) >= 4:
            telephone = ''.join(inp.get_attribute("value").strip() for inp in inputs[1:4])
        else:
            telephone = "N/A"
        print(f"📞 Téléphone extrait : {telephone}")

        inputs_2 = driver.find_elements(By.NAME, "mobile2")
        if len(inputs_2) >= 4:
            telephone_2 = ''.join(inp.get_attribute("value").strip() for inp in inputs_2[1:4])
        else:
            telephone_2 = "N/A"
        print(f"📞 Téléphone extrait : {telephone_2}")


        # 3️⃣ Extraire nom et période dans titleFrame
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "titleFrame"))
        )

        # Nom abonné
        try:
            element_nom = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "names"))
            )
            nom_abonne = element_nom.find_element(By.TAG_NAME, "b").text.strip()
            print(f"👤 Nom abonné trouvé : {nom_abonne}")
        except Exception:
            nom_abonne = None
            print("⚠️ Nom d'abonné introuvable.")

        # Période d'abonnement
        date_debut, date_fin = None, None
        try:
            element_periode = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "period"))
            )
            texte_periode = element_periode.text.strip()
            print(f"📅 Texte période trouvé : '{texte_periode}'")

            if "Période :" in texte_periode:
                texte_periode = texte_periode.replace("Période :", "").strip()
            if "-" in texte_periode:
                date_debut, date_fin = [d.strip() for d in texte_periode.split("-", 1)]
        except Exception:
            print("⚠️ Élément #period introuvable ou mal formé.")

        # 4️⃣ Cliquer sur view-contract-anchor si nécessaire
        for _ in range(2):  # retry en cas de stale element
            try:
                lien_contrat = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "view-contract-anchor"))
                )
                lien_contrat.click()
                break
            except StaleElementReferenceException:
                print("⚠️ Élément 'view-contract-anchor' obsolète, tentative de rechargement...")
                time.sleep(1)

        return telephone, nom_abonne, date_debut, date_fin, telephone_2

    except Exception as e:
        print(f"❌ Erreur extraction téléphone + infos : {e}")
        return "N/A", None, None, None, None


    except Exception as e:
        print(f"❌ Erreur extraction téléphone + clic contrat : {e}")
        return "N/A"
# Extraction de la date de fin 

# --- ----------------Extraction infos abonné ---
def extraire_infos_abonne(fiche_abonnes, num_decodeur, driver, numero_abonne):
    infos = {
    "numero_decodeur": num_decodeur,
    "nom_abonne": "",
    "numero_abonne": numero_abonne,
    "date_recrutement": "",
    "num_distributeur": "",
    "nom_distributeur": "",
    "telephone": "",
    "telephone_2": "",
    "fin_abonnement": "",
    "statut": "",
    "detail-statut": "",
    "temps_traitement (sec)": "",
    "temps_moyen_traitement (sec)": "",
}


    try:
        infos.update({
            "num_distributeur": fiche_abonnes.find_element(By.ID, "numdist").text.strip(),
            "nom_distributeur": fiche_abonnes.find_element(By.ID, "nomdist").text.strip(),
            #"telephone": extraire_telephone(driver, fiche_abonnes),
        })

        # Récupération de la période d'abonnement
        telephone, nom_abonne, date_debut, date_fin, telephone_2 = extraire_telephone(driver, fiche_abonnes)
        infos["date_recrutement"] = date_debut
        infos["fin_abonnement"] = date_fin
        infos["nom_abonne"] = nom_abonne
        infos["telephone"] = telephone
        infos["telephone_2"] = telephone_2

        print("nom_abonne:", infos["nom_abonne"])
        print("num_distributeur:", infos["num_distributeur"])
        print("nom_distributeur:", infos["nom_distributeur"])
        print("numero_abonne:", infos["numero_abonne"])
        print("telephone:", infos["telephone"])
        print("telephone_2:", infos["telephone_2"])
        print("date_recrutement:",infos["date_recrutement"])
        print("fin_abonnement:", infos["fin_abonnement"])

        # Vérification sécurisée de la date
        if infos["fin_abonnement"]:
            date_fin_dt = datetime.strptime(infos["fin_abonnement"], "%d/%m/%Y")
            delta = (date_fin_dt - datetime.now()).days
            if delta > 0:
                infos["statut"] = "Actif"
                infos["detail-statut"] = f"Reste {delta} jours"
            elif delta == -1:
                infos["statut"] = "Actif"
                infos["detail-statut"] = "Expire aujourd’hui"
            else:
                infos["statut"] = "Échu"
                infos["detail-statut"] = f"depuis {abs(delta)} jours"
        else:
            infos["statut"] = "Inconnu"
            infos["detail-statut"] = "Impossible de récupérer la date"

        print("Statut:", infos["statut"])
        print("Détail statut:", infos["detail-statut"])
        return infos

    except Exception as e:
        print(f"❌ Erreur extraction infos : {e}")
        return None



# --- Traitement décodeurs ---

def traiter_decodeurs(driver, df, original_window, new_window, statut_txt=None, progress_bar=None):
    resultats = []
    traitements = []
    total = len(df)

    for i, num in enumerate(df["numéro de décodeur"].dropna(), 1):
        if st.session_state.get("stop_processing", False):
            if statut_txt:
                statut_txt.text("⏸️ Traitement interrompu par l'utilisateur.")
            break

        debut = time.time()
        try:
            res = rechercher_par_numero(driver, str(num), original_window, new_window)
            if res:
                numero_abonne, fiche_abonne = res
                infos = extraire_infos_abonne(fiche_abonne, str(num), driver, numero_abonne)
                if infos:
                    tps = round(time.time() - debut, 2)
                    traitements.append(tps)
                    infos["temps_traitement (sec)"] = tps
                    resultats.append(infos)
                    print(f"✅ Traitement réussi pour décodeur {num} / abonné {numero_abonne}")
                    maj_progression(i, total, statut_txt, progress_bar)
                    print(f"{i}/ {total}")
                    continue

            tps = round(time.time() - debut, 2)
            traitements.append(tps)
            resultats.append({
                "numero_decodeur": num,
                "numero_abonne": "Non trouvé",
                "nom_abonne": "Non trouvé",
                "num_distributeur": "Non trouvé",
                "nom_distributeur": "Non trouvé",
                "telephone": "Non trouvé",
                "fin_abonnement": "Non trouvé",
                "date_recrutement": "Non trouvé",
                "statut": "Non trouvé",
                "detail_statut": "Non trouvé",
                "temps_traitement (sec)": tps,
                "temps_moyen_traitement (sec)": ""
            })
            print(f"⚠️ Décodeur {num} non trouvé ou erreur dans l'extraction.")
            #maj_progression(i, total, statut_txt, progress_bar)

        except Exception as e:
            print(f"⚠️ Erreur traitement {num} : {e}")

        

    if traitements:
        temps_moyen = round(sum(traitements) / len(traitements), 2)
        print(f"⏱️ Temps moyen de traitement par décodeur : {temps_moyen} secondes")
        for r in resultats:
            r["temps_moyen_traitement (sec)"] = temps_moyen

    return resultats

# fonction de progression
def maj_progression(i, total, statut_txt=None, progress_bar=None, sleep_time=0.05):
    """
    Met à jour le texte de statut et la barre de progression.

    i : numéro d'élément en cours de traitement (1-based)
    total : nombre total d'éléments à traiter
    statut_txt : élément Streamlit text() (optionnel)
    progress_bar : élément Streamlit progress() (optionnel)
    sleep_time : temps d'attente pour forcer le rafraîchissement UI
    """
    if statut_txt:
        pourcentage = int((i / total) * 100)
        statut_txt.text(f"Traitement : {pourcentage}% ({i} sur {total})")

    if progress_bar:
        progress_bar.progress(i / total)
        time.sleep(sleep_time)



# --- Traitement multi-navigateurs ---
def traiter_decodeurs_multi_navigateurs(df, url, utilisateur, mot_de_passe, statut_txt=None, progress_bar=None, session_state=None):
    # ⚙️ Si identifiants RPE sont présents dans session_state, on les utilise en priorité
    if session_state:
        utilisateur_rpe = session_state.get("rpe_utilisateur")
        mot_de_passe_rpe = session_state.get("rpe_mot_de_passe")
        if utilisateur_rpe and mot_de_passe_rpe:
            utilisateur = utilisateur_rpe
            mot_de_passe = mot_de_passe_rpe

    df_pairs = df[df.index % 2 == 0].reset_index(drop=True)
    df_impairs = df[df.index % 2 != 0].reset_index(drop=True)

    resultats1, resultats2 = [], []

    try:
        # Connexion navigateurs
        driver1, original_window1, new_window1 = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)
    except Exception as e:
        print(f"❌ Échec de connexion navigateur 1 : {e}")
        driver1 = None

    try:
        driver2, original_window2, new_window2 = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)
    except Exception as e:
        print(f"❌ Échec de connexion navigateur 2 : {e}")
        driver2 = None

    from concurrent.futures import ThreadPoolExecutor

    def traiter(driver, sous_df, original_window, new_window):
        try:
            return traiter_decodeurs(driver, sous_df, original_window, new_window, statut_txt, progress_bar)
        except Exception as e:
            print(f"❌ Erreur de traitement : {e}")
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}

        if driver1:
            futures["nav1"] = executor.submit(traiter, driver1, df_pairs, original_window1, new_window1)
        if driver2:
            futures["nav2"] = executor.submit(traiter, driver2, df_impairs, original_window2, new_window2)

        for key, future in futures.items():
            try:
                if key == "nav1":
                    resultats1 = future.result()
                elif key == "nav2":
                    resultats2 = future.result()
            except Exception as e:
                print(f"❌ Erreur future {key} : {e}")

    # Cas de reprise : si l’un a échoué complètement, on tente avec l’autre navigateur encore connecté
    if not resultats1 and driver2:
        print("⚠️ Reprise des lignes paires avec navigateur 2...")
        try:
            resultats1 = traiter_decodeurs(driver2, df_pairs, original_window2, new_window2, statut_txt, progress_bar)
        except Exception as e:
            print(f"❌ Échec reprise avec navigateur 2 : {e}")

    if not resultats2 and driver1:
        print(" Reprise des lignes impaires avec navigateur 1...")
        try:
            resultats2 = traiter_decodeurs(driver1, df_impairs, original_window1, new_window1, statut_txt, progress_bar)
        except Exception as e:
            print(f"❌ Échec reprise avec navigateur 1 : {e}")

    # Déconnexion à la fin seulement
    if driver1:
        try:
            deconnexion_cgaweb(driver1)
        except:
            pass

    if driver2:
        try:
            deconnexion_cgaweb(driver2)
        except:
            pass

    resultats = resultats1 + resultats2
    return resultats


# --- Export Excel ---
from openpyxl.styles import PatternFill

def resultat(resultats):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nom_fichier = f"résultats_cgaweb_{now}.xlsx"
    df = pd.DataFrame(resultats)

    colonnes_finales = [
        "numero_decodeur", "nom_abonne", "numero_abonne","date_recrutement", "num_distributeur", "nom_distributeur",
        "telephone","telephone_2", "fin_abonnement", "statut", "detail-statut",
        "temps_traitement (sec)", "temps_moyen_traitement (sec)",
    ]
    for col in colonnes_finales:
        if col not in df.columns:
            df[col] = ""
    df = df[colonnes_finales]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultats')
        ws = writer.sheets['Résultats']

        # Couleurs
        vert = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")   # Actif
        rouge = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Échu
        jaune = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Échu dans ≤ 5 jours

        # Récupérer l'index 1-based des colonnes pour excel (ligne d'en-tête = 1)
        col_statut_idx = colonnes_finales.index("statut") + 1
        col_finab_idx = colonnes_finales.index("fin_abonnement") + 1

        for row_idx in range(2, len(df) + 2):  # à partir de la ligne 2 (données)
            statut_cell = ws.cell(row=row_idx, column=col_statut_idx)
            finab_cell = ws.cell(row=row_idx, column=col_finab_idx)

            try:
                date_fin = pd.to_datetime(finab_cell.value, dayfirst=True).date()
                aujourd_hui = datetime.now().date()
                jours_restant = (date_fin - aujourd_hui).days
            except Exception:
                jours_restant = None
            # Appliquer les couleurs selon le statut
            statut_val = statut_cell.value

            if statut_val == "Actif":
                if jours_restant is not None and  jours_restant <= 5:
                    statut_cell.fill = jaune
                else:
                    statut_cell.fill = vert
            elif statut_val == "Échu":
                statut_cell.fill = rouge

    output.seek(0)
    return output, nom_fichier


    
# --------------------- ARRET D'URGENCE ---------------------
def arret_urgence(driver):
    try:
        if driver:
            print("🔌 Déconnexion...")
            try:
                deconnexion_cgaweb(driver)
            except Exception as e:
                print(f"⚠️ Déconnexion échouée : {e}")
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️ Fermeture navigateur échouée : {e}")
        else:
            print("⚠️ Aucun navigateur actif.")

        if resultats_en_cours:
            print("💾 Sauvegarde partielle...")
            try:
                output, nom_fichier = resultat(resultats_en_cours)
                with open(nom_fichier, "wb") as f:
                    f.write(output.read())
                print(f"✅ Sauvegardé sous {nom_fichier}")
            except Exception as e:
                print(f"❌ Erreur sauvegarde partielle : {e}")

        print("🛑 Arrêt d'urgence terminé.")
    except Exception as e:
        print(f"❌ Erreur inattendue arrêt d'urgence : {e}")

# --------------------- FONCTION DE RECHERCHE AVEC NUMERO D'ABONNE ---------------------
def rechercher_par_abonne(driver, num_abonne):
    try:
        # passer sur le popus de recherche
        driver.switch_to.window(driver.new_window)
        driver.switch_to.default_content()
        print("Formulaire de recherche par abonné trouvé.")
        champ_numabo = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "numabo")))
        champ_numabo.clear()
        champ_numabo.send_keys(num_abonne)
        driver.find_element(By.NAME, "search").click()
        print(f"Recherche pour l'abonné {num_abonne} lancée.")
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            message = alert.text  # Récupérer le message de l'alerte
            alert.accept()        # Fermer l'alerte
            return message        # Retourner le message
        except TimeoutException:
            pass  # Aucune alerte détectée

        lien = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#subscriberDTABLE a")))
        numero_abonne = lien.text.strip()
        lien.click()
        print(" Lien vers l'abonné cliqué.")
        # Revenir à la fenêtre principale
        driver.switch_to.window(driver.original_window)
        driver.switch_to.default_content()
        driver.switch_to.frame("_right")
        fiche_abonnes = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "view-contract")))
        return numero_abonne, fiche_abonnes
    except Exception as e:
        print(f"❌ Erreur recherche par abonné : {e}")
        return None

#-------------la fonction de recherche par décodeur ou par numero d'abonne -------------

def rechercher_par_numero(driver, numero, original_window, new_window):
    """
    Recherche générique (abonné, décodeur ou téléphone).
    Retourne :
      - (numero_abonne, fiche_abonnes) pour abonné/décodeur
      - liste de dictionnaires pour téléphone
      - None en cas d'échec
    """
    type_recherche = "inconnu"


    if driver is None:
        print("❌ La connexion au site CGAWEB a échoué.")
        #st.error("❌ La connexion au site CGAWEB a échoué.")
        st.stop() 
    try:
        numero_str = str(numero).strip()

# --- Cas téléphone ---
        if len(numero_str) == 14 and numero_str.startswith("00237"):
            type_recherche = "téléphone"
            return rechercher_par_telephone(driver, numero_str, new_window)

        # --- Cas décodeur ---
        elif len(numero_str) == 14:
            type_recherche = "decodeur"
            champ_name = "numdec"

        # --- Cas abonné ---
        elif len(numero_str) == 8:
            type_recherche = "abonne"
            champ_name = "numabo"

        # --- Cas invalide ---
        else:
            print(f"❌ Numéro invalide : {numero}")
            return None


        # Passer sur la fenêtre popup
        driver.switch_to.window(new_window)
        driver.switch_to.default_content()

        champ = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, champ_name))
        )
        champ.clear()
        champ.send_keys(numero_str)
        driver.find_element(By.NAME, "search").click()

        # Vérifier alerte
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            message = alert.text
            alert.accept()
            print(f"⚠️ Alerte détectée : {message}")
            return None
        except TimeoutException:
            pass

        # Lien vers l’abonné
        lien = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#subscriberDTABLE a"))
        )
        numero_abonne = lien.text.strip()
        lien.click()

        # Retour fenêtre principale
        driver.switch_to.window(original_window)
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "_right"))
        )

        fiche_abonnes = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "view-contract"))
        )

        return numero_abonne, fiche_abonnes

    except Exception as e:
        print(f"❌ Erreur lors de la recherche par {type_recherche} : {e}")
        return None




# --------------------- FONCTIONS DE RECHERCHE AVEC NUMERO TELEPHONE ---------------------

def rechercher_par_telephone(driver, numero_str, new_window, timeout=15):
    """
    Recherche un ou plusieurs abonnés via un numéro de téléphone sur CGAWEB.
    Récupère les données directement depuis la variable JavaScript subscriberT.
    """
    try:
        # 🔹 Basculer sur la popup
        driver.switch_to.window(new_window)
        driver.switch_to.default_content()
        print("Formulaire de recherche par téléphone trouvé.")

        # 🔹 Remplir le champ téléphone
        champ_telephone = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "phonenumber"))
        )
        champ_telephone.clear()
        champ_telephone.send_keys(numero_str)
        print(f"Numéro de téléphone {numero_str} saisi.")

        # 🔹 Cliquer sur "search"
        driver.find_element(By.NAME, "search").click()
        print("Recherche par téléphone lancée.")

        # 🔹 Vérifier les alertes éventuelles
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            message = alert.text
            alert.accept()
            print(f"Alerte détectée : {message}")
            return {"erreur": message}
        except TimeoutException:
            pass

        # 🔹 Attendre que la variable JS subscriberT soit chargée
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return typeof subscriberT !== 'undefined' && subscriberT.length >= 0;")
        )

        # 🔹 Extraire les données depuis subscriberT
        subscriberT = driver.execute_script("return subscriberT;")
        if not subscriberT:
            print(f"Aucun abonné trouvé pour le numéro {numero_str}.")
            return []

        resultats = []
        for ligne in subscriberT:
            # ligne est une liste avec toutes les colonnes
            donnees = {
                "abonne": ligne[0],
                "c": ligne[1],
                "nom": ligne[2],
                "prenom": ligne[3],
                "some_checkbox": ligne[5],  # indwholesale
                "pays": ligne[6],
                "code_postal": ligne[7],
                "ville": ligne[8],
                "adresse": ligne[9],
                "option_majeure": ligne[10],
                "annule": ligne[12],
                "ret": ligne[11],
                "cl": ligne[13],
                "societe": ligne[14]
            }
            resultats.append(donnees)

        print(f"{len(resultats)} abonnés trouvés pour le numéro {numero_str}.")
        return resultats

    except Exception as e:
        print(f"❌ Erreur recherche par téléphone : {e}")
        return {"erreur": str(e)}

#----------------------Fonction pour le suivi abonné----------------

def extraction_suivi_abonne(fiche_abonne, driver):
    try:
        print(f"🔍 Extraction du suivi abonné pour : {fiche_abonne}")

        # 1. Cliquer sur "Suivi abonné" à partir du fragment donné
        lien_suivi = fiche_abonne.find_element(By.LINK_TEXT, "Suivi abonné")
        lien_suivi.click()

        # 2. Attendre que le fragment formContainer apparaisse
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "formContainer"))
        )
        print("✅ Section 'Suivi abonné' chargée")

        # 3. Vérifier la pagination
        div_followup = driver.find_element(By.ID, "divFOLLOWUP")
        pages_elements = div_followup.find_elements(By.TAG_NAME, "a")
        pages = set()
        for elem in pages_elements:
            txt = elem.text.strip(">< ")
            if txt.isdigit():
                pages.add(int(txt))
        total_pages = max(pages) if pages else 1
        print(f"🔢 Nombre de pages : {total_pages}")

        all_suivis = []

        # 4. Parcourir les pages
        for page in range(1, total_pages + 1):
            print(f"📄 Traitement de la page {page}")

            if page != 1:
                try:
                    lien_page = driver.find_element(By.XPATH, f"//div[@id='divFOLLOWUP']//a[contains(text(), '{page}')]")
                    lien_page.click()
                    time.sleep(2)
                except:
                    print(f"⚠️ Impossible de naviguer vers la page {page}")
                    continue

            # Attendre le tableau principal
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "FOLLOWUPDTABLE"))
            )
            tableau = driver.find_element(By.ID, "FOLLOWUPDTABLE")
            lignes = tableau.find_elements(By.TAG_NAME, "tr")

            for ligne in lignes[1:]:  # ignorer l'en-tête
                try:
                    lien_detail = ligne.find_element(By.TAG_NAME, "a")
                    lien_detail.click()
                    time.sleep(1)

                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "CONTEXTDTABLE"))
                    )
                    tableau_detail = driver.find_element(By.ID, "CONTEXTDTABLE")
                    lignes_detail = tableau_detail.find_elements(By.TAG_NAME, "tr")

                    details = {}
                    for tr in lignes_detail:
                        tds = tr.find_elements(By.TAG_NAME, "td")
                        if len(tds) >= 2:
                            cle = tds[0].text.strip()
                            valeur = tds[1].text.strip()
                            details[cle] = valeur
                    all_suivis.append(details)

                except Exception as e:
                    print(f"⚠️ Erreur lors de l'extraction d'un détail : {e}")
                    continue

        print(f"✅ Extraction terminée ({len(all_suivis)} entrées)")
        return all_suivis

    except Exception as e:
        print(f"❌ Erreur dans extract_suivi_abonne : {e}")
        return []
#---------------afficher suivi abonné-----------------
def afficher_suivi_abonne(all_suivis):
    # Pagination
    nb_par_page = 10
    nb_total = len(all_suivis)
    nb_pages = (nb_total - 1) // nb_par_page + 1

    # Choisir la page
    page = st.number_input("Page", min_value=1, max_value=nb_pages, step=1, value=1)

    debut = (page - 1) * nb_par_page
    fin = min(debut + nb_par_page, nb_total)

    for i, mouvement in enumerate(all_suivis[debut:fin], start=debut + 1):
        with st.expander(f"🔸 Mouvement {i} - {mouvement.get('Date', 'Date inconnue')}"):
            for cle, valeur in mouvement.items():
                st.markdown(f"**{cle}** : {valeur}")

    # Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if page > 1:
            st.button("⬅️ Page précédente", on_click=st.session_state.update, args=("page_suivi", page - 1))
    with col2:
        if page < nb_pages:
            st.button("➡️ Page suivante", on_click=st.session_state.update, args=("page_suivi", page + 1))

# --------------------- GESTION DES UTILISATEURS ---------------------
FICHIER_UTILISATEURS = "utilisateurs.csv"

# --------------------- FONCTIONS DE HACHAGE ---------------------
def hash_mot_de_passe(mdp):
    return hashlib.sha256(mdp.encode()).hexdigest()

# --------------------- INITIALISATION FICHIER UTILISATEURS ---------------------
def init_fichier_utilisateurs():
    if not os.path.exists(FICHIER_UTILISATEURS):
        df = pd.DataFrame(columns=["nom", "username", "code", "telephone", "email", "mot_de_passe", "role"])
        df.to_csv(FICHIER_UTILISATEURS, index=False)

# Chargement des utilisateurs depuis le fichier CSV
def charger_utilisateurs():
    init_fichier_utilisateurs()
    return pd.read_csv(FICHIER_UTILISATEURS)

# Enregistrement d'un nouvel utilisateur
def enregistrer_utilisateur(nom, username, code, telephone, email, mot_de_passe, role="Utilisateur"):
    df = charger_utilisateurs()
    if code in df["code"].values:
        return False, "❌ Code déjà utilisé."

    new_user = pd.DataFrame([{
        "nom": nom, "username": username, "code": code, "telephone": telephone,
        "email": email, "mot_de_passe": hash_mot_de_passe(mot_de_passe), "role": role
    }])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(FICHIER_UTILISATEURS, index=False)
    return True, "✅ Utilisateur enregistré."

# MOIFICATION UTILISATEUR
def modifier_utilisateur(index, utilisateur_modifie):
    df = charger_utilisateurs()
    for cle, val in utilisateur_modifie.items():
        if cle == "mot_de_passe" and val:
            df.at[index, cle] = hash_mot_de_passe(val)
        elif cle != "mot_de_passe":
            df.at[index, cle] = val
    df.to_csv(FICHIER_UTILISATEURS, index=False)

# SUPPRESSION UTILISATEUR
def supprimer_utilisateur(index):
    df = charger_utilisateurs()
    df = df.drop(index).reset_index(drop=True)
    df.to_csv(FICHIER_UTILISATEURS, index=False)

# Vérification des identifiants

def hasher_mot_de_passe(mot_de_passe):
    return hashlib.sha256(mot_de_passe.encode()).hexdigest()

def verifier_identifiants(username, password, fichier="utilisateurs.csv"):
    try:
        df = pd.read_csv(fichier)
        mot_de_passe_hash = hasher_mot_de_passe(password)

        utilisateur = df[(df["username"] == username) & (df["mot_de_passe"] == mot_de_passe_hash)]

        if not utilisateur.empty:
            role = utilisateur.iloc[0]["role"] if "role" in df.columns else "utilisateur"
            return True, role
        else:
            return False, None
    except FileNotFoundError:
        return False, None


# Vérification si l'utilisateur est connecté
def est_connecte():
    return "utilisateur_connecte" in st.session_state and st.session_state["utilisateur_connecte"] is not None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
accounts_file = os.path.join(BASE_DIR, "cgaweb_accounts.json")

#def sauvegarder_comptes(comptes):
    #with open(accounts_file, "w", encoding="utf-8") as f:
        #json.dump(comptes, f, indent=4, ensure_ascii=False)

class CompteCGA:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    def to_dict(self):
        return {"user": self.user, "pass": self.password}

    @classmethod
    def from_dict(cls, data):
        return cls(user=data["user"], password=data["pass"])

def charger_comptes():
    if os.path.exists(accounts_file):
        with open(accounts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [CompteCGA.from_dict(c) for c in data]
    return []

def sauvegarder_comptes(comptes):
    with open(accounts_file, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in comptes], f, indent=4, ensure_ascii=False)
#-------------------Fonction pour réactivation et réinitialisation du code parental-------------------

def action_abonne(driver, fiche_abonne, action="reactivation", timeout=10):
    """
    Exécute une action sur la fiche abonné CGAWEB.

    Paramètres :
        driver : Selenium WebDriver connecté
        fiche_abonne : WebElement de la fiche abonné ouverte
        action : "reactivation" ou "reinit"
        timeout : temps d'attente pour le formulaire (par défaut 10s)

    Retour :
        (True, None) si succès
        (False, message) si échec (alerte ou erreur)
    """
    # --- mapping des boutons ---
    boutons = {
        "reactivation": {"name": "reactivation", "value": "Réactivation"},
        "reinit": {"name": "reinit", "value": "Reinit. Code Parental"}
    }

    if action not in boutons:
        return (False, f"Action '{action}' non reconnue")

    try:
        # 1. Cliquer sur le lien "Activité" dans la fiche abonné
        try:
            bouton_activite = fiche_abonne.find_element(
                By.XPATH, "//a[@title='Activité' and contains(@href, 'modActivity.do')]"
            )
            bouton_activite.click()
        except NoSuchElementException:
            return (False, "Bouton 'Activité' introuvable dans la fiche abonné")

        # 2. Attendre que le formulaire modactivity soit visible
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.NAME, "modactivity"))
            )
        except TimeoutException:
            return (False, "Le formulaire modactivity n'est pas apparu")

        # 3. Cliquer sur le bouton correspondant à l'action
        try:
            bouton = driver.find_element(
                By.XPATH,
                f"//input[@name='{boutons[action]['name']}' and @value=\"{boutons[action]['value']}\"]"
            )
            bouton.click()
            time.sleep(2)  # attendre la réaction du site
        except NoSuchElementException:
            return (False, f"Bouton '{boutons[action]['value']}' introuvable")

        # 4. Vérifier si une alerte apparaît
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            message = alert.text
            alert.accept()  # fermer l'alerte
            return (False, message)  # échec avec message
        except TimeoutException:
            return (True, None)  # pas d'alerte → succès

    except Exception as e:
        return (False, f"Erreur pendant l'action '{action}' : {e}")

