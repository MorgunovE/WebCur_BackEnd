from marshmallow import Schema, fields, validate

class SocieteSchema(Schema):
    """
    Schéma de sérialisation et de validation pour le modèle Société (informations sur la société).
    """
    id = fields.Str(dump_only=True)  # ID MongoDB
    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=10))  # Symbole de l'action, ex: "AAPL"
    date = fields.Str(required=True)  # Date de mise à jour, ex: "2025-06-08"
    price = fields.Float()  # Prix actuel de l'action
    marketCap = fields.Float()  # Capitalisation boursière
    beta = fields.Float()
    lastDividend = fields.Float()
    range = fields.Str()  # Plage de prix sur la période
    change = fields.Float()
    changePercentage = fields.Float()
    volume = fields.Int()
    averageVolume = fields.Int()
    companyName = fields.Str()  # Nom complet de la société
    currency = fields.Str(validate=validate.Length(equal=3))
    cik = fields.Str()
    isin = fields.Str()
    cusip = fields.Str()
    exchangeFullName = fields.Str()
    exchange = fields.Str()
    industry = fields.Str()
    website = fields.Str()
    description = fields.Str()
    ceo = fields.Str()
    sector = fields.Str()
    country = fields.Str()
    fullTimeEmployees = fields.Str()
    phone = fields.Str()
    address = fields.Str()
    city = fields.Str()
    state = fields.Str()
    zip = fields.Str()
    image = fields.Str()
    ipoDate = fields.Str()
    defaultImage = fields.Bool()
    isEtf = fields.Bool()
    isActivelyTrading = fields.Bool()
    isAdr = fields.Bool()
    isFund = fields.Bool()