export interface POItem {
  id: number;
  ingredient_name: string;
  qty_ordered: number;
  qty_received: number;
  outstanding_qty: number;
  unit_cost: number;
  line_total: number;
}

export interface PODetail {
  id: number;
  po_number: string;
  supplier_name: string;
  created_at: string;
  status: 'DRAFT' | 'ORDERED' | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CANCELLED';
  status_display: string;
  is_read_only: boolean;
  notes?: string | null;
  items: POItem[];
}

export interface SupplierOption {
  id: number;
  name: string;
}

export interface IngredientOption {
  id: number;
  name: string;
  unit_of_measure?: string;
}

export interface POCreateMeta {
  suppliers: SupplierOption[];
  ingredients: IngredientOption[];
}

export interface CreatePOItemPayload {
  ingredient: number;
  qty_ordered: number;
  unit_cost: number;
}

export interface CreatePOPayload {
  supplier: number;
  notes?: string;
  items: CreatePOItemPayload[];
}

export interface POListItem {
  id: number;
  po_number: string;
  supplier_name: string;
  created_at: string;
  total: number;
  status: 'DRAFT' | 'ORDERED' | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CANCELLED';
  status_display: string;
}

export interface POListResponse {
  pos: POListItem[];
  suppliers: SupplierOption[];
  statuses: [string, string][];
}

export interface SupplierPOHistoryItem {
  id: number;
  po_number: string;
  created_at: string;
  total: number;
  received_total: number;
  status: string;
  status_display: string;
}

export interface SupplierDetailData {
  id: number;
  name: string;
  payment_terms: string;
  phone?: string | null;
  is_active: boolean;
  outstanding_balance: number;
  pos: SupplierPOHistoryItem[];
}

export interface SupplierPaymentPayload {
  amount: number;
  notes?: string;
  reference_number?: string;
}

export interface SupplierFormData {
  name: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  payment_terms: 'COD' | '7D' | '15D' | '30D';
  is_active?: boolean;
}

export interface SupplierEditDetail extends SupplierFormData {
  id: number;
}

export interface SupplierListItem {
  id: number;
  name: string;
  contact_person?: string | null;
  phone?: string | null;
  payment_terms: string;
  is_active: boolean;
}

export interface SupplierListResponse {
  suppliers: SupplierListItem[];
}