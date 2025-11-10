import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import LoadingSpinner from './components/LoadingSpinner';
import UserRegistration from './components/UserRegistration';
import * as api from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [error, setError] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [authInitialized, setAuthInitialized] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize authentication on startup - ONCE ONLY
  useEffect(() => {
    if (authInitialized) return; // Prevent multiple initializations
    
    const storedUser = localStorage.getItem('csaUserInfo');
    if (storedUser) {
      try {
        const userInfo = JSON.parse(storedUser);
        setUserInfo(userInfo);
        setShowRegistration(false);
      } catch (e) {
        // If stored data is corrupted, show registration
        localStorage.removeItem('csaUserInfo');
        setShowRegistration(true);
      }
    } else {
      // Show registration popup for new users
      setShowRegistration(true);
    }
    setAuthInitialized(true);
  }, [authInitialized]);

  useEffect(() => {
    // Load suggested questions on startup
    const loadSuggestions = async () => {
      try {
        const suggestions = await api.getSuggestedQuestions();
        setSuggestedQuestions(suggestions);
      } catch (error) {
        console.error('Failed to load suggestions:', error);
      }
    };
    loadSuggestions();
  }, []);

  const handleSendMessage = async (userMessage) => {
    if (!userMessage.trim() || isLoading) return;

    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.askQuestion(userMessage, userInfo?.name || 'Anonymous', sessionId);
      
      const botMessage = {
        id: Date.now() + 1,
        queryId: response.query_id, // Store query ID for feedback
        text: response.answer || response,
        sender: 'assistant',
        timestamp: new Date(),
        responseTime: response.response_time_ms
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error getting response:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: `Sorry, I encountered an error: ${error.message}. Please try again or check if the service is available.`,
        sender: 'assistant',
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (question) => {
    handleSendMessage(question);
  };

  const handleUserRegistered = useCallback((userData) => {
    setUserInfo(userData);
    setShowRegistration(false);
    // Authentication completed successfully
  }, []);



  return (
    <div className="App flex flex-col min-h-screen">
      {/* User Registration Modal - Only render when needed to prevent loops */}
      {showRegistration && authInitialized && (
        <UserRegistration onUserRegistered={handleUserRegistered} />
      )}
      
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold">CSA Shag Archive Q&A</h1>
          <p className="text-blue-100 text-sm">Ask questions about Competitive Shaggers Association history and contests</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto flex-1 flex flex-col w-full">
        {/* Welcome Message and Suggested Questions */}
        {messages.length === 0 && (
          <div className="p-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-blue-900 mb-3">
                Welcome to the CSA Shag Archive! 🕺💃
              </h2>
              <p className="text-blue-800 mb-4">
                I'm your guide to the complete Competitive Shaggers Association database, 
                covering decades of shag dance competitions, rules, and championship history.
              </p>
              
              {/* About This Data Section */}
              <div className="bg-white border border-blue-300 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 text-lg">ℹ️</span>
                  <div>
                    <h3 className="text-sm font-semibold text-blue-900 mb-2">About This Data</h3>
                    <p className="text-xs text-blue-800 leading-relaxed">
                      This analysis is based on CSA public archives (1988-present) and NSDC public archives, 
                      representing over 7,800 competitive shag dancing contest entries spanning 35+ years. 
                      Please note some data limitations: Pre-1988 records are incomplete, which affects total 
                      contest counts for pioneering dancers like Charlie Womble and Jackie McGee. Most contests 
                      record placements for the top 6 couples, and approximately 50% of records include judge 
                      names. These limitations mean some historical totals may underrepresent early careers, 
                      but all dancers competing since 1988 have comprehensive coverage. The trends, patterns, 
                      and insights identified in this data are statistically valid and will only be reinforced—not 
                      contradicted—as we integrate additional detail from private CSA archives in future updates. 
                      This database provides the most complete publicly available analysis of competitive shag 
                      dancing history.
                    </p>
                  </div>
                </div>
              </div>
              

              
              {suggestedQuestions.length > 0 && (
                <div>
                  <p className="text-blue-800 font-medium mb-3">Try asking me about:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {suggestedQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(question)}
                        className="text-left p-3 bg-white border border-blue-300 rounded hover:bg-blue-100 hover:border-blue-400 transition-colors text-sm text-blue-900"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input - Prominent position when no messages */}
            <div className="mb-6">
              <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
            </div>
          </div>
        )}

        {/* Messages Area */}
        {messages.length > 0 && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {messages.map(message => (
                <ChatMessage key={message.id} message={message} />
              ))}
              
              {isLoading && (
                <div className="flex justify-center py-4">
                  <LoadingSpinner />
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input - After messages */}
            <div className="px-6 pb-4">
              <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-2 text-xs text-gray-600">
        <p>CSA Archive data spans 1990-2025 • Built with 🕺 for the shag community</p>
      </footer>
    </div>
  );
}

export default App;