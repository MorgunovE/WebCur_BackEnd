import os
from datetime import timedelta


class Config:
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DBNAME = os.getenv("MONGODB_DBNAME")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES"))
    )