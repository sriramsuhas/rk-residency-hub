import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { auditApi } from '../api/audit';
import './RoomListing.css';
import './AuditLog.css';

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AuditLog() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const pageSize = 25;

  const load = useCallback(() => {
    setLoading(true);
    auditApi
      .search({ page, page_size: pageSize, action: actionFilter || undefined })
      .then((res) => {
        setItems(res.data.data.items);
        setTotal(res.data.data.total);
      })
      .finally(() => setLoading(false));
  }, [page, actionFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <TopNav />
      <div className="audit-page">
        <div className="audit-header">
          <div>
            <h1>Audit log</h1>
            <p>{total} recorded event{total === 1 ? '' : 's'}</p>
          </div>
          <input
            type="text"
            placeholder="Filter by action, e.g. BOOKING_CREATED"
            value={actionFilter}
            onChange={(e) => {
              setPage(1);
              setActionFilter(e.target.value);
            }}
          />
        </div>

        {loading && <p className="listing-status">Loading…</p>}

        <table className="audit-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Action</th>
              <th>User</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((entry) => (
              <tr key={entry.id}>
                <td>{formatTimestamp(entry.created_at)}</td>
                <td>
                  <span className="audit-action">{entry.action}</span>
                </td>
                <td>{entry.user ? entry.user.full_name : 'System'}</td>
                <td>{entry.entity_type ? `${entry.entity_type} #${entry.entity_id}` : '—'}</td>
                <td className="audit-details">{entry.details || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && items.length === 0 && <p className="listing-status">No matching events.</p>}

        {totalPages > 1 && (
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
