import os
import requests
from datetime import datetime, UTC, timedelta
from repositories.company_repository import SocieteRepository
from models.company import Societe
from schemas.company import SocieteSchema

class SocieteService:
    """
    Service métier pour la gestion des sociétés cotées en bourse.
    """

    def __init__(self):
        self.repo = SocieteRepository()
        self.schema = SocieteSchema()
        self.api_key = os.getenv("API_KEY_FMP")
        self.api_url = os.getenv("FMP_PROFILE_API_URL", "https://financialmodelingprep.com/stable/profile")

    def _get_today_str(self):
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def obtenir_societe(self, symbole):
        """
        Récupère les informations d'une société pour aujourd'hui.
        1. Cherche dans la base par symbole et date_maj.
        2. Si non trouvée, requête à l'API FMP, sauvegarde et retourne.
        """
        date_maj = self._get_today_str()
        societe = self.repo.chercher_par_symbole_et_date(symbole, date_maj)
        if societe:
            return self.schema.dump(societe)

        # Requête à l'API FMP
        url = f"{self.api_url}?symbol={symbole}&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return {"message": "Erreur lors de la récupération des données société."}, 502

        data = response.json()
        if not data or not isinstance(data, list) or not data[0].get("symbol"):
            return {"message": "Réponse API FMP invalide."}, 502

        societe_data = data[0]
        societe = Societe(
            symbole=societe_data.get("symbol"),
            date_maj=date_maj,
            companyName=societe_data.get("companyName"),
            price=societe_data.get("price"),
            marketCap=societe_data.get("marketCap"),
            beta=societe_data.get("beta"),
            lastDividend=societe_data.get("lastDividend"),
            range_=societe_data.get("range"),
            change=societe_data.get("change"),
            changePercentage=societe_data.get("changePercentage"),
            volume=societe_data.get("volume"),
            averageVolume=societe_data.get("averageVolume"),
            currency=societe_data.get("currency"),
            cik=societe_data.get("cik"),
            isin=societe_data.get("isin"),
            cusip=societe_data.get("cusip"),
            exchangeFullName=societe_data.get("exchangeFullName"),
            exchange=societe_data.get("exchange"),
            industry=societe_data.get("industry"),
            website=societe_data.get("website"),
            description=societe_data.get("description"),
            ceo=societe_data.get("ceo"),
            sector=societe_data.get("sector"),
            country=societe_data.get("country"),
            fullTimeEmployees=societe_data.get("fullTimeEmployees"),
            phone=societe_data.get("phone"),
            address=societe_data.get("address"),
            city=societe_data.get("city"),
            state=societe_data.get("state"),
            zip_=societe_data.get("zip"),
            image=societe_data.get("image"),
            ipoDate=societe_data.get("ipoDate"),
            defaultImage=societe_data.get("defaultImage"),
            isEtf=societe_data.get("isEtf"),
            isActivelyTrading=societe_data.get("isActivelyTrading"),
            isAdr=societe_data.get("isAdr"),
            isFund=societe_data.get("isFund")
        )
        self.repo.creer(societe)
        return self.schema.dump(societe)

    def obtenir_historique(self, symbole, nb_jours):
        """
        Récupère l'historique des informations société pour les derniers nb_jours jours.
        """
        dates = [(datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(nb_jours)]
        records = self.repo.lire_historique_par_symbole(symbole, dates)
        return self.schema.dump(records, many=True)

    def obtenir_historique_periode(self, symbole, date_debut, date_fin):
        """
        Récupère l'historique des informations société pour une période donnée.
        """
        records = self.repo.lire_historique_sur_periode(symbole, date_debut, date_fin)
        return self.schema.dump(records, many=True)

    def obtenir_societes_populaires(self):
        popular = [s.strip().upper() for s in os.getenv("POPULAR_COMPANIES", "AAPL,MSFT,GOOGL,AMZN,TSLA").split(",")]
        results = []
        for symbole in popular:
            res = self.obtenir_societe(symbole)
            if isinstance(res, dict) and "symbole" in res:
                results.append(res)
        return results