import logging
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
        # Correction ici pour utiliser des noms de variables cohérents
        self.api_url_profile = os.getenv("FMP_PROFILE_API_URL", "https://financialmodelingprep.com/api/v3/profile")
        self.api_url_historical = os.getenv("FMP_HISTORICAL_API_URL", "https://financialmodelingprep.com/api/v3/historical-price-full")


    def _get_today_str(self):
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def obtenir_societe(self, symbole):
        """
        Récupère les informations d'une société pour aujourd'hui.
        1. Cherche dans la base par symbole et date_maj.
        2. Si non trouvée, requête à l'API FMP, sauvegarde et retourne.
        Retourne None si la société n'est pas trouvée par l'API FMP.
        """
        date_maj = self._get_today_str()
        societe = self.repo.chercher_par_symbole_et_date(symbole, date_maj)
        if societe:
            return self.schema.dump(societe)

        # Utilisation de la variable correcte pour l'URL de profil
        url = f"{self.api_url_profile}/{symbole}?apikey={self.api_key}"

        try:
            response = requests.get(url)
            
            if response.status_code == 404:
                return None 

            response.raise_for_status() 

            data = response.json()

            if not data or not isinstance(data, list) or not data[0].get("symbol"):
                if isinstance(data, dict) and "message" in data:
                    message_lower = data["message"].lower()
                    if "invalid api call" in message_lower or "symbol not found" in message_lower:
                        return None 

                return None 

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

        except requests.exceptions.HTTPError as e:
            logging.error(f"Erreur HTTP lors de la récupération des informations de société pour {symbole}: {e.response.status_code} - {e.response.text}")
            return {"message": f"Erreur de l'API externe (HTTP {e.response.status_code})."}, e.response.status_code
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur de connexion à l'API FMP pour {symbole}: {e}")
            return {"message": "Erreur de connexion à l'API externe."}, 503 
        except ValueError as e: 
            logging.error(f"Erreur de traitement de la réponse JSON de l'API FMP pour {symbole}: {e}")
            return {"message": "Erreur de traitement de la réponse de l'API externe."}, 500
        except Exception as e:
            logging.error(f"Une erreur inattendue est survenue dans obtenir_societe pour {symbole}: {e}", exc_info=True)
            return {"message": "Une erreur interne du service est survenue."}, 500

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
            # Correction ici pour gérer les 'None' retournés par obtenir_societe
            if res and isinstance(res, dict) and "symbole" in res:
                results.append(res)
        return results