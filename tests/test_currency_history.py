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
    repo.supprimer_par_email("currencyhistorytest@mail.com")

def get_jwt_token(client):
    client.post('/utilisateurs', json={
        "email": "currencyhistorytest@mail.com",
        "mot_de_passe": "currhistorypass",
        "nom_utilisateur": "CurrencyHistoryTest"
    })
    resp = client.post('/connexion', json={
        "email": "currencyhistorytest@mail.com",
        "mot_de_passe": "currhistorypass"
    })
    return resp.get_json()["access_token"]

def test_history_2_last_days(client):
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/devises/CAD/historique?jours=2',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) <= 2
        for entry in data:
            assert entry["nom"] == "CAD"
            assert "date_maj" in entry
        log_test_result("test_history_last_2_days", True)
    except AssertionError:
        log_test_result("test_history_last_2_days", False)
        raise

def test_history_cad_two_days_specific_dates(client):
    try:
        response = client.get('/devises/CAD/historique?date_debut=2025-06-07&date_fin=2025-06-08')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) <= 2
        for entry in data:
            assert entry["nom"] == "CAD"
            assert entry["date_maj"] in ["2025-06-07", "2025-06-08"]
        log_test_result("test_history_cad_two_days_specific_dates", True)
    except AssertionError:
        log_test_result("test_history_cad_two_days_specific_dates", False)
        raise