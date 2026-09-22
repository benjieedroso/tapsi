import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../../api/client';

interface DashboardData {
  user: {
    display_name: string;
    role_display: string;
    restaurant_name: string;
  };
  show_financials: boolean;
  net_sales: number;
  gross_sales: number;
  order_count: number;
  avg_order_value: number;
  status_counts: {
    PENDING: number;
    PREPARING: number;
    READY: number;
    COMPLETED: number;
    CANCELLED: number;
  };
  menu_count: number;
  category_count: number;
  addon_count: number;
  low_stock: Array<{ name: string; current_stock: number; unit_of_measure: string }>;
  top_today: Array<{ name: string; qty: number; revenue: number }>;
  top_month: Array<{ name: string; qty: number; revenue: number }>;
  month_profit: number;
  month_revenue: number;
  month_expenses: number;
  trend: Array<{ date: string; revenue: number }>;
  trend_max: number;
}

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await apiClient.get('/api/v1/dashboard/');
        setData(response.data);
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Hero Header */}
      <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-600">
          {data?.user?.role_display || 'Owner'}
        </span>
        <h1 className="text-3xl font-bold text-gray-900 mt-1">
          Good day, {data?.user?.display_name || 'Manager'}.
        </h1>
        <p className="text-gray-600 mt-1">
          {data?.user?.restaurant_name || 'TAPSI Restaurant'} is ready for its first service.
        </p>
      </section>

      {/* Main Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-3">Quick Actions</h2>
          <div className="flex flex-col gap-2">
            <Link to="/orders/new" className="text-blue-600 hover:underline">New order</Link>
            <Link to="/orders/kitchen" className="text-blue-600 hover:underline">Kitchen queue</Link>
            <Link to="/closing" className="text-blue-600 hover:underline">Daily closing</Link>
            <Link to="/reports/daily-sales" className="text-blue-600 hover:underline">Reports</Link>
            <Link to="/menu/new" className="text-blue-600 hover:underline">Add menu item</Link>
            <Link to="/staff" className="text-blue-600 hover:underline">Manage staff</Link>
          </div>
        </article>

        {/* Today's Sales */}
        {data?.show_financials && (
          <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900">Today's Sales</h2>
            <p className="text-3xl font-bold text-gray-900 my-2">
              ₱{(data.net_sales || 0).toFixed(2)}
            </p>
            <p className="text-xs text-gray-500 mb-4">
              Gross ₱{(data.gross_sales || 0).toFixed(2)} · {data.order_count || 0} orders · ₱{(data.avg_order_value || 0).toFixed(2)} AOV
            </p>
            <Link to="/reports/daily-sales" className="text-blue-600 hover:underline text-sm font-medium">
              View daily report →
            </Link>
          </article>
        )}

        {/* Order Status */}
        {data?.show_financials && (
          <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900">Order Status</h2>
            <p className="text-3xl font-bold text-gray-900 my-2">
              {data.status_counts?.PENDING || 0}
            </p>
            <div className="flex flex-wrap gap-1 mb-4 text-xs">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{data.status_counts?.PENDING || 0} Pending</span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">{data.status_counts?.PREPARING || 0} Preparing</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded">{data.status_counts?.READY || 0} Ready</span>
              <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{data.status_counts?.COMPLETED || 0} Completed</span>
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded">{data.status_counts?.CANCELLED || 0} Cancelled</span>
            </div>
            <Link to="/orders" className="text-blue-600 hover:underline text-sm font-medium">
              View all orders →
            </Link>
          </article>
        )}

        {/* Menu Items */}
        <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Menu Items</h2>
          <p className="text-3xl font-bold text-gray-900 my-2">{data?.menu_count || 0}</p>
          {(data?.menu_count || 0) > 0 ? (
            <Link to="/menu" className="text-blue-600 hover:underline text-sm font-medium">View all items →</Link>
          ) : (
            <div>
              <p className="text-sm text-gray-600 mb-2">Add menu items to start taking orders.</p>
              <Link to="/menu/new" className="text-blue-600 hover:underline text-sm font-medium">Add first item →</Link>
            </div>
          )}
        </article>

        {/* Categories */}
        <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Categories</h2>
          <p className="text-3xl font-bold text-gray-900 my-2">{data?.category_count || 0}</p>
          {(data?.category_count || 0) > 0 ? (
            <Link to="/categories" className="text-blue-600 hover:underline text-sm font-medium">Manage categories →</Link>
          ) : (
            <div>
              <p className="text-sm text-gray-600 mb-2">Organize your menu into categories.</p>
              <Link to="/categories/new" className="text-blue-600 hover:underline text-sm font-medium">Add first category →</Link>
            </div>
          )}
        </article>

        {/* Add-Ons */}
        <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Add-Ons</h2>
          <p className="text-3xl font-bold text-gray-900 my-2">{data?.addon_count || 0}</p>
          <p className="text-sm text-gray-600 mb-3">Extra items like extra rice or extra egg.</p>
          <Link to="/addons" className="text-blue-600 hover:underline text-sm font-medium">Manage add-ons →</Link>
        </article>

        {/* Low Stock */}
        {data?.show_financials && (
          <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900">Low Stock</h2>
            <p className="text-3xl font-bold text-gray-900 my-2">{data.low_stock?.length || 0}</p>
            {data.low_stock && data.low_stock.length > 0 ? (
              <ul className="text-sm space-y-1 mb-3">
                {data.low_stock.map((ing, idx) => (
                  <li key={idx} className="text-gray-700">
                    {ing.name} — {ing.current_stock.toFixed(2)} {ing.unit_of_measure}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-600 mb-3">All ingredients are above their minimum stock.</p>
            )}
            <Link to="/inventory" className="text-blue-600 hover:underline text-sm font-medium">Manage inventory →</Link>
          </article>
        )}

        {/* This Month Profit */}
        {data?.show_financials && (
          <article className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900">This Month</h2>
            <p className="text-3xl font-bold text-gray-900 my-2">₱{(data.month_profit || 0).toFixed(2)}</p>
            <p className="text-xs text-gray-500 mb-3">
              Revenue ₱{(data.month_revenue || 0).toFixed(2)} − Expenses ₱{(data.month_expenses || 0).toFixed(2)}
            </p>
            <Link to="/reports/profit-loss" className="text-blue-600 hover:underline text-sm font-medium">Profit &amp; loss report →</Link>
          </article>
        )}
      </section>
    </div>
  );
};