export interface NotificationItem {
  id: number;
  unread: boolean;
  type_display: string;
  title: string;
  body?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
}