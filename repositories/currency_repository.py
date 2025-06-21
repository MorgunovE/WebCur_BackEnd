from pymongo import MongoClient
from models.currency import Devise
import os

class CurrencyRepository:
    """
    Dépôt pour la gestion des devises et des favoris dans MongoDB.
    """

    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        dbname = os.getenv("MONGODB_DBNAME")
        self.client = MongoClient(uri)
        self.db = self.client[dbname]
        self.collection = self.db["devises"]
        self.favoris_collection = self.db["favoris_devises"]

    def chercher_par_nom_et_date(self, nom, date_maj):
        """
        Cherche une devise par son nom et la date de mise à jour.
        """
        doc = self.collection.find_one({"nom": nom, "date_maj": date_maj})
        if doc:
            return Devise.from_dict(doc)
        return None

    def lire_historique_par_nom(self, nom: str, dates: list) -> list:
        """
        Récupère l'historique d'une devise pour une liste de dates.
        """
        cursor = self.collection.find({
            "nom": nom,
            "date_maj": {"$in": dates}
        })
        return [Devise.from_dict(doc) for doc in cursor]

    def lire_historique_sur_periode(self, nom: str, date_debut: str, date_fin: str) -> list:
        """
        Récupère l'historique d'une devise pour une période donnée (dates inclusives).
        """
        cursor = self.collection.find({
            "nom": nom,
            "date_maj": {"$gte": date_debut, "$lte": date_fin}
        }).sort("date_maj", 1)
        return [Devise.from_dict(doc) for doc in cursor]

    def creer(self, devise: Devise):
        """
        Crée une nouvelle devise dans la base de données.
        """
        data = devise.to_dict()
        result = self.collection.insert_one(data)
        devise.id = str(result.inserted_id)
        return devise

    def mettre_a_jour(self, nom, date_maj, data):
        """
        Met à jour une devise existante.
        """
        result = self.collection.update_one(
            {"nom": nom, "date_maj": date_maj},
            {"$set": data}
        )
        return result.modified_count > 0

    def lire_les_plus_populaires(self, popular_currencies, date_maj):
        """
        Récupère les devises les plus populaires pour la date donnée.
        """
        devises = []
        for nom in popular_currencies:
            doc = self.collection.find_one({"nom": nom, "date_maj": date_maj})
            if doc:
                devises.append(Devise.from_dict(doc))
        return devises

    def ajouter_favori(self, user_id, nom_devise):
        """
        Ajoute une devise aux favoris de l'utilisateur.
        """
        self.favoris_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"devises": nom_devise}},
            upsert=True
        )

    def supprimer_favori(self, user_id, nom_devise):
        """
        Supprime une devise des favoris de l'utilisateur.
        """
        self.favoris_collection.update_one(
            {"user_id": user_id},
            {"$pull": {"devises": nom_devise}}
        )

    def lire_favoris_par_utilisateur(self, user_id):
        """
        Récupère la liste des devises favorites de l'utilisateur.
        """
        doc = self.favoris_collection.find_one({"user_id": user_id})
        return doc["devises"] if doc and "devises" in doc else []