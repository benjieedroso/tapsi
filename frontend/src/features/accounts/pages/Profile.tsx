import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProfile, updateProfile } from '../api/accounts';
import type { UserProfile, ApiErrorResponse } from '../types/accounts.types';

export const Profile: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const [initialLoading, setInitialLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    firstName?: string;
    lastName?: string;
    avatar?: string;
  }>({});

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const data = await getProfile();
        setProfile(data);
        setFirstName(data.first_name || '');
        setLastName(data.last_name || '');
        if (data.avatar) {
          setAvatarPreview(data.avatar);
        }
      } catch (err) {
        setErrorMessage('Failed to load profile details.');
      } finally {
        setInitialLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      setAvatarPreview(URL.createObjectURL(file));
      setFieldErrors((prev) => ({ ...prev, avatar: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      const updated = await updateProfile({
        first_name: firstName,
        last_name: lastName,
        avatar: avatarFile,
      });

      setProfile(updated);
      setSuccessMessage('Profile updated successfully.');
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setErrorMessage(apiErr.detail);
      } else {
        setFieldErrors({
          firstName: Array.isArray(apiErr.first_name) ? apiErr.first_name[0] : undefined,
          lastName: Array.isArray(apiErr.last_name) ? apiErr.last_name[0] : undefined,
          avatar: Array.isArray(apiErr.avatar) ? apiErr.avatar[0] : undefined,
        });
        if (!apiErr.first_name && !apiErr.last_name && !apiErr.avatar) {
          setErrorMessage('Failed to save profile. Please check your inputs.');
        }
      }
    } finally {
      setSaving(false);
    }
  };

  if (initialLoading) {
    return (
      <section className="profile-card">
        <p>Loading profile...</p>
      </section>
    );
  }

  return (
    <section className="profile-card">
      <h1>Your profile</h1>
      {profile?.email && <p className="profile-email">{profile.email}</p>}

      {avatarPreview && (
        <img
          className="profile-avatar"
          src={avatarPreview}
          alt="Your avatar"
        />
      )}

      {successMessage && (
        <div className="alert alert-success" role="alert">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger" role="alert">
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} encType="multipart/form-data" noValidate>
        <div className="field">
          <label htmlFor="firstName">First Name</label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            disabled={saving}
          />
          {fieldErrors.firstName && (
            <span className="error-message">{fieldErrors.firstName}</span>
          )}
        </div>

        <div className="field">
          <label htmlFor="lastName">Last Name</label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            disabled={saving}
          />
          {fieldErrors.lastName && (
            <span className="error-message">{fieldErrors.lastName}</span>
          )}
        </div>

        <div className="field">
          <label htmlFor="avatar">Avatar Image</label>
          <input
            type="file"
            id="avatar"
            name="avatar"
            accept="image/*"
            onChange={handleFileChange}
            disabled={saving}
          />
          {fieldErrors.avatar && (
            <span className="error-message">{fieldErrors.avatar}</span>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%' }}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save profile'}
        </button>
      </form>

      <div className="profile-links">
        <Link to="/accounts/email-change">Change email</Link>
        <span>·</span>
        <Link to="/accounts/change-password">Change password</Link>
      </div>
    </section>
  );
};

export default Profile;