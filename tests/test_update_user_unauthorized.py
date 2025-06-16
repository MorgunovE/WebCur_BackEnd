import pytest
import logging
import sys
import os
import secrets 

# Ajoute le chemin vers le répertoire racine du projet pour que les importations fonctionnent correctement
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

# Fonction pour enregistrer les résultats des tests
def log_test_result(test_name, result):
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

# Ajoute le chemin du projet pour importer l'application Flask
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from repositories.user_repository import UserRepository 

# Fixtures pour les tests
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Nettoyage des utilisateurs après chaque test
@pytest.fixture(autouse=True)
def cleanup_users():
    repo = UserRepository()
    yield
    test_emails = [
        "testuser@mail.com",
        "authuser@mail.com",
        "updateuser@mail.com",
        "loginuser@mail.com",
        "deleteuser@mail.com",
        "unauthorized@mail.com", 
        "invalidtoken@mail.com",
        "existinguser_for_nonexistent_id@mail.com", 
        "user_for_invalid_data_test@mail.com",
        "invalid-email" 
    ]
    for email in test_emails:
        repo.supprimer_par_email(email)

# Fonction d'aide pour obtenir le token JWT 
def get_jwt_token(client, email, mot_de_passe):
    response = client.post('/connexion', json={
        "email": email,
        "mot_de_passe": mot_de_passe
    })
    return response.get_json().get("access_token")

# Mise à jour de l'utilisateur sans en-tête d'autorisation ---
def test_update_user_unauthorized_no_header(client):
    test_name = "test_update_user_unauthorized_no_header"
    logging.info(f"Test: {test_name} - Tentative de mise à jour d'un utilisateur sans en-tête d'autorisation.")

    try:
        
        res = client.post('/utilisateurs', json={
            "email": "unauthorized@mail.com",
            "mot_de_passe": "pass123",
            "nom_utilisateur": "UnauthorizedUser"
        })
        assert res.status_code == 201, "Échec de la création de l'utilisateur pour le test non autorisé."
        user_id = res.get_json()["id"]

        # Étape 2: Envoyer une requête PUT sans l'en-tête Authorization
        response = client.put(
            f'/utilisateurs/{user_id}',
            json={"nom_utilisateur": "NewNameWithoutAuth"}
            # Omission délibérée de headers={"Authorization": "Bearer ..."}
        )

        # Attendu: Code de statut 401 Unauthorized
        assert response.status_code == 401, \
            f"Attendu 401 Unauthorized, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"

    
        response_data = response.get_json()
        assert "msg" in response_data, "Le JSON de réponse ne contient pas la clé 'msg'."
        assert response_data["msg"] == "Missing or invalid Authorization header", \
            f"Message d'erreur inattendu: {response_data['msg']}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise

# Mise à jour de l'utilisateur avec un token invalide ---
def test_update_user_unauthorized_invalid_token(client):
    test_name = "test_update_user_unauthorized_invalid_token"
    logging.info(f"Test: {test_name} - Tentative de mise à jour d'un utilisateur avec un token invalide.")

    try:
        # Étape 1: Créer un utilisateur pour avoir un ID valide
        res = client.post('/utilisateurs', json={
            "email": "invalidtoken@mail.com",
            "mot_de_passe": "pass123",
            "nom_utilisateur": "InvalidTokenUser"
        })
        assert res.status_code == 201, "Échec de la création de l'utilisateur pour le test de token invalide."
        user_id = res.get_json()["id"]

        # Étape 2: Envoyer une requête PUT avec un token invalide
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid_signature_this_is_not_a_real_token"
        response = client.put(
            f'/utilisateurs/{user_id}',
            json={"nom_utilisateur": "NewNameWithInvalidToken"},
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Attendu: Code de statut 401 Unauthorized
        assert response.status_code == 401, \
            f"Attendu 401 Unauthorized, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"

    
        response_data = response.get_json()
        assert "message" in response_data, "Le JSON de réponse ne contient pas la clé 'message'."
        # Flask-JWT-Extended peut renvoyer différents messages pour différents types de tokens invalides.
        expected_messages_part = ["Invalid Token", "Signature verification failed", "Bad header", "Token has expired", "Invalid JWT"]
        assert any(msg_part in response_data["message"] for msg_part in expected_messages_part), \
            f"Message d'erreur inattendu pour token invalide: {response_data['message']}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise


# Mise à jour d'un utilisateur avec un ID inexistant ---
def test_update_user_nonexistent_id_with_auth(client):
    test_name = "test_update_user_nonexistent_id_with_auth"
    logging.info(f"Test: {test_name} - Tentative de mise à jour d'un utilisateur avec un ID inexistant et un token valide.")

    try:
        # Étape 1: Créer un utilisateur pour obtenir un token valide
        res_create = client.post('/utilisateurs', json={
            "email": "existinguser_for_nonexistent_id@mail.com",
            "mot_de_passe": "testpass404",
            "nom_utilisateur": "ExistingUserFor404Test"
        })
        assert res_create.status_code == 201, "Échec de la création de l'utilisateur pour le test 404."
        
        # Obtenir un token valide pour cet utilisateur
        token = get_jwt_token(client, "existinguser_for_nonexistent_id@mail.com", "testpass404")
        assert token is not None, "Échec de l'obtention du token JWT."

        non_existent_id = "60c728e1d2c67c001f3e4b5d" # Exemple d'ID inexistant (24 caractères hexadécimaux)
                                                     
        # Étape 2: Envoyer une requête PUT avec un token valide, mais un ID inexistant
        response = client.put(
            f'/utilisateurs/{non_existent_id}',
            json={"nom_utilisateur": "UpdatedNameForNonExistent"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Résultat attendu: 404 Not Found
        assert response.status_code == 404, \
            f"Attendu 404 Not Found, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        response_data = response.get_json()
        assert "message" in response_data, "La réponse devrait contenir un message d'erreur."
        assert response_data["message"] == "Utilisateur non trouvé", \
            f"Message d'erreur inattendu pour ID inexistant: {response_data['message']}"

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise
        
# Mise à jour d'un utilisateur avec des données invalides ---
def test_update_user_with_invalid_data(client):
    test_name = "test_update_user_with_invalid_data"
    logging.info(f"Test: {test_name} - Tentative de mise à jour d'un utilisateur avec des données invalides (email ou mot de passe) et un token valide.")

    try:
        # Étape 1: Créer un utilisateur à mettre à jour (et obtenir le token)
        res_create = client.post('/utilisateurs', json={
            "email": "user_for_invalid_data_test@mail.com",
            "mot_de_passe": "valid_pass123",
            "nom_utilisateur": "InvalidDataTestUser"
        })
        assert res_create.status_code == 201, "Échec de la création de l'utilisateur pour le test de données invalides."
        user_id = res_create.get_json()["id"]
        
        # Obtenir un token valide pour cet utilisateur
        token = get_jwt_token(client, "user_for_invalid_data_test@mail.com", "valid_pass123")
        assert token is not None, "Échec de l'obtention du token JWT."

        logging.info(f"   Sous-scénario 1: Email invalide (ожидается 200 OK, если API не валидирует формат).")
        response_invalid_email = client.put(
            f'/utilisateurs/{user_id}',
            json={"email": "invalid-email"}, # Email invalide
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_invalid_email.status_code == 200, \
            f"Attendu 200 OK pour email invalide (si non validé), mais reçu {response_invalid_email.status_code}. Réponse: {response_invalid_email.get_data(as_text=True)}"
        
        response_data_email = response_invalid_email.get_json()
        assert "message" in response_data_email, "Le JSON de réponse ne contient pas la clé 'message'."
        assert response_data_email["message"] == "Utilisateur mis à jour", \
            f"Message inattendu pour mise à jour avec email invalide: {response_data_email['message']}"

        # Scénario 2: Mot de passe слишком короткий
        logging.info(f"   Sous-scénario 2: Mot de passe trop court (ожидается 200 OK, если API не валидирует длину).")
        response_short_password = client.put(
            f'/utilisateurs/{user_id}',
            json={"mot_de_passe": "short"}, # Mot de passe trop court
            headers={"Authorization": f"Bearer {token}"}
        )
     
        assert response_short_password.status_code == 200, \
            f"Attendu 200 OK pour mot de passe trop court (si non validé), mais reçu {response_short_password.status_code}. Réponse: {response_short_password.get_data(as_text=True)}"

        response_data_password = response_short_password.get_json()
    
        assert "message" in response_data_password, "Le JSON de réponse ne contient pas de clé de message."
        assert response_data_password["message"] == "Utilisateur mis à jour", \
            f"Message inattendu pour mise à jour avec mot de passe court: {response_data_password['message']}"
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur inattendue: {e}")
        log_test_result(test_name, False)
        raise