import os
import requests
from datetime import datetime
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
        return datetime.utcnow().strftime("%Y-%m-%d")

    def obtenir_devise(self, nom):
        """
        Récupère la devise pour aujourd'hui, depuis la base ou l'API si besoin.
        """
        date_maj = self._get_today_str()
        devise = self.repo.chercher_par_nom_et_date(nom, date_maj)
        if devise:
            return self.schema.dump(devise)

        # Si non trouvée, requête à l'API ExchangeRate (on ne stocke que la devise de base)
        url = f"{self.api_url}/{self.api_key}/latest/{self.base_currency}"
        response = requests.get(url)
        if response.status_code != 200:
            return {"message": "Erreur lors de la récupération des taux de change."}, 502

        data = response.json()
        if data.get("result") != "success":
            return {"message": "Réponse API ExchangeRate invalide."}, 502

        conversion_rates = data.get("conversion_rates", {})
        date_maj = data.get("time_last_update_utc", self._get_today_str())[:10]
        base_code = data.get("base_code", self.base_currency)

        # On ne stocke que la devise de base
        d = Devise(
            nom=base_code,
            taux=1.0,
            date_maj=date_maj,
            base_code=base_code,
            conversion_rates=conversion_rates
        )
        self.repo.creer(d)

        # Retourner la devise demandée (si c'est la base, sinon on la reconstitue à partir des taux)
        if nom == base_code:
            return self.schema.dump(d)
        if nom in conversion_rates:
            devise = Devise(
                nom=nom,
                taux=conversion_rates[nom],
                date_maj=date_maj,
                base_code=base_code,
                conversion_rates=conversion_rates
            )
            return self.schema.dump(devise)
        return {"message": "Devise non trouvée après mise à jour."}, 404

    def convertir(self, code_source, code_cible, montant):
        """
        Calcule la conversion d'un montant d'une devise à une autre.
        """
        if not isinstance(montant, (int, float)) or montant < 0:
            return {"message": "Montant invalide."}, 400

        date_maj = self._get_today_str()
        devise_base = self.repo.chercher_par_nom_et_date(self.base_currency, date_maj)
        if not devise_base:
            self.obtenir_devise(self.base_currency)
            devise_base = self.repo.chercher_par_nom_et_date(self.base_currency, date_maj)
            if not devise_base:
                return {"message": "Taux de change non disponible."}, 404

        rates = devise_base.conversion_rates
        if code_source not in rates or code_cible not in rates:
            return {"message": "Devise source ou cible non trouvée."}, 404

        montant_converti = montant / rates[code_source] * rates[code_cible]
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