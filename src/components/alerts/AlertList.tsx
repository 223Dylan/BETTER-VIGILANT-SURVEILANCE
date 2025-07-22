import React, { useState, useEffect } from 'react';
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
  onBulkAcknowledge?: (alertIds: string[], notes?: string) => void;
  onBulkResolve?: (alertIds: string[], notes?: string) => void;
  showBulkActions?: boolean;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  loading = false,
  emptyMessage = 'No alerts found',
  title,
  onAcknowledge,
  onResolve,
  onViewDetails,
  onBulkAcknowledge,
  onBulkResolve,
  showBulkActions = true,
}) => {
  const [selectedAlerts, setSelectedAlerts] = useState<Set<string>>(new Set());
  const [bulkActionNotes, setBulkActionNotes] = useState('');
  const [showNotesInput, setShowNotesInput] = useState(false);
  const [pendingAction, setPendingAction] = useState<'acknowledge' | 'resolve' | null>(null);

  // Reset selections when alerts change
  useEffect(() => {
    setSelectedAlerts(new Set());
  }, [alerts]);

  const activeAlerts = alerts.filter(alert => alert.status === 'active');
  const allSelected = activeAlerts.length > 0 && selectedAlerts.size === activeAlerts.length;
  const someSelected = selectedAlerts.size > 0;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(activeAlerts.map(alert => alert.id)));
    }
  };

  const handleSelectAlert = (alertId: string) => {
    const newSelected = new Set(selectedAlerts);
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId);
    } else {
      newSelected.add(alertId);
    }
    setSelectedAlerts(newSelected);
  };

  const handleBulkAction = (action: 'acknowledge' | 'resolve') => {
    if (selectedAlerts.size === 0) return;

    setPendingAction(action);
    setShowNotesInput(true);
  };

  const executeBulkAction = () => {
    if (!pendingAction || selectedAlerts.size === 0) return;

    const alertIds = Array.from(selectedAlerts);

    if (pendingAction === 'acknowledge' && onBulkAcknowledge) {
      onBulkAcknowledge(alertIds, bulkActionNotes || undefined);
    } else if (pendingAction === 'resolve' && onBulkResolve) {
      onBulkResolve(alertIds, bulkActionNotes || undefined);
    }

    // Reset state
    setSelectedAlerts(new Set());
    setBulkActionNotes('');
    setShowNotesInput(false);
    setPendingAction(null);
  };

  const cancelBulkAction = () => {
    setShowNotesInput(false);
    setPendingAction(null);
    setBulkActionNotes('');
  };

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
      {/* Header with title and bulk actions */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {title} ({alerts.length})
          </h2>

          {showBulkActions && activeAlerts.length > 0 && (
            <div className="flex items-center gap-4">
              {someSelected && (
                <span className="text-sm text-gray-600">
                  {selectedAlerts.size} selected
                </span>
              )}

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm">Select All</span>
              </label>
            </div>
          )}
        </div>

        {/* Bulk action buttons */}
        {showBulkActions && someSelected && (
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => handleBulkAction('acknowledge')}
              disabled={showNotesInput}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
            >
              Acknowledge Selected ({selectedAlerts.size})
            </button>
            <button
              onClick={() => handleBulkAction('resolve')}
              disabled={showNotesInput}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-green-800 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              Resolve Selected ({selectedAlerts.size})
            </button>
          </div>
        )}

        {/* Notes input for bulk action */}
        {showNotesInput && pendingAction && (
          <div className="mt-3 p-3 bg-gray-50 rounded-md">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes for bulk {pendingAction} (optional):
            </label>
            <textarea
              value={bulkActionNotes}
              onChange={(e) => setBulkActionNotes(e.target.value)}
              placeholder={`Add notes for bulk ${pendingAction}...`}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              rows={2}
            />
            <div className="mt-2 flex items-center gap-2">
              <button
                onClick={executeBulkAction}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Confirm {pendingAction} ({selectedAlerts.size} alerts)
              </button>
              <button
                onClick={cancelBulkAction}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

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
              // Pass selection props to AlertCard
              isSelected={selectedAlerts.has(alert.id)}
              onSelect={handleSelectAlert}
              showCheckbox={showBulkActions && alert.status === 'active'}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertList;
