from pymongo import MongoClient
import os
from models.stock import Action

class StockRepository:
    """
    Dépôt pour la gestion des actions en base MongoDB.
    """

    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        dbname = os.getenv("MONGODB_DBNAME")
        self.client = MongoClient(uri)
        self.db = self.client[dbname]
        self.collection = self.db["actions"]
        self.favoris_collection = self.db["favoris_actions"]

    def chercher_par_symbole_et_date(self, symbole, date):
        """
        Cherche une action par son symbole et sa date.
        """
        doc = self.collection.find_one({"symbole": symbole, "date": date})
        if doc:
            return Action.from_dict(doc)
        return None

    def creer(self, action: Action):
        """
        Ajoute une nouvelle action à la base de données.
        """
        data = action.to_dict()
        result = self.collection.insert_one(data)
        action.id = str(result.inserted_id)
        return action

    def chercher_dates_existantes(self, symbole, dates):
        """
        Retourne la liste des dates déjà présentes pour un symbole donné.
        """
        cursor = self.collection.find(
            {"symbole": symbole, "date": {"$in": dates}},
            {"date": 1, "_id": 0}
        )
        return [doc["date"] for doc in cursor]

    def lire_historique_sur_periode(self, symbole, date_debut, date_fin):
        """
        Retrieve the history of a stock for a given period (inclusive dates).
        """
        cursor = self.collection.find({
            "symbole": symbole,
            "date": {"$gte": date_debut, "$lte": date_fin}
        }).sort("date", 1)
        return [Action.from_dict(doc) for doc in cursor]

    def lire_historique_par_jours(self, symbole, dates):
        """
        Retrieve the history of a stock for a list of dates.
        """
        cursor = self.collection.find({
            "symbole": symbole,
            "date": {"$in": dates}
        }).sort("date", 1)
        return [Action.from_dict(doc) for doc in cursor]

    def get_all_dates_for_symbol(self, symbole):
        cursor = self.collection.find({"symbole": symbole}, {"date": 1, "_id": 0})
        return [doc["date"] for doc in cursor]

    def creer_plusieurs(self, actions):
        """
        Ajoute plusieurs actions en une seule opération.
        """
        data = [a.to_dict() for a in actions]
        if not data:
            return []
        result = self.collection.insert_many(data)
        for action, inserted_id in zip(actions, result.inserted_ids):
            action.id = str(inserted_id)
        return actions

    def ajouter_favori(self, user_id, symbole):
        self.favoris_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"actions": symbole}},
            upsert=True
        )

    def supprimer_favori(self, user_id, symbole):
        self.favoris_collection.update_one(
            {"user_id": user_id},
            {"$pull": {"actions": symbole}}
        )

    def lire_favoris_par_utilisateur(self, user_id):
        doc = self.favoris_collection.find_one({"user_id": user_id})
        return doc["actions"] if doc and "actions" in doc else []