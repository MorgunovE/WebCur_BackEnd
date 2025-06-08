import pytest
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

def log_test_result(test_name, result):
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

from app import app
from repositories.user_repository import UserRepository

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_users():
    repo = UserRepository()
    yield
    repo.supprimer_par_email("stocktest@mail.com")

def get_jwt_token(client):
    client.post('/utilisateurs', json={
        "email": "stocktest@mail.com",
        "mot_de_passe": "stockpass",
        "nom_utilisateur": "StockTest"
    })
    resp = client.post('/connexion', json={
        "email": "stocktest@mail.com",
        "mot_de_passe": "stockpass"
    })
    return resp.get_json()["access_token"]

def test_get_stock(client):
    response = client.get('/actions/AAPL')
    assert response.status_code == 200
    data = response.get_json()
    assert data["symbole"] == "AAPL"

def test_get_stock_not_found(client):
    response = client.get('/actions/FAKESTOCK')
    assert response.status_code in (404, 502)

def test_bulk_add_stock(client):
    # Ce test suppose que les actions populaires sont définies dans l'environnement
    response = client.get('/actions/MSFT')
    assert response.status_code == 200
    data = response.get_json()
    assert data["symbole"] == "MSFT"

def test_calculate_purchase_cost(client):
    token = get_jwt_token(client)
    # Verifier que l'action existe avant de calculer le coût
    client.get('/actions/AAPL')
    response = client.post(
        '/actions/calculer',
        json={"symbole": "AAPL", "date": "2025-06-06", "quantite": 2, "code_devise": "USD"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["symbole"] == "AAPL"
    assert "cout_total" in data

def test_calculate_purchase_cost_unauth(client):
    response = client.post(
        '/actions/calculer',
        json={"symbole": "AAPL", "date": "2025-06-06", "quantite": 2, "code_devise": "USD"}
    )
    assert response.status_code == 401

def test_favorites_flow(client):
    token = get_jwt_token(client)
    # Ajouter aux favoris
    resp_add = client.post(
        '/actions/favoris',
        json={"symbole": "AAPL"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_add.status_code == 200
    # Obtenir les favoris
    resp_get = client.get(
        '/actions/favoris',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_get.status_code == 200
    favs = resp_get.get_json()["favoris"]
    assert "AAPL" in favs
    # Supprimer des favoris
    resp_del = client.delete(
        '/actions/favoris',
        json={"symbole": "AAPL"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_del.status_code == 200
    # Vérifier que l'action a été supprimée des favoris
    resp_get2 = client.get(
        '/actions/favoris',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert "AAPL" not in resp_get2.get_json()["favoris"]