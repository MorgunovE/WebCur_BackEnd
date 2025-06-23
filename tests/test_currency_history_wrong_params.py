import pytest
import logging
import sys
import os
import datetime
import uuid

# Configuration du logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

# Ajouter le chemin du projet pour importer l'application Flask et les repos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from repositories.user_repository import UserRepository
from repositories.currency_repository import CurrencyRepository 

@pytest.fixture
def client():
    """
    Fixtur Pytest pour obtenir un client de test Flask.
    Configure l'application en mode test.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def cleanup_users():
    repo = UserRepository()
    users_created_in_this_test_run = []
    yield users_created_in_this_test_run

    for email in users_created_in_this_test_run:
        try:
            repo.supprimer_par_email(email)
            logging.info(f"Utilisateur de test '{email}' nettoyé.")
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage de l'utilisateur '{email}': {e}")


# --- Fonctions utilitaires ---

def log_test_result(test_name, result):
    """
    Enregistre le résultat d'un test dans le fichier de log.
    """
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

def get_jwt_token_for_currency_tests(client, users_to_cleanup_list):
    """
    Fonction d'aide pour obtenir un token JWT pour les tests de devise.
    Crée un utilisateur de test spécifique pour les devises si nécessaire.
    """
    unique_email = f"cur_history_test_user_{uuid.uuid4()}@mail.com"
    user_password = "currhistorypass"
    user_username = "CurrencyHistoryUser"

    users_to_cleanup_list.append(unique_email) 

    client.post('/utilisateurs', json={
        "email": unique_email, 
        "mot_de_passe": user_password,
        "nom_utilisateur": user_username
    })
    
    response = client.post('/connexion', json={
        "email": unique_email, 
        "mot_de_passe": user_password
    })
    token = response.get_json().get("access_token")
    assert token is not None, f"Échec de l'obtention du token JWT pour {unique_email}."
    return token

# --- Tests pour GET /devises/{nom}/historique (Histoire des devises) ---

def test_get_currency_history_success_jours(client, cleanup_users):
    """
    Scénario: Requête réussie pour l'historique des devises avec le paramètre 'jours'.
    Le test s'attend à ce que l'API gère le cache et les appels externes.
    """
    test_name = "test_get_currency_history_success_jours"
    logging.info(f"Test: {test_name} - Tentative de récupération de l'historique d'une devise avec 'jours'.")

    try:
        currency_name = "USD"
        jours = 7 
        token = get_jwt_token_for_currency_tests(client, cleanup_users)

        logging.info(f"   Envoi de la requête GET /devises/{currency_name}/historique?jours={jours}")
        response = client.get(
            f'/devises/{currency_name}/historique?jours={jours}',
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, \
            f"Statut attendu 200, obtenu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        
        assert isinstance(data, list), "La réponse devrait être une liste d'objets historiques."
        assert len(data) > 0, "La liste de données historiques ne devrait pas être vide."

        for item in data:
            assert isinstance(item, dict), "Chaque élément de la liste devrait être un dictionnaire."
            assert "nom" in item and item["nom"] == currency_name, "Le nom de la devise est incorrect dans un élément."
            assert "date_maj" in item and isinstance(item["date_maj"], str) and len(item["date_maj"]) == 10, "Le format de la date est incorrect (AAAA-MM-JJ)."
            assert "conversion_rates" in item and isinstance(item["conversion_rates"], dict), "Les taux de conversion devraient être un dictionnaire."
            assert item["taux"] is not None, "Le taux devrait être présent."
            assert any(isinstance(val, (int, float)) for val in item["conversion_rates"].values()), \
                "Les taux de conversion devraient être des nombres."
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_get_currency_history_success_date_range(client, cleanup_users):
    """
    Scénario: Requête réussie pour l'historique des devises avec les paramètres 'date_debut' et 'date_fin'.
    """
    test_name = "test_get_currency_history_success_date_range"
    logging.info(f"Test: {test_name} - Tentative de récupération de l'historique d'une devise avec une plage de dates.")

    try:
        currency_name = "EUR"
        today = datetime.date.today()
        date_fin = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        date_debut = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        token = get_jwt_token_for_currency_tests(client, cleanup_users)

        logging.info(f"   Envoi de la requête GET /devises/{currency_name}/historique?date_debut={date_debut}&date_fin={date_fin}")
        response = client.get(
            f'/devises/{currency_name}/historique?date_debut={date_debut}&date_fin={date_fin}',
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, \
            f"Statut attendu 200, obtenu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
   
        assert isinstance(data, list), "La réponse devrait être une liste d'objets JSON."
        assert len(data) > 0, "Aucune donnée historique retournée."

        for item in data:
            assert isinstance(item, dict), "Chaque élément de la liste devrait être un dictionnaire."
            assert "nom" in item and item["nom"] == currency_name, "Le nom de la devise est incorrect dans un élément."
            assert "date_maj" in item and isinstance(item["date_maj"], str) and len(item["date_maj"]) == 10, "Le format de la date est incorrect (AAAA-MM-JJ)."
            assert "conversion_rates" in item and isinstance(item["conversion_rates"], dict), "Les taux de conversion devraient être un dictionnaire."
            assert item["taux"] is not None, "Le taux devrait être présent."
            assert any(isinstance(val, (int, float)) for val in item["conversion_rates"].values()), \
                "Les taux de conversion devraient être des nombres."


        response_dates = sorted([item["date_maj"] for item in data])
        assert response_dates[0] >= date_debut, f"La date de début de la réponse ({response_dates[0]}) est antérieure à la date demandée ({date_debut})."
        assert response_dates[-1] <= date_fin, f"La date de fin de la réponse ({response_dates[-1]}) est postérieure à la date demandée ({date_fin})."

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_get_currency_history_nonexistent_currency(client, cleanup_users):
    """
    Scénario: Tentative de récupération de l'historique pour une devise inexistante.
    """
    test_name = "test_get_currency_history_nonexistent_currency"
    logging.info(f"Test: {test_name} - Tentative de récupération de l'historique pour une devise inexistante.")

    try:
        currency_name = "XYZ" # Devise qui n'existe pas
        jours = 7
        token = get_jwt_token_for_currency_tests(client, cleanup_users)

        logging.info(f"   Envoi de la requête GET /devises/{currency_name}/historique?jours={jours}")
        response = client.get(
            f'/devises/{currency_name}/historique?jours={jours}',
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404, \
            f"Statut attendu 404 pour devise inexistante, obtenu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        assert "message" in data, "La réponse devrait contenir un message d'erreur."
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_get_currency_history_invalid_jours_parameter(client, cleanup_users):
    """
    Scénario: Requête avec un paramètre 'jours' invalide (inférieur au minimum, si défini dans README).
    """
    test_name = "test_get_currency_history_invalid_jours_parameter"
    logging.info(f"Test: {test_name} - Tentative de récupération avec un paramètre 'jours' invalide.")

    try:
        currency_name = "USD"
        jours = 3 
        token = get_jwt_token_for_currency_tests(client, cleanup_users)

        logging.info(f"   Envoi de la requête GET /devises/{currency_name}/historique?jours={jours}")
        response = client.get(
            f'/devises/{currency_name}/historique?jours={jours}',
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, \
            f"Statut attendu 200 pour 'jours' invalide, obtenu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        assert isinstance(data, list), "La réponse devrait être une liste d'objets historiques."
        assert len(data) > 0, "La liste de données historiques ne devrait pas être vide."
        
        for item in data:
            assert isinstance(item, dict)
            assert "nom" in item and item["nom"] == currency_name
            assert "date_maj" in item
            assert "conversion_rates" in item

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_get_currency_history_invalid_date_parameters(client, cleanup_users):
    """
    Scénario: Requête avec des paramètres de date invalides (dates inversées ou format incorrect).
    """
    test_name = "test_get_currency_history_invalid_date_parameters"
    logging.info(f"Test: {test_name} - Tentative de récupération avec des paramètres de date invalides.")

    try:
        currency_name = "USD"
        token = get_jwt_token_for_currency_tests(client, cleanup_users)
        
        # Cas 1: Dates inversées (date_debut > date_fin)
        date_debut_reversed = "2024-01-07"
        date_fin_reversed = "2024-01-01"
        logging.info(f"   Cas 1: Dates inversées - {date_debut_reversed} à {date_fin_reversed}")
        response_reversed = client.get(
            f'/devises/{currency_name}/historique?date_debut={date_debut_reversed}&date_fin={date_fin_reversed}',
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response_reversed.status_code == 404, \
            f"Statut attendu 404 pour dates inversées, obtenu {response_reversed.status_code}. Réponse: {response_reversed.get_data(as_text=True)}"
        data_reversed = response_reversed.get_json()
        assert "message" in data_reversed, "La réponse devrait contenir un message d'erreur pour dates inversées."
       
        assert "Aucune donnée disponible pour cette période." in data_reversed["message"], \
            "Le message d'erreur pour dates inversées est inattendu." 

        # Cas 2: Format de date incorrect
        date_debut_bad_format = "2024/01/01" # Format invalide
        date_fin_correct_format = "2024-01-07"
        logging.info(f"   Cas 2: Format de date incorrect - {date_debut_bad_format}")
        response_bad_format = client.get(
            f'/devises/{currency_name}/historique?date_debut={date_debut_bad_format}&date_fin={date_fin_correct_format}',
            headers={"Authorization": f"Bearer {token}"}
        )
   
        assert response_bad_format.status_code == 404, \
            f"Statut attendu 404 pour format de date invalide, obtenu {response_bad_format.status_code}. Réponse: {response_bad_format.get_data(as_text=True)}"
        data_bad_format = response_bad_format.get_json()
        assert "message" in data_bad_format, "La réponse devrait contenir un message d'erreur pour format de date invalide."
        assert "Aucune donnée disponible pour cette période." in data_bad_format["message"], \
            "Le message d'erreur pour format de date invalide est inattendu." 
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise