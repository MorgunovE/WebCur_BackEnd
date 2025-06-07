from typing import Dict, Any

class Devise:
    """
    Modèle de devise pour la base de données MongoDB.
    """
    def __init__(self, nom: str, taux: float, date_maj: str, base_code: str, conversion_rates: Dict[str, float], _id=None):
        self.id = str(_id) if _id else None
        self.nom = nom  # Code de la devise (ex: "EUR")
        self.taux = taux  # Taux de change par rapport à la base
        self.date_maj = date_maj  # Date de mise à jour (ex: "2025-06-06")
        self.base_code = base_code  # Code de la devise de base (ex: "USD")
        self.conversion_rates = conversion_rates  # Dictionnaire des taux de conversion

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Devise en dictionnaire pour MongoDB.
        """
        data = {
            "nom": self.nom,
            "taux": self.taux,
            "date_maj": self.date_maj,
            "base_code": self.base_code,
            "conversion_rates": self.conversion_rates
        }
        if self.id:
            data["_id"] = self.id
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Devise":
        """
        Crée un objet Devise à partir d'un dictionnaire MongoDB.
        """
        return Devise(
            nom=data.get("nom"),
            taux=data.get("taux"),
            date_maj=data.get("date_maj"),
            base_code=data.get("base_code"),
            conversion_rates=data.get("conversion_rates", {}),
            _id=data.get("_id")
        )