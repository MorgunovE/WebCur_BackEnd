import os
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.currency_service import CurrencyService

class DeviseRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self, nom):
        # Obtain currency information by name
        result = self.service.obtenir_devise(nom.upper())
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class ConversionRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = CurrencyService()

    def post(self):
        # Convertir une somme d'une devise à une autre
        data = request.get_json()
        code_source = data.get("code_source")
        code_cible = data.get("code_cible")
        montant = data.get("montant")
        if not code_source or not code_cible or montant is None:
            return {"message": "Code source, code cible et montant sont requis."}, 400
        result = self.service.convertir(code_source.upper(), code_cible.upper(), montant)
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class FavorisRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = CurrencyService()

    def get(self):
        # Returne le list des devises favorites de l'utilisateur
        user_id = get_jwt_identity()
        return self.service.lire_favoris(user_id), 200

    def post(self):
        # Ajouter a currency to favorites
        user_id = get_jwt_identity()
        data = request.get_json()
        nom_devise = data.get("nom_devise")
        if not nom_devise:
            return {"message": "Nom de la devise est requis."}, 400
        return self.service.ajouter_favori(user_id, nom_devise.upper()), 200

    def delete(self):
        # Supprimer une devise des favoris
        user_id = get_jwt_identity()
        data = request.get_json()
        nom_devise = data.get("nom_devise")
        if not nom_devise:
            return {"message": "Nom de la devise est requis."}, 400
        return self.service.supprimer_favori(user_id, nom_devise.upper()), 200

class PopulairesRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self):
        # Returne les devises les plus populaires
        popular = [c.strip().upper() for c in os.getenv("POPULAR_CURRENCIES", "USD,EUR,GBP,JPY,CAD").split(",")]
        results = []
        for code in popular:
            result = self.service.obtenir_devise(code)
            if isinstance(result, dict) and "nom" in result:
                results.append(result)
        return results, 200

class DeviseHistoriqueRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self, nom):
        jours = request.args.get("jours")
        date_debut = request.args.get("date_debut")
        date_fin = request.args.get("date_fin")

        if jours:
            try:
                jours = int(jours)
            except ValueError:
                return {"message": "Paramètre 'jours' invalide."}, 400
            historique = self.service.obtenir_historique(nom.upper(), jours)
        elif date_debut and date_fin:
            historique = self.service.obtenir_historique_periode(nom.upper(), date_debut, date_fin)
        else:
            return {"message": "Paramètres requis: 'jours' ou 'date_debut' et 'date_fin'."}, 400

        if not historique:
            return {"message": "Aucune donnée disponible pour cette période."}, 404
        return historique, 200