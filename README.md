# WebCur API

API RESTful pour la gestion des utilisateurs et l'accès à des données financières, développée avec Flask, MongoDB et JWT. Documentation interactive via Swagger UI.

## Fonctionnalités

- CRUD utilisateurs (création, lecture, mise à jour, suppression)
- Authentification avec JWT
- Documentation Swagger (OpenAPI)
- Sécurité CORS
- Intégration de plusieurs APIs financières (FMP, ExchangeRate, Alpha Vantage)
- Gestion des devises populaires : L'endpoint /devises/populaires retourne toujours les informations à jour pour toutes les devises listées dans la variable d'environnement POPULAR_CURRENCIES (par défaut : USD, EUR, GBP, JPY, CAD). Si une devise n'est pas présente dans la base de données pour aujourd'hui, elle est automatiquement récupérée via l'API ExchangeRate, stockée, puis renvoyée.
- Conversion de devises : L'endpoint /devises/conversion permet de convertir un montant d'une devise à une autre, en utilisant les taux du jour. Si le taux n'est pas en base, il est récupéré à la volée.
- Favoris devises : Les utilisateurs authentifiés peuvent ajouter, lister et supprimer des devises favorites via /devises/favoris.
- Gestion des actions favorites pour les utilisateurs (endpoints `/actions/favoris`)
- Endpoint pour calculer le coût d'achat d'une action avec conversion de devise (`/actions/calculer`)
- Messages d'erreur pour les opérations sur les actions et devises
- Historique des taux de change d'une devise sur une période donnée (`/devises/<nom>/historique`)

## Technologies utilisées

- Python 3.11
- Flask & Flask-RESTful
- Flask-JWT-Extended
- Flask-CORS
- Flask-Swagger-UI
- MongoDB (pymongo)
- Marshmallow (validation)
- Pytest (tests)
- Requests (pour les appels API externes)
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

## Endpoints API disponibles

| Méthode | Endpoint                       | Description                                                                                 | Authentification |
|---------|-------------------------------|---------------------------------------------------------------------------------------------|------------------|
| GET     | `/utilisateurs`               | Liste tous les utilisateurs                                                                 | Non              |
| POST    | `/utilisateurs`               | Crée un nouvel utilisateur                                                                  | Non              |
| GET     | `/utilisateurs/{id}`          | Récupère un utilisateur par ID                                                              | Non              |
| PUT     | `/utilisateurs/{id}`          | Met à jour un utilisateur par ID                                                            | Oui              |
| DELETE  | `/utilisateurs/{id}`          | Supprime un utilisateur par ID                                                              | Oui              |
| POST    | `/connexion`                  | Authentifie un utilisateur et retourne un token JWT                                         | Non              |
| POST    | `/deconnexion`                | Déconnecte l'utilisateur (suppression du token côté client)                                 | Non              |
| GET     | `/devises/{nom}`              | Récupère les informations d'une devise (ex : USD, EUR)                                      | Non              |
| POST    | `/devises/conversion`         | Convertit un montant d'une devise à une autre                                               | Oui              |
| GET     | `/devises/favoris`            | Liste les devises favorites de l'utilisateur                                                | Oui              |
| POST    | `/devises/favoris`            | Ajoute une devise aux favoris                                                               | Oui              |
| DELETE  | `/devises/favoris`            | Supprime une devise des favoris                                                             | Oui              |
| GET     | `/devises/populaires`         | Retourne la liste des devises populaires (toujours à jour, API si besoin)                   | Non              |
| GET     | `/devises/{nom}/historique`   | Récupère l'historique des taux de change d'une devise sur une période ou un nombre de jours | Non              |
| GET     | `/health`                     | Vérifie l'état de santé de l'API                                                            | Non              |
| GET     | `/swagger`                    | Accès à la documentation interactive Swagger                                                | Non              |
| POST    | `/actions/calculer`           | Calculer le coût d'achat d'une action                  | Oui              |
| GET     | `/actions/favoris`            | Liste des actions favorites de l'utilisateur           | Oui              |
| POST    | `/actions/favoris`            | Ajouter une action aux favoris                         | Oui              |
| DELETE  | `/actions/favoris`            | Supprimer une action des favoris                       | Oui              |

---

## Détail des endpoints devises

- **/devises/{nom}** :  
  Retourne les informations complètes d'une devise (code, taux, date, base, conversion_rates).

- **/devises/conversion** :  
  Corps attendu :  
  ```json
  {
    "code_source": "USD",
    "code_cible": "EUR",
    "montant": 100
  }
  ```
  Réponse : montant converti, taux utilisés, date.

- **/devises/favoris** :  
  - `GET` : liste des favoris  
  - `POST` : ajouter une devise  
    Corps : `{ "nom_devise": "EUR" }`  
  - `DELETE` : supprimer une devise  
    Corps : `{ "nom_devise": "EUR" }`

- **/devises/populaires** :  
  Retourne la liste complète des devises populaires, toujours à jour.

---

### Exemple: Ajouter une action aux favoris

```bash
curl -X POST http://localhost:5000/actions/favoris \
  -H "Authorization: Bearer <votre_token_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"symbole": "AAPL"}'
```

### Exemple: Calculer le coût d'achat d'une action

```bash
curl -X POST http://localhost:5000/actions/calculer \
  -H "Authorization: Bearer <votre_token_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"symbole": "AAPL", "date": "2025-06-07", "quantite": 10, "code_devise": "EUR"}'
```

---
## Licence

MIT License © 2025 Morgunov Evgenii