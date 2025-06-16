import pytest
import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    from logging_config import setup_logging
    setup_logging('test_results.log')
except ImportError:
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.warning("logging_config.py not found. Using basic logging configuration.")


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
    
    repo.supprimer_par_email("companyerrortest@mail.com") 

def get_jwt_token(client):
    client.post('/utilisateurs', json={
        "email": "companyerrortest@mail.com",
        "mot_de_passe": "companyerrorpass",
        "nom_utilisateur": "CompanyErrorTest"
    })
    resp = client.post('/connexion', json={
        "email": "companyerrortest@mail.com",
        "mot_de_passe": "companyerrorpass"
    })
   
    if resp.status_code != 200:
        logging.error(f"Failed to get JWT token: {resp.status_code} - {resp.get_data(as_text=True)}")
        pytest.fail(f"Could not get JWT token. Response: {resp.get_data(as_text=True)}")
    return resp.get_json()["access_token"]

def test_get_company_info_not_found(client):
    nom_test = "test_get_company_info_not_found"
    logging.info(f"Test: {nom_test} - Demande d'informations pour une société inexistante.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/NONEXISTENT', 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, \
            f"Attendu 404 pour société inexistante, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data 
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_not_found(client):
    nom_test = "test_company_history_not_found"
    logging.info(f"Test: {nom_test} - Demande d'historique pour une société inexistante.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/NONEXISTENT/historique?jours=5', 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, \
            f"Attendu 404 pour historique société inexistante, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_invalid_jours_negative(client):
    nom_test = "test_company_history_invalid_jours_negative"
    logging.info(f"Test: {nom_test} - Demande d'historique avec 'jours' négatif.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?jours=-5',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour jours négatif, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_invalid_jours_non_numeric(client):
    nom_test = "test_company_history_invalid_jours_non_numeric"
    logging.info(f"Test: {nom_test} - Demande d'historique avec 'jours' non numérique.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?jours=abc',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour jours non numérique, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_invalid_date_range(client):
    nom_test = "test_company_history_invalid_date_range"
    logging.info(f"Test: {nom_test} - Demande d'historique avec date_debut > date_fin.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?date_debut=2025-06-10&date_fin=2025-06-08', 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour plage de dates invalide, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_invalid_date_format(client):
    nom_test = "test_company_history_invalid_date_format"
    logging.info(f"Test: {nom_test} - Demande d'historique avec format de date invalide.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?date_debut=08/06/2025&date_fin=2025-06-09', 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour format de date invalide, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_no_parameters(client):
    nom_test = "test_company_history_no_parameters"
    logging.info(f"Test: {nom_test} - Demande d'historique sans paramètres.")
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 pour paramètres manquants, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_unauthorized(client):
    nom_test = "test_company_history_unauthorized"
    logging.info(f"Test: {nom_test} - Demande d'historique sans jeton JWT.")
    try:
        response = client.get('/societes/AAPL/historique?jours=5')
        assert response.status_code == 401, \
            f"Attendu 401 sans jeton, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data 
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise

def test_company_history_jours_less_than_4(client):
    nom_test = "test_company_history_jours_less_than_4"
    logging.info(f"Test: {nom_test} - Demande d'historique  'jours' < 2.") 
    try:
        token = get_jwt_token(client)
        response = client.get(
            '/societes/AAPL/historique?jours=1', 
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, \
            f"Attendu 400 для jours < 2, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert "message" in data or "msg" in data
        log_test_result(nom_test, True)
    except AssertionError:
        log_test_result(nom_test, False)
        raise