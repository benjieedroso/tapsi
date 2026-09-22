export interface ChangeInitialPasswordPayload {
  new_password: string;
  confirm_password: string;
}

export interface ApiErrorResponse {
  detail?: string;
  email?: string[];
  first_name?: string[];
  last_name?: string[];
  role?: string[];
  avatar?: string[];
  new_password?: string[];
  confirm_password?: string[];
  new_email?: string[];
  name?: string[];
  address?: string[];
  contact_number?: string[];
  tin?: string[];
  receipt_footer?: string[];
  is_vat_registered?: string[];
  [key: string]: string[] | string | unknown;
}

export interface RequestEmailChangePayload {
  new_email: string;
}

export interface EmailChangeResponse {
  detail: string;
}

export interface PasswordResetConfirmPayload {
  uid: string;
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetConfirmResponse {
  detail: string;
}

export interface RequestPasswordResetPayload {
  email: string;
}

export interface RequestPasswordResetResponse {
  detail?: string;
}

export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  avatar?: string | null;
}

export interface UpdateProfilePayload {
  first_name: string;
  last_name: string;
  avatar?: File | null;
}

//restuarant_settings.html
export interface RestaurantSettingsData {
  id?: number;
  name: string;
  address: string;
  contact_number: string;
  tin: string;
  receipt_footer: string;
  is_vat_registered: boolean;
}

export type UpdateRestaurantSettingsPayload = Omit<RestaurantSettingsData, 'id'>;


//staff_form.html
export interface CreateStaffPayload {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

//staff_list
export type StaffRole = 'OWNER' | 'MANAGER' | 'CASHIER' | 'KITCHEN';

//staff_edit.html
export interface StaffMember {
  id: number;
  email: string;
  display_name: string;
  first_name: string;
  last_name: string;
  role: StaffRole;
  is_active: boolean;
}

export interface UpdateStaffPayload {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_active?: boolean;
}


export interface UpdateStaffRolePayload {
  role: StaffRole;
}

export interface ToggleStaffStatusPayload {
  is_active: boolean;
}

export interface ResetStaffPasswordPayload {
  new_password: string;
  confirm_password: string;
}

export interface ResetStaffPasswordErrors {
  new_password?: string[];
  confirm_password?: string[];
  non_field_errors?: string[];
  detail?: string;
}