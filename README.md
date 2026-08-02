# TAPSI

Restaurant Management System for Tapsilogans, Karinderyas, and Small Philippine Food Businesses.

## Quick Start

Requires Python 3.12 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and register the first restaurant owner.

**Notes:**
- SQLite is used for local development; PostgreSQL planned for production.
- Password-reset emails appear in the server terminal during development.

## Module Status

| Module | Description | Status |
|--------|-------------|--------|
| **Module 1** | Authentication & User Profile | ✅ Complete |
| **Module 2** | Restaurant & User Management | ✅ Complete |
| Module 3 | Dashboard | 🔲 Pending |
| Module 4 | Menu Management | 🔲 Pending |
| Module 5 | Inventory Management | 🔲 Pending |
| Module 6 | Supplier Management | 🔲 Pending |
| Module 7 | Purchase Orders | 🔲 Pending |
| Module 8 | Recipe Management | 🔲 Pending |
| Module 9 | Order Management | 🔲 Pending |
| Module 10 | Table Management | 🔲 Pending |
| Module 11 | Payments & Receipts | 🔲 Pending |
| Module 12 | Expense Management | 🔲 Pending |
| Module 13 | Employee Management | 🔲 Pending |
| Module 14 | Reports | 🔲 Pending |
| Module 15 | Daily Closing | 🔲 Pending |
| Module 16 | Notifications | 🔲 Pending |
| Module 17 | Audit Logs | 🔲 Pending |

## Module 1: Authentication & User Profile — Complete

All functional requirements (FR-001 to FR-009) implemented:

- JWT authentication (15-min access, 7-day refresh with rotation) — FR-001
- Generic error messages (no account enumeration) — FR-002
- Account lockout after 5 failed attempts (15 min) — FR-003
- Logout with refresh token blacklisting — FR-004
- Password reset via email (1-hour expiry) — FR-005
- Password change with session invalidation — FR-006
- Password policy (10+ chars, letter+number, common password denylist) — FR-007
- Profile update (name, phone, avatar) with email re-verification — FR-008
- Login audit logging (timestamp, IP, user agent) — FR-009
- 35 tests covering registration, login, lockout, JWT, password flows, profile, and validation

## Module 2: Restaurant & User Management — Complete

All functional requirements (FR-010 to FR-017) implemented:

- Restaurant registration with Owner account — FR-010
- Owner-only restaurant settings (name, address, TIN, VAT, receipt footer) — FR-011
- Staff account creation (Owner: all roles; Manager: Cashier/Kitchen only) — FR-012
- Forced password change on first login — FR-013
- Role change by Owner with audit trail — FR-014
- Soft deletes with `is_deleted`/`deleted_at` fields — FR-015
- Last-active Owner protection — cannot deactivate the sole Owner — FR-016
- Tenant isolation via restaurant FK on all queries — FR-017
- Staff edit, admin password reset, `StaffAudit` logging
- 31 tests covering staff CRUD, roles, deactivation, settings, and validation

## JWT API

Template pages use Django sessions. JSON clients use:

- `POST /accounts/api/token/` — `{"email": "...", "password": "..."}`
- `POST /accounts/api/token/refresh/` — `{"refresh": "..."}`
- `POST /accounts/api/token/logout/` — `{"refresh": "..."}`

## Tech Stack

- **Backend:** Django 6.0, Python 3.14
- **Database:** SQLite (dev), PostgreSQL (planned)
- **Frontend:** Django templates with Inter font, green design system
- **Auth:** JWT (custom implementation), session auth for web
- **Deployment:** Azure App Service

## Design System

The project includes a design guide in `design-guide/` with:

- `tokens.css` — Colors, typography, spacing, shadows
- `components.css` — Buttons, cards, badges, avatars, tables
- `README.md` — Full documentation with usage examples

## Deployment

For Azure App Service, set:
- `DJANGO_ALLOWED_HOSTS` — Comma-separated list of hostnames
- `DJANGO_CSRF_TRUSTED_ORIGINS` — Comma-separated HTTPS origins

Run `python manage.py collectstatic --noinput` during deployment.

### Gaps (SRS Spec vs Current Implementation)

| Area | SRS Spec | Current | Action Needed |
|------|----------|---------|---------------|
| API Framework | Django REST Framework | Django views + custom JWT | Add DRF for API layer |
| Frontend | React + Vite SPA | Django templates | Build React frontend |
| Database | PostgreSQL 16 on AWS RDS | SQLite | Migrate to PostgreSQL |
| Tenant Isolation | DRF permission classes, tenant-aware base queryset | Restaurant FK on models | Add DRF permission classes |
| Infrastructure | AWS (EC2, RDS, S3, CloudFront) | Azure App Service | Migrate to AWS (or keep Azure) |
