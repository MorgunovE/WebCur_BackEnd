class Action:
    """
    Modèle d'action d'une société pour MongoDB.
    """
    def __init__(self, symbole, date, open, high, low, close, volume, _id=None):
        self.id = str(_id) if _id else None
        self.symbole = symbole  # Symbole de l'action, ex: "AAPL"
        self.date = date        # Date de la cotation, ex: "2025-06-05"
        self.open = open        # Prix d'ouverture
        self.high = high        # Prix le plus haut
        self.low = low          # Prix le plus bas
        self.close = close      # Prix de clôture
        self.volume = volume    # Volume échangé

    def to_dict(self):
        """
        Convertit l'objet Action en dictionnaire pour MongoDB.
        """
        data = {
            "symbole": self.symbole,
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }
        if self.id:
            data["_id"] = self.id
        return data

    @staticmethod
    def from_dict(data):
        """
        Crée un objet Action à partir d'un dictionnaire MongoDB.
        """
        return Action(
            symbole=data.get("symbole"),
            date=data.get("date"),
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            close=data.get("close"),
            volume=data.get("volume"),
            _id=data.get("_id")
        )