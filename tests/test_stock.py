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
    try:
        response = client.get('/actions/AAPL')
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbole"] == "AAPL"
        assert "close" in data
        log_test_result("test_get_stock", True)
    except AssertionError:
        log_test_result("test_get_stock", False)
        raise

def test_calculate_stock_purchase(client):
    try:
        token = get_jwt_token(client)
        response = client.post(
            '/actions/calculer',
            json={"symbole": "AAPL", "date": "2025-06-07", "quantite": 5, "code_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbole"] == "AAPL"
        assert data["quantite"] == 5
        assert "cout_total" in data
        log_test_result("test_calculate_stock_purchase", True)
    except AssertionError:
        log_test_result("test_calculate_stock_purchase", False)
        raise

def test_favorites_flow(client):
    try:
        token = get_jwt_token(client)
        resp_add = client.post(
            '/actions/favoris',
            json={"symbole": "AAPL"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_add.status_code == 200
        resp_get = client.get(
            '/actions/favoris',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_get.status_code == 200
        favs = resp_get.get_json()["favoris"]
        assert "AAPL" in favs
        resp_del = client.delete(
            '/actions/favoris',
            json={"symbole": "AAPL"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_del.status_code == 200
        resp_get2 = client.get(
            '/actions/favoris',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert "AAPL" not in resp_get2.get_json()["favoris"]
        log_test_result("test_favorites_flow", True)
    except AssertionError:
        log_test_result("test_favorites_flow", False)
        raise

def test_get_popular_stocks(client):
    try:
        response = client.get('/actions/populaires')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "symbole" in data[0]
        log_test_result("test_get_popular_stocks", True)
    except AssertionError:
        log_test_result("test_get_popular_stocks", False)
        raise