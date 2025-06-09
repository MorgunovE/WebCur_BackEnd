from pymongo import MongoClient
import os
from models.company import Societe

class SocieteRepository:
    """
    Dépôt pour la gestion des sociétés en base MongoDB.
    """

    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        dbname = os.getenv("MONGODB_DBNAME")
        self.client = MongoClient(uri)
        self.db = self.client[dbname]
        self.collection = self.db["societes"]

    def chercher_par_symbole_et_date(self, symbole, date_maj):
        """
        Cherche une société par son symbole et la date de mise à jour.
        """
        doc = self.collection.find_one({"symbole": symbole, "date_maj": date_maj})
        if doc:
            return Societe.from_dict(doc)
        return None

    def creer(self, societe: Societe):
        """
        Ajoute une nouvelle société à la base de données.
        """
        data = societe.to_dict()
        result = self.collection.insert_one(data)
        societe.id = str(result.inserted_id)
        return societe

    def chercher_historique(self, symbole, dates):
        """
        Récupère l'historique d'une société pour une liste de dates.
        """
        cursor = self.collection.find({
            "symbole": symbole,
            "date_maj": {"$in": dates}
        })
        return [Societe.from_dict(doc) for doc in cursor]

    def chercher_historique_periode(self, symbole, date_debut, date_fin):
        """
        Récupère l'historique d'une société pour une période donnée (dates inclusives).
        """
        cursor = self.collection.find({
            "symbole": symbole,
            "date_maj": {"$gte": date_debut, "$lte": date_fin}
        }).sort("date_maj", 1)
        return [Societe.from_dict(doc) for doc in cursor]