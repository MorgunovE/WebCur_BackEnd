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
    repo.supprimer_par_email("companytest@mail.com")

def get_jwt_token(client):
    client.post('/utilisateurs', json={
        "email": "companytest@mail.com",
        "mot_de_passe": "companypass",
        "nom_utilisateur": "CompanyTest"
    })
    resp = client.post('/connexion', json={
        "email": "companytest@mail.com",
        "mot_de_passe": "companypass"
    })
    return resp.get_json()["access_token"]

def test_get_company_info(client):
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["symbole"] == "AAPL"
        assert "companyName" in data
        assert "price" in data
        log_test_result("test_get_company_info", True)
    except AssertionError:
        log_test_result("test_get_company_info", False)
        raise

def test_company_history_days(client):
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?jours=2',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert 1 <= len(data) <= 2
        for entry in data:
            assert entry["symbole"] == "AAPL"
            assert "date_maj" in entry
        log_test_result("test_company_history_days", True)
    except AssertionError:
        log_test_result("test_company_history_days", False)
        raise

def test_company_history_period(client):
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?date_debut=2025-06-08&date_fin=2025-06-09',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        for entry in data:
            assert entry["symbole"] == "AAPL"
            assert entry["date_maj"] in ["2025-06-08", "2025-06-09"]
        log_test_result("test_company_history_period", True)
    except AssertionError:
        log_test_result("test_company_history_period", False)
        raise

def test_get_popular_companies(client):
    try:
        response = client.get('/societes/populaires')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        log_test_result("test_get_popular_companies", True)
    except AssertionError:
        log_test_result("test_get_popular_companies", False)
        raise