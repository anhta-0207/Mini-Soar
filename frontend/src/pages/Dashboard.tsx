import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import DistributionChart from "../components/DistributionChart";
import RemediationTable from "../components/RemediationTable";
import SummaryCard from "../components/SummaryCard";

import {
  getRemediationDistribution,
  getRemediations,
  getRemediationSummary,
} from "../services/api";

import type {
  RemediationDistribution,
  RemediationRecord,
  RemediationSummary,
} from "../types/remediation";

const AUTO_REFRESH_MS = 15_000;

type LoadMode = "initial" | "manual" | "auto";

export default function Dashboard() {
  const [summary, setSummary] =
    useState<RemediationSummary | null>(null);

  const [distribution, setDistribution] =
    useState<RemediationDistribution | null>(null);

  const [remediations, setRemediations] =
    useState<RemediationRecord[]>([]);

  const [statusFilter, setStatusFilter] =
    useState("");

  const [eventTypeFilter, setEventTypeFilter] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [lastUpdated, setLastUpdated] =
    useState<Date | null>(null);

  const requestInProgress = useRef(false);
  const hasLoadedOnce = useRef(false);

  const loadDashboard = useCallback(
    async (mode: LoadMode = "auto") => {
      if (requestInProgress.current) {
        return;
      }

      requestInProgress.current = true;

      try {
        if (mode === "initial") {
          setLoading(true);
        }

        if (mode === "manual") {
          setRefreshing(true);
        }

        const [
          summaryData,
          remediationData,
          distributionData,
        ] = await Promise.all([
          getRemediationSummary(),

          getRemediations({
            limit: 10,
            status:
              statusFilter || undefined,
            eventType:
              eventTypeFilter || undefined,
          }),

          getRemediationDistribution(),
        ]);

        setSummary(summaryData);

        setRemediations(
          remediationData.items
        );

        setDistribution(
          distributionData
        );

        setLastUpdated(new Date());

        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard"
        );
      } finally {
        if (mode === "initial") {
          setLoading(false);
        }

        if (mode === "manual") {
          setRefreshing(false);
        }

        requestInProgress.current = false;
      }
    },
    [
      statusFilter,
      eventTypeFilter,
    ]
  );

  useEffect(() => {
    const mode: LoadMode =
      hasLoadedOnce.current
        ? "auto"
        : "initial";

    hasLoadedOnce.current = true;

    void loadDashboard(mode);

    const intervalId =
      window.setInterval(
        () => {
          void loadDashboard("auto");
        },
        AUTO_REFRESH_MS
      );

    return () => {
      window.clearInterval(
        intervalId
      );
    };
  }, [loadDashboard]);

  function clearFilters() {
    setStatusFilter("");
    setEventTypeFilter("");
  }

  function formatLastUpdated(): string {
    if (!lastUpdated) {
      return "Not updated yet";
    }

    return lastUpdated.toLocaleTimeString();
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-header__eyebrow">
            SECURITY AUTOMATION
          </p>

          <h1>
            Mini-SOAR Dashboard
          </h1>

          <p className="dashboard-header__subtitle">
            Event-driven monitoring,
            automated remediation and
            incident audit
          </p>
        </div>

        <div className="header-status">
          <div className="refresh-info">
            <span>
              Auto-refresh every 15s
            </span>

            <span>
              Last updated:{" "}
              {formatLastUpdated()}
            </span>
          </div>

          <div
            className={`system-status ${error
              ? "system-status--error"
              : "system-status--online"
              }`}
          >
            <span className="system-status__dot" />

            {error
              ? "API Unavailable"
              : "Operational"}
          </div>
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
            Unable to load Mini-SOAR
            dashboard.
          </strong>

          <span>
            {error}
          </span>
        </section>
      )}

      {!loading && summary && (
        <>
          <section className="summary-grid">
            <SummaryCard
              label="Total Incidents"
              value={summary.total}
              description="Recorded remediation events"
            />

            <SummaryCard
              label="Success Rate"
              value={`${summary.success_rate.toFixed(
                1
              )}%`}
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
              value={`${summary.average_duration_seconds.toFixed(
                1
              )}s`}
              description="Average successful recovery time"
            />
          </section>

          {distribution && (
            <section className="analytics-grid">
              <DistributionChart
                eyebrow="REMEDIATION OUTCOMES"
                title="Status Distribution"
                data={
                  distribution.status
                }
              />

              <DistributionChart
                eyebrow="INCIDENT TYPES"
                title="Event Distribution"
                data={
                  distribution.event_type
                }
              />
            </section>
          )}

          <section className="dashboard-panel">
            <div className="dashboard-panel__header">
              <div>
                <p className="section-eyebrow">
                  REMEDIATION ACTIVITY
                </p>

                <h2>
                  Recent Remediations
                </h2>
              </div>

              <span className="record-count">
                {remediations.length} events
              </span>
            </div>

            <div className="remediation-toolbar">
              <div className="filter-group">
                <label htmlFor="status-filter">
                  Status
                </label>

                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    All statuses
                  </option>

                  <option value="SUCCESS">
                    SUCCESS
                  </option>

                  <option value="SKIPPED">
                    SKIPPED
                  </option>

                  <option value="FAILED">
                    FAILED
                  </option>

                  <option value="ERROR">
                    ERROR
                  </option>
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="event-filter">
                  Event Type
                </label>

                <select
                  id="event-filter"
                  value={eventTypeFilter}
                  onChange={(event) =>
                    setEventTypeFilter(
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    All event types
                  </option>

                  <option value="CONTAINER_DOWN">
                    CONTAINER_DOWN
                  </option>

                  <option value="CONTAINER_UNHEALTHY">
                    CONTAINER_UNHEALTHY
                  </option>

                  <option value="HIGH_CPU">
                    HIGH_CPU
                  </option>
                </select>
              </div>

              <div className="toolbar-actions">
                {(statusFilter ||
                  eventTypeFilter) && (
                    <button
                      type="button"
                      className="toolbar-button toolbar-button--secondary"
                      onClick={
                        clearFilters
                      }
                    >
                      Clear
                    </button>
                  )}

                <button
                  type="button"
                  className="toolbar-button"
                  onClick={() =>
                    void loadDashboard(
                      "manual"
                    )
                  }
                  disabled={
                    refreshing
                  }
                >
                  {refreshing
                    ? "Refreshing..."
                    : "Refresh"}
                </button>
              </div>
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