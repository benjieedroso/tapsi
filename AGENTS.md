# AGENTS.md

TAPSI — Restaurant Management System (Django 6.0, Python 3.14) for Philippine food businesses. Source of truth for requirements: `TAPSI_SRS_v2.0.docx` (17 modules, FR-001+). Frontend is **Django templates** (not the React SPA the SRS describes — this is an accepted deviation so far). Deployed on Azure App Service (`tapsidaily.online`).

## Commands

All commands run from repo root. Venv is `.venv\Scripts\python.exe` — plain `python` is a *different* interpreter without Django installed.

```powershell
.\.venv\Scripts\python.exe manage.py test accounts   # 66 tests, ~50s
.\.venv\Scripts\python.exe manage.py test menu       # 54 tests, ~37s
.\.venv\Scripts\python.exe manage.py test inventory  # 38 tests, ~45s
.\.venv\Scripts\python.exe manage.py test            # full suite ~155s
.\.venv\Scripts\python.exe manage.py makemigrations <app>
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

- **No pytest, no ruff, no lint/typecheck tooling is installed.** `manage.py test` is the only verification; there is no lint step.
- Shell is Windows PowerShell 5.1: no `&&`; chain with `;` or `if ($?)`. `tail`/`grep` don't exist — use `Select-Object -Last N`.
- Tests print to stderr in PowerShell as red "errors" even when passing — ignore unless you see `FAILED`/`ERROR:` lines.
- Test DB is in-memory shared SQLite; migrations for all apps run automatically per suite.

## Architecture

- `config/` — Django project (settings, root urls). Dashboard mounted at `/`, plus `accounts/` and `menu/`.
- `accounts/` — auth (Module 1) + restaurant/staff management (Module 2): `models.py` (Restaurant, User, StaffAudit, AuthenticationAudit, RefreshToken), `forms.py`, `views.py`, `services.py` (custom JWT — no DRF), `validators.py`.
- `menu/` — Menu Management (Module 4): Category, MenuItem, MenuItemPriceHistory, AddOn, MenuItemAddOn.
- `inventory/` — Inventory (Module 5): Ingredient, InventoryTransaction (append-only ledger, `delete()` raises), LowStockAlert. Stock is derived from the ledger's latest `resulting_balance` (`Ingredient.current_stock`); `InventoryTransaction.save()` computes the balance, rejects negative stock (FR-044), applies weighted-average cost on PURCHASE (FR-047), and reconciles low-stock alerts (FR-045).
- `templates/` — shared `base.html` navbar + `templates/accounts/`, `templates/menu/`, `dashboard.html`.
- `static/css/design/tokens.css` + `components.css` — design system; `static/css/app.css` — app styles. **All new pages must use these tokens** (`--tapsi-*`, `--gray-*`, `--space-*`, `btn`, `badge`, `table-card`, `field`, `page-heading`). Preview at `design-guide/preview.html`.
- `landing/index.html` — static marketing page; all CTAs point to `https://tapsidaily.online/accounts/register/`.
- Role checks: `user.role in {User.Role.OWNER, User.Role.MANAGER}` for management views (`user_passes_test`); Cashier/Kitchen blocked.

## Critical gotchas (all cost real debugging time)

1. **`restaurant_id` on menu models is a plain `PositiveIntegerField`, NOT a FK.** `Category`, `MenuItem`, `AddOn` have no `restaurant` field — filter with `restaurant_id=<pk>` only. `MenuItem.objects.filter(restaurant=...)` raises FieldError. (`accounts.User` DOES have a real `restaurant` FK.)
2. **Django `CharField.to_python` strips whitespace before field validators run**, so any custom rule (min length, not-blank) must live in `clean_<field>()` methods, not `validators=` args. Follow this pattern in every new form.
3. **`User.username` is synced to email** (email is USERNAME_FIELD). Staff-creation forms must set `user.username = user.email` before save.
4. **`UserManager.get_queryset()` filters `is_deleted=False`** — soft-deleted users are invisible to `objects` unless you use `objects.all()` semantics carefully; hard deletion of users is disallowed (use `User.soft_delete()`).
5. **Price history is auto-created in `MenuItem.save()`** when price changes (no changed_by capture). Don't add another price-history write in forms/views.
6. **Django 6.0 requires the `default` key in `STORAGES`** (set in `config/settings.py`). DEBUG mode uses `StaticFilesStorage`, not `CompressedManifestStaticFilesStorage` — changing this breaks tests (missing manifest).
7. **`ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` read `DJANGO_ALLOWED_HOSTS`/`DJANGO_CSRF_TRUSTED_ORIGINS` env vars** (Azure). Defaults must keep `tapsidaily.online`.
8. **Pillow is required** (`requirements.txt`) — `ImageField` fails system check without it.
9. Password reset emails go to console via `accounts.email_backends.DevelopmentConsoleEmailBackend` (lines kept unwrapped for copy-paste).
10. `Dashboard` view lazily imports `menu.models` inside the function (avoids circular import) and must handle users with `restaurant=None` (test users).
11. Password policy: min 10 chars + letter + number (`PasswordLetterAndNumberValidator`); `must_change_password` flow forces first-login change; `failed_login_count`/`locked_until` implement the 5-strikes/15-min lockout.
12. Phone validation: local `09xxxxxxxxx` = 11 digits, international `+63...` = 12 digits (`accounts/validators.py`). TIN format `XXX-XXX-XXX-XXX`.
13. **ModelForm `required` comes from `blank=`, not `default=`.** Fields like `display_order`, `minimum_stock`, `prep_minutes` are required in forms despite having model defaults — tests and POSTs must send them explicitly.
14. **Django template `|default:` does not short-circuit** — the fallback expression is resolved eagerly. `{{ x.y|default:x.z }}` crashes when `x` is None; guard with `{% if x %}` first.

## Conventions

- New module = new app + `templates/<app>/` + tests in `tests.py` of that app, following `menu/` structure.
- Templates: extend `base.html`, use `.page-heading` + `.table-card` for lists, `.form-card` + `.field` for forms, `.errorlist`/`.field-error` inside `.field`, modals for destructive confirms, `empty-state` rows for zero data.
- Forms: `StyledFormMixin`-style `_apply_classes()` (class="input"), `restaurant_id` kwarg pattern from `menu/forms.py`, labels in Meta.
- Every create/update/delete: tenant-scoped (filter by `restaurant_id`), role-checked server-side, and audit-logged where the SRS requires (StaffAudit for staff ops).
- New models → `makemigrations <app>` then migrate; register in `admin.py`.
- Media uploads: max 5 MB, JPEG/PNG/WebP only (see `validate_avatar`/`validate_menu_image`).

## Status & roadmap

Modules 1–5 complete (FR-001..009, 010..017, 020..026 dashboard shell w/ placeholders until Order modules, 030..037, 040..047). Per SRS Appendix D, next up: Module 6 Suppliers, then Purchase Orders (7), Recipes (8), Orders (9), Tables (10), Payments/Receipts (11), Expenses (12), Employees (13), Reports (14), Daily Closing (15), Notifications (16), Audit (17).

Dashboard FR-020..025 widgets are placeholders — wire them to real queries when Order/Inventory models exist. The SRS is AWS-agnostic now (updated to Azure: App Service, Front Door, Azure Database for PostgreSQL, Blob Storage, Key Vault, Monitor, Container Registry, Communication Services Email).
