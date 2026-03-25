"""
Module d'initialisation des workers - À importer au démarrage de l'application
"""
import logging
import atexit
from file_attente import (
    lancer_worker, 
    supprimer_verrou_worker,
    compter_requetes_en_attente
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("WorkerInit")

# Flag global pour éviter les initialisations multiples
_workers_initialises = False


def initialiser_workers_au_demarrage():
    """
    Initialise les workers au démarrage de l'application.
    À appeler UNE SEULE FOIS dans main.py
    """
    global _workers_initialises
    
    if _workers_initialises:
        logger.info("⚠️ Workers déjà initialisés, skip")
        return
    
    try:
        # Nettoyer les anciens verrous au démarrage
        supprimer_verrou_worker(1)
        supprimer_verrou_worker(2)
        logger.info("🧹 Nettoyage des anciens verrous effectué")
        
        # Vérifier s'il y a des requêtes en attente
        nb_requetes = compter_requetes_en_attente()
        
        if nb_requetes > 0:
            logger.info(f"📋 {nb_requetes} requête(s) en attente au démarrage")
            workers = lancer_worker()
            if workers:
                logger.info(f"✅ {len(workers)} worker(s) démarré(s) au lancement de l'application")
        else:
            logger.info("💤 Aucune requête en attente, workers non démarrés")
        
        _workers_initialises = True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des workers : {e}")


def nettoyer_workers_a_larret():
    """
    Nettoie les verrous des workers à l'arrêt de l'application.
    Appelé automatiquement via atexit.
    """
    logger.info("🛑 Nettoyage des workers à l'arrêt...")
    try:
        supprimer_verrou_worker(1)
        supprimer_verrou_worker(2)
        logger.info("✅ Nettoyage terminé")
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage : {e}")


# Enregistrer le nettoyage automatique à l'arrêt
atexit.register(nettoyer_workers_a_larret)