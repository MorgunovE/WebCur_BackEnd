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
        Retrieve stock data for a given symbol, optionally for a specific date.
        """
        # 1. If date is provided, try DB first
        if date:
            action = self.repo.chercher_par_symbole_et_date(symbole, date)
            if action:
                return self.schema.dump(action)
            # Not found, try API for that date
            api_data = self._fetch_action_from_api(symbole, date)
            if not api_data:
                return {"message": "Données d'action non disponibles."}, 404
            action_obj = Action(**api_data)
            self.repo.creer(action_obj)
            return self.schema.dump(action_obj)

        # 2. No date: use today
        date_today = self._get_today_str()
        action = self.repo.chercher_par_symbole_et_date(symbole, date_today)
        if action:
            return self.schema.dump(action)
        # Not found, try API for today, fallback to latest
        api_data = self._fetch_action_from_api(symbole, date_today)
        if not api_data:
            return {"message": "Données d'action non disponibles."}, 404
        action_obj = Action(**api_data)
        self.repo.creer(action_obj)
        return self.schema.dump(action_obj)

    def _fetch_action_from_api(self, symbole, date):
        """
        Fetch action data from Alpha Vantage API for a given symbol and date.
        """
        url = os.getenv("ALPHAVANTAGE_API_URL", "https://www.alphavantage.co/query")
        function = os.getenv("ALPHAVANTAGE_FUNCTION", "TIME_SERIES_DAILY")
        if not self.api_key:
            return None
        params = {
            "function": function,
            "symbol": symbole,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None
        data = response.json()
        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            return None
        # Use the requested date or the latest available
        if date and date in time_series:
            day_data = time_series[date]
            used_date = date
        else:
            # Get the latest date
            latest_date = sorted(time_series.keys())[-1]
            day_data = time_series[latest_date]
            used_date = latest_date
        return {
            "symbole": symbole,
            "date": used_date,
            "open": float(day_data["1. open"]),
            "high": float(day_data["2. high"]),
            "low": float(day_data["3. low"]),
            "close": float(day_data["4. close"]),
            "volume": int(day_data["5. volume"])
        }

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