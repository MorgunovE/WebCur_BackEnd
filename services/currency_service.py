import os
import requests
from datetime import datetime, UTC, timedelta
from repositories.currency_repository import CurrencyRepository
from models.currency import Devise
from schemas.currency import DeviseSchema
from marshmallow import ValidationError

class CurrencyService:
    """
    Service métier pour la gestion des devises et des favoris.
    """

    def __init__(self):
        self.repo = CurrencyRepository()
        self.schema = DeviseSchema()
        self.api_key = os.getenv("API_KEY_ERAPI")
        self.base_currency = os.getenv("BASE_CURRENCY")
        self.api_url = os.getenv("EXCHANGERATE_API_URL")

    def _get_today_str(self):
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _parse_api_date(self, api_date_str):
        # Example: "Sat, 07 Jun 2025 00:00:01 +0000"
        try:
            dt = datetime.strptime(api_date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            # Si le format est incorrect, on retourne la date d'aujourd'hui
            return self._get_today_str()

    def obtenir_devise(self, nom):
        """
        Récupère la devise pour aujourd'hui, depuis la base ou l'API si besoin.
        """
        date_maj = self._get_today_str()
        devise = self.repo.chercher_par_nom_et_date(nom, date_maj)
        if devise:
            return self.schema.dump(devise)

        # Si non trouvée, requête à l'API ExchangeRate
        url = f"{self.api_url}/{self.api_key}/latest/{nom}"
        response = requests.get(url)
        if response.status_code != 200:
            return {"message": "Erreur lors de la récupération des taux de change."}, 502

        data = response.json()
        if data.get("result") != "success":
            return {"message": "Réponse API ExchangeRate invalide."}, 502

        conversion_rates = data.get("conversion_rates", {})
        api_date_str = data.get("time_last_update_utc", "")
        date_maj = self._parse_api_date(api_date_str)
        base_code = data.get("base_code", self.base_currency)

        # Vérifier à nouveau si la devise existe (race condition possible)
        devise = self.repo.chercher_par_nom_et_date(base_code, date_maj)
        if devise:
            return self.schema.dump(devise)

        # Ajouter la devise à la base de données
        devise = Devise(
            nom=base_code,
            taux=1.0,
            date_maj=date_maj,
            base_code=base_code,
            conversion_rates=conversion_rates
        )
        self.repo.creer(devise)
        return self.schema.dump(devise)

    def obtenir_historique(self, nom, nb_jours):
        """
        Récupère l'historique des taux de change d'une devise pour les derniers nb_jours jours.
        """
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        dates = [(datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(nb_jours)]
        records = self.repo.lire_historique_par_nom(nom, dates)
        return self.schema.dump(records, many=True)

    def obtenir_historique_periode(self, nom, date_debut, date_fin):
        """
        Récupère l'historique des taux de change d'une devise pour une période donnée
        """
        records = self.repo.lire_historique_sur_periode(nom, date_debut, date_fin)
        return self.schema.dump(records, many=True)


    def convertir(self, code_source, code_cible, montant):
        """
        Calcule la conversion d'un montant d'une devise à une autre.
        """
        if not isinstance(montant, (int, float)) or montant < 0:
            return {"message": "Montant invalide."}, 400

        date_maj = self._get_today_str()
        devise = self.repo.chercher_par_nom_et_date(code_source, date_maj)
        if not devise:
            self.obtenir_devise(code_source)
            devise = self.repo.chercher_par_nom_et_date(code_source, date_maj)
            if not devise:
                return {"message": "Taux de change non disponible."}, 404

        rates = devise.conversion_rates
        if code_cible not in rates:
            return {"message": "Devise source ou cible non trouvée."}, 404

        montant_converti = montant * rates[code_cible]
        return {
            "code_source": code_source,
            "code_cible": code_cible,
            "montant_source": montant,
            "montant_converti": round(montant_converti, 4),
            "taux_source": rates[code_source],
            "taux_cible": rates[code_cible],
            "date_maj": date_maj
        }

    def ajouter_favori(self, user_id, nom_devise):
        self.repo.ajouter_favori(user_id, nom_devise)
        return {"message": "Devise ajoutée aux favoris."}

    def supprimer_favori(self, user_id, nom_devise):
        self.repo.supprimer_favori(user_id, nom_devise)
        return {"message": "Devise supprimée des favoris."}

    def lire_favoris(self, user_id):
        favoris = self.repo.lire_favoris_par_utilisateur(user_id)
        return {"favoris": favoris}