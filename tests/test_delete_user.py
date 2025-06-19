import pytest
import logging
import sys
import os

# Configuration du logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

# Ajouter le chemin du projet pour importer l'application Flask
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from repositories.user_repository import UserRepository
from bson import ObjectId 



@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_users():
    repo = UserRepository()
    yield 
    
    # Liste des emails d'utilisateurs de test à supprimer
    test_emails = [
        "delete_success_test@mail.com",
        "delete_unauth_test@mail.com",
        "temp_user_for_nonexistent_delete@mail.com"
    ]
    for email in test_emails:
        repo.supprimer_par_email(email)

# --- Fonctions utilitaires ---

def log_test_result(test_name, result):
    """
    Enregistre le résultat d'un test dans le fichier de log.
    """
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

def get_jwt_token(client, email, mot_de_passe):
    """
    Fonction d'aide pour obtenir un token JWT via l'API de connexion.
    """
    response = client.post('/connexion', json={
        "email": email,
        "mot_de_passe": mot_de_passe
    })
    return response.get_json().get("access_token")

# --- Tests de suppression d'utilisateur ---

def test_delete_user_success(client):
    """
    Scénario: Suppression réussie d'un utilisateur avec un token JWT valide.
    Vérifie le statut 204 et l'impossibilité de récupérer l'utilisateur ensuite (404).
    """
    test_name = "test_delete_user_success"
    logging.info(f"Test: {test_name} - Tentative de suppression d'un utilisateur avec un token valide.")

    try:
        # Étape 1: Créer un utilisateur de test pour la suppression
        user_email = "delete_success_test@mail.com"
        user_password = "delete_pass_success"
        user_username = "DeleteUserSuccess"

        res_create = client.post('/utilisateurs', json={
            "email": user_email,
            "mot_de_passe": user_password,
            "nom_utilisateur": user_username
        })
        assert res_create.status_code == 201, "Échec de la création de l'utilisateur pour le test de suppression réussie."
        user_id = res_create.get_json()["id"]

        # Étape 2: Obtenir un token JWT valide pour l'utilisateur créé
        token = get_jwt_token(client, user_email, user_password)
        assert token is not None, "Échec de l'obtention du token JWT pour le test de suppression réussie."

        # Étape 3: Envoyer la requête DELETE avec le token valide
        logging.info(f"  Envoi de la requête DELETE pour l'utilisateur ID: {user_id}")
        response_delete = client.delete(
            f'/utilisateurs/{user_id}',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_delete.status_code == 204, \
            f"Échec de la suppression de l'utilisateur. Statut attendu 204, obtenu {response_delete.status_code}. " \
            f"Réponse: {response_delete.get_data(as_text=True)}"

        # Étape 4: Vérifier que l'utilisateur n'existe plus (GET doit retourner 404)
        logging.info(f"  Vérification que l'utilisateur a bien été supprimé (GET sur ID: {user_id}).")
        response_get_after_delete = client.get(f'/utilisateurs/{user_id}')
        assert response_get_after_delete.status_code == 404, \
            f"L'utilisateur n'a pas été supprimé ou est toujours accessible. Statut attendu 404, obtenu {response_get_after_delete.status_code}."

        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_delete_user_unauthorized(client):
    """
    Scénario: Tentative de suppression d'un utilisateur sans token d'autorisation.
    Vérifie le statut 401 Unauthorized.
    """
    test_name = "test_delete_user_unauthorized"
    logging.info(f"Test: {test_name} - Tentative de suppression d'un utilisateur sans token d'autorisation.")

    try:
        # Étape 1: Créer un utilisateur de test (qui ne sera PAS supprimé par ce test, mais par la fixture)
        user_email = "delete_unauth_test@mail.com"
        user_password = "unauth_pass_delete"
        user_username = "UnauthDeleteUser"

        res_create = client.post('/utilisateurs', json={
            "email": user_email,
            "mot_de_passe": user_password,
            "nom_utilisateur": user_username
        })
        assert res_create.status_code == 201, "Échec de la création de l'utilisateur pour le test non autorisé."
        user_id = res_create.get_json()["id"] # Récupérer l'ID pour la requête

        # Étape 2: Envoyer la requête DELETE SANS le header 'Authorization'
        logging.info(f"  Envoi de la requête DELETE sans autorisation pour l'utilisateur ID: {user_id}")
        response = client.delete(f'/utilisateurs/{user_id}')
        
        assert response.status_code == 401, \
            f"La suppression non autorisée a réussi ou a donné un statut inattendu. Statut attendu 401, obtenu {response.status_code}." \
            f"Réponse: {response.get_data(as_text=True)}"
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise

def test_delete_nonexistent_user(client):
    """
    Scénario: Tentative de suppression d'un utilisateur inexistant avec un token valide.
    Vérifie le statut 404 Not Found.
    """
    test_name = "test_delete_nonexistent_user"
    logging.info(f"Test: {test_name} - Tentative de suppression d'un utilisateur inexistant avec un token valide.")

    try:
        # Étape 1: Créer un utilisateur temporaire pour obtenir un token valide
        temp_user_email = "temp_user_for_nonexistent_delete@mail.com"
        temp_user_password = "temp_pass_delete"
        temp_user_username = "TempDeleteUser"

        res_create = client.post('/utilisateurs', json={
            "email": temp_user_email,
            "mot_de_passe": temp_user_password,
            "nom_utilisateur": temp_user_username
        })
        assert res_create.status_code == 201, "Échec de la création de l'utilisateur temporaire pour obtenir le token."
        
        # Obtenir le token pour l'utilisateur temporaire
        token = get_jwt_token(client, temp_user_email, temp_user_password)
        assert token is not None, "Échec de l'obtention du token JWT pour le test d'utilisateur inexistant."

        # Étape 2: Utiliser un ID qui n'existe PAS en base de données.
        # Il est crucial que cet ID soit au format ObjectId valide, mais qu'il ne corresponde à aucun document.
        non_existent_id = str(ObjectId()) # Génère un nouvel ObjectId aléatoire qui n'existe pas en base
        logging.info(f"  Envoi de la requête DELETE pour un ID inexistant: {non_existent_id}")
        
        response = client.delete(
            f'/utilisateurs/{non_existent_id}',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, \
            f"La suppression d'un utilisateur inexistant a réussi ou a donné un statut inattendu. Statut attendu 404, obtenu {response.status_code}." \
            f"Réponse: {response.get_data(as_text=True)}"
        
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise