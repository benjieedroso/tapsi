export interface Category {
  id: number;
  name: string;
  display_order: number;
  items_count?: number;
  is_active: boolean;
}

export interface Addon {
  id: number;
  name: string;
  price: string | number;
  is_available: boolean;
}

export interface PriceHistoryEntry {
  id: number;
  created_at: string;
  old_price: number | string;
  new_price: number | string;
  changed_by?: {
    id: number;
    display_name?: string;
  } | null;
}

export interface MenuItem {
  id: number;
  name: string;
  category: number | null;
  category_name?: string;
  price: string | number;
  prep_minutes: number;
  description?: string;
  is_available: boolean;
  image?: string | null;
  addon_ids?: number[];
  addons?: Addon[];
}

export interface ApiErrorResponse {
  detail?: string;
  [key: string]: string | string[] | undefined;
}