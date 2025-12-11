import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const askQuestion = async (question, userContact = 'Anonymous', sessionId = null) => {
  try {
    const requestData = { 
      question,
      user_contact: userContact,
      session_id: sessionId
    };
    
    const response = await api.post('/ask', requestData, {
      timeout: 45000 // 45 second timeout for complex queries
    });
    return response.data;
  } catch (error) {
    console.error('API Error Details:', error);
    
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timed out. The query might be too complex. Please try a simpler question.');
    }
    if (error.response?.status === 429) {
      // Check if it's a daily limit error
      if (error.response?.data?.error === 'daily_limit_reached') {
        throw new Error(`daily_limit_reached: ${JSON.stringify(error.response.data)}`);
      }
      throw new Error('Rate limit exceeded. Please wait before asking another question.');
    }
    if (error.response?.status === 500) {
      throw new Error('Server error occurred. Please try again in a moment.');
    }
    if (error.response?.status === 503) {
      throw new Error('Service temporarily unavailable. Please try again in a moment.');
    }
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    if (error.message.includes('Network Error')) {
      throw new Error('Network connection issue. Please check your internet connection.');
    }
    throw new Error(`Connection failed (${error.response?.status || 'unknown'}). Please try again.`);
  }
};

export const getSuggestedQuestions = async () => {
  try {
    const response = await api.get('/suggested-questions');
    return response.data.suggestions;
  } catch (error) {
    console.error('Failed to fetch suggested questions:', error);
    return [];
  }
};

export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
};