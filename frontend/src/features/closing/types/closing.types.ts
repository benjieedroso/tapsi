export interface DailyClosingItem {
  id: number;
  business_date: string;
  status: 'CLOSED' | 'REOPENED';
  expected_cash: number;
  counted_cash: number;
  variance: number;
  variance_note?: string | null;
}

export interface DailyClosingListResponse {
  closings: DailyClosingItem[];
}

export interface OpenOrder {
  id: number;
  order_number: string;
  status_display: string;
  total: number;
}

export interface ClosingPrepareData {
  business_date: string;
  already_closed?: {
    status: string;
    get_status_display: string;
  } | null;
  open_orders?: OpenOrder[];
  opening_float?: number;
  expected_cash?: number;
}

export interface ClosingCompletePayload {
  counted_cash: number;
  variance_note?: string;
}

export interface EODReportData {
  business_date: string;
  status: 'CLOSED' | 'REOPENED';
  status_display: string;
  opening_float: number;
  expected_cash: number;
  counted_cash: number;
  variance: number;
  variance_note?: string | null;
  closed_by: {
    get_full_name?: string;
    email: string;
  };
  reopened_by?: {
    get_full_name?: string;
    email: string;
  } | null;
  reopen_reason?: string | null;
}