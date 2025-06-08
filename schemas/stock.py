from marshmallow import Schema, fields, validate

class ActionSchema(Schema):
    """
    Schéma de sérialisation et de validation pour le modèle Action (action d'une société).
    """
    id = fields.Str(dump_only=True)
    symbole = fields.Str(required=True, validate=validate.Length(min=1, max=10))  # Symbole de l'action, ex: "AAPL"
    date = fields.Str(required=True)  # Date de la cotation, ex: "2025-06-05"
    open = fields.Float(required=True)  # Prix d'ouverture
    high = fields.Float(required=True)  # Prix le plus haut
    low = fields.Float(required=True)   # Prix le plus bas
    close = fields.Float(required=True) # Prix de clôture
    volume = fields.Int(required=True)  # Volume échangé