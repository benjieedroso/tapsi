import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { employeesApi } from '../api/employees';
import type { EmployeeDetail } from '../types/employees.types'; 
import type { UserRole } from '../../orders/types/orders.types';


export const EmployeeList: React.FC = () => {
  const [employees, setEmployees] = useState<EmployeeDetail[]>([]);
  const [currentUserRole, setCurrentUserRole] = useState<UserRole | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchEmployees = useCallback(async (query?: string) => {
    setLoading(true);
    try {
      const data = await employeesApi.getEmployeeList({ q: query });
      
      // Handle response whether it's an array or a wrapped object containing role info
      if (Array.isArray(data)) {
        setEmployees(data);
      } else {
        setEmployees((data as any).results || (data as any).employees || []);
        if ((data as any).currentUserRole) {
          setCurrentUserRole((data as any).currentUserRole);
        }
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEmployees(searchQuery);
  };

  // FR-121 Check: Only OWNER or MANAGER can see salaries
  const canViewSalary = currentUserRole === 'OWNER' || currentUserRole === 'MANAGER';
  const colSpanCount = canViewSalary ? 7 : 5;

  return (
    <div style={{ padding: 'var(--space-6)' }}>
      <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <div>
          <h1>Employees</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Staff records — salary is visible only to Owner/Manager (FR-121).
          </p>
        </div>
        <Link className="btn btn-primary" to="/employees/create" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
          Add employee
        </Link>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-5)' }}>
        <input
          type="text"
          className="input"
          placeholder="Search by name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ maxWidth: '320px' }}
        />
        <button type="submit" className="btn btn-secondary">Search</button>
      </form>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <div className="table-card" style={{ background: 'var(--bg-surface, #fff)', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Position</th>
              <th>Phone</th>
              <th>Status</th>
              {canViewSalary && (
                <>
                  <th style={{ textAlign: 'right' }}>Daily Rate</th>
                  <th style={{ textAlign: 'right' }}>Monthly Salary</th>
                </>
              )}
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={colSpanCount} style={{ textAlign: 'center', padding: 'var(--space-5)' }}>Loading employees...</td>
              </tr>
            ) : employees.length === 0 ? (
              <tr>
                <td colSpan={colSpanCount} className="empty-state" style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
                  <h3>No employees yet</h3>
                  <p style={{ color: 'var(--gray-500)', marginBottom: 'var(--space-4)' }}>Add staff records for attendance tracking.</p>
                  <Link to="/employees/create" className="btn btn-primary">Add employee</Link>
                </td>
              </tr>
            ) : (
              employees.map((emp) => (
                <tr key={emp.id}>
                  <td style={{ fontWeight: 600 }}>
                    <Link to={`/employees/${emp.id}`} style={{ color: 'var(--tapsi-700, #047857)' }}>
                      {emp.full_name}
                    </Link>
                    {emp.nickname && <span style={{ color: 'var(--gray-500)', fontWeight: 400, fontSize: 'var(--font-size-xs)', display: 'block' }}>"{emp.nickname}"</span>}
                  </td>
                  <td>{emp.position || '—'}</td>
                  <td>{emp.phone || '—'}</td>
                  <td>
                    <span className={`badge ${emp.employment_status === 'active' ? 'badge-success' : 'badge-secondary'}`}>
                      {emp.employment_status}
                    </span>
                  </td>
                  {canViewSalary && (
                    <>
                      <td style={{ textAlign: 'right' }}>{emp.daily_rate ? `₱${parseFloat(emp.daily_rate).toFixed(2)}` : '—'}</td>
                      <td style={{ textAlign: 'right' }}>{emp.monthly_salary ? `₱${parseFloat(emp.monthly_salary).toFixed(2)}` : '—'}</td>
                    </>
                  )}
                  <td style={{ textAlign: 'right' }}>
                    <Link to={`/employees/${emp.id}/edit`} className="btn btn-ghost btn-sm">Edit</Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EmployeeList;