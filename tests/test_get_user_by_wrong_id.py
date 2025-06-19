import pytest
import os
import sys
import logging
import secrets # Pour generer des données randomes


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logging_config import setup_logging
from app import app


setup_logging('test_results.log')

def log_test_result(test_name, result):
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test pour GET /utilisateurs/{id} (Récupération d'un utilisateur par ID) - ID inexistant ***

def test_get_user_by_non_existent_id(client):
    test_name = "test_get_user_by_non_existent_id"
     # Génère une chaîne hexadécimale de 24 caractères qui imite un ObjectId
    # et est garantie de ne pas exister dans la base de données
    non_existent_mongo_id = secrets.token_hex(12) # 12 octets = 24 caractères hexadécimaux
    logging.info(f"Test: Attempting to get user with non-existent Mongo-like ID: {non_existent_mongo_id}")

    try:
        #  Envoie une requête GET à /utilisateurs/ID_inexistant
        response = client.get(f'/utilisateurs/{non_existent_mongo_id}')
        
        # Attendu 1: Code de statut 404 Not Found
        assert response.status_code == 404, \
            f"Expected 404 Not Found, but got {response.status_code}. Response: {response.get_data(as_text=True)}"
        
        # Attendu 2: Vérifie le message d'erreur
        response_data = response.get_json()
        assert "message" in response_data, "Response JSON does not contain 'message' key."
        assert "Utilisateur non trouvé" in response_data["message"], \
            f"Expected message 'Utilisateur non trouvé', but got: {response_data['message']}"
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        # Journalise toute erreur inattendue qui pourrait survenir avant les vérifications
        logging.error(f"Test {test_name} failed due to unexpected error: {e}")
        log_test_result(test_name, False)
        raise
