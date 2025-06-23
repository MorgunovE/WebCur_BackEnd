import pytest
import os
import sys
import logging
import uuid

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
from repositories.user_repository import UserRepository

@pytest.fixture
def client():
    """
    Fixture Pytest pour créer un client de test Flask.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def cleanup_users():
    """
    Fixture Pytest pour nettoyer les utilisateurs créés par ce test.
    """
    repo = UserRepository()
    users_created_in_this_test_run = [] 
    yield users_created_in_this_test_run 
    
    for email in users_created_in_this_test_run:
        try:
            repo.supprimer_par_email(email)
            logging.info(f"Utilisateur de test '{email}' nettoyé.")
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage de l'utilisateur '{email}': {e}")


def get_jwt_token(client, users_to_cleanup_list):
    unique_email = f"currency_error_test_user_{uuid.uuid4()}@mail.com" 
    password = "errpass"
    
    users_to_cleanup_list.append(unique_email)

    client.post('/utilisateurs', json={
        "email": unique_email,
        "mot_de_passe": password,
        "nom_utilisateur": "CurrencyErrorTest"
    })
    
    resp = client.post('/connexion', json={
        "email": unique_email,
        "mot_de_passe": password
    })
    return resp.get_json()["access_token"]


def get_error_message(data):
    """
    Extrait un message d'erreur d'une réponse JSON qui peut être un dict ou une liste.
    """
    if isinstance(data, dict):
        if "message" in data:
            return data["message"]
        elif "errors" in data: # Pour les erreurs de validation de schéma
            # Cherche le premier message d'erreur dans les 'errors'
            for field, messages in data["errors"].items():
                if isinstance(messages, list) and messages:
                    return messages[0] # Retourne le premier message du premier champ
            return str(data["errors"]) # Fallback si format inattendu
    elif isinstance(data, list) and data:
        
        if isinstance(data[0], dict):
            if "message" in data[0]:
                return data[0]["message"]
            elif "errors" in data[0]:
                for field, messages in data[0]["errors"].items():
                    if isinstance(messages, list) and messages:
                        return messages[0]
                return str(data[0]["errors"])
        elif isinstance(data[0], str): 
            return data[0]
    return str(data) 


# --- Tests pour GET /devises/<CODE> ---
def test_get_currency_non_existent_code(client):
    """
    Scénario: Demander des détails sur une devise qui n'existe pas.
    Attendu: 404 Not Found ou 502 Bad Gateway si l'API externe échoue.
    """
    test_name = "test_get_currency_non_existent_code"
    logging.info(f"Test: {test_name} - Demander des détails sur une devise inexistante.")
    try:
        response = client.get('/devises/XYZ') # Code inexistant
        # Accept either 404 (resource not found) or 502 (bad gateway, implying external API issue)
        assert response.status_code in [404, 502], \
            f"Attendu 404 ou 502 pour une devise inexistante, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        
        # le cas où data est None
        if response.status_code == 502:
            if data is None:
               
                assert response.get_data(as_text=True) == "", \
                    f"Attendu corps vide pour 502 sans JSON, mais reçu: '{response.get_data(as_text=True)}'"
            else:
             
                error_message = get_error_message(data)
                assert "Erreur lors de la récupération des taux de change" in error_message, \
                    f"Message inattendu pour 502: {error_message}. Réponse complète: {data}"
        elif response.status_code == 404:
        
            assert isinstance(data, dict) and "message" in data, \
                f"Le JSON de réponse pour 404 devrait être un dictionnaire avec une clé 'message', mais reçu: {data}"
            assert "non trouvé" in data["message"] or "not found" in data["message"] or "pas disponible" in data["message"], \
                f"Message inattendu pour 404: {data['message']}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

# --- Tests pour POST /devises/conversion ---
def test_convert_currency_missing_source_code(client, cleanup_users):
    """
    Scénario: Tenter une conversion avec un code source manquant dans la requête.
    Attendu: 400 Bad Request.
    """
    test_name = "test_convert_currency_missing_source_code"
    logging.info(f"Test: {test_name} - Tenter une conversion avec un code source manquant.")
    try:
        token = get_jwt_token(client, cleanup_users) 
        response = client.post(
            '/devises/conversion',
            json={"code_cible": "EUR", "montant": 100}, # code_source manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour un code source manquant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "code_source" in error_message or \
               "Code source, code cible et montant sont requis." in error_message, \
            f"Message d'erreur inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_convert_currency_missing_target_code(client, cleanup_users):
    """
    Scénario: Tenter une conversion avec un code cible manquant dans la requête.
    Attendu: 400 Bad Request.
    """
    test_name = "test_convert_currency_missing_target_code"
    logging.info(f"Test: {test_name} - Tenter une conversion avec un code cible manquant.")
    try:
        token = get_jwt_token(client, cleanup_users)
        response = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "montant": 100}, # code_cible manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour un code cible manquant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "code_cible" in error_message or \
               "Code source, code cible et montant sont requis." in error_message, \
            f"Message d'erreur inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_convert_currency_invalid_amount(client, cleanup_users):
    """
    Scénario: Tenter une conversion avec un montant invalide (non-numérique или négatif).
    Attendu: 400 Bad Request.
    """
    test_name = "test_convert_currency_invalid_amount"
    logging.info(f"Test: {test_name} - Tenter une conversion avec un montant invalide.")
    try:
        token = get_jwt_token(client, cleanup_users)
        # Test 1: Montant non numérique
        response1 = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "code_cible": "EUR", "montant": "abc"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 400, \
            f"Attendu 400 pour un montant non numérique, mais reçu {response1.status_code}. Réponse: {response1.get_data(as_text=True)}"
        data1 = response1.get_json()
        error_message1 = get_error_message(data1)
        assert "Montant invalide" in error_message1 or \
               "Not a valid number" in error_message1 or \
               "Doit être un nombre" in error_message1 or \
               "Code source, code cible et montant sont requis." in error_message1, \
            f"Message inattendu pour un montant non numérique: {error_message1}"

        # Test 2: Montant négatif
        response2 = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "code_cible": "EUR", "montant": -100},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 400, \
            f"Attendu 400 pour un montant négatif, mais reçu {response2.status_code}. Réponse: {response2.get_data(as_text=True)}"
        data2 = response2.get_json()
        error_message2 = get_error_message(data2)
        assert "Montant invalide" in error_message2 or \
               "Doit être positif" in error_message2 or \
               "Code source, code cible et montant sont requis." in error_message2, \
            f"Message inattendu pour un montant négatif: {error_message2}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_convert_currency_non_existent_source_or_target(client, cleanup_users):
    """
    Scénario: Tenter une conversion avec un code source ou cible inexistant.
    Attendu: 404 Not Found.
    """
    test_name = "test_convert_currency_non_existent_source_or_target"
    logging.info(f"Test: {test_name} - Tenter une conversion avec une devise source/cible inexistante.")
    try:
        token = get_jwt_token(client, cleanup_users)
        # Test 1: Code source inexistant
        response1 = client.post(
            '/devises/conversion',
            json={"code_source": "XXX", "code_cible": "EUR", "montant": 100},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 404, \
            f"Attendu 404 pour une devise source inexistante, mais reçu {response1.status_code}. Réponse: {response1.get_data(as_text=True)}"
        data1 = response1.get_json()
        error_message1 = get_error_message(data1)
        assert "Taux de change non disponible" in error_message1 or \
               "Devise source ou cible non trouvée" in error_message1 or \
               "non trouvée" in error_message1, \
            f"Message inattendu pour source inexistante: {error_message1}"

        # Test 2: Code cible inexistant
        response2 = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "code_cible": "YYY", "montant": 100},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 404, \
            f"Attendu 404 pour une devise cible inexistante, mais reçu {response2.status_code}. Réponse: {response2.get_data(as_text=True)}"
        data2 = response2.get_json()
        error_message2 = get_error_message(data2)
        assert "Devise source ou cible non trouvée" in error_message2 or "non trouvée" in error_message2, \
            f"Message inattendu pour cible inexistante: {error_message2}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_convert_currency_unauthenticated(client):
    """
    Scénario: Tenter une conversion sans authentification.
    Attendu: 401 Unauthorized.
    """
    test_name = "test_convert_currency_unauthenticated"
    logging.info(f"Test: {test_name} - Tenter une conversion sans authentification.")
    try:
        response = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "code_cible": "EUR", "montant": 100}
        )
        assert response.status_code == 401, \
            f"Attendu 401 pour une conversion non authentifiée, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing or invalid Authorization header" in error_message or \
               "Unauthorized" in error_message or \
               "Jeton manquant" in error_message, \
            f"Message inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise