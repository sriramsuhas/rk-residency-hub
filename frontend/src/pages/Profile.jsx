import { useState } from 'react';
import TopNav from '../components/TopNav';
import RoleAvatar from '../components/RoleAvatar';
import { useAuth } from '../context/AuthContext';
import { authApi, userApi } from '../api/auth';
import '../styles/forms.css';
import './Profile.css';

export default function Profile() {
  const { user, refreshCurrentUser } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [profileMsg, setProfileMsg] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState(null);
  const [savingPassword, setSavingPassword] = useState(false);

  if (!user) return null;

  async function handleProfileSave(e) {
    e.preventDefault();
    setProfileMsg(null);
    setSavingProfile(true);
    try {
      await userApi.updateProfile({ full_name: fullName, phone });
      await refreshCurrentUser();
      setProfileMsg({ type: 'success', text: 'Profile updated.' });
    } catch (err) {
      setProfileMsg({ type: 'error', text: err.response?.data?.message || 'Could not update profile.' });
    } finally {
      setSavingProfile(false);
    }
  }

  async function handlePasswordSave(e) {
    e.preventDefault();
    setPasswordMsg(null);

    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'New password must be at least 8 characters.' });
      return;
    }

    setSavingPassword(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setPasswordMsg({ type: 'success', text: 'Password changed. Use it next time you sign in.' });
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      setPasswordMsg({ type: 'error', text: err.response?.data?.message || 'Could not change password.' });
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="profile-page">
        <h1 className="profile-page__title">Your profile</h1>

        <section className="profile-card">
          <div className="profile-card__avatar-row">
            <RoleAvatar role={user.role} className="profile-card__avatar" />
            <div>
              <p className="profile-card__role-label">{user.role}</p>
              <p className={`profile-card__status profile-card__status--${user.is_active ? 'active' : 'inactive'}`}>
                {user.is_active ? 'Account active' : 'Account deactivated'}
              </p>
            </div>
          </div>

          <h2 className="profile-card__heading">Basic details</h2>
          {profileMsg && <div className={`alert alert-${profileMsg.type}`}>{profileMsg.text}</div>}
          <form onSubmit={handleProfileSave}>
            <div className="form-field">
              <label htmlFor="full_name">Full name</label>
              <input id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div className="form-field">
              <label>Email</label>
              <input value={user.email} disabled />
              <p className="form-hint">Email can't be changed here.</p>
            </div>
            <div className="form-field">
              <label htmlFor="phone">Phone</label>
              <input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <button className="btn-primary" type="submit" disabled={savingProfile}>
              {savingProfile ? 'Saving…' : 'Save changes'}
            </button>
          </form>
        </section>

        <section className="profile-card">
          <h2 className="profile-card__heading">Change password</h2>
          {passwordMsg && <div className={`alert alert-${passwordMsg.type}`}>{passwordMsg.text}</div>}
          <form onSubmit={handlePasswordSave}>
            <div className="form-field">
              <label htmlFor="current_password">Current password</label>
              <input
                id="current_password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <div className="form-field">
              <label htmlFor="new_password">New password</label>
              <input
                id="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <button className="btn-primary" type="submit" disabled={savingPassword}>
              {savingPassword ? 'Updating…' : 'Update password'}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
