# TAPSI

Initial server-rendered Django implementation of the TAPSI restaurant-management system.

## Quick start

Requires Python 3.12 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and register the first restaurant owner. SQLite is used for local development; the database configuration is isolated in `config/settings.py` for a later PostgreSQL deployment.

During local development, password-reset emails appear in the server terminal. Use the single-line URL printed beneath the message as `Open this link in your browser:`. SMTP/SES settings replace this development backend in deployment.

## Initial scope

- Atomic restaurant + owner registration
- Email-based custom user model with Owner, Manager, Cashier, and Kitchen roles
- Login, logout, password-policy validation, and first-login password change
- Role-aware dashboard and owner staff-user creation

## JWT API authentication

Template pages use Django sessions. JSON clients use the SRS authentication endpoints:

- `POST /accounts/api/token/` — JSON body: `{"email": "...", "password": "..."}`
- `POST /accounts/api/token/refresh/` — JSON body: `{"refresh": "..."}`
- `POST /accounts/api/token/logout/` — JSON body: `{"refresh": "..."}`

Access tokens expire in 15 minutes. Refresh tokens expire in 7 days, rotate on refresh, are revoked on logout, and are all revoked after a password change or reset.

## Deployment configuration

For Azure App Service, set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of the App Service hostname and any custom domains. Set `DJANGO_CSRF_TRUSTED_ORIGINS` to the corresponding comma-separated HTTPS origins. The currently deployed Azure hostname is included as a safe default; custom domains must be explicitly added.

Static files are collected during deployment and served by WhiteNoise. Run `python manage.py collectstatic --noinput` in any custom Azure deployment command.

The SRS plans later modules (menu, inventory, orders, payments, and reporting) on top of this tenant-aware foundation.
