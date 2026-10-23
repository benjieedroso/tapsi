export interface ExpenseCategory {
  id: number;
  name: string;
  label: string;
  value: string;
}

export interface ExpenseDetail {
  id: number;
  category: number;
  category_name?: string;
  amount: number;
  description: string;
  expense_date: string; // YYYY-MM-DD
  receipt_image?: string | null;
  is_locked?: boolean;
}

export interface ExpenseListItem {
  id: number;
  expense_date: string;
  category_display: string;
  category?: number;
  payee?: string | null;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  status_display: string;
  created_by_display?: string | null;
}

export interface ExpenseListResponse {
  expenses: ExpenseListItem[];
  categories: [string, string][];
  statuses: [string, string][];
}

export interface ExpenseFilterParams {
  category?: string;
  status?: string;
  from?: string;
  to?: string;
}