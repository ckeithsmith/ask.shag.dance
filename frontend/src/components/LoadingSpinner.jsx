import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-4">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span className="ml-2 text-gray-600">Getting your answer...</span>
    </div>
  );
};

export default LoadingSpinner;