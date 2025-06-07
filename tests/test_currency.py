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
    repo.supprimer_par_email("currencytest@mail.com")

def get_jwt_token(client):
    client.post('/utilisateurs', json={
        "email": "currencytest@mail.com",
        "mot_de_passe": "currpass",
        "nom_utilisateur": "CurrencyTest"
    })
    resp = client.post('/connexion', json={
        "email": "currencytest@mail.com",
        "mot_de_passe": "currpass"
    })
    return resp.get_json()["access_token"]

def test_get_currency(client):
    try:
        response = client.get('/devises/USD')
        assert response.status_code == 200
        data = response.get_json()
        assert data["nom"] == "USD"
        assert "taux" in data
        log_test_result("test_get_currency", True)
    except AssertionError:
        log_test_result("test_get_currency", False)
        raise

def test_convert_currency(client):
    try:
        token = get_jwt_token(client)
        response = client.post(
            '/devises/conversion',
            json={"code_source": "USD", "code_cible": "EUR", "montant": 100},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["code_source"] == "USD"
        assert data["code_cible"] == "EUR"
        assert "montant_converti" in data
        log_test_result("test_convert_currency", True)
    except AssertionError:
        log_test_result("test_convert_currency", False)
        raise

def test_favorites_flow(client):
    try:
        token = get_jwt_token(client)
        resp_add = client.post(
            '/devises/favoris',
            json={"nom_devise": "EUR"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_add.status_code == 200
        resp_get = client.get(
            '/devises/favoris',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_get.status_code == 200
        favs = resp_get.get_json()["favoris"]
        assert "EUR" in favs
        resp_del = client.delete(
            '/devises/favoris',
            json={"nom_devise": "EUR"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_del.status_code == 200
        resp_get2 = client.get(
            '/devises/favoris',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert "EUR" not in resp_get2.get_json()["favoris"]
        log_test_result("test_favorites_flow", True)
    except AssertionError:
        log_test_result("test_favorites_flow", False)
        raise

def test_get_popular_currencies(client):
    try:
        response = client.get('/devises/populaires')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "nom" in data[0]
        log_test_result("test_get_popular_currencies", True)
    except AssertionError:
        log_test_result("test_get_popular_currencies", False)
        raise