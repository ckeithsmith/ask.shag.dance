import React, { useState } from 'react';

const FeedbackButton = ({ messageId, onFeedbackSubmitted }) => {
  const [showModal, setShowModal] = useState(false);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const userInfo = JSON.parse(localStorage.getItem('csaUserInfo') || '{}');
      
      const feedbackData = {
        query_id: messageId,
        feedback_type: 'incorrect_answer',
        comment: comment.trim() || null,
        user_id: userInfo.id || null
      };

      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData)
      });

      if (!response.ok) {
        throw new Error(`Failed to submit feedback: ${response.status}`);
      }

      setSubmitted(true);
      
      // Notify parent component
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(messageId, comment);
      }

      // Auto-close after 2 seconds
      setTimeout(() => {
        setShowModal(false);
        setSubmitted(false);
        setComment('');
      }, 2000);

    } catch (error) {
      console.error('Feedback submission error:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setComment('');
    setSubmitted(false);
  };

  return (
    <>
      {/* Feedback Button */}
      <button
        onClick={() => setShowModal(true)}
        className="text-sm text-gray-500 hover:text-red-600 transition-colors duration-200 flex items-center gap-1"
        title="Report incorrect answer"
      >
        <span className="text-lg">⚠️</span>
        <span>Incorrect answer?</span>
      </button>

      {/* Feedback Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              {!submitted ? (
                <>
                  {/* Header */}
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-2">⚠️</span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Report Incorrect Answer
                    </h3>
                  </div>

                  {/* Description */}
                  <p className="text-gray-600 mb-4">
                    Help us improve! Let us know what was incorrect about this response.
                    Your feedback helps train our system to provide better answers.
                  </p>

                  {/* Feedback Form */}
                  <form onSubmit={handleSubmitFeedback}>
                    <div className="mb-4">
                      <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
                        What was incorrect? <span className="text-gray-400">(optional)</span>
                      </label>
                      <textarea
                        id="comment"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="e.g., Wrong year, missing information, factual error..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        rows="3"
                        disabled={isSubmitting}
                      />
                    </div>

                    {/* Buttons */}
                    <div className="flex space-x-3">
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:bg-red-400 disabled:cursor-not-allowed transition-colors"
                      >
                        {isSubmitting ? (
                          <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Submitting...
                          </div>
                        ) : (
                          'Submit Report'
                        )}
                      </button>
                      
                      <button
                        type="button"
                        onClick={handleClose}
                        disabled={isSubmitting}
                        className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                /* Success Message */
                <div className="text-center">
                  <div className="text-4xl mb-3">✅</div>
                  <h3 className="text-lg font-semibold text-green-900 mb-2">
                    Feedback Submitted!
                  </h3>
                  <p className="text-green-700">
                    Thank you for helping us improve. Your report has been recorded.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackButton;