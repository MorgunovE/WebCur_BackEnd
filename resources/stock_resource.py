from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.stock_service import StockService
import os

class ActionRessource(Resource):
    def __init__(self):
        self.service = StockService()

    def get(self, symbole):
        # Obtenir les données d'une action pour un symbole donné
        date = request.args.get("date")
        result = self.service.obtenir_action(symbole.upper(), date)
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class CalculerAchatRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = StockService()

    def post(self):
        # Calculer le coût d'achat d'une action
        data = request.get_json()
        symbole = data.get("symbole")
        date = data.get("date")
        quantite = data.get("quantite")
        code_devise = data.get("code_devise")
        if not all([symbole, date, quantite, code_devise]):
            return {"message": "Tous les champs sont requis."}, 400
        result = self.service.calculer_cout_achat(symbole.upper(), date, quantite, code_devise)
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class PopulairesActionsRessource(Resource):
    def __init__(self):
        self.service = StockService()

    def get(self):
        # Returner les actions populaires
        popular = [s.strip().upper() for s in os.getenv("POPULAR_STOCKS", "AAPL,MSFT,GOOGL,AMZN,TSLA").split(",")]
        results = []
        for symbole in popular:
            res = self.service.obtenir_action(symbole)
            if isinstance(res, dict) and "symbole" in res:
                results.append(res)
        return results, 200

class FavorisActionsRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = StockService()

    def get(self):
        # Obtanir la liste des actions favorites de l'utilisateur
        user_id = get_jwt_identity()
        return self.service.lire_favoris(user_id), 200

    def post(self):
        # Ajouter une action aux favoris
        user_id = get_jwt_identity()
        data = request.get_json()
        symbole = data.get("symbole")
        if not symbole:
            return {"message": "Symbole requis."}, 400
        return self.service.ajouter_favori(user_id, symbole.upper()), 200

    def delete(self):
        # Supprimer une action des favoris
        user_id = get_jwt_identity()
        data = request.get_json()
        symbole = data.get("symbole")
        if not symbole:
            return {"message": "Symbole requis."}, 400
        return self.service.supprimer_favori(user_id, symbole.upper()), 200

class ActionHistoriqueRessource(Resource):
    def __init__(self):
        self.service = StockService()

    def get(self, symbole):
        nb_jours = request.args.get("jours", type=int)
        date_debut = request.args.get("date_debut")
        date_fin = request.args.get("date_fin")
        if nb_jours:
            if nb_jours < 1:
                return {"message": "Le nombre de jours doit être au moins 1."}, 400
            result = self.service.obtenir_historique(symbole.upper(), nb_jours)
        elif date_debut and date_fin:
            result = self.service.obtenir_historique_periode(symbole.upper(), date_debut, date_fin)
        else:
            return {"message": "Paramètres manquants ou invalides."}, 400
        if not result:
            return {"message": "Aucune donnée disponible pour cette période."}, 404
        return result, 200