import os

class Config:
    MONGODB_URI = os.getenv("MONGODB_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"