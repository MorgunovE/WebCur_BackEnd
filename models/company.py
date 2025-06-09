from typing import Dict, Any

class Societe:
    """
    Modèle de société pour la base de données MongoDB.
    Représente les informations détaillées d'une société cotée en bourse.
    """

    def __init__(
        self,
        symbole: str,
        date_maj: str,
        companyName: str,
        price: float = None,
        marketCap: float = None,
        beta: float = None,
        lastDividend: float = None,
        range_: str = None,
        change: float = None,
        changePercentage: float = None,
        volume: int = None,
        averageVolume: int = None,
        currency: str = None,
        cik: str = None,
        isin: str = None,
        cusip: str = None,
        exchangeFullName: str = None,
        exchange: str = None,
        industry: str = None,
        website: str = None,
        description: str = None,
        ceo: str = None,
        sector: str = None,
        country: str = None,
        fullTimeEmployees: str = None,
        phone: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        zip_: str = None,
        image: str = None,
        ipoDate: str = None,
        defaultImage: bool = None,
        isEtf: bool = None,
        isActivelyTrading: bool = None,
        isAdr: bool = None,
        isFund: bool = None,
        _id=None
    ):
        self.id = str(_id) if _id else None
        self.symbole = symbole
        self.date_maj = date_maj
        self.companyName = companyName
        self.price = price
        self.marketCap = marketCap
        self.beta = beta
        self.lastDividend = lastDividend
        self.range = range_
        self.change = change
        self.changePercentage = changePercentage
        self.volume = volume
        self.averageVolume = averageVolume
        self.currency = currency
        self.cik = cik
        self.isin = isin
        self.cusip = cusip
        self.exchangeFullName = exchangeFullName
        self.exchange = exchange
        self.industry = industry
        self.website = website
        self.description = description
        self.ceo = ceo
        self.sector = sector
        self.country = country
        self.fullTimeEmployees = fullTimeEmployees
        self.phone = phone
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip_
        self.image = image
        self.ipoDate = ipoDate
        self.defaultImage = defaultImage
        self.isEtf = isEtf
        self.isActivelyTrading = isActivelyTrading
        self.isAdr = isAdr
        self.isFund = isFund

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Societe en dictionnaire pour MongoDB.
        """
        data = {
            "symbole": self.symbole,
            "date_maj": self.date_maj,
            "companyName": self.companyName,
            "price": self.price,
            "marketCap": self.marketCap,
            "beta": self.beta,
            "lastDividend": self.lastDividend,
            "range": self.range,
            "change": self.change,
            "changePercentage": self.changePercentage,
            "volume": self.volume,
            "averageVolume": self.averageVolume,
            "currency": self.currency,
            "cik": self.cik,
            "isin": self.isin,
            "cusip": self.cusip,
            "exchangeFullName": self.exchangeFullName,
            "exchange": self.exchange,
            "industry": self.industry,
            "website": self.website,
            "description": self.description,
            "ceo": self.ceo,
            "sector": self.sector,
            "country": self.country,
            "fullTimeEmployees": self.fullTimeEmployees,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "image": self.image,
            "ipoDate": self.ipoDate,
            "defaultImage": self.defaultImage,
            "isEtf": self.isEtf,
            "isActivelyTrading": self.isActivelyTrading,
            "isAdr": self.isAdr,
            "isFund": self.isFund
        }
        if self.id:
            data["_id"] = self.id
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Societe":
        """
        Crée un objet Societe à partir d'un dictionnaire MongoDB.
        """
        return Societe(
            symbole=data.get("symbole"),
            date_maj=data.get("date_maj"),
            companyName=data.get("companyName"),
            price=data.get("price"),
            marketCap=data.get("marketCap"),
            beta=data.get("beta"),
            lastDividend=data.get("lastDividend"),
            range_=data.get("range"),
            change=data.get("change"),
            changePercentage=data.get("changePercentage"),
            volume=data.get("volume"),
            averageVolume=data.get("averageVolume"),
            currency=data.get("currency"),
            cik=data.get("cik"),
            isin=data.get("isin"),
            cusip=data.get("cusip"),
            exchangeFullName=data.get("exchangeFullName"),
            exchange=data.get("exchange"),
            industry=data.get("industry"),
            website=data.get("website"),
            description=data.get("description"),
            ceo=data.get("ceo"),
            sector=data.get("sector"),
            country=data.get("country"),
            fullTimeEmployees=data.get("fullTimeEmployees"),
            phone=data.get("phone"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_=data.get("zip"),
            image=data.get("image"),
            ipoDate=data.get("ipoDate"),
            defaultImage=data.get("defaultImage"),
            isEtf=data.get("isEtf"),
            isActivelyTrading=data.get("isActivelyTrading"),
            isAdr=data.get("isAdr"),
            isFund=data.get("isFund"),
            _id=data.get("_id")
        )