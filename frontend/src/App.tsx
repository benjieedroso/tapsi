import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './features/accounts/pages/Login';
import { Register } from './features/accounts/pages/Register';
import { SidebarLayout } from './components/layout/SidebarLayout';
import { ProtectedRoute } from './components/routes/ProtectedRoute';
import { Dashboard } from './features/dashboard/pages/Dashboard';
import { authApi } from './features/accounts/api/accounts';

import { Profile } from './features/accounts/pages/Profile';
import { StaffList } from './features/accounts/pages/StaffList';
import { StaffForm } from './features/accounts/pages/StaffForm';
import { StaffEdit } from './features/accounts/pages/StaffEdit';
import { StaffResetPassword } from './features/accounts/pages/StaffResetPassword';
import { RestaurantSettings } from './features/accounts/pages/RestaurantSettings';
import { MenuPage } from './features/menu/pages/MenuPage';
import { PasswordReset } from './features/accounts/pages/PasswordReset';
import { PasswordResetConfirm } from './features/accounts/pages/PasswordResetConfirm';
import { PasswordResetDone } from './features/accounts/pages/PasswordResetDone';

// Orders & Tables Imports
import { OrderList } from './features/orders/pages/OrderList';
import { OrderForm } from './features/orders/pages/OrderForm';
import { OrderDetailPage } from './features/orders/pages/OrderDetailPage';
import { KitchenQueue } from './features/orders/pages/KitchenQueue';
import { Receipt } from './features/orders/pages/Receipt';
import { TableList } from './features/orders/pages/TableList';
import { TableForm } from './features/orders/pages/TableForm';

// Inventory Imports
import { IngredientList } from './features/inventory/pages/IngredientList';
import { IngredientForm } from './features/inventory/pages/IngredientForm';
import { StockCard } from './features/inventory/pages/StockCard';
import { TransactionForm } from './features/inventory/pages/TransactionForm';

// Expenses Imports
import { ExpenseList } from './features/expenses/pages/ExpenseList';
import { ExpenseForm } from './features/expenses/pages/ExpenseForm';

// Employees Imports
import { EmployeeList } from './features/employees/pages/EmployeeList';
import { EmployeeForm } from './features/employees/pages/EmployeeForm';
import { AttendanceList } from './features/employees/pages/AttendanceList';
import { AttendanceForm } from './features/employees/pages/AttendanceForm';

// Suppliers & Purchase Orders Imports
import { SupplierList } from './features/suppliers/pages/SupplierList';
import { SupplierForm } from './features/suppliers/pages/SupplierForm';
import { SupplierDetail } from './features/suppliers/pages/SupplierDetail';
import { POList } from './features/suppliers/pages/POList';
import { POForm } from './features/suppliers/pages/POForm';
import { PODetail } from './features/suppliers/pages/PODetail';
import { POReceive } from './features/suppliers/pages/POReceive';

// Closing Imports
import { ClosingList } from './features/closing/pages/ClosingList';
import { ClosingPrepare } from './features/closing/pages/ClosingPrepare';
import { EODReport } from './features/closing/pages/EODReport';

// Reports Imports
import { DailySalesReport } from './features/reports/pages/DailySalesReport';
import { InventoryReport } from './features/reports/pages/InventoryReport';
import { MonthlySalesReport } from './features/reports/pages/MonthlySalesReport';
import { ProductMixReport } from './features/reports/pages/ProductMixReport';
import { ProfitLossReport } from './features/reports/pages/ProfitLossReport';
import { PurchaseReport } from './features/reports/pages/PurchaseReport';
import { TaxSummaryReport } from './features/reports/pages/TaxSummaryReport';

// Recipes Imports
import { RecipeList } from './features/recipes/pages/RecipeList';
import { RecipeDetail } from './features/recipes/pages/RecipeDetail';
import { RecipeForm } from './features/recipes/pages/RecipeForm';

// Notifications Imports
import { NotificationList } from './features/notifications/pages/NotificationList';

// Audit Logs Import
import { AuditLogList } from './features/audit/pages/AuditLogList';

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('access_token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">
        Loading...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Password Reset Flow Routes */}
        <Route path="/forgot-password" element={<PasswordReset />} />
        <Route path="/password-reset/done" element={<PasswordResetDone />} />
        <Route 
          path="/reset-password-confirm/:uid/:token" 
          element={<PasswordResetConfirm />} 
        />
      
        {/* Auth Routes */}
        <Route path="/login" element={<Login onLoginSuccess={setUser} />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<SidebarLayout user={user} />}>
            {/* Dashboard & Profile */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/profile/settings" element={<RestaurantSettings />} />
            <Route path="/menu" element={<MenuPage />} />

            {/* Orders & Kitchen Routes */}
            <Route path="/orders" element={<OrderList userRole={user?.role} />} />
            <Route path="/orders/create" element={<OrderForm />} />
            <Route path="/orders/:id" element={<OrderDetailPage userRole={user?.role} />} />
            <Route path="/orders/:id/receipt" element={<Receipt />} />
            <Route path="/kitchen" element={<KitchenQueue />} />
            <Route path="/kitchen-queue" element={<Navigate to="/kitchen" replace />} />

            {/* Tables Routes */}
            <Route path="/tables" element={<TableList />} />
            <Route path="/tables/create" element={<TableForm />} />
            <Route path="/tables/:id/edit" element={<TableForm />} />

            {/* Staff Routes */}
            <Route path="/accounts/staff" element={<StaffList />} />
            <Route path="/accounts/staff/add" element={<StaffForm />} />
            <Route path="/accounts/staff/:id/edit" element={<StaffEdit />} />
            <Route path="/accounts/staff/:id/reset-password" element={<StaffResetPassword />} />

            {/* Inventory Routes */}
            <Route path="/inventory" element={<Navigate to="/inventory/ingredients" replace />} />
            <Route path="/inventory/ingredients" element={<IngredientList />} />
            <Route path="/inventory/ingredients/create" element={<IngredientForm />} />
            <Route path="/inventory/ingredients/:id/edit" element={<IngredientForm />} />
            <Route path="/inventory/ingredients/:id/stock-card" element={<StockCard />} />
            <Route path="/inventory/transactions/create" element={<TransactionForm />} />

            {/* Expenses Routes */}
            <Route path="/expenses" element={<ExpenseList userRole={user?.role} />} />
            <Route path="/expenses/create" element={<ExpenseForm />} />
            <Route path="/expenses/:id/edit" element={<ExpenseForm />} />

            {/* Employees & Attendance Routes */}
            <Route path="/employees" element={<EmployeeList userRole={user?.role} />} />
            <Route path="/employees/create" element={<EmployeeForm />} />
            <Route path="/employees/:id/edit" element={<EmployeeForm />} />
            <Route path="/attendance" element={<AttendanceList userRole={user?.role} />} />
            <Route path="/attendance/:id/edit" element={<AttendanceForm />} />

            {/* Suppliers & Purchase Orders Routes */}
            <Route path="/suppliers" element={<SupplierList />} />
            <Route path="/suppliers/create" element={<SupplierForm />} />
            <Route path="/suppliers/:id" element={<SupplierDetail />} />
            <Route path="/suppliers/:id/edit" element={<SupplierForm />} />
            <Route path="/suppliers/purchase-orders" element={<POList />} />
            <Route path="/suppliers/purchase-orders/create" element={<POForm />} />
            <Route path="/suppliers/purchase-orders/:id" element={<PODetail />} />
            <Route path="/suppliers/purchase-orders/:id/receive" element={<POReceive />} />

            {/* Closing Routes */}
            <Route path="/closing" element={<ClosingList userRole={user?.role} />} />
            <Route path="/closing/prepare" element={<ClosingPrepare />} />
            <Route path="/closing/:id/report" element={<EODReport />} />

            {/* Reports Routes */}
            <Route path="/reports" element={<Navigate to="/reports/daily-sales" replace />} />
            <Route path="/reports/daily-sales" element={<DailySalesReport />} />
            <Route path="/reports/inventory" element={<InventoryReport />} />
            <Route path="/reports/monthly-sales" element={<MonthlySalesReport />} />
            <Route path="/reports/product-mix" element={<ProductMixReport />} />
            <Route path="/reports/profit-loss" element={<ProfitLossReport />} />
            <Route path="/reports/purchases" element={<PurchaseReport />} />
            <Route path="/reports/tax-summary" element={<TaxSummaryReport />} />

            {/* Recipe Routes */}
            <Route path="/recipes" element={<RecipeList />} />
            <Route path="/recipes/create" element={<RecipeForm />} />
            <Route path="/recipes/:id" element={<RecipeDetail />} />
            <Route path="/recipes/:id/edit" element={<RecipeForm />} />

            {/* Notification Routes */}
            <Route path="/notifications" element={<NotificationList />} />

            {/* Audit Routes */}
            <Route path="/audit" element={<AuditLogList userRole={user?.role} />} />
          </Route>
        </Route>

        {/* Default route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}