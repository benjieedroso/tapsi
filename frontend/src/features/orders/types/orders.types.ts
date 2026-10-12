export type UserRole = 'OWNER' | 'MANAGER' | 'CASHIER' | 'KITCHEN';
export type OrderStatus = 'PENDING' | 'PREPARING' | 'READY' | 'COMPLETED' | 'CANCELLED';
export type OrderType = 'DINE_IN' | 'TAKE_OUT' | 'DELIVERY';
export type TableStatus = 'AVAILABLE' | 'OCCUPIED' | 'RESERVED' | 'CLEANING';

export interface OrderItemAddon {
  id: number;
  addon_name: string;
  price: string;
}

export interface OrderItem {
  id: number;
  item_name: string;
  quantity: number;
  line_total: string;
  notes?: string;
  addons: OrderItemAddon[];
}

export interface Payment {
  id: number;
  method: string;
  method_display: string;
  amount: string;
  created_at: string;
}

export interface StatusHistoryEntry {
  id: number;
  old_status_display: string;
  new_status_display: string;
  changed_by: string;
  reason?: string;
  created_at: string;
}

export interface Shortfall {
  ingredient_name: string;
  have: number;
  need: number;
}

export interface KitchenOrder {
  id: number;
  order_number: string;
  order_type_display: string;
  table_name?: string;
  status: OrderStatus;
  status_display: string;
  elapsed_minutes: number;
  items: OrderItem[];
}

export interface OrderDetail {
  id: number;
  order_number: string;
  order_type: OrderType;
  order_type_display: string;
  table?: { id: number; name: string };
  customer_name?: string;
  status: OrderStatus;
  status_display: string;
  
  subtotal: string;
  discount_type_display?: string;
  discount_ref?: string;
  discount_amount: string;
  discount_needs_approval: boolean;
  vat_amount: string;
  total: string;
  paid_amount: string;
  outstanding_balance: string;
  is_settled: boolean;

  items: OrderItem[];
  payments: Payment[];
  status_history: StatusHistoryEntry[];
}

export interface TableOption {
  id: number;
  name: string;
}

export interface MenuItemOption {
  id: number;
  name: string;
  price: string;
}

export interface CreateOrderPayload {
  order_type: OrderType;
  table_id?: number | null;
  customer_name?: string;
  notes?: string;
}

export interface OrderFormMeta {
  available_tables: TableOption[];
}

export interface OrderListItem {
  id: number;
  order_number: string;
  order_type: OrderType;
  order_type_display: string;
  table_name?: string;
  status: OrderStatus;
  status_display: string;
  total: string;
  created_by_name: string;
  created_at: string;
}

export interface OrderListFilterOptions {
  statusChoices: { value: string; label: string }[];
  typeChoices: { value: string; label: string }[];
}

export interface OrderListResponse {
  orders: OrderListItem[];
  filters: OrderListFilterOptions;
}

export interface RestaurantProfile {
  name: string;
  address?: string;
  contact_number?: string;
  tin?: string;
  is_vat_registered: boolean;
  receipt_footer?: string;
}

export interface ReceiptData {
  order: {
    id: number;
    order_number: string;
    receipt_no: string;
    receipt_reprinted_count: number;
    created_at: string;
    created_by_name: string;
    subtotal: string;
    discount_amount: string;
    discount_type_display?: string;
    discount_ref?: string;
    vatable_sales: string;
    vat_exempt_sales?: string;
    vat_amount: string;
    total: string;
  };
  reprint: boolean;
  restaurant: RestaurantProfile;
  items: OrderItem[];
  payments: (Payment & { reference_no?: string; change_given?: string })[];
}

export interface TableFormData {
  name: string;
  capacity: number;
}

export interface TableDetail extends TableFormData {
  id: number;
  is_occupied?: boolean;
}

export interface TableOpenOrder {
  id: number;
  order_number: string;
  status_display: string;
}

export interface TableListItem {
  id: number;
  name: string;
  seating_capacity: number;
  status: TableStatus;
  status_display: string;
  running_bill?: string;
  open_orders?: TableOpenOrder[];
}

export interface TableListResponse {
  tables: TableListItem[];
  currentUserRole: UserRole;
}