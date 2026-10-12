import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { employeesApi } from '../api/employees';
import type { EmployeeListItem } from '../types/employees.types';

interface EmployeeListProps {
  userRole?: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
}

export const EmployeeList: React.FC<EmployeeListProps> = ({ userRole }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [employees, setEmployees] = useState<EmployeeListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>(searchParams.get('q') || '');
  const [searchInput, setSearchInput] = useState<string>(searchParams.get('q') || '');
  const [processingId, setProcessingId] = useState<number | null>(null);

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const params: { q?: string } = {};
      const qParam = searchParams.get('q');
      if (qParam) params.q = qParam;

      const res = await employeesApi.getEmployeeList(params);
      setEmployees(res.employees || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput);
    if (searchInput) {
      setSearchParams({ q: searchInput });
    } else {
      setSearchParams({});
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Deactivate ${name}?`)) return;
    setProcessingId(id);
    try {
      await employeesApi.deleteEmployee(id);
      await fetchEmployees();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to deactivate employee.');
    } finally {
      setProcessingId(null);
    }
  };

  const isOwnerOrManager = userRole === 'OWNER' || userRole === 'MANAGER';

  if (loading && employees.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading employees...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Employees</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Staff records — salary is visible only to Owner/Manager (FR-121).
          </p>
        </div>
        <Link className="btn btn-primary" to="/employees/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add employee
        </Link>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleSearchSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)', maxWidth: '400px' }}
      >
        <input
          type="text"
          name="q"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name..."
          className="input"
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-secondary btn-sm">
          Search
        </button>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Position</th>
              <th>Phone</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Daily Rate</th>
              <th style={{ textAlign: 'right' }}>Monthly Salary</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  <h3>No employees yet</h3>
                  <p>Add staff records for attendance tracking.</p>
                  <Link to="/employees/create" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    Add employee
                  </Link>
                </td>
              </tr>
            ) : (
              employees.map((employee: EmployeeListItem) => {
                const isActive = employee.employment_status === 'ACTIVE';
                return (
                  <tr key={employee.id}>
                    <td>
                      <strong>{employee.full_name}</strong>
                      {employee.nickname && <span style={{ color: 'var(--gray-400)' }}> ({employee.nickname})</span>}
                    </td>
                    <td>{employee.position || '—'}</td>
                    <td>{employee.phone || '—'}</td>
                    <td>
                      {isActive ? (
                        <span className="badge badge-success">Active</span>
                      ) : (
                        <span className="badge badge-warning">Inactive</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {isOwnerOrManager && employee.daily_rate != null ? `₱${employee.daily_rate.toFixed(2)}` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {isOwnerOrManager && employee.monthly_salary != null ? `₱${employee.monthly_salary.toFixed(2)}` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link to={`/employees/${employee.id}/edit`} className="btn btn-ghost btn-sm">
                        Edit
                      </Link>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--color-error)' }}
                        onClick={() => handleDelete(employee.id, employee.full_name)}
                        disabled={processingId === employee.id}
                      >
                        Deactivate
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default EmployeeList;