# app.py
from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Vérifier les variables d'environnement essentielles
if not os.getenv("MONGODB_URI") or not os.getenv("JWT_SECRET"):
    raise RuntimeError("MONGODB_URI et JWT_SECRET doivent être définis dans .env")

# Créer l'application Flask
app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = app.config['JWT_SECRET_KEY']

# Initialiser les extensions
api = Api(app)
jwt = JWTManager(app)
CORS(app)

# Configurer Swagger UI
SWAGGER_URL = app.config['SWAGGER_URL']
API_URL = app.config['API_URL']
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "WebCur API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Endpoint de test
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()