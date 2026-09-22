export interface ChangeInitialPasswordPayload {
  new_password: string;
  confirm_password: string;
}

export interface ApiErrorResponse {
  detail?: string;
  new_password?: string[];
  confirm_password?: string[];
  [key: string]: unknown;
}