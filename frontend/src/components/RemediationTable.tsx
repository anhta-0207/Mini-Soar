import type { RemediationRecord } from "../types/remediation";

interface RemediationTableProps {
  items: RemediationRecord[];
}

function formatDuration(value: number): string {
  if (value < 0.001) {
    return "0.0s";
  }

  return `${value.toFixed(1)}s`;
}

function formatTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function getStatusClass(status: string): string {
  return `status-badge status-badge--${status.toLowerCase()}`;
}

export default function RemediationTable({
  items,
}: RemediationTableProps) {
  if (items.length === 0) {
    return (
      <div className="table-empty">
        No remediation events recorded yet.
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="remediation-table">
        <thead>
          <tr>
            <th>Event Type</th>
            <th>Service</th>
            <th>Action</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Time</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                <div className="event-cell">
                  <span className="event-type">
                    {item.event_type}
                  </span>

                  <span className="event-id">
                    #{item.event_id}
                  </span>
                </div>
              </td>

              <td>
                <code className="service-name">
                  {item.service}
                </code>
              </td>

              <td>
                <span className="action-name">
                  {item.action}
                </span>
              </td>

              <td>
                <span className={getStatusClass(item.status)}>
                  {item.status}
                </span>
              </td>

              <td>
                {formatDuration(item.duration_seconds)}
              </td>

              <td className="table-time">
                {formatTime(item.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
