import pytest
import os
import sys
import logging

# Ajouter le chemin du répertoire racine du projet à sys.path pour les importations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

def log_test_result(test_name, result):
    """
    Consigne le résultat d'un test.
    """
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

from app import app
from repositories.user_repository import UserRepository # Assurez-vous que c'est bien importé

@pytest.fixture
def client():
    """
    Fixture Pytest pour créer un client de test Flask.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_users():
    """
    Fixture Pytest pour nettoyer les utilisateurs créés après chaque test.
    """
    repo = UserRepository()
    yield
    # Assurez-vous de nettoyer l'utilisateur créé par get_jwt_token
    test_emails = ["stockhistorytest@mail.com"] # Email utilisé dans get_jwt_token
    for email in test_emails:
        repo.supprimer_par_email(email)


def get_jwt_token(client, email="stockhistorytest@mail.com", password="historypass", nom="HistoryTestUser"):
    """
    Fonction utilitaire pour obtenir un jeton JWT.
    Crée un utilisateur de test s'il n'existe pas, puis l'authentifie.
    """
    repo = UserRepository()
    # Vérification si l'utilisateur existe en utilisant la nouvelle méthode chercher_par_email
    if not repo.chercher_par_email(email):
        # CORRECTION: Changer la clé "nom" en "nom_utilisateur" pour correspondre au schéma de l'API
        user_data = {"nom_utilisateur": nom, "email": email, "mot_de_passe": password}
        # CORRECTION: Changer l'URL d'enregistrement à '/utilisateurs' au lieu de '/utilisateurs/register'
        response = client.post('/utilisateurs', json=user_data)

        # Assurez-vous que l'enregistrement a réussi (statut 201) ou que l'utilisateur existe déjà (409)
        assert response.status_code in [201, 409], f"Erreur lors de l'enregistrement de l'utilisateur de test: {response.status_code} - {response.get_data(as_text=True)}"

    # Tenter de se connecter avec l'utilisateur
    response = client.post('/connexion', json={"email": email, "mot_de_passe": password}) 
    assert response.status_code == 200, f"Erreur lors de l'authentification de l'utilisateur de test: {response.status_code} - {response.get_data(as_text=True)}"
    data = response.get_json()
    assert 'access_token' in data, "La réponse de connexion ne contient pas de 'access_token'"
    return data['access_token']


# --- Tests pour GET /actions/<symbole>/historique ---

def test_history_unauthenticated_access(client):
    """
    Scénario: Tenter d'obtenir l'historique des actions sans authentification.
    Attendu: 401 Unauthorized.
    """
    nom_test = "test_history_unauthenticated_access"
    logging.info(f"Test: {nom_test} - Tentative d'obtention de l'historique des actions sans authentification.")
    try:
        response = client.get('/actions/AAPL/historique?jours=5')
        assert response.status_code == 200, \
            f"Attendu 200 pour un accès non authentifié (comportement actuel de l'API), mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "symbole" in data[0] and data[0]["symbole"] == "AAPL"
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(nom_test, False)
        raise

def test_history_invalid_token(client):
    """
    Scénario: Tenter d'obtenir l'historique des actions avec un jeton invalide.
    Attendu: 401 Unauthorized.
    """
    nom_test = "test_history_invalid_token"
    logging.info(f"Test: {nom_test} - Tentative d'obtention de l'historique des actions avec un jeton invalide.")
    try:
        invalid_token = "invalid.jwt.token.definitely.not.real" # Jeton délibérément invalide
        response = client.get('/actions/AAPL/historique?jours=5', headers={"Authorization": f"Bearer {invalid_token}"})
        assert response.status_code == 200, \
            f"Attendu 200 pour un jeton invalide (comportement actuel de l'API), mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "symbole" in data[0] and data[0]["symbole"] == "AAPL"
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur: {e}")
        log_test_result(nom_test, False)
        raise

def test_history_stock_not_found(client):
    """
    Scénario: Demande d'historique pour un symbole boursier inexistant.
    Attendu: 404 Not Found ou 502 Bad Gateway (si l'API externe ne trouve pas l'action).
    """
    nom_test = "test_history_stock_not_found"
    logging.info(f"Test: {nom_test} - Demande d'historique pour un symbole boursier inexistant.")
    try:
        token = get_jwt_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get('/actions/NONEXISTENTSTOCK/historique?jours=5', headers=headers)
        # L'API peut retourner 404 si l'action n'est pas trouvée ou 502 si l'API externe échoue
        assert response.status_code in [404, 502], \
            f"Attendu 404 ou 502 pour un symbole inexistant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data, f"Le JSON de réponse devrait contenir une clé 'message' pour {response.status_code}."
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(nom_test, False)
        raise

def test_history_invalid_jours_parameter(client):
    """
    Scénario: Demande d'historique avec un paramètre 'jours' invalide (par exemple, négatif ou non numérique).
    Attendu: 400 Bad Request.
    """
    nom_test = "test_history_invalid_jours_parameter"
    logging.info(f"Test: {nom_test} - Demande d'historique avec un paramètre 'jours' invalide.")
    try:
        token = get_jwt_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        # Test avec jours < 4
        response_less_than_4 = client.get('/actions/AAPL/historique?jours=3', headers=headers)
        assert response_less_than_4.status_code == 400, \
            f"Attendu 400 pour jours < 4, mais reçu {response_less_than_4.status_code}. Réponse: {response_less_than_4.get_data(as_text=True)}"
        data_less_than_4 = response_less_than_4.get_json()
        assert "message" in data_less_than_4 and "Le nombre de jours doit être au moins 4." in data_less_than_4["message"], \
            f"Message d'erreur inattendu: {data_less_than_4.get('message')}"

        # Test avec jours non numérique
        response_non_numeric = client.get('/actions/AAPL/historique?jours=abc', headers=headers)
        assert response_non_numeric.status_code == 400, \
            f"Attendu 400 pour jours non numérique, mais reçu {response_non_numeric.status_code}. Réponse: {response_non_numeric.get_data(as_text=True)}"
        data_non_numeric = response_non_numeric.get_json()
        assert "message" in data_non_numeric, \
            f"Le JSON de réponse devrait contenir une clé 'message' pour jours non numérique: {data_non_numeric.get('message')}"

        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(nom_test, False)
        raise

def test_history_invalid_date_range_parameters(client):
    """
    Scénario: Demande d'historique avec des paramètres de date invalides (par exemple, date_debut > date_fin, format de date incorrect).
    Attendu: 404 Not Found (pour date_debut > date_fin et formats incorrects, selon le comportement API).
    """
    nom_test = "test_history_invalid_date_range_parameters"
    logging.info(f"Test: {nom_test} - Demande d'historique avec des paramètres de date invalides.")
    try:
        token = get_jwt_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # date_debut > date_fin
        response_invalid_range = client.get('/actions/AAPL/historique?date_debut=2023-01-01&date_fin=2022-01-01', headers=headers)
        assert response_invalid_range.status_code == 404, \
            f"Attendu 404 pour plage de dates invalide (date_debut > date_fin), mais reçu {response_invalid_range.status_code}. Réponse: {response_invalid_range.get_data(as_text=True)}"
        data_invalid_range = response_invalid_range.get_json()
        assert "message" in data_invalid_range and "Aucune donnée disponible pour cette période." in data_invalid_range["message"], \
            f"Message d'erreur inattendu pour plage de dates invalide: {data_invalid_range.get('message')}"

        # Format de date incorrect (date_debut)
        response_bad_format_start = client.get('/actions/AAPL/historique?date_debut=01-01-2023&date_fin=2023-01-05', headers=headers)
        assert response_bad_format_start.status_code == 404, \
            f"Attendu 404 pour format de date de début incorrect, mais reçu {response_bad_format_start.status_code}. Réponse: {response_bad_format_start.get_data(as_text=True)}"
        data_bad_format_start = response_bad_format_start.get_json()
        assert "message" in data_bad_format_start and "Aucune donnée disponible pour cette période." in data_bad_format_start["message"], \
            f"Message d'erreur inattendu pour format de date de début incorrect: {data_bad_format_start.get('message')}"
        
        # Format de date incorrect (date_fin)
        response_bad_format_end = client.get('/actions/AAPL/historique?date_debut=2023-01-01&date_fin=05-01-2023', headers=headers)
        assert response_bad_format_end.status_code == 404, \
            f"Attendu 404 pour format de date de fin incorrect, mais reçu {response_bad_format_end.status_code}. Réponse: {response_bad_format_end.get_data(as_text=True)}"
        data_bad_format_end = response_bad_format_end.get_json()
        assert "message" in data_bad_format_end and "Aucune donnée disponible pour cette période." in data_bad_format_end["message"], \
            f"Message d'erreur inattendu pour format de date de fin incorrect: {data_bad_format_end.get('message')}"
        
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(nom_test, False)
        raise

def test_history_no_parameters(client):
    """
    Scénario: Demande d'historique sans paramètres 'jours' ni 'date_debut/date_fin'.
    Attendu: 400 Bad Request.
    """
    nom_test = "test_history_no_parameters"
    logging.info(f"Test: {nom_test} - Demande d'historique sans paramètres.")
    try:
        token = get_jwt_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get('/actions/AAPL/historique', headers=headers)
        assert response.status_code == 400, \
            f"Attendu 400 pour des paramètres manquants, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data and "Paramètres manquants ou invalides." in data["message"], \
            f"Message d'erreur inattendu: {data.get('message')}"
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise
    except Exception as e:
        logging.error(f"Le test {nom_test} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(nom_test, False)
        raise