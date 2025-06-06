from repositories.user_repository import UserRepository
from schemas.user import UtilisateurSchema
from models.user import Utilisateur
from marshmallow import ValidationError

class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.schema = UtilisateurSchema()

    def register(self, data):
        # Validation le schéma des données d'entrée
        try:
            user_data = self.schema.load(data)
        except ValidationError as err:
            return {"errors": err.messages}, 400

        # verifier si l'utilisateur existe déjà
        if self.repo.collection.find_one({"email": user_data["email"]}):
            return {"message": "Un utilisateur avec cet email existe déjà."}, 409

        utilisateur = Utilisateur(**user_data)
        created_user = self.repo.creer(utilisateur)
        return self.schema.dump(created_user), 201

    def authenticate(self, email, mot_de_passe):
        # Authentification de l'utilisateur
        user_doc = self.repo.collection.find_one({
            "email": email,
            "mot_de_passe": mot_de_passe
        })
        if not user_doc:
            return None
        utilisateur = Utilisateur.from_dict(user_doc)
        return self.schema.dump(utilisateur)

    def get_all(self):
        users = self.repo.lire_tous()
        return self.schema.dump(users, many=True)

    def get_by_id(self, user_id):
        user = self.repo.lire_par_id(user_id)
        if user:
            return self.schema.dump(user)
        return None

    def update(self, user_id, data):
        updated = self.repo.mettre_a_jour(user_id, data)
        return updated

    def delete(self, user_id):
        return self.repo.supprimer(user_id)