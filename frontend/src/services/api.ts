import type {
  RemediationDistribution,
  RemediationListResponse,
  RemediationSummary,
} from "../types/remediation";

const API_BASE = "/api/v1";

async function request<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

export interface RemediationFilters {
  limit?: number;
  status?: string;
  eventType?: string;
}

export async function getRemediationSummary():
  Promise<RemediationSummary> {
  return request<RemediationSummary>(
    `${API_BASE}/remediations/summary`
  );
}

export async function getRemediationDistribution():
  Promise<RemediationDistribution> {
  return request<RemediationDistribution>(
    `${API_BASE}/remediations/distribution`
  );
}

export async function getRemediations(
  filters: RemediationFilters = {}
): Promise<RemediationListResponse> {
  const params = new URLSearchParams();

  params.set(
    "limit",
    String(filters.limit ?? 20)
  );

  if (filters.status) {
    params.set(
      "status",
      filters.status
    );
  }

  if (filters.eventType) {
    params.set(
      "event_type",
      filters.eventType
    );
  }

  return request<RemediationListResponse>(
    `${API_BASE}/remediations?${params.toString()}`
  );
}
