from marshmallow import Schema, fields, validate

class DeviseSchema(Schema):
    """
    Schéma de sérialisation et de validation pour le modèle Devise.
    """
    id = fields.Str(dump_only=True)
    nom = fields.Str(required=True, validate=validate.Length(equal=3))  # Code devise, ex: "EUR"
    taux = fields.Float(required=True)  # Taux de change par rapport à la base
    date_maj = fields.Str(required=True)  # Date de mise à jour, ex: "2025-06-06"
    base_code = fields.Str(required=True, validate=validate.Length(equal=3))  # Code devise de base, ex: "USD"
    conversion_rates = fields.Dict(keys=fields.Str(), values=fields.Float(), required=True)  # Taux de conversion