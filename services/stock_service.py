import os
import requests
from datetime import datetime, timedelta, UTC
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
        Récupère les données d'une action pour un symbole donné, avec option de date.
        """
        if date:
            action = self.repo.chercher_par_symbole_et_date(symbole, date)
            if action:
                return self.schema.dump(action)
            api_data = self._fetch_action_from_api(symbole)
            if not api_data or "series" not in api_data or "Information" in getattr(api_data, "keys", lambda: [])():
                # Si l'API ne retourne pas de données, on essaie de récupérer la dernière date disponible
                latest_dates = self.repo.get_all_dates_for_symbol(symbole)
                if latest_dates:
                    latest_date = sorted(latest_dates, reverse=True)[0]
                    action = self.repo.chercher_par_symbole_et_date(symbole, latest_date)
                    if action:
                        return self.schema.dump(action)
                return {"message": "Données d'action non disponibles."}, 404
            # Vérifier les dates existantes dans la base de données
            all_dates = [a.date for a in api_data["series"]]
            existing_dates = self.repo.chercher_dates_existantes(symbole, all_dates)
            # Filtrer les nouvelles actions à ajouter
            new_actions = [a for a in api_data["series"] if a.date not in existing_dates]
            if new_actions:
                self.repo.creer_plusieurs(new_actions)
            action = self.repo.chercher_par_symbole_et_date(symbole, date)
            if action:
                return self.schema.dump(action)
            # Si aucune action trouvée pour la date spécifique, on retourne la dernière date disponible
            latest_dates = self.repo.get_all_dates_for_symbol(symbole)
            if latest_dates:
                latest_date = sorted(latest_dates, reverse=True)[0]
                action = self.repo.chercher_par_symbole_et_date(symbole, latest_date)
                if action:
                    return self.schema.dump(action)
            return {"message": "Données d'action non disponibles."}, 404
        else:
            date_today = self._get_today_str()
            action = self.repo.chercher_par_symbole_et_date(symbole, date_today)
            if action:
                return self.schema.dump(action)
            api_data = self._fetch_action_from_api(symbole)
            if not api_data or "series" not in api_data:
                return {"message": "Données d'action non disponibles."}, 404
            all_dates = [a.date for a in api_data["series"]]
            existing_dates = self.repo.chercher_dates_existantes(symbole, all_dates)
            new_actions = [a for a in api_data["series"] if a.date not in existing_dates]
            if new_actions:
                self.repo.creer_plusieurs(new_actions)
            latest_dates = self.repo.get_all_dates_for_symbol(symbole)
            if latest_dates:
                latest_date = sorted(latest_dates, reverse=True)[0]
                action = self.repo.chercher_par_symbole_et_date(symbole, latest_date)
                if action:
                    return self.schema.dump(action)
            return {"message": "Données d'action non disponibles."}, 404

    def _fetch_action_from_api(self, symbole):
        """
        Récupère les données d'une action depuis l'API Alpha Vantage.
        Si l'API ne retourne pas de données, retourne None.
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
        series = []
        for d, day_data in time_series.items():
            series.append(Action(
                symbole=symbole,
                date=d,
                open=float(day_data["1. open"]),
                high=float(day_data["2. high"]),
                low=float(day_data["3. low"]),
                close=float(day_data["4. close"]),
                volume=int(day_data["5. volume"])
            ))
        return {"series": series}

    def obtenir_historique(self, symbole, nb_jours):
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        dates = [(datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(nb_jours)]
        records = self.repo.lire_historique_par_jours(symbole, dates)
        return self.schema.dump(records, many=True)

    def obtenir_historique_periode(self, symbole, date_debut, date_fin):
        records = self.repo.lire_historique_sur_periode(symbole, date_debut, date_fin)
        return self.schema.dump(records, many=True)

    def calculer_cout_achat(self, symbole, date, quantite, code_devise):
        """
        Calcule le coût d'achat d'une action pour un symbole donné, à une date spécifique.
        """
        action = self.repo.chercher_par_symbole_et_date(symbole, date)
        if not action:
            # Essayer de récupérer et sauvegarder depuis l'API
            self.obtenir_action(symbole, date)
            action = self.repo.chercher_par_symbole_et_date(symbole, date)
            if not action:
                # Fallback: utiliser la dernière date disponible
                latest_dates = self.repo.get_all_dates_for_symbol(symbole)
                if latest_dates:
                    latest_date = sorted(latest_dates, reverse=True)[0]
                    action = self.repo.chercher_par_symbole_et_date(symbole, latest_date)
                    if action:
                        date = latest_date  # Mettre à jour la date utilisée
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
        # Conversion de la devise
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