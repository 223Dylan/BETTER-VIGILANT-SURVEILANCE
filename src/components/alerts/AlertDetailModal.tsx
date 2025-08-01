import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Alert } from '../../types';
import { getSeverityColor } from './AlertUtils';
import AlertActions from './AlertActions';
import { useThemeClasses } from '../../contexts/ThemeContext';

interface AlertDetailModalProps {
  alert: Alert | null;
  isOpen: boolean;
  onClose: () => void;
  onAcknowledge: (alertId: string, notes?: string) => void;
  onResolve: (alertId: string, notes?: string) => void;
}

const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  isOpen,
  onClose,
  onAcknowledge,
  onResolve,
}) => {
  const themeClasses = useThemeClasses();

  if (!isOpen || !alert) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`${themeClasses.bg.primary} rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto`}>
        <div className={`p-6 border-b ${themeClasses.border.primary} flex justify-between items-center`}>
          <h2 className={`text-xl font-semibold ${themeClasses.text.primary}`}>Alert Details</h2>
          <button
            onClick={onClose}
            className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} transition-colors`}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Alert ID</label>
              <div className={`text-sm font-mono ${themeClasses.text.primary}`}>{alert.id}</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Camera</label>
              <div className={`text-sm ${themeClasses.text.primary}`}>{alert.cameraId}</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Severity</label>
              <span className={`inline-block px-2 py-1 rounded text-sm ${getSeverityColor(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </span>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Status</label>
              <div className={`text-sm ${themeClasses.text.primary} capitalize`}>{alert.status}</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Confidence</label>
              <div className={`text-sm ${themeClasses.text.primary}`}>{Math.round(alert.confidence * 100)}%</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Type</label>
              <div className={`text-sm ${themeClasses.text.primary} capitalize`}>{alert.type.replace('_', ' ')}</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Timestamp</label>
              <div className={`text-sm ${themeClasses.text.primary}`}>{new Date(alert.timestamp).toLocaleString()}</div>
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.secondary}`}>Source</label>
              <div className={`text-sm ${themeClasses.text.primary} capitalize`}>{alert.source}</div>
            </div>
          </div>

          <div className="mb-4">
            <label className={`block text-sm font-medium ${themeClasses.text.secondary} mb-1`}>Message</label>
            <div className={`text-sm ${themeClasses.text.primary} ${themeClasses.bg.secondary} p-3 rounded`}>{alert.message}</div>
          </div>

          {alert.detectionData && Object.keys(alert.detectionData).length > 0 && (
            <div className="mb-4">
              <label className={`block text-sm font-medium ${themeClasses.text.secondary} mb-1`}>Detection Data</label>
              <pre className={`text-xs ${themeClasses.bg.secondary} p-3 rounded overflow-x-auto ${themeClasses.text.primary}`}>
                {JSON.stringify(alert.detectionData, null, 2)}
              </pre>
            </div>
          )}

          {alert.notes && (
            <div className="mb-4">
              <label className={`block text-sm font-medium ${themeClasses.text.secondary} mb-1`}>Notes</label>
              <div className={`text-sm ${themeClasses.text.primary} ${themeClasses.bg.secondary} p-3 rounded`}>{alert.notes}</div>
            </div>
          )}

          {/* Acknowledgment/Resolution History */}
          {(alert.acknowledgedBy || alert.resolvedBy) && (
            <div className="mb-4">
              <h3 className={`text-sm font-medium ${themeClasses.text.primary} mb-2`}>History</h3>
              <div className="space-y-2">
                {alert.acknowledgedBy && (
                  <div className={`text-sm ${themeClasses.text.secondary}`}>
                    Acknowledged by {alert.acknowledgedBy} at {new Date(alert.acknowledgedAt || '').toLocaleString()}
                  </div>
                )}
                {alert.resolvedBy && (
                  <div className={`text-sm ${themeClasses.text.secondary}`}>
                    Resolved by {alert.resolvedBy} at {new Date(alert.resolvedAt || '').toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <AlertActions
              alert={alert}
              onAcknowledge={onAcknowledge}
              onResolve={onResolve}
              onViewDetails={() => {}} // No-op since we're already viewing details
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertDetailModal;
