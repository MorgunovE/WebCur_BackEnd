import pytest
from app import app
from repositories.user_repository import UserRepository


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_users():
    # Ce fixture s'assure que les utilisateurs de test sont nettoyés après chaque test
    repo = UserRepository()
    yield
    # Supprimer les utilisateurs de test
    test_emails = [
        "testuser@mail.com",
        "authuser@mail.com",
        "updateuser@mail.com",
        "deleteuser@mail.com"
    ]
    for email in test_emails:
        repo.supprimer_par_email(email)

def test_register_user(client):
    response = client.post('/utilisateurs', json={
        "email": "testuser@mail.com",
        "mot_de_passe": "testpass",
        "nom_utilisateur": "TestUser"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == "testuser@mail.com"
    assert "id" in data

def test_authenticate_user(client):
    # Register first
    client.post('/utilisateurs', json={
        "email": "authuser@mail.com",
        "mot_de_passe": "authpass",
        "nom_utilisateur": "AuthUser"
    })
    # Authenticate
    response = client.post('/connexion', json={
        "email": "authuser@mail.com",
        "mot_de_passe": "authpass"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data

def test_get_users(client):
    response = client.get('/utilisateurs')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_update_user(client):
    # Register user
    res = client.post('/utilisateurs', json={
        "email": "updateuser@mail.com",
        "mot_de_passe": "updatepass",
        "nom_utilisateur": "UpdateUser"
    })
    user_id = res.get_json()["id"]
    # Update user
    response = client.put(f'/utilisateurs/{user_id}', json={
        "nom_utilisateur": "UpdatedName"
    })
    assert response.status_code == 200

def test_delete_user(client):
    # Register user
    res = client.post('/utilisateurs', json={
        "email": "deleteuser@mail.com",
        "mot_de_passe": "deletepass",
        "nom_utilisateur": "DeleteUser"
    })
    user_id = res.get_json()["id"]
    # Delete user
    response = client.delete(f'/utilisateurs/{user_id}')
    assert response.status_code == 204