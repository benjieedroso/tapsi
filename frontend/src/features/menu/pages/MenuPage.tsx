import React, { useState } from 'react';
import { MenuItemsTab } from '../components/MenuItemsTab';
import { CategoriesTab } from '../components/CategoriesTab';
import { AddonsTab } from '../components/AddonsTab';
import { PriceHistoryTab } from '../components/PriceHistoryTab';
import type { MenuItem } from '../types/menu.types';

type Tab = 'items' | 'categories' | 'addons' | 'history';

export const MenuPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('items');
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<MenuItem | null>(null);

  const handleViewPriceHistory = (item: MenuItem) => {
    setSelectedHistoryItem(item);
    setActiveTab('history');
  };

  const handleBackToItems = () => {
    setSelectedHistoryItem(null);
    setActiveTab('items');
  };

  return (
    <div
      className="menu-page-container"
      style={{
        width: '100%',
        padding: '2rem 2.5rem',
        boxSizing: 'border-box',
        textAlign: 'left',
      }}
    >
      {/* Page Header */}
      {/* Page Header */}
      <header className="page-header" style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, margin: 0, color: '#111827' }}>
          Menu Management
        </h1>
        <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Manage items, categories, add-ons, and pricing history.
        </p>
      </header>

      {/* Navigation Tabs */}
      <nav
        className="tabs"
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid #e5e7eb',
          marginBottom: '1.5rem',
          width: '100%',
        }}
      >
        {[
          { id: 'items', label: 'Menu Items' },
          { id: 'categories', label: 'Categories' },
          { id: 'addons', label: 'Add-ons' },
          { id: 'history', label: 'Price History' },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              style={{
                padding: '0.625rem 1rem',
                border: 'none',
                background: 'transparent',
                borderBottom: isActive ? '2px solid #10b981' : '2px solid transparent',
                color: isActive ? '#059669' : '#6b7280',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.875rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Tab Content */}
      <main className="tab-content" style={{ textAlign: 'left', width: '100%' }}>
        {activeTab === 'items' && (
          <MenuItemsTab onViewPriceHistory={handleViewPriceHistory} />
        )}
        {activeTab === 'categories' && <CategoriesTab />}
        {activeTab === 'addons' && <AddonsTab />}
        {activeTab === 'history' && (
          selectedHistoryItem ? (
            <PriceHistoryTab item={selectedHistoryItem} onBack={handleBackToItems} />
          ) : (
            <div style={{ padding: '3rem 1rem', textAlign: 'center' }}>
              <h3 style={{ margin: 0, color: '#374151' }}>No Item Selected</h3>
              <p style={{ color: '#6b7280', marginTop: '0.5rem' }}>
                Select a menu item from the "Menu Items" tab to view its price history.
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setActiveTab('items')}
                style={{ marginTop: '1rem' }}
              >
                Go to Menu Items
              </button>
            </div>
          )
        )}
      </main>
    </div>
  );
};

export default MenuPage;