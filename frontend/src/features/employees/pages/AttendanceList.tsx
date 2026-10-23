// src/components/AttendanceList.tsx

import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { employeesApi } from '../api/employees';
import type { AttendanceRecord } from '../types/employees.types';

interface AttendanceListProps {
  userRole?: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
}

export const AttendanceList: React.FC<AttendanceListProps> = ({ userRole }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [month, setMonth] = useState<string>(searchParams.get('month') || '');
  const [clocking, setClocking] = useState<boolean>(false);

  const fetchAttendance = useCallback(async () => {
    try {
      const params: { month?: string } = {};
      const monthParam = searchParams.get('month');
      if (monthParam) params.month = monthParam;

      const res: AttendanceRecord[] = await employeesApi.getAttendanceList(params);
      setRecords(res);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load attendance records.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchAttendance();
  }, [fetchAttendance]);

  const handleClock = async (action: 'in' | 'out') => {
    setClocking(true);
    setError(null);
    try {
      if (action === 'in') {
        await employeesApi.clockIn();
      } else {
        await employeesApi.clockOut();
      }
      await fetchAttendance();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to clock ${action}.`);
    } finally {
      setClocking(false);
    }
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (month) params.month = month;
    setSearchParams(params);
  };

  const isOwnerOrManager = userRole === 'OWNER' || userRole === 'MANAGER';

  if (loading && records.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading attendance...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Attendance</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Clock in and out for your linked employee profile (FR-122).
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => handleClock('in')}
            disabled={clocking}
          >
            {clocking ? 'Processing...' : 'Clock in'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleClock('out')}
            disabled={clocking}
          >
            {clocking ? 'Processing...' : 'Clock out'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleFilterSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)' }}
      >
        <input
          type="month"
          name="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
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
              <th>Employee</th>
              <th>Date</th>
              <th>Clock In</th>
              <th>Clock Out</th>
              <th style={{ textAlign: 'right' }}>Hours</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-state">
                  <h3>No attendance records</h3>
                  <p>Clock in to start tracking your hours.</p>
                </td>
              </tr>
            ) : (
              records.map((record: AttendanceRecord) => (
                <tr key={record.id}>
                  <td>{record.employee_name}</td>
                  <td>
                    {new Date(record.work_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td>
                    {record.clock_in
                      ? new Date(record.clock_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : '—'}
                  </td>
                  <td>
                    {record.clock_out
                      ? new Date(record.clock_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : '—'}
                  </td>
                  <td style={{ textAlign: 'right' }}>{record.hours}</td>
                  <td style={{ textAlign: 'right' }}>
                    {isOwnerOrManager && (
                      <Link to={`/attendance/${record.id}/edit`} className="btn btn-ghost btn-sm">
                        Edit
                      </Link>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default AttendanceList;