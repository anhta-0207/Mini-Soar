export interface RemediationSummary {
  total: number;
  success: number;
  failed: number;
  error: number;
  skipped: number;
  success_rate: number;
  average_duration_seconds: number;
}

export interface RemediationRecord {
  id: number;
  event_id: string;
  event_type: string;
  host: string;
  service: string;
  action: string;
  status: string;
  duration_seconds: number;
  message: string | null;
  created_at: string;
}

export interface RemediationListResponse {
  count: number;
  items: RemediationRecord[];
}
