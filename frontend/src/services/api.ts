import type {
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

export async function getRemediationSummary(): Promise<RemediationSummary> {
  return request<RemediationSummary>(
    `${API_BASE}/remediations/summary`
  );
}

export async function getRemediations(
  limit = 20
): Promise<RemediationListResponse> {
  return request<RemediationListResponse>(
    `${API_BASE}/remediations?limit=${limit}`
  );
}
