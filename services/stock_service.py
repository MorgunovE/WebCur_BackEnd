import os
import requests
from datetime import datetime, UTC
from repositories.stock_repository import StockRepository
from models.stock import Action
from schemas.stock import ActionSchema
from services.currency_service import CurrencyService

class StockService:
    """
    Service métier pour la gestion des actions.
    """

    def __init__(self):
        self.repo = StockRepository()
        self.schema = ActionSchema()
        self.api_key = os.getenv("API_KEY_AV")
        self.currency_service = CurrencyService()

    def _get_today_str(self):
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def obtenir_action(self, symbole, date=None):
        """
        Récupère les données d'une action pour une date donnée (ou aujourd'hui).
        """
        if not date:
            date = self._get_today_str()
        action = self.repo.chercher_par_symbole_et_date(symbole, date)
        if action:
            return self.schema.dump(action)

        # Si non trouvée, requête à l'API Alpha Vantage
        url = os.getenv("ALPHAVANTAGE_API_URL", "https://www.alphavantage.co/query")
        function = os.getenv("ALPHAVANTAGE_FUNCTION", "TIME_SERIES_DAILY")
        if not self.api_key:
            return {"message": "API_KEY_AV non défini dans l'environnement."}, 500
        params = {
            "function": function,
            "symbol": symbole,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return {"message": "Erreur lors de la récupération des données Alpha Vantage."}, 502

        data = response.json()
        if "Time Series (Daily)" not in data:
            return {"message": "Réponse API Alpha Vantage invalide."}, 502

        series = data["Time Series (Daily)"]
        dates = list(series.keys())
        existantes = self.repo.chercher_dates_existantes(symbole, dates)
        nouvelles = [d for d in dates if d not in existantes]
        actions = []
        for d in nouvelles:
            info = series[d]
            action = Action(
                symbole=symbole,
                date=d,
                open=float(info["1. open"]),
                high=float(info["2. high"]),
                low=float(info["3. low"]),
                close=float(info["4. close"]),
                volume=int(info["5. volume"])
            )
            actions.append(action)
        if actions:
            self.repo.creer_plusieurs(actions)

        # Retourner la donnée demandée (après insertion)
        action = self.repo.chercher_par_symbole_et_date(symbole, date)
        if action:
            return self.schema.dump(action)
        return {"message": "Aucune donnée pour cette date."}, 404

    def calculer_cout_achat(self, symbole, date, quantite, code_devise):
        """
        Calcule le coût d'achat d'un certain nombre d'actions avec conversion de devise.
        """
        action = self.repo.chercher_par_symbole_et_date(symbole, date)
        if not action:
            # Essayer de récupérer et sauvegarder depuis l'API
            self.obtenir_action(symbole, date)
            action = self.repo.chercher_par_symbole_et_date(symbole, date)
            if not action:
                return {"message": "Données d'action non disponibles."}, 404

        montant_usd = action.close * quantite
        if code_devise.upper() == "USD":
            return {
                "symbole": symbole,
                "date": date,
                "quantite": quantite,
                "devise": "USD",
                "cout_total": round(montant_usd, 2)
            }
        # Conversion via CurrencyService
        conversion = self.currency_service.convertir("USD", code_devise.upper(), montant_usd)
        if isinstance(conversion, tuple):  # error
            return conversion
        return {
            "symbole": symbole,
            "date": date,
            "quantite": quantite,
            "devise": code_devise.upper(),
            "cout_total": conversion["montant_converti"],
            "taux": conversion["taux_cible"]
        }

    def ajouter_favori(self, user_id, symbole):
        self.repo.ajouter_favori(user_id, symbole)
        return {"message": "Action ajoutée aux favoris."}

    def supprimer_favori(self, user_id, symbole):
        self.repo.supprimer_favori(user_id, symbole)
        return {"message": "Action supprimée des favoris."}

    def lire_favoris(self, user_id):
        favoris = self.repo.lire_favoris_par_utilisateur(user_id)
        return {"favoris": favoris}