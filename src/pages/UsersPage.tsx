import React, { useState, useEffect } from 'react';
import { User, CreateUserRequest, UpdateUserRequest } from '../types';
import { userService, UserListParams } from '../services/user.service';
import { authService } from '../services/auth.service';
import { SimplePermissionManager } from '../components/user/SimplePermissionManager';
import { RolePermissionMatrix } from '../components/user/RolePermissionMatrix';

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  user?: User;
  onUserSaved: () => void;
}

const UserModal: React.FC<UserModalProps> = ({ isOpen, onClose, user, onUserSaved }) => {
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'user',
  });
  const [customPermissions, setCustomPermissions] = useState(false);
  const [permissions, setPermissions] = useState(userService.getDefaultPermissionsByRole('user'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        role: user.role,
      });
      setPermissions(user.permissions);
      const defaultPerms = userService.getDefaultPermissionsByRole(user.role);
      setCustomPermissions(JSON.stringify(user.permissions) !== JSON.stringify(defaultPerms));
    } else {
      setFormData({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'user',
      });
      setPermissions(userService.getDefaultPermissionsByRole('user'));
      setCustomPermissions(false);
    }
    setError(null);
  }, [user]);

  const handleRoleChange = (role: 'admin' | 'user' | 'viewer') => {
    setFormData({ ...formData, role });
    if (!customPermissions) {
      setPermissions(userService.getDefaultPermissionsByRole(role));
    }
  };

  const handlePermissionChange = (key: keyof typeof permissions, value: boolean) => {
    setPermissions({ ...permissions, [key]: value });
    setCustomPermissions(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (user) {
        // For updates, exclude password if empty and prepare update data
        const updateData: UpdateUserRequest = {
          username: formData.username,
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          role: formData.role,
          permissions: customPermissions ? permissions : undefined,
        };

        await userService.updateUser(user.id, updateData);

        // Handle password separately if provided
        if (formData.password) {
          await userService.changePassword(user.id, formData.password);
        }
      } else {
        // For creation, include all data including password
        const createData: CreateUserRequest = {
          ...formData,
          permissions: customPermissions ? permissions : undefined,
        };
        await userService.createUser(createData);
      }

      onUserSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {user ? 'Edit User' : 'Create New User'}
          </h3>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">First Name</label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Last Name</label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => handleRoleChange(e.target.value as 'admin' | 'user' | 'viewer')}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="viewer">Viewer</option>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Password {user ? '(leave blank to keep current)' : ''}
                </label>
                <input
                  type="password"
                  required={!user}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center mb-3">
                <input
                  type="checkbox"
                  checked={customPermissions}
                  onChange={(e) => {
                    setCustomPermissions(e.target.checked);
                    if (!e.target.checked) {
                      setPermissions(userService.getDefaultPermissionsByRole(formData.role));
                    }
                  }}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">Custom Permissions</label>
              </div>

              {customPermissions && (
                <div className="grid grid-cols-2 gap-2 p-4 border rounded-md bg-gray-50">
                  {Object.entries(permissions).map(([key, value]) => (
                    <label key={key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={(e) => handlePermissionChange(key as keyof typeof permissions, e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">
                        {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {loading ? 'Saving...' : (user ? 'Update User' : 'Create User')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | undefined>();
  const [showModal, setShowModal] = useState(false);
  const [showPermissionManager, setShowPermissionManager] = useState(false);
  const [permissionUser, setPermissionUser] = useState<User | undefined>();
  const [showPermissionMatrix, setShowPermissionMatrix] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  });

  const currentUser = authService.getCurrentUser();

  useEffect(() => {
    fetchUsers();
  }, [searchTerm, roleFilter, pagination.page]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params: UserListParams = {
        page: pagination.page,
        per_page: pagination.per_page,
      };

      if (searchTerm) params.search = searchTerm;
      if (roleFilter) params.role = roleFilter;

      const response = await userService.getUsers(params);
      setUsers(response.users);
      setPagination({
        page: response.page,
        per_page: response.per_page,
        total: response.total,
        total_pages: response.total_pages,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleUserSaved = () => {
    fetchUsers();
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setShowModal(true);
  };

  const handleCreateUser = () => {
    setSelectedUser(undefined);
    setShowModal(true);
  };

  const handleManagePermissions = (user: User) => {
    setPermissionUser(user);
    setShowPermissionManager(true);
  };

  const handlePermissionUserUpdate = (updatedUser: User) => {
    setUsers(users.map(u => u.id === updatedUser.id ? updatedUser : u));
  };

  const handleDeleteUser = async (userId: string) => {
    if (userId === currentUser?.id) {
      alert('You cannot delete your own account');
      return;
    }

    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await userService.deleteUser(userId);
        fetchUsers();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete user');
      }
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    if (user.id === currentUser?.id && user.is_active) {
      alert('You cannot deactivate your own account');
      return;
    }

    try {
      await userService.updateUserStatus(user.id, !user.is_active);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status');
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'user': return 'bg-blue-100 text-blue-800';
      case 'viewer': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && users.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              User Management
            </h2>
          </div>
          <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
            <button
              onClick={() => setShowPermissionMatrix(true)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Permission Matrix
            </button>
            <button
              onClick={handleCreateUser}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Add User
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:p-6">
            <div className="md:flex md:items-center md:justify-between mb-6">
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full md:w-80 border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="mt-4 md:mt-0 md:ml-4">
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="block w-full border border-gray-300 rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Permissions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Login
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-700">
                                {user.first_name?.[0] || user.username[0].toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {user.first_name && user.last_name
                                ? `${user.first_name} ${user.last_name}`
                                : user.username}
                            </div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                            {user.username !== (user.first_name && user.last_name
                              ? `${user.first_name} ${user.last_name}`
                              : user.username) && (
                              <div className="text-xs text-gray-400">@{user.username}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(user.permissions)
                            .filter(([_, enabled]) => enabled)
                            .slice(0, 3)
                            .map(([permission, _]) => (
                              <span
                                key={permission}
                                className="inline-flex px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                              >
                                {permission.replace('can', '').replace(/([A-Z])/g, ' $1').trim()}
                              </span>
                            ))}
                          {Object.values(user.permissions).filter(Boolean).length > 3 && (
                            <span className="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                              +{Object.values(user.permissions).filter(Boolean).length - 3} more
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => handleEditUser(user)}
                            className="text-blue-600 hover:text-blue-900 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleManagePermissions(user)}
                            className="text-purple-600 hover:text-purple-900 text-sm"
                          >
                            Permissions
                          </button>
                          <button
                            onClick={() => handleToggleUserStatus(user)}
                            className={`text-sm ${user.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}`}
                            disabled={user.id === currentUser?.id && user.is_active}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                            disabled={user.id === currentUser?.id}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination.total_pages > 1 && (
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                  {pagination.total} results
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                    disabled={pagination.page === 1}
                    className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md disabled:opacity-50 hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                    disabled={pagination.page === pagination.total_pages}
                    className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md disabled:opacity-50 hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <UserModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        user={selectedUser}
        onUserSaved={handleUserSaved}
      />

      {showPermissionManager && permissionUser && (
        <SimplePermissionManager
          user={permissionUser}
          onUserUpdate={handlePermissionUserUpdate}
          onClose={() => setShowPermissionManager(false)}
        />
      )}

      {showPermissionMatrix && (
        <RolePermissionMatrix
          onClose={() => setShowPermissionMatrix(false)}
        />
      )}
    </div>
  );
};

export default UsersPage;
