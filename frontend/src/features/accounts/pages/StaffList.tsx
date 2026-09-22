import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  getStaffList,
  updateStaffRole,
  toggleStaffStatus,
  getRestaurantSettings,
} from '../api/accounts';
import type { StaffMember, StaffRole } from '../types/accounts.types';

export const StaffList: React.FC = () => {
  const location = useLocation();

  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [restaurantName, setRestaurantName] = useState<string>('your restaurant');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [flashMessage, setFlashMessage] = useState<string | null>(
    (location.state as { message?: string })?.message || null
  );

  // Current logged in user ID (can also be retrieved from an AuthContext)
  const currentUserId = 1;

  // Modal State
  const [selectedMember, setSelectedMember] = useState<StaffMember | null>(null);
  const [modalType, setModalType] = useState<'deactivate' | 'activate' | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const fetchStaffData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [staffData, settingsData] = await Promise.all([
        getStaffList(),
        getRestaurantSettings(),
      ]);
      setStaff(staffData);
      if (settingsData.name) {
        setRestaurantName(settingsData.name);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load staff list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaffData();
  }, []);

  const handleRoleChange = async (member: StaffMember, newRole: StaffRole) => {
    const confirmChange = window.confirm(
      `Change ${member.display_name}'s role to ${newRole}?`
    );

    if (!confirmChange) return;

    try {
      const updatedMember = await updateStaffRole(member.id, newRole);
      setStaff((prev) =>
        prev.map((item) => (item.id === member.id ? updatedMember : item))
      );
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update staff role.');
    }
  };

  const handleOpenModal = (member: StaffMember, type: 'deactivate' | 'activate') => {
    setSelectedMember(member);
    setModalType(type);
  };

  const handleCloseModal = () => {
    setSelectedMember(null);
    setModalType(null);
  };

  const handleStatusToggle = async () => {
    if (!selectedMember || !modalType) return;

    setActionLoading(true);
    const targetStatus = modalType === 'activate';

    try {
      const updatedMember = await toggleStaffStatus(selectedMember.id, targetStatus);
      setStaff((prev) =>
        prev.map((item) => (item.id === selectedMember.id ? updatedMember : item))
      );
      setFlashMessage(
        `Staff member ${selectedMember.display_name} has been ${
          targetStatus ? 'activated' : 'deactivated'
        }.`
      );
      handleCloseModal();
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${modalType} staff member.`);
    } finally {
      setActionLoading(false);
    }
  };

  const getRoleLabel = (role: StaffRole): string => {
    const roleLabels: Record<StaffRole, string> = {
      OWNER: 'Owner',
      MANAGER: 'Manager',
      CASHIER: 'Cashier',
      KITCHEN: 'Kitchen',
    };
    return roleLabels[role] || role;
  };

  if (loading) {
    return <div className="loading-state">Loading staff members...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Staff</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Accounts for {restaurantName}.
          </p>
        </div>
        <Link className="btn btn-primary" to="/accounts/staff/add">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add staff member
        </Link>
      </div>

      {flashMessage && (
        <div className="alert alert-success" role="alert" style={{ marginBottom: 'var(--space-4)' }}>
          {flashMessage}
        </div>
      )}

      {error && (
        <div className="alert alert-danger" role="alert" style={{ marginBottom: 'var(--space-4)' }}>
          {error}
        </div>
      )}

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {staff.length > 0 ? (
              staff.map((member) => {
                const isSelfOrOwner = member.id === currentUserId || member.role === 'OWNER';

                return (
                  <tr key={member.id}>
                    <td>{member.display_name}</td>
                    <td>{member.email}</td>
                    <td>
                      {!isSelfOrOwner ? (
                        <select
                          className="role-select"
                          value={member.role}
                          onChange={(e) => handleRoleChange(member, e.target.value as StaffRole)}
                        >
                          <option value="MANAGER">Manager</option>
                          <option value="CASHIER">Cashier</option>
                          <option value="KITCHEN">Kitchen</option>
                        </select>
                      ) : (
                        <span className={`badge badge-${member.role.toLowerCase()}`}>
                          {getRoleLabel(member.role)}
                        </span>
                      )}
                    </td>
                    <td>
                      {member.is_active ? (
                        <span className="badge badge-success">Active</span>
                      ) : (
                        <span className="badge badge-error">Inactive</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {!isSelfOrOwner && (
                        <>
                          <Link
                            to={`/accounts/staff/${member.id}/edit`}
                            className="btn btn-ghost btn-sm"
                          >
                            Edit
                          </Link>
                          <Link
                            to={`/accounts/staff/${member.id}/reset-password`}
                            className="btn btn-ghost btn-sm"
                          >
                            Reset PW
                          </Link>
                          {member.is_active ? (
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm deactivate-btn"
                              style={{ color: 'var(--color-error)' }}
                              onClick={() => handleOpenModal(member, 'deactivate')}
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm activate-btn"
                              style={{ color: 'var(--tapsi-600)' }}
                              onClick={() => handleOpenModal(member, 'activate')}
                            >
                              Activate
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} className="empty-state">
                  <h3>No staff accounts yet</h3>
                  <p>Add your first staff member to get started.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Deactivate Modal */}
      {modalType === 'deactivate' && selectedMember && (
        <div
          className="modal-overlay"
          style={{ display: 'flex' }}
          onClick={(e) => e.target === e.currentTarget && handleCloseModal()}
        >
          <div className="modal">
            <h3>Deactivate Staff Member</h3>
            <p>
              Are you sure you want to deactivate <strong>{selectedMember.display_name}</strong>? They will not be able to log in until reactivated.
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-6)' }}>
              <button className="btn btn-secondary" onClick={handleCloseModal} disabled={actionLoading}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ background: 'var(--color-error)' }}
                onClick={handleStatusToggle}
                disabled={actionLoading}
              >
                {actionLoading ? 'Deactivating...' : 'Deactivate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Activate Modal */}
      {modalType === 'activate' && selectedMember && (
        <div
          className="modal-overlay"
          style={{ display: 'flex' }}
          onClick={(e) => e.target === e.currentTarget && handleCloseModal()}
        >
          <div className="modal">
            <h3>Activate Staff Member</h3>
            <p>
              Are you sure you want to activate <strong>{selectedMember.display_name}</strong>?
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-6)' }}>
              <button className="btn btn-secondary" onClick={handleCloseModal} disabled={actionLoading}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleStatusToggle}
                disabled={actionLoading}
              >
                {actionLoading ? 'Activating...' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default StaffList;