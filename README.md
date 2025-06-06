# WebCur API

API RESTful pour la gestion des utilisateurs et l'accès à des données financières, développée avec Flask, MongoDB et JWT. Documentation interactive via Swagger UI.

## Fonctionnalités

- CRUD utilisateurs (création, lecture, mise à jour, suppression)
- Authentification avec JWT
- Documentation Swagger (OpenAPI)
- Sécurité CORS
- Intégration de plusieurs APIs financières (FMP, ExchangeRate, Alpha Vantage)

## Technologies utilisées

- Python 3.11
- Flask & Flask-RESTful
- Flask-JWT-Extended
- Flask-CORS
- Flask-Swagger-UI
- MongoDB (pymongo)
- Marshmallow (validation)
- Pytest (tests)
- Docker

## Configuration

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```
MONGODB_URI=mongodb+srv://<utilisateur>:<motdepasse>@<cluster>.mongodb.net/
MONGODB_DBNAME=WebCur
JWT_SECRET=VotreSecretJWT
FLASK_ENV=development
API_KEY_FMP=VotreCléAPI_FMP
API_KEY_ERAPI=VotreCléAPI_ExchangeRate
API_KEY_AV=VotreCléAPI_AlphaVantage
```

## Documentation API

La documentation interactive est disponible à l'adresse :  
`http://localhost:5000/swagger`

Le fichier OpenAPI est en `static/swagger.json`.

## Lancer le projet en local

1. **Installer Python 3.11 et MongoDB (ou utiliser MongoDB Atlas).**
2. **Installer les dépendances :**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configurer les variables d'environnement dans `.env`.**
4. **Démarrer l'application :**
   ```sh
   flask run
   ```
   ou
   ```sh
   python app.py
   ```
5. **Accéder à l'API :**
   - API : `http://localhost:5000/`
   - Swagger : `http://localhost:5000/swagger`

## Lancer le projet avec Docker

1. **Vérifier que Docker est installé sur votre machine.**
2. **Placer le fichier `.env` à la racine du projet.**
3. **Construire l'image Docker :**
   ```sh
   docker build -t webcur-backend .
   ```
4. **Lancer le conteneur :**
   ```sh
   docker run -p 5000:5000 --env-file .env webcur-backend
   ```
5. **Accéder à l'API et à Swagger comme ci-dessus.**

## Lancer les tests

```sh
pytest
```

## Licence

MIT License © 2025 Morgunov Evgenii