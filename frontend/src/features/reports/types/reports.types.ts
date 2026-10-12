export interface DailySalesData {
  day: string;
  gross: number;
  discounts: number;
  net: number;
  vatable: number;
  exempt: number;
  vat: number;
  refunds: number;
  order_count: number;
  aov: number;
  cancelled: number;
  method_breakdown: Record<string, number>;
}

export interface DailySalesResponse {
  data: DailySalesData;
}

export interface InventoryIngredientItem {
  id: number;
  name: string;
  unit_of_measure: string;
  current_stock: number;
  minimum_stock: number;
  average_unit_cost: number;
}

export interface InventoryUsageRow {
  name: string;
  qty: number;
  count: number;
}

export interface InventoryReportData {
  start: string;
  end: string;
  ingredients: InventoryIngredientItem[];
  usage_rows: InventoryUsageRow[];
  spoilage_cost: number;
}

export interface InventoryReportResponse {
  data: InventoryReportData;
}

export interface MonthlySalesDayItem {
  day: number | string;
  total: number;
  prev: number;
  change?: number | null;
}

export interface MonthlySalesData {
  month: {
    year: number;
    month: number;
    formatted: string; // e.g. "2026-06"
  };
  days: MonthlySalesDayItem[];
  month_total: number;
  prev_total: number;
}

export interface MonthlySalesResponse {
  data: MonthlySalesData;
}

export interface ProductCategoryOption {
  id: number;
  name: string;
}

export interface ProductMixRow {
  item_name: string;
  qty: number;
  revenue: number;
  count: number;
}

export interface ProductMixData {
  start: string;
  end: string;
  category_id?: string | null;
  categories: ProductCategoryOption[];
  rows: ProductMixRow[];
}

export interface ProductMixResponse {
  data: ProductMixData;
}

export interface ProfitLossData {
  start: string;
  end: string;
  net_sales: number;
  cogs: number;
  expenses: number;
  profit: number;
}

export interface ProfitLossResponse {
  data: ProfitLossData;
}

export interface PurchaseReportPORow {
  po: {
    id: number;
    po_number: string;
    get_status_display: string;
  };
  supplier: string;
  total: number;
  received: number;
  outstanding: number;
}

export interface PurchaseReportData {
  start: string;
  end: string;
  suppliers: [number, string][];
  rows: PurchaseReportPORow[];
  total_received: number;
  total_outstanding: number;
}

export interface PurchaseReportResponse {
  data: PurchaseReportData;
}

export interface TaxSummaryData {
  start: string;
  end: string;
  vatable: number;
  exempt: number;
  discounts: number;
  output_vat: number;
}

export interface TaxSummaryResponse {
  data: TaxSummaryData;
}