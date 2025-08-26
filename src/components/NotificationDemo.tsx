import React, { useState } from 'react';
import { BellIcon } from '@heroicons/react/24/outline';
import NotificationsTab from './NotificationsTab';
import { useNotifications } from '../contexts/NotificationContext';

const NotificationDemo: React.FC = () => {
  const { unreadCount } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button
        onClick={() => setShowNotifications(true)}
        className="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        title="View notifications"
      >
        <BellIcon className="w-6 h-6 text-gray-600 dark:text-gray-300" />

        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Tab */}
      {showNotifications && (
        <NotificationsTab onClose={() => setShowNotifications(false)} />
      )}
    </div>
  );
};

export default NotificationDemo;
