from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.currency_service import CurrencyService

class DeviseRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self, nom):
        # Obtenir details d'une devise par son nom
        result = self.service.obtenir_devise(nom.upper())
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class ConversionRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = CurrencyService()

    def post(self):
        # Convertir un montant d'une devise à une autre
        data = request.get_json()
        code_source = data.get("code_source")
        code_cible = data.get("code_cible")
        montant = data.get("montant")
        result = self.service.convertir(code_source.upper(), code_cible.upper(), montant)
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class FavorisRessource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self):
        self.service = CurrencyService()

    def get(self):
        # Returne la list des devises favorites de l'utilisateur
        user_id = get_jwt_identity()
        return self.service.lire_favoris(user_id), 200

    def post(self):
        # Ajouter a currency to favorites
        user_id = get_jwt_identity()
        data = request.get_json()
        nom_devise = data.get("nom_devise")
        return self.service.ajouter_favori(user_id, nom_devise.upper()), 200

    def delete(self):
        # Supprimer une devise des favoris
        user_id = get_jwt_identity()
        data = request.get_json()
        nom_devise = data.get("nom_devise")
        return self.service.supprimer_favori(user_id, nom_devise.upper()), 200

class PopulairesRessource(Resource):
    def __init__(self):
        self.service = CurrencyService()

    def get(self):
        # Retourne les devises les plus populaires
        popular = ["USD", "EUR", "GBP", "JPY", "CAD"]
        date_maj = self.service._get_today_str()
        devises = self.service.repo.lire_les_plus_populaires(popular, date_maj)
        return [self.service.schema.dump(devise) for devise in devises], 200