import React from 'react';
import { Alert } from '../../types';
import { getSeverityColor, getStatusColor, formatTimestamp } from './AlertUtils';
import AlertActions from './AlertActions';

interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (alertId: string, notes?: string) => void;
  onResolve: (alertId: string, notes?: string) => void;
  onViewDetails: (alert: Alert) => void;
  isSelected?: boolean;
  onSelect?: (alertId: string) => void;
  showCheckbox?: boolean;
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onResolve,
  onViewDetails,
  isSelected = false,
  onSelect,
  showCheckbox = false,
}) => {
  const handleCheckboxChange = () => {
    if (onSelect) {
      onSelect(alert.id);
    }
  };

  return (
    <div className={`p-6 hover:bg-gray-50 border-b border-gray-200 last:border-b-0 ${isSelected ? 'bg-blue-50 border-blue-200' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          {/* Checkbox for selection */}
          {showCheckbox && (
            <div className="pt-1">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={handleCheckboxChange}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
          )}

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(alert.status)}`}></div>
              <span className={`px-2 py-1 rounded text-sm font-medium ${getSeverityColor(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </span>
              <span className="text-sm text-gray-500 font-mono">{alert.cameraId}</span>
              <span className="text-sm text-gray-500">{formatTimestamp(alert.timestamp)}</span>
            </div>

          <div className="mb-2">
            <h3 className="font-medium text-gray-900 mb-1">{alert.message}</h3>
            <div className="text-sm text-gray-600">
              Confidence: {Math.round(alert.confidence * 100)}% |
              Type: {alert.type.replace('_', ' ')} |
              Status: {alert.status}
            </div>
          </div>

          {alert.notes && (
            <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded mt-2">
              <strong>Notes:</strong> {alert.notes}
            </div>
          )}

          {/* Acknowledgment/Resolution info */}
          {alert.acknowledgedBy && (
            <div className="text-xs text-gray-500 mt-2">
              Acknowledged by {alert.acknowledgedBy} at {formatTimestamp(alert.acknowledgedAt || '')}
            </div>
          )}
            {alert.resolvedBy && (
              <div className="text-xs text-gray-500 mt-1">
                Resolved by {alert.resolvedBy} at {formatTimestamp(alert.resolvedAt || '')}
              </div>
            )}
          </div>
        </div>

        <div className="ml-4">
          <AlertActions
            alert={alert}
            onAcknowledge={onAcknowledge}
            onResolve={onResolve}
            onViewDetails={onViewDetails}
          />
        </div>
      </div>
    </div>
  );
};

export default AlertCard;
