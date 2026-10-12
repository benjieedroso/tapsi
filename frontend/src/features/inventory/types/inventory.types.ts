export interface IngredientFormData {
  name: string;
  unit: string;
  minimum_stock: number;
  cost_per_unit?: number;
}

export interface IngredientDetail extends IngredientFormData {
  id: number;
}

export interface LowStockAlert {
  ingredient: {
    id: number;
    name: string;
    current_stock: number;
    unit_of_measure: string;
  };
}

export interface IngredientListItem {
  id: number;
  name: string;
  unit_of_measure: string;
  stock: number;
  minimum_stock: number;
  average_unit_cost: number;
}

export interface IngredientListResponse {
  ingredients: IngredientListItem[];
  open_alerts: LowStockAlert[];
}

export interface StockCardTransaction {
  id: number;
  created_at: string;
  transaction_type_display: string;
  quantity: number;
  unit_cost: number | null;
  resulting_balance: number;
  reference: string | null;
  reason: string | null;
  user_display: string | null;
}

export interface StockCardResponse {
  ingredient: {
    id: number;
    name: string;
    unit_of_measure: string;
    current_stock: number;
    minimum_stock: number;
    average_unit_cost: number;
  };
  types: [string, string][];
  transactions: StockCardTransaction[];
  txn_type: string;
  date_from: string;
  date_to: string;
}

export interface IngredientOption {
  id: number;
  name: string;
  unit_of_measure: string;
}

export interface TransactionFormMeta {
  ingredients: IngredientOption[];
  transaction_types: [string, string][];
  directions: [string, string][];
}

export interface CreateTransactionPayload {
  ingredient: number;
  transaction_type: string;
  quantity: number;
  direction?: string;
  unit_cost?: number;
  reference?: string;
  reason?: string;
}