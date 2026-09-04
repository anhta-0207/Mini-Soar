import { useEffect, useState } from "react";

import RemediationTable from "../components/RemediationTable";
import SummaryCard from "../components/SummaryCard";

import {
  getRemediations,
  getRemediationSummary,
} from "../services/api";

import type {
  RemediationRecord,
  RemediationSummary,
} from "../types/remediation";

export default function Dashboard() {
  const [summary, setSummary] =
    useState<RemediationSummary | null>(null);

  const [remediations, setRemediations] =
    useState<RemediationRecord[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);

        const [summaryData, remediationData] =
          await Promise.all([
            getRemediationSummary(),
            getRemediations(10),
          ]);

        setSummary(summaryData);
        setRemediations(remediationData.items);

        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard"
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-header__eyebrow">
            SECURITY AUTOMATION
          </p>

          <h1>Mini-SOAR Dashboard</h1>

          <p className="dashboard-header__subtitle">
            Event-driven monitoring, automated remediation
            and incident audit
          </p>
        </div>

        <div
          className={`system-status ${
            error
              ? "system-status--error"
              : "system-status--online"
          }`}
        >
          <span className="system-status__dot" />

          {error ? "API Unavailable" : "Operational"}
        </div>
      </header>

      {loading && (
        <section className="dashboard-message">
          Loading remediation data...
        </section>
      )}

      {error && (
        <section className="dashboard-message dashboard-message--error">
          <strong>
            Unable to load Mini-SOAR dashboard.
          </strong>

          <span>{error}</span>
        </section>
      )}

      {!loading && !error && summary && (
        <>
          <section className="summary-grid">
            <SummaryCard
              label="Total Incidents"
              value={summary.total}
              description="Recorded remediation events"
            />

            <SummaryCard
              label="Success Rate"
              value={`${summary.success_rate.toFixed(1)}%`}
              description={`${summary.success} successful remediations`}
              variant="success"
            />

            <SummaryCard
              label="Skipped"
              value={summary.skipped}
              description="Blocked by remediation policy"
              variant="warning"
            />

            <SummaryCard
              label="Avg. Remediation"
              value={`${summary.average_duration_seconds.toFixed(1)}s`}
              description="Average successful recovery time"
            />
          </section>

          <section className="dashboard-panel">
            <div className="dashboard-panel__header">
              <div>
                <p className="section-eyebrow">
                  REMEDIATION ACTIVITY
                </p>

                <h2>Recent Remediations</h2>
              </div>

              <span className="record-count">
                {remediations.length} latest events
              </span>
            </div>

            <RemediationTable
              items={remediations}
            />
          </section>
        </>
      )}
    </div>
  );
}
