import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { userService, UserListParams } from '../services/user.service';
import { authService } from '../services/auth.service';
import { UnifiedUserModal } from '../components/user/UnifiedUserModal';
import { RolePermissionMatrix } from '../components/user/RolePermissionMatrix';
import { useThemeClasses } from '../contexts/ThemeContext';

// Remove the old UserModal component since we're using UnifiedUserModal now

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | undefined>();
  const [showModal, setShowModal] = useState(false);
  const [showPermissionMatrix, setShowPermissionMatrix] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  });
  const themeClasses = useThemeClasses();

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
      case 'admin':
        return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300';
      case 'user':
        return 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300';
      case 'viewer':
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300';
    }
  };

  if (loading && users.length === 0) {
    return (
      <div className={`min-h-screen ${themeClasses.bg.secondary} flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className={`mt-4 ${themeClasses.text.secondary}`}>Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${themeClasses.bg.secondary} py-8`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className={`text-2xl font-bold leading-7 ${themeClasses.text.primary} sm:text-3xl sm:truncate`}>
              User Management
            </h2>
          </div>
          <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
            <button
              onClick={() => setShowPermissionMatrix(true)}
              className={`inline-flex items-center px-4 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm text-sm font-medium ${themeClasses.text.secondary} ${themeClasses.bg.primary} hover:${themeClasses.bg.secondary} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
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
          <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className={`mt-8 ${themeClasses.card} shadow overflow-hidden sm:rounded-md`}>
          <div className="px-4 py-5 sm:p-6">
            <div className="md:flex md:items-center md:justify-between mb-6">
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={`block w-full md:w-80 border ${themeClasses.border.primary} rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
                />
              </div>
              <div className="mt-4 md:mt-0 md:ml-4">
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className={`block w-full border ${themeClasses.border.primary} rounded-md px-3 py-2 shadow-sm focus:ring-blue-500 focus:border-blue-500 ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
                >
                  <option value="">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className={themeClasses.bg.secondary}>
                  <tr>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      User
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      Role
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      Status
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      Permissions
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      Last Login
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider`}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className={`${themeClasses.bg.primary} divide-y divide-gray-200 dark:divide-gray-700`}>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                              <span className={`text-sm font-medium ${themeClasses.text.primary}`}>
                                {user.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className={`text-sm font-medium ${themeClasses.text.primary}`}>
                              {user.first_name && user.last_name
                                ? `${user.first_name} ${user.last_name}`
                                : user.username}
                            </div>
                            <div className={`text-sm ${themeClasses.text.secondary}`}>{user.email}</div>
                            {user.username !== (user.first_name && user.last_name
                              ? `${user.first_name} ${user.last_name}`
                              : user.username) && (
                              <div className={`text-xs ${themeClasses.text.tertiary}`}>@{user.username}</div>
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
                            ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                            : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${themeClasses.text.secondary}`}>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(user.permissions)
                            .filter(([_, enabled]) => enabled)
                            .slice(0, 3)
                            .map(([permission, _]) => (
                              <span
                                key={permission}
                                className="inline-flex px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 rounded-full"
                              >
                                {permission.replace('can', '').replace(/([A-Z])/g, ' $1').trim()}
                              </span>
                            ))}
                          {Object.values(user.permissions).filter(Boolean).length > 3 && (
                            <span className="inline-flex px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                              +{Object.values(user.permissions).filter(Boolean).length - 3} more
                            </span>
                          )}
                        </div>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${themeClasses.text.secondary}`}>
                        {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => handleEditUser(user)}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleToggleUserStatus(user)}
                            className={`text-sm ${user.is_active ? 'text-yellow-600 dark:text-yellow-400 hover:text-yellow-900 dark:hover:text-yellow-300' : 'text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300'}`}
                            disabled={user.id === currentUser?.id && user.is_active}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 text-sm"
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
                <div className={`text-sm ${themeClasses.text.secondary}`}>
                  Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                  {pagination.total} results
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                    disabled={pagination.page === 1}
                    className={`px-3 py-2 text-sm ${themeClasses.bg.primary} border ${themeClasses.border.primary} rounded-md disabled:opacity-50 hover:${themeClasses.bg.secondary}`}
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                    disabled={pagination.page === pagination.total_pages}
                    className={`px-3 py-2 text-sm ${themeClasses.bg.primary} border ${themeClasses.border.primary} rounded-md disabled:opacity-50 hover:${themeClasses.bg.secondary}`}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <UnifiedUserModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        user={selectedUser}
        onUserSaved={handleUserSaved}
      />

      {showPermissionMatrix && (
        <RolePermissionMatrix
          onClose={() => setShowPermissionMatrix(false)}
        />
      )}
    </div>
  );
};

export default UsersPage;
