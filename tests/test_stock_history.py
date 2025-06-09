import pytest
import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

def log_test_result(test_name, result):
    if result:
        logging.info(f"{test_name}: PASSED")
    else:
        logging.error(f"{test_name}: FAILED")

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_history_last_2_days(client):
    try:
        response = client.get('/actions/AAPL/historique?jours=4')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        # Si l'action a été créée il y a moins de 2 jours, on peut avoir 1 ou 2 entrées
        assert 1 <= len(data) <= 4
        for entry in data:
            assert entry["symbole"] == "AAPL"
        log_test_result("test_history_last_4_days", True)
    except AssertionError:
        log_test_result("test_history_last_4_days", False)
        raise

def test_history_last_7_days(client):
    try:
        response = client.get('/actions/AAPL/historique?jours=7')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        # Si l'action a été créée il y a moins de 7 jours, on peut avoir entre 3 et 7 entrées
        assert 3 <= len(data) <= 7
        log_test_result("test_history_last_7_days", True)
    except AssertionError:
        log_test_result("test_history_last_7_days", False)
        raise

def test_history_last_30_days(client):
    try:
        response = client.get('/actions/AAPL/historique?jours=30')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        # Si l'action a été créée il y a moins de 30 jours, on peut avoir entre 15 et 30 entrées
        assert 15 <= len(data) <= 30
        log_test_result("test_history_last_30_days", True)
    except AssertionError:
        log_test_result("test_history_last_30_days", False)
        raise

def test_history_custom_period(client):
    try:
        # Test pour une période personnalisée de 10 jours
        date_fin = datetime.now().strftime("%Y-%m-%d")
        date_debut = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        url = f'/actions/AAPL/historique?date_debut={date_debut}&date_fin={date_fin}'
        response = client.get(url)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        # Si l'action a été créée il y a moins de 10 jours, on peut avoir entre 5 et 11 entrées
        assert 5 <= len(data) <= 11
        log_test_result("test_history_custom_period", True)
    except AssertionError:
        log_test_result("test_history_custom_period", False)
        raise