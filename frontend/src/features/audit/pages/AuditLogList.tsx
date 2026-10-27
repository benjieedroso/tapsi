import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { auditApi } from '../api/audit';
import type { AuditLogItem, AuditActor, AuditLogListResponse } from '../types/audit.types';

interface AuditLogListProps {
  userRole?: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
}

export const AuditLogList: React.FC<AuditLogListProps> = ({ userRole }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<AuditLogListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter input states
  const [actionInput, setActionInput] = useState<string>(searchParams.get('action') || '');
  const [entityInput, setEntityInput] = useState<string>(searchParams.get('entity') || '');
  const [actorInput, setActorInput] = useState<string>(searchParams.get('actor') || '');
  const [dateFromInput, setDateFromInput] = useState<string>(searchParams.get('date_from') || '');
  const [dateToInput, setDateToInput] = useState<string>(searchParams.get('date_to') || '');

  const fetchAuditLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {};
      const action = searchParams.get('action');
      const entity = searchParams.get('entity');
      const actor = searchParams.get('actor');
      const date_from = searchParams.get('date_from');
      const date_to = searchParams.get('date_to');
      const page = searchParams.get('page');

      if (action) params.action = action;
      if (entity) params.entity = entity;
      if (actor) params.actor = actor;
      if (date_from) params.date_from = date_from;
      if (date_to) params.date_to = date_to;
      if (page) params.page = Number(page);

      const res = await auditApi.getAuditLogs(params);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams: Record<string, string> = {};
    if (actionInput) newParams.action = actionInput;
    if (entityInput) newParams.entity = entityInput;
    if (actorInput) newParams.actor = actorInput;
    if (dateFromInput) newParams.date_from = dateFromInput;
    if (dateToInput) newParams.date_to = dateToInput;
    setSearchParams(newParams);
  };

  const handlePageChange = (newPage: number) => {
    const currentParams = Object.fromEntries(searchParams.entries());
    setSearchParams({ ...currentParams, page: String(newPage) });
  };

  if (loading && !data) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading audit logs...</div>;
  }

  const isManager = userRole === 'MANAGER';
  const logs = data?.logs || [];
  const actions = data?.actions || [];
  const entities = data?.entities || [];
  const staff = data?.staff || [];

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Audit Logs</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Append-only trail (FR-160..162). {isManager && 'Read-only for Managers.'}
          </p>
        </div>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleFilterSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}
      >
        <select
          name="action"
          className="input"
          style={{ width: 'auto' }}
          value={actionInput}
          onChange={(e) => setActionInput(e.target.value)}
        >
          <option value="">All actions</option>
          {actions.map((a: string) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        <select
          name="entity"
          className="input"
          style={{ width: 'auto' }}
          value={entityInput}
          onChange={(e) => setEntityInput(e.target.value)}
        >
          <option value="">All entities</option>
          {entities.map((e: string) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>

        <select
          name="actor"
          className="input"
          style={{ width: 'auto' }}
          value={actorInput}
          onChange={(e) => setActorInput(e.target.value)}
        >
          <option value="">All users</option>
          {staff.map((s: AuditActor) => (
            <option key={s.id} value={String(s.id)}>
              {s.email}
            </option>
          ))}
        </select>

        <input
          type="date"
          name="date_from"
          value={dateFromInput}
          onChange={(e) => setDateFromInput(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />
        <input
          type="date"
          name="date_to"
          value={dateToInput}
          onChange={(e) => setDateToInput(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />
        <button type="submit" className="btn btn-secondary btn-sm">
          Filter
        </button>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Time (UTC)</th>
              <th>User</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-state">
                  <h3>No audit entries</h3>
                  <p>Entries are written automatically for logins, status changes, payments, and more.</p>
                </td>
              </tr>
            ) : (
              logs.map((entry: AuditLogItem) => {
                const createdAtFormatted = entry.created_at
                  ? entry.created_at.replace('T', ' ').substring(0, 16)
                  : '';

                return (
                  <tr key={entry.id}>
                    <td style={{ whiteSpace: 'nowrap' }}>{createdAtFormatted}</td>
                    <td>
                      {entry.actor?.email || 'system'}{' '}
                      <span className="badge badge-secondary">{entry.actor_role}</span>
                    </td>
                    <td>
                      <span className="badge badge-secondary">{entry.action}</span>
                    </td>
                    <td>
                      {entry.entity}
                      {entry.entity_id ? `#${entry.entity_id}` : ''}
                    </td>
                    <td
                      style={{
                        maxWidth: '320px',
                        fontSize: 'var(--font-size-sm)',
                        color: 'var(--gray-500)',
                        wordBreak: 'break-word',
                      }}
                    >
                      {entry.before && (
                        <>
                          before: {(() => { const s = typeof entry.before === 'string' ? entry.before : JSON.stringify(entry.before); return s.length > 80 ? s.substring(0, 80) + '...' : s; })()}
                          <br />
                        </>
                      )}
                      {entry.after && (
                        <>
                          after: {(() => { const s = typeof entry.after === 'string' ? entry.after : JSON.stringify(entry.after); return s.length > 120 ? s.substring(0, 120) + '...' : s; })()}
                        </>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {data && data.num_pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-4)' }}>
          {data.has_previous ? (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handlePageChange(data.page - 1)}
            >
              Previous
            </button>
          ) : (
            <div />
          )}
          <span style={{ color: 'var(--gray-500)' }}>
            Page {data.page} of {data.num_pages}
          </span>
          {data.has_next ? (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handlePageChange(data.page + 1)}
            >
              Next
            </button>
          ) : (
            <div />
          )}
        </div>
      )}
    </>
  );
};

export default AuditLogList;