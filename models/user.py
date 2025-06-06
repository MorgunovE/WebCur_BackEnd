class Utilisateur:
    def __init__(self, email, mot_de_passe, nom_utilisateur, _id=None):
        self.id = str(_id) if _id else None
        self.email = email
        self.mot_de_passe = mot_de_passe
        self.nom_utilisateur = nom_utilisateur

    def to_dict(self):
        # Convertit l'objet en dictionnaire pour MongoDB
        data = {
            "email": self.email,
            "mot_de_passe": self.mot_de_passe,
            "nom_utilisateur": self.nom_utilisateur
        }
        if self.id:
            data["_id"] = self.id
        return data

    @staticmethod
    def from_dict(data):
        # Crée un objet Utilisateur à partir d'un dictionnaire MongoDB
        return Utilisateur(
            email=data.get("email"),
            mot_de_passe=data.get("mot_de_passe"),
            nom_utilisateur=data.get("nom_utilisateur"),
            _id=data.get("_id")
        )