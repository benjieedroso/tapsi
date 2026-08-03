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
| **Module 3** | Dashboard | ✅ Complete |
| **Module 4** | Menu Management | ✅ Complete |
| **Module 5** | Inventory Management | ✅ Complete |
| **Module 6** | Supplier Management | ✅ Complete |
| **Module 7** | Purchase Orders | ✅ Complete |
| **Module 8** | Recipe Management | ✅ Complete |
| **Module 9** | Order Management | ✅ Complete |
| **Module 10** | Table Management | ✅ Complete |
| **Module 11** | Payments & Receipts | ✅ Complete |
| **Module 12** | Expense Management | ✅ Complete |
| **Module 13** | Employee Management | ✅ Complete |
| **Module 14** | Reports | ✅ Complete |
| **Module 15** | Daily Closing | ✅ Complete |
| **Module 16** | Notifications | ✅ Complete |
| **Module 17** | Audit Logs | ✅ Complete |

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

## Module 3: Dashboard — Complete

All functional requirements (FR-020 to FR-026) implemented:

- Role-based widget visibility — financial widgets hidden for Cashier — FR-026
- Today's sales summary: gross, net, order count, average order value (business day) — FR-020
- Order status counts: Pending, Preparing, Ready, Completed, Cancelled — FR-021
- Top 5 selling items today and this month (by revenue, then quantity) — FR-022
- Low stock alerts: ingredients at or below minimum stock with quantity and unit — FR-023
- Current-month revenue vs expenses vs profit + 30-day revenue trend chart — FR-024
- Menu items, categories, add-ons counts and role-aware quick action links
- Dashboard template with hero section and grid layout matching design guide

## Module 4: Menu Management — Complete

All functional requirements (FR-030 to FR-037) implemented:

- **Category CRUD** — name (unique per restaurant), display order, active flag — FR-030
- **Menu Item CRUD** — name, description, category, price (≥₱0.00), prep time, availability, image — FR-031
- **Image upload** — JPEG/PNG/WebP, max 5 MB validation — FR-032
- **Add-Ons** — name, price, toggle per menu item — FR-033
- **Toggle availability** — hide/show on order screen without deleting — FR-034
- **Soft delete** — items preserved in historical records — FR-035
- **Price change history** — old price, new price, timestamp — FR-036
- **Menu search & filtering** — search by name, filter by category — FR-037
- Role-based access: Owner and Manager can manage; Cashier cannot
- Tenant isolation via `restaurant_id` on all queries
- 54 tests covering category CRUD, menu item CRUD, add-ons, price history, access control, and validation

## Module 5: Inventory Management — Complete

All functional requirements (FR-040 to FR-047) implemented:

- **Ingredient CRUD** — name, unit of measure (g, kg, ml, L, pc, pack), minimum stock, average unit cost, default supplier — FR-040
- **Derived stock** — current stock is computed from the ledger's latest resulting balance; no direct stock edits — FR-041
- **Transaction types** — PURCHASE, CONSUMPTION, ADJUSTMENT (in/out), SPOILAGE, RETURN; reason mandatory for adjustment/spoilage/return; unit cost mandatory for purchases — FR-042
- **Immutable ledger** — every transaction records ingredient, type, signed quantity, unit cost, resulting balance, reference, user, timestamp; `delete()` raises; corrections are compensating entries — FR-043
- **Negative stock rejected** — descriptive error naming the ingredient and shortfall — FR-044
- **Low-stock alerts** — one open alert per ingredient until restocked above the minimum, then re-armable — FR-045
- **Stock card** — running balance per ingredient, filterable by type and date range — FR-046
- **Weighted average cost** — recalculated on every purchase — FR-047
- Role access per SRS matrix: Owner/Manager full control; Cashier/Kitchen read-only (list + stock card)
- Tenant isolation via `restaurant_id` on all queries
- 38 tests covering ingredient CRUD, ledger mechanics, weighted average, low-stock lifecycle, filters, access control, and validation

### Models (`inventory/models.py`)

| Model | Fields |
|-------|--------|
| `Ingredient` | restaurant_id, name, unit_of_measure, minimum_stock, average_unit_cost, default_supplier_id, is_deleted, deleted_at |
| `InventoryTransaction` | restaurant_id, ingredient (FK), transaction_type, quantity (signed), unit_cost, resulting_balance, reference, reason, user (FK→User), created_at |
| `LowStockAlert` | restaurant_id, ingredient (FK), opened_at, resolved_at |

### Endpoints

| Path | Description |
|------|-------------|
| `/inventory/ingredients/` | Ingredient list (search, low-stock filter, open alerts banner) |
| `/inventory/ingredients/new/` | Create ingredient |
| `/inventory/ingredients/<id>/edit/` | Edit ingredient |
| `/inventory/ingredients/<id>/delete/` | Soft delete ingredient |
| `/inventory/ingredients/<id>/transactions/` | Stock card ledger (filter by type + date range) |
| `/inventory/transactions/new/` | Record stock movement (purchase/consumption/adjustment/spoilage/return) |

### Models (`menu/models.py`)

| Model | Fields |
|-------|--------|
| `Category` | restaurant_id, name (unique per restaurant), display_order, is_active |
| `MenuItem` | restaurant_id, category (FK), name, description, price, prep_minutes, is_available, image, is_deleted, deleted_at |
| `MenuItemPriceHistory` | menu_item (FK), old_price, new_price, changed_by (FK→User), created_at |
| `AddOn` | restaurant_id, name, price, is_available |
| `MenuItemAddOn` | menu_item (FK), addon (FK) — unique together |

### Endpoints

| Path | Description |
|------|-------------|
| `/menu/categories/` | Category list |
| `/menu/categories/new/` | Create category |
| `/menu/categories/<id>/edit/` | Edit category |
| `/menu/categories/<id>/delete/` | Delete category |
| `/menu/items/` | Menu item list (search, filter) |
| `/menu/items/new/` | Create menu item |
| `/menu/items/<id>/edit/` | Edit menu item |
| `/menu/items/<id>/delete/` | Soft delete menu item |
| `/menu/items/<id>/toggle/` | Toggle availability |
| `/menu/items/<id>/price-history/` | Price change log |
| `/menu/addons/` | Add-on list |
| `/menu/addons/new/` | Create add-on |
| `/menu/addons/<id>/edit/` | Edit add-on |

## Module 6: Supplier Management — Complete

All functional requirements (FR-050 to FR-053) implemented:

- **Supplier CRUD** — name, contact person, phone, email, address, TIN, payment terms — FR-050
- **Search & filtering** — by name, email, phone — FR-051
- **Supplier balance** — outstanding payables computed from purchase orders vs payments — FR-052
- **Supplier payments** — record payments against a supplier, audit-trailed — FR-053
- Role access per SRS matrix: Owner/Manager full; others read-only
- 15 tests covering CRUD, search, payables, payments, access control, and validation

## Module 7: Purchase Orders — Complete

All functional requirements (FR-060 to FR-065) implemented:

- **Purchase order CRUD** — supplier, line items (ingredient, qty, unit cost), status lifecycle (DRAFT → ORDERED → RECEIVED / CANCELLED) — FR-060
- **Sequential PO number** — `PO-YYYY-00001` per restaurant — FR-061
- **Status guard** — only DRAFT editable; ORDERED can be received; CANCELLED only from DRAFT — FR-062
- **Receive order** — records PURCHASE ledger entries (stock up, weighted-average cost recalc) and validates quantities — FR-063
- **Partial receipt** — receiving line-by-line recorded as compensating ADJUSTMENT entries
- **Notifications** — PO received fires a notification for Owner/Manager — FR-150
- 15 tests covering the PO lifecycle, numbering, receive math, access control

## Module 8: Recipe Management — Complete

All functional requirements (FR-070 to FR-074) implemented:

- **Recipe CRUD** — one default recipe per menu item (ingredient lines with quantity) — FR-070
- **Cost & margin** — estimated ingredient cost and margin % computed live — FR-071
- **Ingredients restricted** to the restaurant's own ingredient list; quantities must be positive — FR-072
- **Consumption on order completion** — completing an order deducts recipe stock per line; completed orders are immutable; cancellations restore stock via compensating ADJUSTMENT — FR-073
- **Validation** — duplicate default recipe per menu item rejected
- 11 tests covering recipe CRUD, cost math, completion/cancellation stock effects

## Module 9: Order Management — Complete

All functional requirements (FR-080 to FR-090) implemented:

- **Order creation** — DINE_IN / TAKE_OUT / DELIVERY; line items snapshot name and price; add-ons per line; daily sequential order number `#0001` per restaurant — FR-080
- **Status workflow** — PENDING → PREPARING → READY → COMPLETED (kitchen advances the first two); CANCELLED with reason; full transition history — FR-081/FR-082
- **Kitchen queue** — role-visible queue of pending/preparing orders with item summaries — FR-083
- **Edit & merge** — line items editable only while PENDING; two pending orders can be merged — FR-084
- **Discounts** — Senior/PWD 20% VAT-exempt with ID capture (RA 9994), manual discounts; >10% manual requires Owner/Manager approval — FR-087
- **Order completion** — `settle_order()` verifies payments and approval, deducts recipe stock atomically, marks immutable; reprints/refunds on completed orders only — FR-088
- **Cancellation** — restores stock with compensating ADJUSTMENT entries — FR-089
- **Search & filter** — by status, type, date, order number
- 36 tests covering the full lifecycle, discounts, kitchen flow, merge, cancellation, access control

## Module 10: Table Management — Complete

All functional requirements (FR-090 to FR-093) implemented:

- **Table CRUD** — name, seating capacity, status (AVAILABLE / OCCUPIED / RESERVED / MAINTENANCE) — FR-090
- **Table status** — auto-occupies on order creation, frees on completion/cancellation — FR-091
- **Table view** — visual layout of tables by status for cashier/manager — FR-092
- 9 tests (in orders suite) covering table CRUD, status transitions, access control

## Module 11: Payments & Receipts — Complete

All functional requirements (FR-100 to FR-103) implemented:

- **Payment recording** — CASH / GCASH / MAYA / CARD / BANK_TRANSFER; change due for cash; overpayment guard — FR-100
- **Multiple payments per order** — order settles when total paid covers the balance — FR-101
- **Refunds** — on completed orders only, credited against the original payment method — FR-102
- **Receipt** — printable receipt with sequential receipt number, VAT breakdown, restaurant footer; reprint for completed orders — FR-103
- 36 tests (in orders suite) covering payment math, refunds, receipts, VAT

## Module 12: Expense Management — Complete

All functional requirements (FR-110 to FR-113) implemented:

- **Expense CRUD** — category (Electricity, Water, Internet, Rent, Salary, Supplies, Maintenance, Gas/LPG, Transportation, Other), amount, date, payee, payment method — FR-110
- **Approval workflow** — expenses above the threshold need Owner/Manager approval — FR-111
- **Search & filter** — by category and date range — FR-112
- **Closed-day lock** — expenses cannot be created/edited on a closed business day (FR-140)
- 9 tests covering CRUD, approval, closed-day lock, access control

## Module 13: Employee Management — Complete

All functional requirements (FR-120 to FR-124) implemented:

- **Employee profiles** — linked to user accounts; name, role title, phone, employment status (ACTIVE/INACTIVE/ON_LEAVE) — FR-120
- **Salary visibility** — only Owner/Manager see salary fields — FR-121
- **Attendance** — clock in/out per employee with duration — FR-122
- **Audit logging** — employee and attendance edits logged to the audit trail (FR-160)
- 9 tests covering profiles, salary visibility, attendance, access control

## Module 14: Reports — Complete

All functional requirements (FR-130 to FR-139) implemented:

- **Daily sales** — per-day revenue, VAT breakdown, order counts, payment-method totals — FR-130
- **Monthly sales** — revenue by day with CSV export — FR-131
- **Profit & loss** — revenue, COGS (consumption + spoilage), gross profit, expenses, net profit — FR-132
- **Inventory report** — stock on hand, min stock, value at weighted-average cost — FR-133
- **Product mix** — top sellers by quantity and revenue (from COMPLETED orders only) — FR-134
- **Purchase report** — by supplier and date with CSV export — FR-135
- **Tax summary** — VATable sales, VAT-exempt, output VAT, input VAT (purchases) — FR-136
- **CSV exports** on all report pages
- 8 tests covering report figures and access control

## Module 15: Daily Closing — Complete

All functional requirements (FR-140 to FR-145) implemented:

- **Closing record** — one per restaurant per business day (Asia/Manila), sequential auto-numbered — FR-140
- **Expected cash** — opening float + cash sales − cash refunds − cash expenses — FR-140
- **Variance** — ±₱100 tolerance; larger variance requires a written note — FR-141
- **Preparation** — lists outstanding orders and unapproved expenses before closing — FR-142
- **Locking** — closed day blocks new orders, payments, and expenses (BR-008) — FR-143
- **Reopen** — only the Owner may reopen a closed day — FR-144
- 7 tests covering the full close/reopen lifecycle, variance rule, and locks

## Module 16: Notifications — Complete

All functional requirements (FR-150 to FR-153) implemented:

- **Notification types** — LOW_STOCK, ORDER_PLACED, ORDER_COMPLETED, ORDER_CANCELLED, LARGE_DISCOUNT, REFUND_ISSUED, PO_RECEIVED, SYSTEM — FR-150
- **Targeting** — by role (e.g., kitchen staff) or by specific user — FR-151
- **Inbox & read state** — unread badge, mark single/all read — FR-152
- **Retention** — 90-day auto-purge — FR-153
- 9 tests covering creation, targeting, read state, purge

## Module 17: Audit Logs — Complete

All functional requirements (FR-160 to FR-163) implemented:

- **Append-only log** — `AuditLog.delete()` raises; no editing — FR-160
- **Events** — staff actions, employee/attendance edits, closings, denied-access attempts — FR-161
- **Search & filter** — by action type, actor, date range, target — FR-162
- **Role access** — Owner full; Manager read-only; others denied — FR-163
- 8 tests covering logging, immutability, filters, access control

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
