export interface AttendanceDetail {
  id: number;
  user_name?: string;
  time_in?: string | null;
  time_out?: string | null;
  status?: string;
  notes?: string;
}

export interface AttendanceUpdatePayload {
  time_in?: string | null;
  time_out?: string | null;
  status?: string;
  notes?: string;
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

export interface EmployeeFormData {
  user?: number | null;
  full_name: string;
  position: string;
  salary_type: 'MONTHLY' | 'DAILY' | 'HOURLY';
  rate: number;
  is_active?: boolean;
}

export interface EmployeeDetail extends EmployeeFormData {
  id: number;
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

export interface EmployeeListResponse {
  employees: EmployeeListItem[];
}