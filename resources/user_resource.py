from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from services.user_service import UserService

# Ressource pour la liste des utilisateurs et la création
class UtilisateurListRessource(Resource):
    def __init__(self):
        self.service = UserService()

    def get(self):
        # Récupérer tous les utilisateurs
        return self.service.get_all(), 200

    def post(self):
        # Créer un nouvel utilisateur
        data = request.get_json()
        return self.service.register(data)

# Ressource pour un utilisateur individuel (CRUD)
class UtilisateurRessource(Resource):
    def __init__(self):
        self.service = UserService()

    def get(self, id):
        # Récupérer un utilisateur par ID
        user = self.service.get_by_id(id)
        if user:
            return user, 200
        return {"message": "Utilisateur non trouvé"}, 404

    @jwt_required()
    def put(self, id):
        # Mettre à jour un utilisateur
        data = request.get_json()
        updated = self.service.update(id, data)
        if updated:
            return {"message": "Utilisateur mis à jour"}, 200
        return {"message": "Utilisateur non trouvé"}, 404

    @jwt_required()
    def delete(self, id):
        # Supprimer un utilisateur
        deleted = self.service.delete(id)
        if deleted:
            return 'Utilisateur supprimé', 204
        else:
            return {"message": "Utilisateur non trouvé"}, 404