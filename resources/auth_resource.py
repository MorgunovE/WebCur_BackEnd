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
            return {
                "access_token": access_token,
                "id": utilisateur["id"],
                "nom_utilisateur": utilisateur["nom_utilisateur"]
            }, 200
        return {"message": "Identifiants invalides"}, 401

# Ressource pour la déconnexion (JWT)
class DeconnexionRessource(Resource):
    def post(self):
        # Implementation de la déconnexion doit faire partie de la gestion du token JWT dans Frontend party
        # En général, la déconnexion est gérée côté client en supprimant le token
        # Ici, nous pouvons juste retourner un message de succès comme exemple
        # Frontend peut supprimer le token JWT du stockage local ou des cookies
        return {"message": "Déconnexion réussie"}, 200