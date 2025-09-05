# file_attente_json.py

import json
import os
import time
from datetime import datetime
from contextlib import contextmanager
from fonction import connexion_cgaweb, deconnexion_cgaweb, rechercher_par_numero
import shutil   
# ==========================
# 📂 Chemins vers fichiers JSON
# ==========================
FICHIER_FILE = "file_attente.json"   # utilisé par le worker
FICHIER_NOUVELLES = "file_nouvelles.json"  # utilisé par les utilisateurs
FICHIER_HISTO = "historique.json"

# ==========================
# 🔒 Gestion du verrou fichier avec timeout
# ==========================
@contextmanager
def verrou_fichier(nom_fichier, timeout=5):
    """Empêche l'accès concurrent au fichier JSON avec timeout en secondes"""
    lockfile = nom_fichier + ".lock"
    start_time = time.time()
    while os.path.exists(lockfile):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"⏳ Timeout verrou pour {nom_fichier}")
        time.sleep(0.05)
    try:
        open(lockfile, "w").close()
        yield
    finally:
        if os.path.exists(lockfile):
            os.remove(lockfile)

# ==========================
# 📂 Fonctions lecture/écriture génériques
# ==========================
def charger_file(path):
    """Charge un fichier JSON, crée une liste vide si inexistant"""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Renommer le fichier corrompu
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{path}.backup_{timestamp}"
        shutil.move(path, backup_path)
        logging.warning(f"⚠️ JSON invalide dans {path}, fichier sauvegardé en {backup_path}. Création d'une liste vide.")
        return []

def sauvegarder_file(path, data):
    """Sauvegarde sécurisée"""
    try:
        with verrou_fichier(path):
            tmp_file = path + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_file, path)
            logging.info(f"✅ Sauvegarde réussie dans {path}")
    except TimeoutError as e:
        logging.error(f"❌ {e}")
    except Exception as e:
        logging.error(f"❌ Erreur inattendue lors de la sauvegarde de {path} :", e)

# ==========================
# 📌 Ajout d'une requête (utilisateurs)
# ==========================
def ajouter_requete(utilisateur, type_recherche, valeur):
    """
    Les utilisateurs ajoutent ICI → écrit dans file_nouvelles.json
    """
    try:
        nouvelles = charger_file(FICHIER_NOUVELLES)
        nouvelle_requete = {
            "id": int(time.time() * 1000),  # ID unique basé sur timestamp
            "utilisateur": utilisateur,
            "type": type_recherche,
            "valeur": valeur,
            "statut": "en_attente",
            "date_creation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resultat": None
        }
        nouvelles.append(nouvelle_requete)
        with open(FICHIER_NOUVELLES, "w", encoding="utf-8") as f:
            json.dump(nouvelles, f, indent=4, ensure_ascii=False)
        print(f"📌 Nouvelle requête ajoutée dans {FICHIER_NOUVELLES} : {valeur}")
        return nouvelle_requete
    except Exception as e:
        print("❌ Erreur lors de l'ajout de la requête :", e)
        return None

# ==========================
# 🔄 Fusion des nouvelles requêtes
# ==========================
def fusionner_nouvelles():
    """Déplace les requêtes de file_nouvelles.json vers file_attente.json"""
    nouvelles = charger_file(FICHIER_NOUVELLES)
    if not nouvelles:
        return

    file_attente = charger_file(FICHIER_FILE)
    file_attente.extend(nouvelles)

    # Facultatif : supprimer doublons sur la clé "id"
    file_unique = {req["id"]: req for req in file_attente}.values()

    sauvegarder_file(FICHIER_FILE, list(file_unique))
    sauvegarder_file(FICHIER_NOUVELLES, [])  # vider après fusion

    logging.info(f"🔄 Fusion de {len(nouvelles)} requêtes dans la file principale")
# 📂 Compatibilité API
# ==========================
def lire_file():
    """Lecture de la file principale (compatibilité ancienne API)"""
    return charger_file(FICHIER_FILE)

def lire_nouvelles():
    """Lecture de la file des nouvelles requêtes"""
    return charger_file(FICHIER_NOUVELLES)


# ==========================
# 📌 Mettre à jour une requête
# ==========================
def mettre_a_jour_requete(req_id, statut=None, resultat=None):
    file_attente = charger_file(FICHIER_FILE)
    for req in file_attente:
        if req["id"] == req_id:
            if statut:
                req["statut"] = statut
            if resultat is not None:
                req["resultat"] = resultat
            break
    sauvegarder_file(FICHIER_FILE, file_attente)

# ==========================
# 📜 Historique
# ==========================
def lire_historique():
    return charger_file(FICHIER_HISTO)

def ajouter_historique(requete):
    histo = lire_historique()
    histo.append(requete)
    sauvegarder_file(FICHIER_HISTO, histo)

# ==========================
# ⚙️ Traitement automatique
# ==========================
from selenium.webdriver.remote.webelement import WebElement

def nettoyer_resultat(res):
    """
    Convertit tous les WebElement en texte ou en structure JSON-friendly
    """
    if isinstance(res, WebElement):
        return res.text  # ou res.get_attribute("value") selon ce que tu veux
    elif isinstance(res, list):
        return [nettoyer_resultat(r) for r in res]
    elif isinstance(res, dict):
        return {k: nettoyer_resultat(v) for k, v in res.items()}
    else:
        return res  # str, int, float, None, etc.# adapte selon ton projet
import logging
# --- Configuration du logger ---
logging.basicConfig(
    filename="Fichierlogging_cgaweb_worker.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CGAWEB_Worker")

def traiter_file_automatique(url, utilisateur, mot_de_passe, pause=0.2, retry_pause=5):
    """Worker : traite les requêtes depuis la file avec un driver isolé"""
    driver = None
    original_window = new_window = None

    while True:
        # Fusion des nouvelles requêtes
        fusionner_nouvelles()
        file_attente = charger_file(FICHIER_FILE)
        requetes_en_attente = [req for req in file_attente if req["statut"] == "en_attente"]

        if not requetes_en_attente:
            logging.info("✅ La file est vide, aucune connexion nécessaire.")
            if driver:
                try:
                    deconnexion_cgaweb(driver)
                    driver.quit()
                    logging.info("🔌 Déconnexion CGAWEB terminée.")
                except:
                    pass
            return

        # Connexion si pas déjà connecté
        if not driver:
            try:
                logging.info("🔄 Tentative de connexion à CGAWEB...")
                driver, original_window, new_window = connexion_cgaweb(url, utilisateur, mot_de_passe, headless=True)
                logging.info("✅ Connexion établie.")
            except Exception as e:
                logging.error(f"❌ Connexion échouée : {e}. Nouvelle tentative dans {retry_pause}s...")
                time.sleep(retry_pause)
                continue  # réessaie sans marquer les requêtes en erreur

        # Traiter chaque requête
        for req in requetes_en_attente:
            req_id = req["id"]
            mettre_a_jour_requete(req_id, statut="en_cours")
            try:
                res = rechercher_par_numero(driver, req["valeur"], original_window, new_window)

                if res is None:
                    mettre_a_jour_requete(req_id, statut="erreur", resultat="Aucun résultat trouvé")
                else:
                    # Nettoyage : transforme WebElements en texte, tuples si nécessaire
                    if isinstance(res, tuple):
                        numero_abonne, fiche_abonne = res
                        fiche_text = nettoyer_resultat(fiche_abonne)  # texte uniquement
                        res_json = (numero_abonne, fiche_text)
                    else:
                        res_json = nettoyer_resultat(res)

                    mettre_a_jour_requete(req_id, statut="terminee", resultat=res_json)

            except Exception as e:
                logging.error(f"⚠️ Erreur pendant la recherche pour {req['valeur']}: {e}")
                mettre_a_jour_requete(req_id, statut="en_attente")  # réessaie plus tard

            # Archiver sans inclure le driver ni WebElements
            file_actuelle = charger_file(FICHIER_FILE)
            for r in file_actuelle:
                if r["id"] == req_id:
                    ajouter_historique(r)
                    break

            time.sleep(pause)

        logging.info("✅ Cycle de traitement terminé, vérification de la file...")



