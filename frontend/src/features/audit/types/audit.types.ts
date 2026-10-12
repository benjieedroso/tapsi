export interface AuditActor {
  id: number;
  email: string;
}

export interface AuditLogItem {
  id: number;
  created_at: string;
  actor?: AuditActor | null;
  actor_role: string;
  action: string;
  entity: string;
  entity_id?: number | null;
  before?: string | null;
  after?: string | null;
}

export interface AuditLogListResponse {
  logs: AuditLogItem[];
  actions: string[];
  entities: string[];
  staff: AuditActor[];
  page: number;
  num_pages: number;
  has_previous: boolean;
  has_next: boolean;
}