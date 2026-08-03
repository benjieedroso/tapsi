# AGENTS.md

TAPSI — Restaurant Management System (Django 6.0, Python 3.14) for Philippine food businesses. Source of truth for requirements: `TAPSI_SRS_v2.0.docx` (17 modules, FR-001+). Frontend is **Django templates** (not the React SPA the SRS describes — this is an accepted deviation so far). Deployed on Azure App Service (`tapsidaily.online`).

## Commands

All commands run from repo root. Venv is `.venv\Scripts\python.exe` — plain `python` is a *different* interpreter without Django installed.

```powershell
.\.venv\Scripts\python.exe manage.py test accounts   # 66 tests, ~50s
.\.venv\Scripts\python.exe manage.py test menu       # 54 tests, ~37s
.\.venv\Scripts\python.exe manage.py test inventory  # 38 tests, ~45s
.\.venv\Scripts\python.exe manage.py test            # full suite 270 tests, ~175s
.\.venv\Scripts\python.exe manage.py makemigrations <app>
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

- **No pytest, no ruff, no lint/typecheck tooling is installed.** `manage.py test` is the only verification; there is no lint step.
- Shell is Windows PowerShell 5.1: no `&&`; chain with `;` or `if ($?)`. `tail`/`grep` don't exist — use `Select-Object -Last N`.
- Tests print to stderr in PowerShell as red "errors" even when passing — ignore unless you see `FAILED`/`ERROR:` lines.
- Test DB is in-memory shared SQLite; migrations for all apps run automatically per suite.

## Architecture

- `config/` — Django project (settings, root urls). Dashboard mounted at `/`.
- `accounts/` — auth (Module 1) + restaurant/staff management (Module 2) + dashboard view (FR-020..026): `models.py` (Restaurant, User, StaffAudit, AuthenticationAudit, RefreshToken), `forms.py`, `views.py`, `services.py` (custom JWT — no DRF), `validators.py`.
- `menu/` — Menu Management (Module 4): Category, MenuItem, MenuItemPriceHistory, AddOn, MenuItemAddOn.
- `inventory/` — Inventory (Module 5): Ingredient, InventoryTransaction (append-only ledger, `delete()` raises), LowStockAlert. Stock is derived from the ledger's latest `resulting_balance` (`Ingredient.current_stock`); `InventoryTransaction.save()` computes the balance, rejects negative stock (FR-044), applies weighted-average cost on PURCHASE (FR-047), and reconciles low-stock alerts (FR-045).
- `suppliers/` — Suppliers (6) + Purchase Orders (7): Supplier, SupplierPayment, PurchaseOrder (number `PO-{year}-{seq:05d}`), PurchaseOrderItem; `po_receive()` writes PURCHASE ledger entries.
- `recipes/` — Recipes (8): Recipe (one default per menu item), RecipeIngredient; completion/cancellation stock math lives in `orders/services.py` (`consume_recipe_stock`/`restore_recipe_stock`).
- `orders/` — Orders (9), Tables (10), Payments & Receipts (11): DiningTable, Order (status machine via `transition_to`, `recompute_totals` for VAT/discount math, `apply_discount` w/ >10% approval), OrderItem, OrderItemAddon, OrderStatusHistory, Payment (sequential receipt_no), Refund; `services.py` has `record_payment`, `settle_order`, refund + stock services. Add-ons relate via `item.addons` (NOT `orderitemaddon_set`).
- `expenses/` — Expenses (12): Expense w/ approval threshold; closed-day lock via `closing.models.is_day_closed()`.
- `employees/` — Employees (13): Employee (linked to User, salary visible O/M only), Attendance.
- `reports/` — Reports (14): daily/monthly sales, P&L, inventory, product mix, purchases, tax summary + CSV exports; figures from COMPLETED orders only.
- `closing/` — Daily Closing (15): DailyClosing (one per restaurant+date, `is_locked()`, expected cash = float + cash sales − cash refunds − cash expenses, ±₱100 variance w/ note, owner-only reopen).
- `notifications/` — Notifications (16): Notification; `services.py` `notify`/`notify_role` + `Notifier` facade (order_placed, order_completed, order_cancelled, large_discount, refund_issued, po_received); 90-day purge.
- `audit_logs/` — Audit Logs (17): AuditLog (append-only, `delete()` raises), `services.log`/`log_denied`.
- `templates/` — shared `base.html` role-based navbar + `templates/<app>/` per module + `dashboard.html` (live FR-020..024 widgets).
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
10. `Dashboard` view (`accounts/views.py:dashboard`) lazily imports menu/orders/inventory/expenses/closing models inside the function (avoids circular import) and must handle users with `restaurant=None` (test users). It queries OrderItem add-ons via `item.addons` (related name is `addons`, NOT `orderitemaddon_set` — prefetch `"addons"`).
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

Modules 1–17 complete (FR-001..009, 010..017, 020..026, 030..037, 040..047, 050..053, 060..065, 070..074, 080..093, 100..103, 110..113, 120..124, 130..139, 140..145, 150..153, 160..163). Full suite: 270 tests green.

Known remaining gaps (accepted so far): FR-025 dashboard auto-refresh (S priority, server-rendered templates); audit logging not yet wired into every event FR-160 lists (currently staff ops, employee/attendance edits, closings, denied access — orders/payments/expenses use `log_denied` only where wired); DRF API layer + React SPA from the SRS (templates are the accepted deviation); PostgreSQL (SQLite in dev, Azure Database for PostgreSQL planned). The SRS is AWS-agnostic now (updated to Azure: App Service, Front Door, Azure Database for PostgreSQL, Blob Storage, Key Vault, Monitor, Container Registry, Communication Services Email).
