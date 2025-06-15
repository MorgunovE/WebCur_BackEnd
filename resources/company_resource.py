from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from services.company_service import SocieteService
import os

class SocieteRessource(Resource):

    def __init__(self):
        self.service = SocieteService()

    def get(self, symbole):
        """
        Récupère les informations d'une société par son symbole.
        JWT requis.
        """
        result = self.service.obtenir_societe(symbole.upper())
        return result, 200 if isinstance(result, dict) and "message" not in result else result[1]

class SocieteHistoriqueRessource(Resource):

    def __init__(self):
        self.service = SocieteService()

    def get(self, symbole):
        """
        Récupère l'historique d'une société (par nombre de jours ou période).
        JWT requis.
        """
        nb_jours = request.args.get("jours", type=int)
        date_debut = request.args.get("date_debut")
        date_fin = request.args.get("date_fin")
        if nb_jours:
            if nb_jours < 2:
                return {"message": "Le nombre de jours doit être au moins 2."}, 400
            result = self.service.obtenir_historique(symbole.upper(), nb_jours)
        elif date_debut and date_fin:
            result = self.service.obtenir_historique_periode(symbole.upper(), date_debut, date_fin)
        else:
            return {"message": "Paramètres manquants ou invalides."}, 400
        if not result:
            return {"message": "Aucune donnée disponible pour cette période."}, 404
        return result, 200

class SocietesPopulairesRessource(Resource):
    def __init__(self):
        self.service = SocieteService()

    def get(self):
        """
        Récupère les informations des sociétés les plus populaires.
        Pas d'authentification requise.
        """
        result = self.service.obtenir_societes_populaires()
        return result, 200