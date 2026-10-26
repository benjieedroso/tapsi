export interface AttendanceDetail {
  id: number;
  user_name?: string;
  time_in?: string | null;
  time_out?: string | null;
  status?: string;
  notes?: string;
  work_date?: string;
}

export interface AttendanceUpdatePayload {
  time_in?: string | null;
  time_out?: string | null;
  status?: string;
  notes?: string;
  work_date?: string;
}

export interface AttendanceRecord {
  id: number;
  employee_name: string;
  work_date: string;
  clock_in: string | null;
  clock_out: string | null;
  hours: number | string;
}

export interface AttendanceListResponse {
  records: AttendanceRecord[];
  month: string;
}

export interface AttendanceRecord {
  id: number;
  employee: number;
  employee_name: string;
  restaurant_id: number;
  work_date: string;       // Formatted as 'YYYY-MM-DD'
  clock_in: string | null; // ISO 8601 datetime string or null
  clock_out: string | null;// ISO 8601 datetime string or null
  hours: number | string;  // Calculated total hours worked
  created_at?: string;
  updated_at?: string;
}

export interface EmployeeDetail {
  id: number;
  full_name: string;
  nickname?: string;
  phone?: string;
  address?: string;
  emergency_contact?: string;
  position: string;
  employment_status: string; // e.g. 'ACTIVE', 'INACTIVE'
  date_hired?: string;
  daily_rate?: string | null;
  monthly_salary?: string | null;
  user?: number | null;
  user_username?: string | null;
}

export interface EmployeeFormData {
  full_name: string;
  nickname: string;
  phone: string;
  address: string;
  emergency_contact: string;
  position: string;
  employment_status: string;
  date_hired: string;
  daily_rate?: string | null;   // <-- Remove null
  monthly_salary?: string | null;  // <-- Remove null
}

export interface EmployeeListResponse {
  results?: EmployeeDetail[];
  count?: number;
  // Fallback if DRF pagination is disabled or custom
  [key: string]: any;
}

export interface EmployeeListItem {
  id: number;
  full_name: string;
  nickname?: string | null;
  position?: string | null;
  phone?: string | null;
  employment_status: string;
  daily_rate?: number | null;
  monthly_salary?: number | null;
}