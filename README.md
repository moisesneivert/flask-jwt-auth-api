# Flask JWT Authentication API

Production-oriented REST API demonstrating secure user authentication and authorization with Flask, JWT access/refresh tokens, SQLAlchemy, migrations, rate limiting, automated tests and CI.

Flask REST API with JWT access and refresh tokens, token rotation, revocation, SQLAlchemy, tests, Docker and CI.

## Highlights

- User registration and normalized unique emails
- Password hashing with Werkzeug `scrypt`
- Short-lived access tokens and rotating refresh tokens
- Fresh-token protection for sensitive operations
- Individual token revocation and logout from all sessions
- Token versioning to invalidate all existing tokens
- Temporary account lock after repeated failed logins
- User and administrator roles
- Profile and password management
- User activation/deactivation by administrators
- Rate limiting on authentication endpoints
- Consistent JSON errors and validation
- Database migrations with Flask-Migrate/Alembic
- SQLite locally and PostgreSQL with Docker Compose
- Pytest coverage threshold of 90%
- Ruff linting and formatting
- GitHub Actions on Python 3.11, 3.12 and 3.13
- VS Code tasks, debugging and extension recommendations
- OpenAPI document and Postman collection

## Architecture

```text
app/
├── auth/          # registration, login, refresh and logout
├── health/        # service and database health checks
├── tokens/        # revoked-token persistence
├── users/         # model, repository, services and user routes
├── commands.py    # administrative CLI commands
├── config.py      # environment-specific configuration
├── errors.py      # JSON error handlers
├── extensions.py  # Flask extension instances
└── jwt_callbacks.py
```

## API routes

| Method | Route | Authentication | Purpose |
|---|---|---|---|
| GET | `/health` | Public | Check API and database |
| POST | `/api/v1/auth/register` | Public | Register user |
| POST | `/api/v1/auth/login` | Public | Issue access and refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh token | Rotate refresh token and issue new token pair |
| POST | `/api/v1/auth/logout` | Access or refresh | Revoke current token |
| POST | `/api/v1/auth/logout-all` | Fresh access | Invalidate all user tokens |
| GET | `/api/v1/users/me` | Access | Get current profile |
| PATCH | `/api/v1/users/me` | Fresh access | Update profile |
| PATCH | `/api/v1/users/me/password` | Fresh access | Change password |
| GET | `/api/v1/users` | Admin | List users |
| GET | `/api/v1/users/{id}` | Admin | Get user |
| PATCH | `/api/v1/users/{id}/status` | Fresh admin | Activate/deactivate user |

## Local setup — Windows PowerShell

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m flask --app run.py db upgrade
python run.py
```

Generate strong secrets before running outside a local study environment:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Create an administrator

```powershell
python -m flask --app run.py create-admin
```

## Example workflow

Register:

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "Moisés Neivert",
  "email": "moises@example.com",
  "password": "SecurePass1!"
}
```

Login:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "moises@example.com",
  "password": "SecurePass1!"
}
```

Protected request:

```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

## Tests and code quality

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Automatic formatting:

```powershell
python -m ruff check . --fix
python -m ruff format .
```

## Docker with PostgreSQL

```powershell
docker compose up --build
```

The API is available at `http://127.0.0.1:5000`.

## Documentation

- `docs/openapi.yaml`
- `docs/Flask-JWT-Auth-API.postman_collection.json`
- `docs/GUIDE.pt-BR.md`

## Security notes

- Replace development secrets before deployment.
- Serve the API only through HTTPS in production.
- Use Redis or another shared persistent backend for rate limiting when running multiple instances.
- Rotate secrets using a controlled migration strategy.
- Add email verification and a time-limited password-reset flow before using this as a public identity system.
- Flask REST API with JWT access and refresh tokens, token rotation, revocation, role-based access control, tests, Docker and CI.

## License

MIT
