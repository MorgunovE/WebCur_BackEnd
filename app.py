# app.py
from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from resources.user_resource import UtilisateurListRessource, UtilisateurRessource
from resources.auth_resource import AuthentificationRessource
from resources.auth_resource import DeconnexionRessource
from resources.currency_resource import (
    DeviseRessource, ConversionRessource, FavorisRessource, PopulairesRessource
)


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

# Enregistrer les ressources utilisateur
api.add_resource(UtilisateurListRessource, '/utilisateurs')
api.add_resource(UtilisateurRessource, '/utilisateurs/<string:id>')

# Enregistrer la ressource d'authentification
api.add_resource(AuthentificationRessource, '/connexion')
api.add_resource(DeconnexionRessource, '/deconnexion')

# Enregistrer les ressources de devise
api.add_resource(DeviseRessource, '/devises/<string:nom>')
api.add_resource(ConversionRessource, '/devises/conversion')
api.add_resource(FavorisRessource, '/devises/favoris')
api.add_resource(PopulairesRessource, '/devises/populaires')

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
def startApp():
    return (
        '<h2> WebCur backend démarré avec succès! / WebCur backend started successfully!</h2>'
        '<p>'
        'Allez sur <a href="/swagger" target="_blank">/swagger</a> pour la documentation API.<br>'
        'Go to <a href="/swagger" target="_blank">/swagger</a> for the API documentation.'
        '</p>'
    ), 200, {'Content-Type': 'text/html'}

if __name__ == '__main__':
    app.run(debug=True)