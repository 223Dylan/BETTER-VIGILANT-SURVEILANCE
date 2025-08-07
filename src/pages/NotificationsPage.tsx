import React, { useState } from 'react';
import { Tab } from '@headlessui/react';
import { BellIcon, Cog6ToothIcon, ClockIcon } from '@heroicons/react/24/outline';
import UserNotificationSettings from '../components/UserNotificationSettings';
import NotificationHistory from '../components/NotificationHistory';

const NotificationsPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);

  const tabs = [
    {
      name: 'Settings',
      icon: Cog6ToothIcon,
      component: <UserNotificationSettings />
    },
    {
      name: 'History',
      icon: ClockIcon,
      component: <NotificationHistory limit={100} showFilters={true} />
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <BellIcon className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
              <p className="text-gray-600 mt-1">
                Manage your notification preferences and view notification history
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white shadow rounded-lg">
          <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
            <Tab.List className="flex border-b border-gray-200">
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.name}
                  className={({ selected }: { selected: boolean }) =>
                    `flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      selected
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`
                  }
                >
                  <tab.icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </Tab>
              ))}
            </Tab.List>
            <Tab.Panels className="p-6">
              {tabs.map((tab, index) => (
                <Tab.Panel key={tab.name}>
                  {tab.component}
                </Tab.Panel>
              ))}
            </Tab.Panels>
          </Tab.Group>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;
