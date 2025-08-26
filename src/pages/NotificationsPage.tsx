import React, { useState } from 'react';
import { Tab } from '@headlessui/react';
import { BellIcon, Cog6ToothIcon, ClockIcon } from '@heroicons/react/24/outline';
import UserNotificationSettings from '../components/UserNotificationSettings';
import NotificationHistory from '../components/NotificationHistory';
import NotificationsTabContent from '../components/NotificationsTabContent';
import { useThemeClasses } from '../contexts/ThemeContext';

const NotificationsPage: React.FC = () => {
  const themeClasses = useThemeClasses();
  const [selectedTab, setSelectedTab] = useState(0); // Start with Notifications tab (index 0)

  const tabs = [
    {
      name: 'Notifications',
      icon: BellIcon,
      component: <NotificationsTabContent />
    },
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
    <div className={`min-h-screen ${themeClasses.bg.secondary}`}>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <BellIcon className="h-8 w-8 text-blue-600 dark:text-blue-400 mr-3" />
            <div>
              <h1 className={`text-3xl font-bold ${themeClasses.text.primary}`}>Notifications</h1>
              <p className={`${themeClasses.text.secondary} mt-1`}>
                Manage your notification preferences and view notification history
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className={`${themeClasses.bg.primary} shadow rounded-lg ${themeClasses.border.primary} border`}>
          <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
            <Tab.List className={`flex border-b ${themeClasses.border.primary}`}>
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.name}
                  className={({ selected }: { selected: boolean }) =>
                    `flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      selected
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : `border-transparent ${themeClasses.text.secondary} hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600`
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
