import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { employeesApi } from '../api/employees';

export const AttendanceForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [timeIn, setTimeIn] = useState<string>('');
  const [timeOut, setTimeOut] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!id) return;
    const fetchAttendance = async () => {
      try {
        const data = await employeesApi.getAttendanceDetail(Number(id));
        setTimeIn(data.time_in ? data.time_in.slice(0, 16) : '');
        setTimeOut(data.time_out ? data.time_out.slice(0, 16) : '');
        setStatus(data.status || '');
        setNotes(data.notes || '');
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load attendance record.']);
      } finally {
        setLoading(false);
      }
    };
    fetchAttendance();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const formatToDjangoDateTime = (val: string) => {
      if (!val) return null;
      return val.length === 16 ? `${val}:00` : val;
    };

    const formattedClockIn = formatToDjangoDateTime(timeIn);
    
    // Derive the work_date from the updated Time In value (YYYY-MM-DD)
    const derivedWorkDate = formattedClockIn ? formattedClockIn.split('T')[0] : undefined;

    const payload = {
      work_date: derivedWorkDate, // Sends the new date (e.g., '2026-10-25')
      clock_in: formattedClockIn,
      clock_out: formatToDjangoDateTime(timeOut),
      status: status || undefined,
      notes: notes || undefined,
    };

    try {
      await employeesApi.updateAttendance(Number(id), payload as any);
      navigate('/attendance');
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
        }
        setFieldErrors(data);
      } else {
        setNonFieldErrors(['An unexpected error occurred. Please try again.']);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading attendance record...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Edit Attendance</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Edits are audit-logged with before/after values (FR-122).
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          <div className="field">
            <label htmlFor="id_time_in">Time In</label>
            <input
              type="datetime-local"
              id="id_time_in"
              className="input"
              value={timeIn}
              onChange={(e) => setTimeIn(e.target.value)}
            />
            {fieldErrors.time_in && (
              <ul className="errorlist">
                <li>{fieldErrors.time_in}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_time_out">Time Out</label>
            <input
              type="datetime-local"
              id="id_time_out"
              className="input"
              value={timeOut}
              onChange={(e) => setTimeOut(e.target.value)}
            />
            {fieldErrors.time_out && (
              <ul className="errorlist">
                <li>{fieldErrors.time_out}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_status">Status</label>
            <input
              type="text"
              id="id_status"
              className="input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            />
            {fieldErrors.status && (
              <ul className="errorlist">
                <li>{fieldErrors.status}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_notes">Notes</label>
            <textarea
              id="id_notes"
              className="input"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            {fieldErrors.notes && (
              <ul className="errorlist">
                <li>{fieldErrors.notes}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save changes'}
            </button>
            <Link to="/attendance" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default AttendanceForm;