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
    repo = UserRepository()
    users_created_in_this_test_run = [] 
    yield users_created_in_this_test_run 

    for email in users_created_in_this_test_run:
        try:
            repo.supprimer_par_email(email)
            logging.info(f"Utilisateur de test '{email}' nettoyé.")
        except Exception as e:
           
            logging.warning(f"Impossible de nettoyer l'utilisateur '{email}': {e}. Il se peut qu'il n'existe pas ou qu'il y ait eu une autre erreur.")

def get_jwt_token(client, users_to_cleanup_list):
    unique_email = f"favorite_test_user_{uuid.uuid4()}@mail.com"
    password = "favpass"

    users_to_cleanup_list.append(unique_email) 

    client.post('/utilisateurs', json={
        "email": unique_email,
        "mot_de_passe": password,
        "nom_utilisateur": "FavoriteErrorTest"
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
        elif "msg" in data: # Pour les messages d'erreur JWT
            return data["msg"]
        elif "errors" in data: # Pour les erreurs de validation de schéma
            for field, messages in data["errors"].items():
                if isinstance(messages, list) and messages:
                    return messages[0]
            return str(data["errors"])
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

# --- Tests pour POST /devises/favoris ---
def test_add_favorite_missing_currency_name(client, cleanup_users):
    """
    Scénario: Tenter d'ajouter un favori sans spécifier le nom de la devise.
    Attendu: 400 Bad Request.
    """
    test_name = "test_add_favorite_missing_currency_name"
    logging.info(f"Test: {test_name} - Tenter d'ajouter un favori sans nom de devise.")
    try:
        token = get_jwt_token(client, cleanup_users)
        response = client.post(
            '/devises/favoris',
            json={}, # nom_devise manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour un nom de devise manquant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "nom_devise" in error_message or \
               "Nom de la devise est requis." in error_message, \
            f"Message d'erreur inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_add_favorite_non_existent_currency(client, cleanup_users):
    """
    Scénario: Tenter d'ajouter une devise inexistante aux favoris.
    Attendu: 404 Not Found (si l'API valide l'existence de la devise), ou 200 OK si l'API ne valide pas.
    """
    test_name = "test_add_favorite_non_existent_currency"
    logging.info(f"Test: {test_name} - Tenter d'ajouter une devise inexistante aux favoris.")
    try:
        token = get_jwt_token(client, cleanup_users)
        response = client.post(
            '/devises/favoris',
            json={"nom_devise": "NONEXISTENT"}, # Devise inexistante
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, \
            f"Attendu 200 pour une devise inexistante à ajouter aux favoris, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Devise ajoutée aux favoris." in error_message, \
            f"Message inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_add_favorite_already_exists(client, cleanup_users):
    """
    Scénario: Tenter d'ajouter une devise déjà présente dans les favoris.
    Attendu: 200 OK ou 409 Conflict.
    """
    test_name = "test_add_favorite_already_exists"
    logging.info(f"Test: {test_name} - Tenter d'ajouter une devise déjà favorite.")
    try:
        token = get_jwt_token(client, cleanup_users)
        client.post(
            '/devises/favoris',
            json={"nom_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        response = client.post(
            '/devises/favoris',
            json={"nom_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Accept 200 OK (idempotent) or 409 Conflict (already exists)
        assert response.status_code in [200, 409], \
            f"Attendu 200 ou 409 pour un favori existant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        if response.status_code == 409:
            assert "Devise déjà dans les favoris." in error_message, \
                f"Message inattendu pour 409: {error_message}"
        elif response.status_code == 200:
            assert "Devise ajoutée aux favoris." in error_message, \
                f"Message inattendu pour 200: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_add_favorite_unauthenticated(client):
    """
    Scénario: Tenter d'ajouter un favori sans authentification.
    Attendu: 401 Unauthorized.
    """
    test_name = "test_add_favorite_unauthenticated"
    logging.info(f"Test: {test_name} - Tenter d'ajouter un favori sans authentification.")
    try:
        response = client.post(
            '/devises/favoris',
            json={"nom_devise": "EUR"}
        )
        assert response.status_code == 401, \
            f"Attendu 401 pour un ajout non authentifié, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
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

# --- Tests pour DELETE /devises/favoris ---
def test_delete_favorite_missing_currency_name(client, cleanup_users):
    """
    Scénario: Tenter de supprimer un favori sans spécifier le nom de la devise.
    Attendu: 400 Bad Request.
    """
    test_name = "test_delete_favorite_missing_currency_name"
    logging.info(f"Test: {test_name} - Tenter de supprimer un favori sans nom de devise.")
    try:
        token = get_jwt_token(client, cleanup_users)
        response = client.delete(
            '/devises/favoris',
            json={}, # nom_devise manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour un nom de devise manquant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "nom_devise" in error_message or \
               "Nom de la devise est requis." in error_message, \
            f"Message d'erreur inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_delete_favorite_non_existent_currency_from_user_favorites(client, cleanup_users):
    """
    Scénario: Tenter de supprimer une devise qui n'est pas dans les favoris de l'utilisateur.
    Attendu: 200 OK (comportement idempotent).
    """
    test_name = "test_delete_favorite_non_existent_currency_from_user_favorites"
    logging.info(f"Test: {test_name} - Tenter de supprimer une devise qui n'est pas dans les favoris de l'utilisateur.")
    try:
        token = get_jwt_token(client, cleanup_users)
        # S'assurer que l'utilisateur n'a pas EUR dans ses favoris pour ce test
        client.delete(
            '/devises/favoris',
            json={"nom_devise": "EUR"},
            headers={"Authorization": f"Bearer {token}"}
        )

        response = client.delete(
            '/devises/favoris',
            json={"nom_devise": "EUR"}, # Devise non présente dans les favoris
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, \
            f"Attendu 200 pour la suppression d'un favori inexistant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Devise retirée des favoris" in error_message or \
               "Devise supprimée des favoris." in error_message, \
            f"Message inattendu pour la suppression d'un favori inexistant: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

def test_delete_favorite_unauthenticated(client):
    """
    Scénario: Tenter de supprimer un favori sans authentification.
    Attendu: 401 Unauthorized.
    """
    test_name = "test_delete_favorite_unauthenticated"
    logging.info(f"Test: {test_name} - Tenter de supprimer un favori sans authentification.")
    try:
        response = client.delete(
            '/devises/favoris',
            json={"nom_devise": "EUR"}
        )
        assert response.status_code == 401, \
            f"Attendu 401 pour une suppression non authentifiée, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
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