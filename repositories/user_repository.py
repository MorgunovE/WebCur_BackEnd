from pymongo import MongoClient
from bson.objectid import ObjectId
from models.user import Utilisateur
import os

class UserRepository:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        dbname = os.getenv("MONGODB_DBNAME")
        self.client = MongoClient(uri)
        # Vérifier si la base de données existe, sinon la créer
        if dbname not in self.client.list_database_names():
            self.client[dbname].create_collection("utilisateurs")
        self.db = self.client[dbname]
        self.collection = self.db["utilisateurs"]

    # Méthodes CRUD pour les utilisateurs
    def creer(self, utilisateur: Utilisateur):
        data = utilisateur.to_dict()
        result = self.collection.insert_one(data)
        utilisateur.id = str(result.inserted_id)
        return utilisateur

    def lire_tous(self):
        utilisateurs = []
        for doc in self.collection.find():
            utilisateurs.append(Utilisateur.from_dict(doc))
        return utilisateurs

    def lire_par_id(self, user_id):
        doc = self.collection.find_one({"_id": ObjectId(user_id)})
        if doc:
            return Utilisateur.from_dict(doc)
        return None

    def mettre_a_jour(self, user_id, data):
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data}
        )
        return result.modified_count > 0
    
    def chercher_par_email(self, email):
        user_doc = self.collection.find_one({"email": email})
        if user_doc:
            return Utilisateur.from_dict(user_doc)
        return None

    def supprimer(self, user_id):
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def supprimer_par_email(self, email):
        result = self.collection.delete_many({"email": email})
        return result.deleted_count