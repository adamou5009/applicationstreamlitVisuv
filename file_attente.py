import json
import os
import time
import threading
import logging
from datetime import datetime
import streamlit as st
from selenium.webdriver.remote.webelement import WebElement

from fonction import (
    connexion_cgaweb, deconnexion_cgaweb,
    rechercher_par_numero, get_connection,
    WebDriverManager, action_abonne
)

# =========================================================
# ⚙️ 1. CONFIGURATION & ÉTAT GLOBAL
# =========================================================
SEUIL_DOUBLE_WORKER     = 150
WORKER_LOCK_FILE        = "worker_{}.lock"
MAX_SESSIONS_CGAWEB     = 2    # limite stricte du serveur CGA
MAX_ECHECS_CONSECUTIFS  = 5    # arrêt du worker après N échecs "max sessions"
BACKOFF_MAX_SESSIONS    = 300  # secondes d'attente si serveur saturé (5 min)
SESSION_TIMEOUT_MINUTES = 60

_worker_lock        = threading.Lock()
_workers            = {}    # { worker_id: threading.Thread }
_echecs_consecutifs = {}    # { worker_id: int }
_started            = False # garde-fou contre les lancements multiples Streamlit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# =========================================================
# 🗄️ 2. GESTION DE LA BASE DE DONNÉES
# =========================================================
def ajouter_log_sql(req_id, message):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO requete_logs (requete_id, message) VALUES (%s, %s)",
                (req_id, message)
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        logging.error(f"Erreur log SQL : {e}")


def mettre_a_jour_requete(req_id, statut=None, resultat=None, logs=None, worker_id=None):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            updates, params = [], []
            if statut:
                updates.append("statut = %s")
                params.append(statut)
            if resultat is not None:
                updates.append("resultat = %s")
                params.append(json.dumps(resultat, ensure_ascii=False))
            if worker_id is not None:
                updates.append("worker_id = %s")
                params.append(worker_id)
            if updates:
                sql = f"UPDATE requetes SET {', '.join(updates)} WHERE id = %s"
                params.append(req_id)
                cursor.execute(sql, tuple(params))
            if logs:
                for log in logs:
                    cursor.execute(
                        "INSERT INTO requete_logs (requete_id, message) VALUES (%s, %s)",
                        (req_id, log)
                    )
            conn.commit()
            cursor.close()
        return True
    except Exception as e:
        logging.error(f"Erreur SQL update (Req {req_id}) : {e}")
        return False


def ajouter_requete(utilisateur, type_recherche, valeur):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            req_id = int(time.time() * 1000)
            cursor.execute(
                """INSERT INTO requetes (id, utilisateur, type_recherche, valeur, statut)
                   VALUES (%s, %s, %s, %s, 'en_attente')""",
                (req_id, utilisateur, type_recherche, valeur)
            )
            conn.commit()
            cursor.close()
        return {"id": req_id, "statut": "en_attente"}
    except Exception as e:
        logging.error(f"Erreur SQL ajout : {e}")
        return None


def lire_requete_par_id(req_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requetes WHERE id = %s", (req_id,))
            res = cursor.fetchone()
            cursor.close()
        if res and res.get('resultat'):
            try:
                res['resultat'] = json.loads(res['resultat'])
            except Exception:
                pass
        return res
    except Exception as e:
        logging.error(f"Erreur lire_requete_par_id : {e}")
        return None


# =========================================================
# 🔑 3. UTILITAIRES & LECTURE
# =========================================================
def charger_compte_actif():
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM comptes_cgaweb WHERE est_actif = TRUE LIMIT 1")
            compte = cursor.fetchone()
            cursor.close()
        if compte:
            url = "https://cgaweb-afrique.canal-plus.com/cgaweb/servlet/Home"
            return (url, compte['user_cga'], compte['password_cga'], compte['secret_otp'])
        return None
    except Exception as e:
        logging.error(f"Erreur charger_compte_actif : {e}")
        return None


def nettoyer_resultat(res):
    if isinstance(res, WebElement): return res.text
    if isinstance(res, list):       return [nettoyer_resultat(r) for r in res]
    if isinstance(res, dict):       return {k: nettoyer_resultat(v) for k, v in res.items()}
    return res


def compter_requetes_en_attente():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM requetes WHERE statut = 'en_attente'")
            count = cursor.fetchone()[0]
            cursor.close()
        return count
    except Exception:
        return 0


def lire_file():
    """Retourne les requêtes en_attente et en_cours (pour le tableau de bord)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM requetes WHERE statut IN ('en_attente', 'en_cours') ORDER BY id DESC"
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows
    except Exception as e:
        logging.error(f"Erreur lire_file : {e}")
        return []


def lire_historique():
    """Retourne les 50 dernières requêtes terminées/échouées/abandonnées."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT * FROM requetes
                   WHERE statut IN ('terminee', 'echouee', 'abandonné')
                   ORDER BY id DESC LIMIT 50"""
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows
    except Exception as e:
        logging.error(f"Erreur lire_historique : {e}")
        return []


# =========================================================
# 🛡️ 4. GESTION DES VERROUS (LOCKS)
# =========================================================
def nettoyer_vieux_verrous():
    for i in range(1, 3):
        lock_file = WORKER_LOCK_FILE.format(i)
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                logging.info(f"Vieux verrou {lock_file} supprimé.")
            except Exception:
                pass


def est_worker_actif(worker_id):
    lock_file = WORKER_LOCK_FILE.format(worker_id)
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except Exception:
            if os.path.exists(lock_file):
                os.remove(lock_file)
    return False


def creer_verrou_worker(worker_id):
    try:
        with open(WORKER_LOCK_FILE.format(worker_id), "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return False


def supprimer_verrou_worker(worker_id):
    lock_file = WORKER_LOCK_FILE.format(worker_id)
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass


# =========================================================
# 👤 5. HELPERS SESSION UTILISATEUR
# =========================================================
def utilisateur_est_connecte(user):
    """Vérifie en base si l'utilisateur a une session active."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT 1 FROM sessions_actives WHERE utilisateur = %s AND active = 1",
                (user,)
            )
            row = cursor.fetchone()
            cursor.close()
        return row is not None
    except Exception as e:
        logging.error(f"Erreur vérif session '{user}' : {e}")
        return False


def verifier_et_abandonner(worker_id, req_id, utilisateur):
    if not utilisateur_est_connecte(utilisateur):
        logging.warning(f"W{worker_id} — '{utilisateur}' déconnecté. Req {req_id} → abandonné.")
        mettre_a_jour_requete(
            req_id,
            statut="abandonné",
            resultat={"erreur": "Requête abandonnée : utilisateur déconnecté ou page changée."},
            logs=[f"Abandon — session inactive pour '{utilisateur}'"]
        )
        return True
    return False


# =========================================================
# ⏱️ 6. NETTOYAGE SESSIONS EXPIRÉES
# =========================================================
def nettoyer_sessions_expirées(timeout_minutes=SESSION_TIMEOUT_MINUTES):
    """Expire les sessions inactives depuis plus de timeout_minutes minutes."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT utilisateur FROM sessions_actives
                   WHERE active = 1
                   AND updated_at < NOW() - INTERVAL %s MINUTE""",
                (timeout_minutes,)
            )
            expires = [row[0] for row in cursor.fetchall()]

            if expires:
                cursor.execute(
                    """UPDATE sessions_actives
                       SET active = 0, token = NULL, updated_at = NOW()
                       WHERE active = 1
                       AND updated_at < NOW() - INTERVAL %s MINUTE""",
                    (timeout_minutes,)
                )
                conn.commit()

                erreur_json = json.dumps(
                    {"erreur": "Session expirée (arrêt brutal détecté)."},
                    ensure_ascii=False
                )
                for user in expires:
                    cursor.execute(
                        """UPDATE requetes
                           SET statut   = 'abandonné',
                               resultat = %s
                           WHERE utilisateur = %s
                           AND statut IN ('en_attente', 'en_cours')""",
                        (erreur_json, user)
                    )
                    logging.info(f"Session expirée nettoyée : '{user}'")
                conn.commit()

            cursor.close()
    except Exception as e:
        logging.error(f"Erreur nettoyage sessions expirées : {e}")


def reset_saturation_cgaweb():
    """Débloque CGAWEB après saturation."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE cgaweb_statut
                   SET bloque = 0, raison = NULL, bloque_at = NULL
                   WHERE id = 1"""
            )
            conn.commit()
            cursor.close()
        logging.info("CGAWEB débloqué via reset_saturation_cgaweb()")
        return True
    except Exception as e:
        msg = str(e)
        if "doesn't exist" in msg or "1146" in msg:
            logging.warning("Table cgaweb_statut absente — déblocage ignoré.")
        else:
            logging.error(f"Erreur reset CGAWEB : {e}")
        return False


def _est_cgaweb_bloque():
    """Vérifie si CGAWEB est marqué comme bloqué en base."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT bloque FROM cgaweb_statut WHERE id = 1")
            row = cursor.fetchone()
            cursor.close()
        return row is not None and row["bloque"] == 1
    except Exception as e:
        msg = str(e)
        if "doesn't exist" in msg or "1146" in msg:
            logging.warning("Table cgaweb_statut absente — CGAWEB considéré non bloqué.")
        else:
            logging.error(f"Erreur statut CGAWEB : {e}")
        return False


# =========================================================
# 🔐 7. GESTION DES SESSIONS CGAWEB (anti-saturation)
# =========================================================
def _compter_sessions_cgaweb_actives():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cgaweb_sessions WHERE connecte = 1")
            count = cursor.fetchone()[0]
            cursor.close()
        return count
    except Exception as e:
        logging.error(f"Erreur lecture cgaweb_sessions : {e}")
        return 0


def _marquer_session_cgaweb(worker_id, connecte: bool):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO cgaweb_sessions (worker_id, connecte)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE connecte = %s, updated_at = NOW()""",
                (worker_id, int(connecte), int(connecte))
            )
            conn.commit()
            cursor.close()
        logging.info(f"W{worker_id} — Session CGAWEB marquée : connecte={connecte}")
    except Exception as e:
        logging.error(f"Erreur update cgaweb_sessions W{worker_id} : {e}")


def _attendre_slot_cgaweb(worker_id, timeout=120, intervalle=3):
    debut = time.time()
    while True:
        try:
            actives = _compter_sessions_cgaweb_actives()

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT connecte FROM cgaweb_sessions WHERE worker_id = %s",
                    (worker_id,)
                )
                row = cursor.fetchone()
                cursor.close()

            deja_compte  = (row is not None and row[0] == 1)
            slots_libres = MAX_SESSIONS_CGAWEB - actives + (1 if deja_compte else 0)

            if slots_libres > 0:
                logging.info(f"W{worker_id} — Slot CGAWEB disponible ({actives} session(s) active(s))")
                return True

        except Exception as e:
            logging.error(f"W{worker_id} — Erreur vérif slots CGAWEB : {e}")
            return True  # fail-safe : on autorise en cas d'erreur DB

        elapsed = time.time() - debut
        if elapsed >= timeout:
            logging.error(
                f"W{worker_id} — Timeout {timeout}s : aucun slot CGAWEB libre "
                f"({actives}/{MAX_SESSIONS_CGAWEB} sessions actives)"
            )
            return False

        logging.info(
            f"W{worker_id} — {actives}/{MAX_SESSIONS_CGAWEB} sessions occupées. "
            f"Attente slot... ({int(elapsed)}s écoulées)"
        )
        time.sleep(intervalle)


# =========================================================
# 🚀 8. CORE WORKER (TRAITEMENT)
# =========================================================
def _deconnecter_proprement(driver, manager, worker_id):
    """
    Déconnexion CGAWEB + fermeture navigateur + libération du slot session.
    Ordre strict : slot libéré EN DERNIER (après fermeture browser confirmée).
    Ne lève jamais d'exception.
    """
    if driver:
        try:
            logging.info(f"W{worker_id} — Déconnexion CGAWEB...")
            deconnexion_cgaweb(driver)
            logging.info(f"W{worker_id} — Déconnexion CGAWEB OK")
        except Exception as e:
            logging.warning(f"W{worker_id} — Erreur déconnexion CGAWEB (on continue) : {e}")

    try:
        manager.stop_driver()
        logging.info(f"W{worker_id} — WebDriver arrêté")
    except Exception as e:
        logging.warning(f"W{worker_id} — Erreur stop_driver (on continue) : {e}")

    _marquer_session_cgaweb(worker_id, False)
    logging.info(f"W{worker_id} — Slot session CGAWEB libéré")


def traiter_file_automatique(worker_id, pause=0.2, retry_pause=5, check_interval=5):
    """
    Worker Thread — un WebDriverManager privé par worker, jamais partagé.
    """
    import base64
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    logging.info(f"Démarrage Worker {worker_id}")

    manager = WebDriverManager()
    driver  = None
    ow, nw  = None, None

    # ----------------------------------------------------------
    def _connecter_cgaweb(req_id_echec=None):
        """Connexion CGAWEB sécurisée avec détection de saturation serveur."""
        compte_info = charger_compte_actif()
        if not compte_info:
            logging.error(f"W{worker_id} — Aucun compte CGAWEB actif.")
            if req_id_echec is not None:
                mettre_a_jour_requete(
                    req_id_echec,
                    statut="echouee",
                    resultat={"erreur": "Aucun compte CGAWEB actif."}
                )
            return None, None, None

        url, user, pwd, secret = compte_info

        if not _attendre_slot_cgaweb(worker_id):
            logging.error(f"W{worker_id} — Aucun slot CGAWEB disponible (timeout).")
            if req_id_echec is not None:
                mettre_a_jour_requete(
                    req_id_echec,
                    statut="echouee",
                    resultat={"erreur": "Aucun slot session CGAWEB disponible (timeout)."}
                )
            return None, None, None

        for tentative in range(1, 3):
            logging.info(f"W{worker_id} — Démarrage WebDriver (tentative {tentative}/2)...")
            try:
                result = connexion_cgaweb(manager, url, user, pwd, secret, headless=True)

                # Cas 1 : serveur saturé
                if (
                    isinstance(result, tuple)
                    and len(result) == 3
                    and result[0] == "MAX_SESSIONS"
                ):
                    logging.warning(
                        f"W{worker_id} — Serveur CGAWEB saturé. "
                        f"Attente {BACKOFF_MAX_SESSIONS}s..."
                    )
                    try:
                        manager.stop_driver()
                    except Exception:
                        pass

                    _marquer_session_cgaweb(worker_id, False)
                    _echecs_consecutifs[worker_id] = _echecs_consecutifs.get(worker_id, 0) + 1
                    nb_echecs = _echecs_consecutifs[worker_id]
                    logging.warning(f"W{worker_id} — Échecs consécutifs : {nb_echecs}/{MAX_ECHECS_CONSECUTIFS}")

                    if nb_echecs >= MAX_ECHECS_CONSECUTIFS:
                        logging.error(
                            f"W{worker_id} — {MAX_ECHECS_CONSECUTIFS} échecs consécutifs. "
                            f"Arrêt du worker."
                        )
                        if req_id_echec is not None:
                            mettre_a_jour_requete(
                                req_id_echec,
                                statut="echouee",
                                resultat={"erreur": "Serveur CGAWEB saturé — trop d'échecs consécutifs."}
                            )
                        return None, None, None

                    time.sleep(BACKOFF_MAX_SESSIONS)
                    break

                # Cas 2 : échec générique
                if result is None or result[0] is None:
                    raise Exception("connexion_cgaweb a retourné None")

                # Cas 3 : succès
                d, o, n = result
                _marquer_session_cgaweb(worker_id, True)
                _echecs_consecutifs[worker_id] = 0
                logging.info(f"W{worker_id} — Connexion CGAWEB OK (tentative {tentative})")
                return d, o, n

            except Exception as e:
                logging.warning(f"W{worker_id} — Tentative {tentative}/2 échouée : {e}")
                try:
                    manager.stop_driver()
                except Exception:
                    pass
                if tentative < 2:
                    time.sleep(retry_pause)

        logging.error(f"W{worker_id} — Connexion CGAWEB impossible après 2 tentatives.")
        if req_id_echec is not None:
            mettre_a_jour_requete(
                req_id_echec,
                statut="echouee",
                resultat={"erreur": "Connexion CGAWEB impossible après 2 tentatives."}
            )
        return None, None, None

    # ----------------------------------------------------------
    def _prendre_screenshot_page(driver_inst, worker_id_log):
        """Capture le viewport via CDP. Retourne base64 ou None."""
        try:
            result = driver_inst.execute_cdp_cmd(
                "Page.captureScreenshot",
                {"format": "png", "fromSurface": False, "captureBeyondViewport": False}
            )
            encoded = result.get("data", "")
            if len(encoded) < 5000:
                logging.warning(f"W{worker_id_log} — Screenshot CDP trop petit, ignoré.")
                return None
            logging.info(f"W{worker_id_log} — Screenshot CDP OK ({len(encoded)} chars)")
            return encoded
        except Exception as e:
            logging.warning(f"W{worker_id_log} — Erreur CDP screenshot, fallback PNG : {e}")
            try:
                image_bytes = driver_inst.get_screenshot_as_png()
                encoded = base64.b64encode(image_bytes).decode('utf-8')
                if len(encoded) < 5000:
                    logging.warning(f"W{worker_id_log} — Fallback screenshot trop petit, ignoré.")
                    return None
                logging.info(f"W{worker_id_log} — Fallback screenshot OK ({len(encoded)} chars)")
                return encoded
            except Exception as e2:
                logging.warning(f"W{worker_id_log} — Erreur fallback screenshot : {e2}")
                return None

    # =========================================================
    # CONNEXION INITIALE
    # =========================================================
    driver, ow, nw = _connecter_cgaweb()
    if driver is None:
        logging.error(f"W{worker_id} — Connexion initiale échouée. Arrêt du worker.")
        supprimer_verrou_worker(worker_id)
        return

    # =========================================================
    # BOUCLE PRINCIPALE
    # =========================================================
    try:
        while True:
            req, req_id = None, None

            # 1. RÉCUPÉRATION DE LA TÂCHE
            try:
                with get_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    query = "SELECT * FROM requetes WHERE statut = 'en_attente' "
                    if worker_id == 2:
                        query += "AND (id % 2) = 1 "
                    query += "ORDER BY id ASC LIMIT 1"
                    cursor.execute(query)
                    candidate = cursor.fetchone()
                    if candidate:
                        cursor.execute(
                            "UPDATE requetes SET statut = 'en_cours', worker_id = %s "
                            "WHERE id = %s AND statut = 'en_attente'",
                            (worker_id, candidate['id'])
                        )
                        conn.commit()
                        if cursor.rowcount > 0:
                            req    = candidate
                            req_id = req["id"]
                    cursor.close()
            except Exception as e:
                logging.error(f"W{worker_id} — Erreur SQL fetch : {e}")
                time.sleep(5)
                continue

            # 2. FILE VIDE → DÉCONNEXION PROPRE ET ARRÊT
            if not req:
                nb = compter_requetes_en_attente()
                if nb == 0 or (worker_id == 2 and nb < SEUIL_DOUBLE_WORKER):
                    logging.info(f"W{worker_id} — File vide. Déconnexion + arrêt.")
                    break
                time.sleep(check_interval)
                continue

            utilisateur = req.get("utilisateur")

            # 3. VÉRIFICATION SESSION UTILISATEUR
            if verifier_et_abandonner(worker_id, req_id, utilisateur):
                time.sleep(pause)
                continue

            # 4. SANTÉ DU BROWSER
            browser_ok = True
            try:
                driver.current_window_handle
            except Exception:
                browser_ok = False

            if not browser_ok:
                logging.warning(f"W{worker_id} — Browser perdu (hors traitement). Reconnexion...")
                _deconnecter_proprement(driver, manager, worker_id)
                driver = ow = nw = None
                new_driver, new_ow, new_nw = _connecter_cgaweb(req_id_echec=req_id)
                if new_driver is None:
                    break
                driver, ow, nw = new_driver, new_ow, new_nw

            # 5. ROUTAGE & EXÉCUTION
            try:
                type_req = req.get("type_recherche", "").lower()
                valeur   = req["valeur"]
                ajouter_log_sql(req_id, f"W{worker_id} — type: {type_req} | valeur: {valeur}")

                if verifier_et_abandonner(worker_id, req_id, utilisateur):
                    time.sleep(pause)
                    continue

                # Recherche standard
                if type_req in ("numéro d'abonné", "numéro de décodeur", "numéro de téléphone"):
                    res = rechercher_par_numero(driver, valeur, ow, nw)

                    if verifier_et_abandonner(worker_id, req_id, utilisateur):
                        time.sleep(pause)
                        continue

                    if res:
                        if isinstance(res, tuple):
                            num_abo, fiche = res
                            encoded_img    = None
                            try:
                                driver.switch_to.window(ow)
                                driver.switch_to.default_content()
                                wait = WebDriverWait(driver, 15)
                                wait.until(
                                    EC.frame_to_be_available_and_switch_to_it((By.NAME, "_right"))
                                )
                                wait.until(
                                    EC.visibility_of_element_located((By.ID, "view-contract"))
                                )
                                driver.execute_script("window.scrollTo(0, 0);")
                                time.sleep(1)
                                encoded_img = _prendre_screenshot_page(driver, worker_id)
                            except Exception as e:
                                logging.warning(f"W{worker_id} — Erreur screenshot : {e}")

                            final = {
                                "numero_abonne":     num_abo,
                                "screenshot_base64": encoded_img,
                                "type":              req["type_recherche"],
                                "date_extraction":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            }
                        else:
                            final = nettoyer_resultat(res)

                        mettre_a_jour_requete(req_id, statut="terminee", resultat=final,
                                              logs=["Extraction réussie"])
                    else:
                        mettre_a_jour_requete(req_id, statut="echouee",
                                              resultat={"erreur": "Non trouvé sur CGAWEB"})

                # Réactivation
                elif type_req == "réactivation":
                    res = rechercher_par_numero(driver, valeur, ow, nw)
                    if verifier_et_abandonner(worker_id, req_id, utilisateur):
                        time.sleep(pause)
                        continue
                    if not res or not isinstance(res, tuple):
                        mettre_a_jour_requete(req_id, statut="echouee",
                                              resultat={"erreur": "Abonné introuvable pour réactivation"})
                    else:
                        _, fiche = res
                        ok, msg  = action_abonne(driver, fiche, action="reactivation")
                        if verifier_et_abandonner(worker_id, req_id, utilisateur):
                            time.sleep(pause)
                            continue
                        if ok:
                            mettre_a_jour_requete(req_id, statut="terminee",
                                                  resultat={"message": "Réactivation effectuée avec succès"},
                                                  logs=["Réactivation OK"])
                        else:
                            mettre_a_jour_requete(req_id, statut="echouee",
                                                  resultat={"erreur": msg or "Échec réactivation"})

                # Réinitialisation code parental
                elif type_req == "réinitialisation":
                    res = rechercher_par_numero(driver, valeur, ow, nw)
                    if verifier_et_abandonner(worker_id, req_id, utilisateur):
                        time.sleep(pause)
                        continue
                    if not res or not isinstance(res, tuple):
                        mettre_a_jour_requete(req_id, statut="echouee",
                                              resultat={"erreur": "Abonné introuvable pour réinitialisation"})
                    else:
                        _, fiche = res
                        ok, msg  = action_abonne(driver, fiche, action="reinit")
                        if verifier_et_abandonner(worker_id, req_id, utilisateur):
                            time.sleep(pause)
                            continue
                        if ok:
                            mettre_a_jour_requete(req_id, statut="terminee",
                                                  resultat={"message": "Code parental réinitialisé avec succès"},
                                                  logs=["Réinitialisation OK"])
                        else:
                            mettre_a_jour_requete(req_id, statut="echouee",
                                                  resultat={"erreur": msg or "Échec réinitialisation"})

                # Type inconnu
                else:
                    logging.warning(f"W{worker_id} — Type de requête inconnu : '{type_req}'")
                    mettre_a_jour_requete(req_id, statut="echouee",
                                          resultat={"erreur": f"Type non géré : {type_req}"})

            except Exception as e:
                logging.error(f"W{worker_id} — Erreur traitement Req {req_id} : {e}", exc_info=True)

                if "session" in str(e).lower() or "window" in str(e).lower():
                    logging.warning(
                        f"W{worker_id} — Browser perdu sur Req {req_id}. "
                        f"Remise en attente + reconnexion..."
                    )
                    mettre_a_jour_requete(
                        req_id,
                        statut="en_attente",
                        logs=[f"W{worker_id} — Browser perdu en cours de traitement, reprise automatique."]
                    )
                    _marquer_session_cgaweb(worker_id, False)
                    try:
                        manager.stop_driver()
                        logging.info(f"W{worker_id} — WebDriver stoppé après crash")
                    except Exception:
                        pass
                    driver = ow = nw = None

                    logging.info(f"W{worker_id} — Reconnexion CGAWEB immédiate...")
                    new_driver, new_ow, new_nw = _connecter_cgaweb()

                    if new_driver is None:
                        logging.error(
                            f"W{worker_id} — Reconnexion impossible. "
                            f"Req {req_id} → echouee. Arrêt du worker."
                        )
                        mettre_a_jour_requete(
                            req_id,
                            statut="echouee",
                            resultat={"erreur": "Browser perdu + reconnexion CGAWEB impossible."},
                            logs=[f"W{worker_id} — Abandon après échec reconnexion."]
                        )
                        break

                    driver, ow, nw = new_driver, new_ow, new_nw
                    logging.info(f"W{worker_id} — Reconnexion OK. Req {req_id} reprise au prochain tour.")

                else:
                    mettre_a_jour_requete(
                        req_id,
                        statut="echouee",
                        resultat={"erreur": str(e)}
                    )

            time.sleep(pause)

    except Exception as e:
        logging.critical(f"Worker {worker_id} crashé de façon inattendue : {e}", exc_info=True)
        raise

    finally:
        logging.info(f"W{worker_id} — Nettoyage final en cours...")
        _deconnecter_proprement(driver, manager, worker_id)
        supprimer_verrou_worker(worker_id)
        logging.info(f"W{worker_id} — Arrêt complet.")


# =========================================================
# 🏁 9. LANCEMENT & WATCHDOG
# =========================================================
def lancer_worker():
    global _workers
    with _worker_lock:
        nb     = compter_requetes_en_attente()
        besoin = 2 if nb >= SEUIL_DOUBLE_WORKER else 1
        lances = []

        for wid in range(1, besoin + 1):
            if wid in _workers and _workers[wid].is_alive():
                lances.append(wid)
                continue
            if est_worker_actif(wid):
                lances.append(wid)
                continue

            supprimer_verrou_worker(wid)
            if creer_verrou_worker(wid):
                t = threading.Thread(
                    target=traiter_file_automatique,
                    args=(wid,),
                    daemon=True,
                    name=f"Worker-{wid}"
                )
                t.start()
                _workers[wid] = t
                lances.append(wid)
                logging.info(f"Worker {wid} lancé")

        return lances


def _watchdog(interval=30):
    """
    Watchdog — surveille les workers et nettoie les sessions expirées.
    Ne relance PAS un worker arrêté pour saturation CGAWEB.
    """
    logging.info("Watchdog démarré — surveillance toutes les %ds", interval)
    while True:
        time.sleep(interval)
        try:
            with _worker_lock:

                # Nettoyage sessions utilisateurs expirées
                try:
                    nettoyer_sessions_expirées(timeout_minutes=30)
                except Exception as e:
                    logging.error(f"Watchdog — erreur nettoyage sessions : {e}")

                # Worker 1 : toujours vivant
                try:
                    w1_vivant = 1 in _workers and _workers[1].is_alive()
                    if not w1_vivant:
                        echecs_w1 = _echecs_consecutifs.get(1, 0)
                        if echecs_w1 >= MAX_ECHECS_CONSECUTIFS:
                            logging.warning(
                                f"Watchdog — Worker 1 arrêté pour saturation CGAWEB "
                                f"({echecs_w1} échecs). Pas de relance immédiate."
                            )
                            _echecs_consecutifs[1] = 0
                        else:
                            logging.warning("Watchdog : Worker 1 mort — relance...")
                            supprimer_verrou_worker(1)
                            if creer_verrou_worker(1):
                                t = threading.Thread(
                                    target=traiter_file_automatique,
                                    args=(1,), daemon=True, name="Worker-1"
                                )
                                t.start()
                                _workers[1] = t
                                logging.info("Watchdog : Worker 1 relancé")
                except Exception as e:
                    logging.error(f"Watchdog — erreur relance Worker 1 : {e}")

                # Worker 2 : selon la charge
                try:
                    nb = compter_requetes_en_attente()
                    if nb >= SEUIL_DOUBLE_WORKER:
                        w2_vivant = 2 in _workers and _workers[2].is_alive()
                        if not w2_vivant:
                            echecs_w2 = _echecs_consecutifs.get(2, 0)
                            if echecs_w2 >= MAX_ECHECS_CONSECUTIFS:
                                logging.warning(
                                    f"Watchdog — Worker 2 arrêté pour saturation CGAWEB "
                                    f"({echecs_w2} échecs). Pas de relance immédiate."
                                )
                                _echecs_consecutifs[2] = 0
                            else:
                                logging.warning("Watchdog : Worker 2 mort — relance (charge élevée)...")
                                supprimer_verrou_worker(2)
                                if creer_verrou_worker(2):
                                    t = threading.Thread(
                                        target=traiter_file_automatique,
                                        args=(2,), daemon=True, name="Worker-2"
                                    )
                                    t.start()
                                    _workers[2] = t
                                    logging.info("Watchdog : Worker 2 relancé")
                except Exception as e:
                    logging.error(f"Watchdog — erreur relance Worker 2 : {e}")

        except Exception as e:
            logging.error(f"Watchdog erreur globale (boucle continue) : {e}")


@st.cache_resource
def demarrage_permanent_workers():
    """
    Initialisation du système VISUV.
    Garde-fou _started pour éviter les lancements multiples liés aux re-runs Streamlit.
    """
    global _started
    if _started:
        logging.info("demarrage_permanent_workers() — déjà initialisé, ignoré.")
        return []

    _started = True
    logging.info("Initialisation du système VISUV...")
    nettoyer_vieux_verrous()

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cgaweb_sessions SET connecte = 0")
            conn.commit()
            cursor.close()
        logging.info("Slots CGAWEB remis à zéro au démarrage")
    except Exception as e:
        logging.warning(f"Impossible de réinitialiser cgaweb_sessions : {e}")

    lances = lancer_worker()

    wd = threading.Thread(
        target=_watchdog, args=(30,), daemon=True, name="Watchdog"
    )
    wd.start()

    logging.info(f"Watchdog actif | Workers lancés : {lances}")
    return lances
