import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import RoleAvatar from '../components/RoleAvatar';
import { userManagementApi } from '../api/userManagement';
import './ManageUsers.css';

const ROLES = ['CUSTOMER', 'RECEPTION', 'HOUSEKEEPING', 'OWNER'];

export default function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyUserId, setBusyUserId] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    userManagementApi
      .list({ page_size: 100, search: search || undefined, role: roleFilter || undefined })
      .then((res) => {
        setUsers(res.data.data.items);
        setTotal(res.data.data.total);
      })
      .catch(() => setError('Could not load users.'))
      .finally(() => setLoading(false));
  }, [search, roleFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRoleChange(user, newRole) {
    if (newRole === user.role) return;
    if (!window.confirm(`Change ${user.full_name}'s role to ${newRole}?`)) return;
    setBusyUserId(user.id);
    setError('');
    try {
      await userManagementApi.changeRole(user.id, newRole);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not change role.');
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleStatusToggle(user) {
    const nextActive = !user.is_active;
    if (!window.confirm(`${nextActive ? 'Activate' : 'Deactivate'} ${user.full_name}'s account?`)) return;
    setBusyUserId(user.id);
    setError('');
    try {
      await userManagementApi.changeStatus(user.id, nextActive);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not change account status.');
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="manage-users-page">
        <div className="manage-users-header">
          <div>
            <h1>Users &amp; staff</h1>
            <p>{total} account{total === 1 ? '' : 's'}</p>
          </div>
          <div className="manage-users-filters">
            <input
              type="text"
              placeholder="Search by name or email"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="">All roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="listing-status">Loading users...</p>}

        {!loading && (
          <table className="users-table">
            <thead>
              <tr>
                <th></th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <RoleAvatar role={u.role} className="users-table__avatar" />
                  </td>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <select
                      value={u.role}
                      disabled={busyUserId === u.id}
                      onChange={(e) => handleRoleChange(u, e.target.value)}
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <span className={`users-table__status ${u.is_active ? 'users-table__status--active' : 'users-table__status--inactive'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="users-table__toggle-btn"
                      disabled={busyUserId === u.id}
                      onClick={() => handleStatusToggle(u)}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && users.length === 0 && <p className="listing-status">No users found.</p>}
      </div>
    </div>
  );
}
