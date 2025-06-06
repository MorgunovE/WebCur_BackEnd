from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from services.user_service import UserService

# Ressource pour l'authentification des utilisateurs
class AuthentificationRessource(Resource):
    def __init__(self):
        self.service = UserService()

    def post(self):
        # Récupérer les données de connexion
        data = request.get_json()
        email = data.get("email")
        mot_de_passe = data.get("mot_de_passe")

        # Vérifier les informations d'identification
        utilisateur = self.service.authenticate(email, mot_de_passe)
        if utilisateur:
            # Générer un token JWT
            access_token = create_access_token(identity=utilisateur["id"])
            return {"access_token": access_token}, 200
        return {"message": "Identifiants invalides"}, 401