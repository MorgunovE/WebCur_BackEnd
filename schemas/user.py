from marshmallow import Schema, fields

class UtilisateurSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True, description="Adresse e-mail de l'utilisateur")
    mot_de_passe = fields.Str(required=True, load_only=True, description="Mot de passe")
    nom_utilisateur = fields.Str(required=True, description="Nom d'utilisateur")