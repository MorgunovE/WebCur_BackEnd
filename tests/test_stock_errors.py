import pytest
import os
import sys
import logging
from datetime import datetime, timedelta

# Ajouter le chemin du répertoire racine du projet à sys.path pour les importations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logging
setup_logging('test_results.log')

def log_test_result(test_name, result):
    """
    Enregistre le résultat du test dans le journal.
    """
    if result:
        logging.info(f"{test_name}: RÉUSSI")
    else:
        logging.error(f"{test_name}: ÉCHOUÉ")


from app import app
from repositories.user_repository import UserRepository

@pytest.fixture
def client():
    """
    Fixture Pytest pour créer un client de test Flask.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_users():
    """
    Fixture Pytest pour nettoyer les utilisateurs créés après chaque test.
    Utilise des e-mails uniques pour les tests dans ce fichier.
    """
    repo = UserRepository()
    yield
    
    test_emails = ["stockerrtest@mail.com", "favstockerrtest@mail.com", "readdstockerrtest@mail.com", "stockerrdatatest@mail.com"]
    for email in test_emails:
        repo.supprimer_par_email(email)

def get_jwt_token(client, email, password, username):
    """
    Fonction utilitaire pour obtenir un jeton JWT en enregistrant et en connectant un utilisateur.
    Accepte l'e-mail, le mot de passe et le nom d'utilisateur pour créer des utilisateurs uniques pour chaque scénario.
    """
    repo = UserRepository()
    repo.supprimer_par_email(email)
    
    register_resp = client.post('/utilisateurs', json={
        "email": email,
        "mot_de_passe": password,
        "nom_utilisateur": username
    })

    if register_resp.status_code not in [201, 409]:
        logging.error(f"Échec de l'enregistrement de l'utilisateur {email}: {register_resp.get_data(as_text=True)}")
        pytest.fail(f"Impossible d'enregistrer l'utilisateur pour le jeton JWT. Réponse: {register_resp.get_data(as_text=True)}")

    login_resp = client.post('/connexion', json={
        "email": email,
        "mot_de_passe": password
    })
    if login_resp.status_code == 200:
        return login_resp.get_json()["access_token"]
    else:
        logging.error(f"Échec de l'obtention du jeton JWT pour {email}: {login_resp.get_data(as_text=True)}")
        pytest.fail(f"Impossible d'obtenir le jeton JWT pour le test. Réponse: {login_resp.get_data(as_text=True)}")

def get_error_message(data):
    """
    Extrait le message d'erreur d'une réponse JSON, qui peut être un dictionnaire ou une liste.
    """
    if isinstance(data, dict):
        if "message" in data:
            return data["message"]
        elif "msg" in data: 
            return data["msg"]
        elif "errors" in data: 
            for field, messages in data["errors"].items():
                if isinstance(messages, list) and messages:
                    return messages[0] 
            return str(data["errors"]) 
    elif isinstance(data, list) and data:
        if isinstance(data[0], dict):
            if "message" in data[0]:
                return data[0]["message"]
            elif "errors" in data[0]:
                for field, messages in data[0]["errors"].items():
                    if isinstance(messages, list) and messages:
                        return messages[0]
                return str(data[0]["errors"])
        elif isinstance(data[0], str):
            return data[0]
    return str(data) 

# --- Tests pour POST /actions/calculer (erreurs) ---

def test_calculate_stock_purchase_unauthenticated(client):
    """
    Scénario: Tentative de calculer le coût d'achat d'une action sans authentification.
    Attendu: 401 Non autorisé.
    """
    test_name = "test_calculate_stock_purchase_unauthenticated"
    logging.info(f"Test: {test_name} - Tentative de calculer le coût d'achat sans authentification.")
    try:
        response = client.post(
            '/actions/calculer',
            json={"symbole": "AAPL", "date": "2025-06-06", "quantite": 5, "code_devise": "USD"}
        )
        assert response.status_code == 401, \
            f"Attendu 401 pour un calcul non authentifié, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Missing or invalid Authorization header" in error_message or \
               "Non autorisé" in error_message or \
               "Jeton manquant" in error_message or \
               "Signature verification failed" in error_message or \
               "Token has expired" in error_message, \
            f"Message d'erreur inattendu: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur: {e}")
        log_test_result(test_name, False)
        raise

def test_calculate_stock_purchase_non_existent_symbol(client):
    """
    Scénario: Tentative de calculer le coût d'achat для несуществующего символа акции.
    Attendu: 404 Non trouvé (или 400 Mauvaise requête, si la validation plus générale).
    """
    test_name = "test_calculate_stock_purchase_non_existent_symbol"
    logging.info(f"Test: {test_name} - Tentative de calculer le coût d'achat pour un symbole inexistant.")
    try:
        token = get_jwt_token(client, "stockerrtest@mail.com", "stockpass", "StockErrTest")
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        response = client.post(
            '/actions/calculer',
            json={"symbole": "NONEXIST", "date": past_date, "quantite": 1, "code_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [404, 400], \
            f"Attendu 404 ou 400 pour un symbole inexistant, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        error_message = get_error_message(data)
        assert "Action non trouvée" in error_message or \
               "Symbole non valide" in error_message or \
               "Données d'action non disponibles" in error_message or \
               "Symbole introuvable" in error_message, \
            f"Message d'erreur inattendu pour un symbole inexistant: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur: {e}")
        log_test_result(test_name, False)
        raise

def test_calculate_stock_purchase_invalid_data(client):
    """
    Scénario: Tentative de calculer le coût d'achat avec des données invalides (quantité, date, code de devise).
    """
    test_name = "test_calculate_stock_purchase_invalid_data"
    logging.info(f"Test: {test_name} - Tentative de calculer le coût d'achat avec des données invalides.")
    token = get_jwt_token(client, "stockerrdatatest@mail.com", "stockdatapass", "StockDataTest")
    
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")


    # Test avec une quantité négative
    try:
        logging.info(f"Test: {test_name} - Exécution du sous-test 'Quantité négative'.")
        response = client.post(
            '/actions/calculer',
            json={"symbole": "AAPL", "date": past_date, "quantite": -5, "code_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, \
            f"Attendu 200 pour une quantité négative (selon l'implémentation actuelle), mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        assert data["symbole"] == "AAPL"
        assert data["quantite"] == -5
        assert "cout_total" in data and isinstance(data["cout_total"], (int, float))
        assert data["cout_total"] < 0, "Le coût total devrait être négatif pour une quantité négative."

        log_test_result(f"{test_name} - Quantité négative", True)
    except AssertionError:
        log_test_result(f"{test_name} - Quantité négative", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - Quantité négative a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - Quantité négative", False)
        raise

    # Test avec une date invalide
    try:
        logging.info(f"Test: {test_name} - Exécution du sous-test 'Date invalide'.")
        response = client.post(
            '/actions/calculer',
            json={"symbole": "AAPL", "date": "INVALID_DATE", "quantite": 5, "code_devise": "USD"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, \
            f"Attendu 200 pour une date invalide (selon l'implémentation actuelle), mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        data = response.get_json()
        assert data["symbole"] == "AAPL"
        assert data["quantite"] == 5
        assert "cout_total" in data and isinstance(data["cout_total"], (int, float))

        try:
            returned_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            assert returned_date <= datetime.now().date(), "La date corrigée ne devrait pas être dans le futur."
        except ValueError:
            pytest.fail(f"La date retournée dans la réponse ({data['date']}) n'est pas au format AAAA-MM-JJ.")

        log_test_result(f"{test_name} - Date invalide", True)
    except AssertionError:
        log_test_result(f"{test_name} - Date invalide", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - Date invalide a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - Date invalide", False)
        raise

    # Test avec un code de devise invalide
    try:
        logging.info(f"Test: {test_name} - Exécution du sous-test 'Code de devise invalide'.")
        response = client.post(
            '/actions/calculer',
            json={"symbole": "AAPL", "date": past_date, "quantite": 5, "code_devise": "XYZ"},
            headers={"Authorization": f"Bearer {token}"}
        )
       
        assert response.status_code == 404, \
            f"Attendu 404 pour une devise invalide, mais reçu {response.status_code}. Réponse: {response.get_data(as_text=True)}"
        
        data = response.get_json()
        error_message = get_error_message(data)
       
        assert "Devise source ou cible non trouvée." in error_message or \
               "Devise non trouvée" in error_message or \
               "Code de devise invalide" in error_message, \
            f"Message d'erreur inattendu pour un code de devise invalide: {error_message}"
        
        log_test_result(f"{test_name} - Code de devise invalide", True)
    except AssertionError:
        log_test_result(f"{test_name} - Code de devise invalide", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - Code de devise invalide a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - Code de devise invalide", False)
        raise

# --- Tests pour GET/POST/DELETE /actions/favoris (erreurs) ---

def test_favorite_stocks_unauthenticated_access(client):
    """
    Scénario: Tentative d'effectuer des opérations sur les actions favorites sans authentification.
    Attendu: 401 Non autorisé pour POST, GET, DELETE.
    """
    test_name = "test_favorite_stocks_unauthenticated_access"
    logging.info(f"Test: {test_name} - Tentative d'opérations sur les actions favorites sans authentification.")

    # Test POST sans authentification
    try:
        response_post = client.post(
            '/actions/favoris',
            json={"symbole": "GOOGL"}
        )
        assert response_post.status_code == 401, \
            f"Attendu 401 pour POST non authentifié, mais reçu {response_post.status_code}. Réponse: {response_post.get_data(as_text=True)}"
        error_message = get_error_message(response_post.get_json())
        assert "Missing or invalid Authorization header" in error_message or \
               "Non autorisé" in error_message or \
               "Jeton manquant" in error_message or \
               "Signature verification failed" in error_message or \
               "Token has expired" in error_message, \
            f"Message d'erreur inattendu POST: {error_message}"
        log_test_result(f"{test_name} - POST sans authentification", True)
    except AssertionError:
        log_test_result(f"{test_name} - POST sans authentification", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - POST sans authentification a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - POST sans authentification", False)
        raise

    # Test GET sans authentification
    try:
        response_get = client.get('/actions/favoris')
        assert response_get.status_code == 401, \
            f"Attendu 401 pour GET non authentifié, mais reçu {response_get.status_code}. Réponse: {response_get.get_data(as_text=True)}"
        error_message = get_error_message(response_get.get_json())
        assert "Missing or invalid Authorization header" in error_message or \
               "Non autorisé" in error_message or \
               "Jeton manquant" in error_message or \
               "Signature verification failed" in error_message or \
               "Token has expired" in error_message, \
            f"Message d'erreur inattendu GET: {error_message}"
        log_test_result(f"{test_name} - GET sans authentification", True)
    except AssertionError:
        log_test_result(f"{test_name} - GET sans authentification", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - GET sans authentification a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - GET sans authentification", False)
        raise

    # Test DELETE sans authentification
    try:
        response_delete = client.delete(
            '/actions/favoris',
            json={"symbole": "GOOGL"}
        )
        assert response_delete.status_code == 401, \
            f"Attendu 401 pour DELETE non authentifié, mais reçu {response_delete.status_code}. Réponse: {response_delete.get_data(as_text=True)}"
        error_message = get_error_message(response_delete.get_json())
        assert "Missing or invalid Authorization header" in error_message or \
               "Non autorisé" in error_message or \
               "Jeton manquant" in error_message or \
               "Signature verification failed" in error_message or \
               "Token has expired" in error_message, \
            f"Message d'erreur inattendu DELETE: {error_message}"
        log_test_result(f"{test_name} - DELETE sans authentification", True)
    except AssertionError:
        log_test_result(f"{test_name} - DELETE sans authentification", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - DELETE sans authentification a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - DELETE sans authentification", False)
        raise

def test_favorite_stocks_invalid_symbol(client):
    """
    Scénario: Tentative d'ajouter/supprimer une action favorite avec un symbole invalide/manquant.
    Attendu: 400 Mauvaise requête.
    """
    test_name = "test_favorite_stocks_invalid_symbol"
    logging.info(f"Test: {test_name} - Tentative d'ajouter/supprimer avec un symbole invalide.")
    token = get_jwt_token(client, "favstockerrtest@mail.com", "favpass", "FavStockErrTest")

    # Test POST avec un symbole manquant
    try:
        response_post = client.post(
            '/actions/favoris',
            json={}, # Symbole manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_post.status_code == 400, \
            f"Attendu 400 pour POST avec un symbole manquant, mais reçu {response_post.status_code}. Réponse: {response_post.get_data(as_text=True)}"
        data = response_post.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "symbole" in error_message or \
               "Le symbole de l'action est requis." in error_message or \
               "Symbole requis." in error_message, \
            f"Message d'erreur inattendu POST avec un symbole manquant: {error_message}"
        log_test_result(f"{test_name} - POST Symbole manquant", True)
    except AssertionError:
        log_test_result(f"{test_name} - POST Symbole manquant", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - POST Symbole manquant a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - POST Symbole manquant", False)
        raise

    # Test POST avec un symbole vide
    try:
        response_post_empty = client.post(
            '/actions/favoris',
            json={"symbole": ""},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_post_empty.status_code == 400, \
            f"Attendu 400 pour POST avec un symbole vide, mais reçu {response_post_empty.status_code}. Réponse: {response_post_empty.get_data(as_text=True)}"
        data = response_post_empty.get_json()
        error_message = get_error_message(data)
        assert "ne peut pas être vide" in error_message or \
               "invalid symbol" in error_message or \
               "Le symbole de l'action est requis." in error_message or \
               "Field may not be empty" in error_message or \
               "Symbole requis." in error_message, \
            f"Message d'erreur inattendu POST avec un symbole vide: {error_message}"
        log_test_result(f"{test_name} - POST Symbole vide", True)
    except AssertionError:
        log_test_result(f"{test_name} - POST Symbole vide", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - POST Symbole vide a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - POST Symbole vide", False)
        raise

    # Test DELETE avec un symbole manquant
    try:
        response_delete = client.delete(
            '/actions/favoris',
            json={}, # Symbole manquant
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_delete.status_code == 400, \
            f"Attendu 400 pour DELETE avec un symbole manquant, mais reçu {response_delete.status_code}. Réponse: {response_delete.get_data(as_text=True)}"
        data = response_delete.get_json()
        error_message = get_error_message(data)
        assert "Missing data for required field" in error_message or \
               "Field missing" in error_message or \
               "symbole" in error_message or \
               "Le symbole de l'action est requis." in error_message or \
               "Symbole requis." in error_message, \
            f"Message d'erreur inattendu DELETE avec un symbole manquant: {error_message}"
        log_test_result(f"{test_name} - DELETE Symbole manquant", True)
    except AssertionError:
        log_test_result(f"{test_name} - DELETE Symbole manquant", False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} - DELETE Symbole manquant a échoué en raison d'une erreur: {e}")
        log_test_result(f"{test_name} - DELETE Symbole manquant", False)
        raise

def test_add_favorite_stock_already_exists(client):
    """
    Scénario: Tentative d'ajouter une action déjà présente dans les favoris.
    Attendu: 200 OK ou 409 Conflit.
    """
    test_name = "test_add_favorite_stock_already_exists"
    logging.info(f"Test: {test_name} - Tentative d'ajouter une action déjà favorite.")
    try:
        token = get_jwt_token(client, "readdstockerrtest@mail.com", "readdpass", "ReaddStockErrTest")
        test_symbol = "AMZN" 

        resp_add_first = client.post(
            '/actions/favoris',
            json={"symbole": test_symbol},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_add_first.status_code == 200, \
            f"Attendu 200 pour le premier ajout, mais reçu {resp_add_first.status_code}. Réponse: {resp_add_first.get_data(as_text=True)}"

        response_readd = client.post(
            '/actions/favoris',
            json={"symbole": test_symbol},
            headers={"Authorization": f"Bearer {token}"}
        )
       
        assert response_readd.status_code in [200, 409], \
            f"Attendu 200 ou 409 pour une action favorite existante, mais reçu {response_readd.status_code}. Réponse: {response_readd.get_data(as_text=True)}"
        data = response_readd.get_json()
        error_message = get_error_message(data)
        if response_readd.status_code == 409:
            assert "Action déjà dans les favoris." in error_message or \
                   "already exists" in error_message, \
                f"Message inattendu pour 409: {error_message}"
        elif response_readd.status_code == 200:
            assert "Action ajoutée aux favoris." in error_message or \
                   "Action déjà dans les favoris." in error_message, \
                f"Message inattendu pour 200: {error_message}"
        log_test_result(test_name, True)
    except AssertionError:
        log_test_result(test_name, False)
        raise
    except Exception as e:
        logging.error(f"Le test {test_name} a échoué en raison d'une erreur: {e}")
        log_test_result(test_name, False)
        raise