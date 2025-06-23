from flask import request
from flask_restful import Resource
from services.company_service import SocieteService

class SocieteRessource(Resource):

    def __init__(self):
        self.service = SocieteService()

    def get(self, symbole):
        """
        Récupère les informations d'une société par son symbole.
        JWT requis.
        """
        result = self.service.obtenir_societe(symbole.upper())
        if result is None:
            return {"message": f"Société avec le symbole '{symbole}' non trouvée."}, 404

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict) and "message" in result[0]:
            return result[0], result[1]

        return result, 200

class SocieteHistoriqueRessource(Resource):

    def __init__(self):
        self.service = SocieteService()

    def get(self, symbole):
        """
        Récupère l'historique d'une société (par nombre de jours ou période).
        """
        nb_jours = request.args.get("jours", type=int)
        date_debut = request.args.get("date_debut")
        date_fin = request.args.get("date_fin")

        if nb_jours is not None:
            if nb_jours < 2:
                return {"message": "Le nombre de jours doit être au moins 2."}, 400
            result = self.service.obtenir_historique(symbole.upper(), nb_jours)
        elif date_debut and date_fin:
            try:
                _date_debut_dt = datetime.strptime(date_debut, '%Y-%m-%d')
                _date_fin_dt = datetime.strptime(date_fin, '%Y-%m-%d')
            except ValueError:
                return {"message": "Format de date invalide. Utilisez AAAA-MM-JJ."}, 400

            if _date_debut_dt > _date_fin_dt:
                return {"message": "La date de début ne peut pas être postérieure à la date de fin."}, 400

            result = self.service.obtenir_historique_periode(symbole.upper(), date_debut, date_fin)
        else:
            return {"message": "Paramètres manquants ou invalides. Fournissez 'jours' ou 'date_debut' и 'date_fin'."}, 400

        if not result:
            return {"message": "Aucune donnée disponible pour cette période ou symbole introuvable."}, 404

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict) and "message" in result[0]:
            return result[0], result[1]

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