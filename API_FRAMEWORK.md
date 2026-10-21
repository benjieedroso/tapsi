# TAPSI Modernization & Decoupled Architecture Documentation

## 1. Architecture Overview
This project is being converted from a monolithic server-side Django web app into a **decoupled, multi-tenant headless REST API platform**.

- **Backend:** Django REST Framework (DRF) + SimpleJWT Authentication
- **Database:** SQLite (Local Dev) / PostgreSQL (Production)
- **Web Frontend:** React + Vite + TypeScript (`frontend/` directory)

---

## 2. Progress Summary

### Backend / API Layer — **COMPLETED**
- **Authentication & Core User Profile (`accounts`):**
- Configured SimpleJWT authentication via `CustomTokenObtainPairView` (`/api/v1/auth/token/` and `/api/v1/auth/token/refresh/`).
- Implemented `CustomTokenObtainPairSerializer` to embed custom JWT claims (`restaurant_id`, `role`, `user_id`) directly into token payloads.
- Implemented `/api/v1/auth/me/` (`CurrentUserView`) using `UserMeSerializer` to return authenticated profile details and tenant details.
- Configured `RestaurantViewSet` with `@action` endpoint `my-restaurant` for retrieving and updating tenant settings.
- **Base Architecture:**
- Standardized `TenantAwareViewSet` base class to automatically scope queries by `restaurant_id`.
- **Module Conversions (`/api/v1/` routes):**
- **`accounts`**: ViewSets & Serializers for `User` and `Restaurant` tenant profiles, handling custom JWT token generation, profile retrieval (`/auth/me/`), and restaurant configuration management.
- **`menu`**: ViewSets & Serializers for `Category`, `MenuItem`, and `AddOn` with custom permission guards (`IsManagerOrOwner`).
- **`orders`**: ViewSets & Serializers for `Order`, `OrderItem`, and `DiningTable` (FR-090..095 table CRUD, operational status management, seating capacity validation, open bill tracking).
- **`inventory`**: Ledger-backed `Ingredient` (derived stock), `InventoryTransaction` (immutable ledger, FR-043/044 validation handling, weighted average cost recalculation), and `LowStockAlert` reconcile integration.
- **`expenses`**: ViewSets & Serializers for `Expense` and `ExpenseCategory`.
- **`employees`**: ViewSets & Serializers for staff records (`Employee`, FR-121 role-based salary security).
- **`suppliers`**: ViewSets & Serializers for `Supplier` (soft-delete FR-050/053, balance tracking FR-051), `PurchaseOrder` & `PurchaseOrderItem` (sequential number generation FR-063, receiving flow FR-065), and `SupplierPayment` (FR-052).
- **`closing`**: ViewSets & Serializers for `DailyClosing` (BR-008 day lock check, FR-140 expected cash calculation, variance auto-computation, and manager reopen action).
- **`reports`**: Read-only analytical API ViewSet wrapping aggregations for Daily Sales (FR-130), Monthly Sales (FR-132), Profit & Loss (FR-133), Inventory Spoilage/Usage (FR-134), Product Mix (FR-135), Purchase Reports (FR-136), and Output VAT Tax Summary (FR-137).
- **`notifications`**: ViewSets & Serializers for `Notification` (role- and user-addressed scoping FR-151, read state management FR-152, unread counts, and 90-day retention purge FR-153).
- **`audit_logs`**: Read-only append-only ViewSet for `AuditLog` (tenant-scoped querying FR-163, explicit DELETE/PUT/PATCH prevention FR-162).

---

### Verification & Testing
- Standardized API client testing using **Bruno API Client** (collection configured with automatic Bearer Token inheritance).
- Resolved circular imports, missing DRF permission imports, and Django router mismatches (correctly registering `DiningTableViewSet` to the `/tables/` endpoint).
- Added end-to-end integration test suite in `accounts/tests/test_auth.py` (`JWTAuthFlowTests`) verifying:
- Real login token retrieval and invalid credential rejection.
- Custom JWT claim decoding (`restaurant_id`, `role`, `user_id`).
- Bearer token header authorization on protected routes (`menu:category-list`).
- Rejection of missing, garbage, and hand-crafted expired tokens.
- Refresh token exchange and cross-tenant claim isolation.
- Verified `GET`, `POST`, `PATCH`, and `DELETE` calls across all backend endpoints with active tenant scoping and role permission checks.

---

### Frontend Integration (`frontend/`) — **ADVANCED UI & FORMS COMPLETED**
- **Step 1 (Initialization):** Bootstrapped React + Vite + TypeScript inside the `frontend/` directory.
- **Step 2 (Environment Setup):** Configured `.env` pointing to backend host (`VITE_API_BASE_URL=http://127.0.0.1:8000`).
- **Step 3 (Axios Client):** Built `src/api/client.ts` with request interceptor automatically injecting `Bearer <token>` from `localStorage`.
- **Step 4 (API Service Layer & Forms):** 
  - Implemented typed API call abstractions across feature modules.
  - Built comprehensive `TableForm` component handling table names, `seating_capacity`, and table operational status selection (`AVAILABLE`, `OCCUPIED`, `RESERVED`, `CLEANING`) adhering to FR-090/091.
  - Synchronized and aligned all TypeScript types (`TableDetail`, `TableFormData`, `TableListItem`, `TableListResponse`, `UserRole`) to eliminate compilation errors.
  - Implemented role-based conditional rendering in `EmployeeList` to secure daily rates and monthly salary visibility exclusively for `OWNER` and `MANAGER` roles (FR-121).

---

## 3. Recommended Frontend Directory Structure

```text
tapsi/
├── manage.py
├── config/
├── accounts/
├── menu/
├── orders/
├── inventory/
├── expenses/
├── employees/
├── suppliers/
├── closing/
├── reports/
├── notifications/
├── audit_logs/
└── frontend/                   <-- React Vite SPA
    ├── src/
    │   ├── api/                <-- Axios client (client.ts) & module services (auth.ts, menu.ts, orders.ts, inventory.ts, employees.ts, etc.)
    │   ├── components/         <-- Reusable UI elements (Tables, Modals, Forms, Navigation)
    │   ├── context/            <-- AuthContext for token state & user session
    │   ├── pages/              <-- App views (Login, POS/Orders, Tables, Employees, Inventory, Suppliers, Closing, Reports, Audit Logs)
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts