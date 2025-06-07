import os
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.currency_service import CurrencyService

class DeviseRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self, nom):
        # Get details of a currency by its code
        result = self.service.obtenir_devise(nom.upper())
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class ConversionRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = CurrencyService()

    def post(self):
        # Convert an amount from one currency to another
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
        # Return the list of user's favorite currencies
        user_id = get_jwt_identity()
        return self.service.lire_favoris(user_id), 200

    def post(self):
        # Add a currency to favorites
        user_id = get_jwt_identity()
        data = request.get_json()
        nom_devise = data.get("nom_devise")
        if not nom_devise:
            return {"message": "Nom de la devise est requis."}, 400
        return self.service.ajouter_favori(user_id, nom_devise.upper()), 200

    def delete(self):
        # Remove a currency from favorites
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
        # Return the most popular currencies
        popular = [c.strip().upper() for c in os.getenv("POPULAR_CURRENCIES", "USD,EUR,GBP,JPY,CAD").split(",")]
        date_maj = self.service._get_today_str()
        devises = self.service.repo.lire_les_plus_populaires(popular, date_maj)
        return [self.service.schema.dump(devise) for devise in devises], 200