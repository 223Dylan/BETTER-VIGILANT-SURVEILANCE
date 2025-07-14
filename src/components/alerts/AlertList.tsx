import React from 'react';
import { Alert } from '../../types';
import AlertCard from './AlertCard';

interface AlertListProps {
  alerts: Alert[];
  loading?: boolean;
  emptyMessage?: string;
  title?: string;
  onAcknowledge: (alertId: string, notes?: string) => void;
  onResolve: (alertId: string, notes?: string) => void;
  onViewDetails: (alert: Alert) => void;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  loading = false,
  emptyMessage = 'No alerts found',
  title,
  onAcknowledge,
  onResolve,
  onViewDetails,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow border">
        <div className="flex items-center justify-center min-h-[200px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      {title && (
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">
            {title} ({alerts.length})
          </h2>
        </div>
      )}

      {alerts.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          {emptyMessage}
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={onAcknowledge}
              onResolve={onResolve}
              onViewDetails={onViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertList; 