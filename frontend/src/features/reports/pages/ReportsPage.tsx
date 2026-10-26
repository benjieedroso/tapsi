import React, { useState } from 'react';
import { DailySalesReport } from './DailySalesReport';
import { MonthlySalesReport } from './MonthlySalesReport';
import { ProductMixReport } from './ProductMixReport';
import { InventoryReport } from './InventoryReport';
import { PurchaseReport } from './PurchaseReport';
import { ProfitLossReport } from './ProfitLossReport';
import { TaxSummaryReport } from './TaxSummaryReport';

export const ReportsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<
    'daily' | 'monthly' | 'product-mix' | 'inventory' | 'purchases' | 'profit-loss' | 'tax'
  >('daily');

  const tabs = [
    { id: 'daily', label: 'Daily Sales' },
    { id: 'monthly', label: 'Monthly Sales' },
    { id: 'product-mix', label: 'Product Mix' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'purchases', label: 'Purchases' },
    { id: 'profit-loss', label: 'Profit & Loss' },
    { id: 'tax', label: 'Tax Summary' },
  ] as const;

  return (
    <div style={{ padding: 'var(--space-4)' }}>
      {/* Navigation Sub-Tabs */}
      <div 
        style={{ 
          display: 'flex', 
          gap: 'var(--space-2)', 
          overflowX: 'auto', 
          marginBottom: 'var(--space-4)', 
          borderBottom: '1px solid var(--gray-250, #e5e7eb)', 
          paddingBottom: 'var(--space-3)' 
        }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab.id)}
            style={{ whiteSpace: 'nowrap' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Render Active Report Page */}
      <div className="report-content-container">
        {activeTab === 'daily' && <DailySalesReport />}
        {activeTab === 'monthly' && <MonthlySalesReport />}
        {activeTab === 'product-mix' && <ProductMixReport />}
        {activeTab === 'inventory' && <InventoryReport />}
        {activeTab === 'purchases' && <PurchaseReport />}
        {activeTab === 'profit-loss' && <ProfitLossReport />}
        {activeTab === 'tax' && <TaxSummaryReport />}
      </div>
    </div>
  );
};

export default ReportsPage;