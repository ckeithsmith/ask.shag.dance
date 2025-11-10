import React, { useState, useEffect } from 'react';

const UserRegistration = ({ onUserRegistered }) => {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  // Component only renders when showRegistration is true in App.jsx
  // This prevents the authentication loop entirely
  useEffect(() => {
    // Show modal immediately since component only renders when needed
    setShowModal(true);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      // Create device fingerprint for tracking
      const deviceInfo = {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      };

      const registrationData = {
        name: formData.name.trim(),
        email: formData.email.trim() || null,
        device_fingerprint: btoa(JSON.stringify(deviceInfo))
      };

      // Send registration to backend
      const response = await fetch('/api/register-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationData)
      });

      if (!response.ok) {
        throw new Error(`Registration failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Store user info locally
      const userInfo = {
        id: result.user_id,
        name: formData.name.trim(),
        email: formData.email.trim() || null,
        device_fingerprint: registrationData.device_fingerprint
      };
      
      localStorage.setItem('csaUserInfo', JSON.stringify(userInfo));
      
      // Notify parent component
      onUserRegistered(userInfo);
      
      // Close modal
      setShowModal(false);
      
    } catch (error) {
      console.error('Registration error:', error);
      setError(`Registration failed: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    // Set anonymous user info
    const anonymousUser = {
      id: null,
      name: 'Anonymous',
      email: null,
      device_fingerprint: null
    };
    
    localStorage.setItem('csaUserInfo', JSON.stringify(anonymousUser));
    onUserRegistered(anonymousUser);
    setShowModal(false);
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  if (!showModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-center mb-6">
            <div className="text-4xl mr-3">🕺💃</div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome to CSA Archive!</h2>
              <p className="text-sm text-gray-600">Let's get you started</p>
            </div>
          </div>

          {/* Description */}
          <div className="mb-6 text-center">
            <p className="text-gray-700 mb-2">
              To help us track usage and improve our service, please provide your contact information.
            </p>
            <p className="text-sm text-gray-500">
              This helps us understand our community and provide better answers!
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Your full name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="your.email@example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSubmitting}
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
                {error}
              </div>
            )}

            {/* Buttons */}
            <div className="flex space-x-3 pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Registering...
                  </div>
                ) : (
                  'Get Started!'
                )}
              </button>
              
              <button
                type="button"
                onClick={handleSkip}
                disabled={isSubmitting}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
              >
                Skip
              </button>
            </div>
          </form>

          {/* Privacy Note */}
          <div className="mt-6 text-xs text-gray-500 text-center border-t pt-4">
            <p>
              🔒 Your information is stored securely and only used for usage analytics.
              We never share your data with third parties.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserRegistration;