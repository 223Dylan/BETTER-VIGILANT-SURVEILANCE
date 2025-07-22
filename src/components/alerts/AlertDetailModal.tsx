import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Alert } from '../../types';
import { getSeverityColor } from './AlertUtils';
import AlertActions from './AlertActions';

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
  if (!isOpen || !alert) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold">Alert Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Alert ID</label>
              <div className="text-sm font-mono text-gray-900">{alert.id}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Camera</label>
              <div className="text-sm text-gray-900">{alert.cameraId}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Severity</label>
              <span className={`inline-block px-2 py-1 rounded text-sm ${getSeverityColor(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Status</label>
              <div className="text-sm text-gray-900 capitalize">{alert.status}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Confidence</label>
              <div className="text-sm text-gray-900">{Math.round(alert.confidence * 100)}%</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Type</label>
              <div className="text-sm text-gray-900 capitalize">{alert.type.replace('_', ' ')}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Timestamp</label>
              <div className="text-sm text-gray-900">{new Date(alert.timestamp).toLocaleString()}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Source</label>
              <div className="text-sm text-gray-900 capitalize">{alert.source}</div>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
            <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded">{alert.message}</div>
          </div>

          {alert.detectionData && Object.keys(alert.detectionData).length > 0 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Detection Data</label>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                {JSON.stringify(alert.detectionData, null, 2)}
              </pre>
            </div>
          )}

          {alert.notes && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded">{alert.notes}</div>
            </div>
          )}

          {/* Acknowledgment/Resolution History */}
          {(alert.acknowledgedBy || alert.resolvedBy) && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Action History</label>
              <div className="bg-gray-50 p-3 rounded space-y-2">
                {alert.acknowledgedBy && (
                  <div className="text-sm">
                    <span className="font-medium">Acknowledged</span> by {alert.acknowledgedBy}
                    {alert.acknowledgedAt && (
                      <span className="text-gray-600 ml-1">
                        on {new Date(alert.acknowledgedAt).toLocaleString()}
                      </span>
                    )}
                  </div>
                )}
                {alert.resolvedBy && (
                  <div className="text-sm">
                    <span className="font-medium">Resolved</span> by {alert.resolvedBy}
                    {alert.resolvedAt && (
                      <span className="text-gray-600 ml-1">
                        on {new Date(alert.resolvedAt).toLocaleString()}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
          <AlertActions
            alert={alert}
            onAcknowledge={(alertId, notes) => {
              onAcknowledge(alertId, notes);
              onClose();
            }}
            onResolve={(alertId, notes) => {
              onResolve(alertId, notes);
              onClose();
            }}
            onViewDetails={() => {}} // Not needed in modal
          />
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertDetailModal;
