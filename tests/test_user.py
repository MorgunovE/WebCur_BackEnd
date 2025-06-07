import pytest
import logging
import sys
import os

# Configuration du logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

# Fonction pour enregistrer les résultats des tests
def log_test_result(test_name, result):
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

# Ajouter le chemin du projet pour importer l'application Flask
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
        "deleteuser@mail.com"
    ]
    for email in test_emails:
        repo.supprimer_par_email(email)

# Tests pour les utilisateurs
def test_register_user(client):
    try:
        response = client.post('/utilisateurs', json={
            "email": "testuser@mail.com",
            "mot_de_passe": "testpass",
            "nom_utilisateur": "TestUser"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["email"] == "testuser@mail.com"
        assert "id" in data
        log_test_result("test_register_user", True)
    except AssertionError:
        log_test_result("test_register_user", False)
        raise

# Tests pour l'authentification des utilisateurs
def test_authenticate_user(client):
    try:
        client.post('/utilisateurs', json={
            "email": "authuser@mail.com",
            "mot_de_passe": "authpass",
            "nom_utilisateur": "AuthUser"
        })
        response = client.post('/connexion', json={
            "email": "authuser@mail.com",
            "mot_de_passe": "authpass"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        log_test_result("test_authenticate_user", True)
    except AssertionError:
        log_test_result("test_authenticate_user", False)
        raise

# Tests pour les opérations CRUD sur les utilisateurs
def test_get_users(client):
    try:
        response = client.get('/utilisateurs')
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
        log_test_result("test_get_users", True)
    except AssertionError:
        log_test_result("test_get_users", False)
        raise

# Tests pour les opérations CRUD sur un utilisateur spécifique
def test_update_user(client):
    try:
        res = client.post('/utilisateurs', json={
            "email": "updateuser@mail.com",
            "mot_de_passe": "updatepass",
            "nom_utilisateur": "UpdateUser"
        })
        user_id = res.get_json()["id"]
        response = client.put(f'/utilisateurs/{user_id}', json={
            "nom_utilisateur": "UpdatedName"
        })
        assert response.status_code == 200
        log_test_result("test_update_user", True)
    except AssertionError:
        log_test_result("test_update_user", False)
        raise

# Tests pour la suppression d'un utilisateur
def test_delete_user(client):
    try:
        res = client.post('/utilisateurs', json={
            "email": "deleteuser@mail.com",
            "mot_de_passe": "deletepass",
            "nom_utilisateur": "DeleteUser"
        })
        user_id = res.get_json()["id"]
        response = client.delete(f'/utilisateurs/{user_id}')
        assert response.status_code == 204
        log_test_result("test_delete_user", True)
    except AssertionError:
        log_test_result("test_delete_user", False)
        raise

# Tests pour la connexion et la déconnexion
def test_connexion_success(client):
    try:
        client.post('/utilisateurs', json={
            "email": "loginuser@mail.com",
            "mot_de_passe": "loginpass",
            "nom_utilisateur": "LoginUser"
        })
        response = client.post('/connexion', json={
            "email": "loginuser@mail.com",
            "mot_de_passe": "loginpass"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        log_test_result("test_connexion_success", True)
    except AssertionError:
        log_test_result("test_connexion_success", False)
        raise

# Test pour la connexion échouée
def test_connexion_failure(client):
    try:
        response = client.post('/connexion', json={
            "email": "wrong@mail.com",
            "mot_de_passe": "wrongpass"
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data["message"] == "Identifiants invalides"
        log_test_result("test_connexion_failure", True)
    except AssertionError:
        log_test_result("test_connexion_failure", False)
        raise

# Test pour la déconnexion
def test_deconnexion(client):
    try:
        response = client.post('/deconnexion')
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Déconnexion réussie"
        log_test_result("test_deconnexion", True)
    except AssertionError:
        log_test_result("test_deconnexion", False)
        raise