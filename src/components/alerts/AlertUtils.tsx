export const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'bg-red-100 text-red-800 border-red-200';
    case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'bg-red-500';
    case 'acknowledged': return 'bg-yellow-500';
    case 'resolved': return 'bg-green-500';
    case 'dismissed': return 'bg-gray-500';
    default: return 'bg-gray-500';
  }
};

export const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};
