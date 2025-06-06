from marshmallow import Schema, fields

class UtilisateurSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True)
    mot_de_passe = fields.Str(required=True, load_only=True)
    nom_utilisateur = fields.Str(required=True)