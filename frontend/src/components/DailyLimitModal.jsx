import React from 'react';

const DailyLimitModal = ({ isOpen, onClose, message, dailyLimit, currentCount }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Daily Message Limit Reached</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        
        <div className="mb-6">
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-gray-700 leading-relaxed">
              {message || "This is a free service paid for by personal funds and is therefore limited to a fixed budget per day. The budget has been hit for today. Please try again tomorrow with your questions."}
            </p>
          </div>
          
          {dailyLimit && currentCount !== undefined && (
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2">Daily Usage</div>
              <div className="text-2xl font-bold text-gray-900">
                {currentCount} / {dailyLimit}
              </div>
              <div className="text-xs text-gray-500">messages used today</div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Got it
          </button>
        </div>
        
        <div className="mt-4 text-xs text-gray-500 text-center">
          Limits reset daily at midnight
        </div>
      </div>
    </div>
  );
};

export default DailyLimitModal;