import React from 'react';
import { CheckIcon, XMarkIcon, EyeIcon } from '@heroicons/react/24/outline';
import { Alert } from '../../types';

interface AlertActionsProps {
  alert: Alert;
  onAcknowledge: (alertId: string, notes?: string) => void;
  onResolve: (alertId: string, notes?: string) => void;
  onViewDetails: (alert: Alert) => void;
  compact?: boolean;
}

const AlertActions: React.FC<AlertActionsProps> = ({
  alert,
  onAcknowledge,
  onResolve,
  onViewDetails,
  compact = false,
}) => {
  const buttonClasses = compact
    ? "px-2 py-1 rounded text-xs hover:opacity-80 transition-colors flex items-center gap-1"
    : "px-3 py-1 rounded text-sm hover:opacity-80 transition-colors flex items-center gap-1";

  return (
    <div className={`flex gap-2 ${compact ? 'flex-col' : ''}`}>
      {alert.status === 'active' && (
        <>
          <button
            onClick={() => onAcknowledge(alert.id)}
            className={`bg-yellow-600 text-white ${buttonClasses}`}
            title="Acknowledge Alert"
          >
            <CheckIcon className="h-3 w-3" />
            {!compact && 'Acknowledge'}
          </button>
          <button
            onClick={() => onResolve(alert.id)}
            className={`bg-green-600 text-white ${buttonClasses}`}
            title="Resolve Alert"
          >
            <XMarkIcon className="h-3 w-3" />
            {!compact && 'Resolve'}
          </button>
        </>
      )}

      <button
        onClick={() => onViewDetails(alert)}
        className={`bg-blue-600 text-white ${buttonClasses}`}
        title="View Details"
      >
        <EyeIcon className="h-3 w-3" />
        {!compact && 'Details'}
      </button>
    </div>
  );
};

export default AlertActions;
