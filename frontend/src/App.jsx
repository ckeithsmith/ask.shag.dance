import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import LoadingSpinner from './components/LoadingSpinner';
import { askQuestion, getSuggestedQuestions, checkHealth } from './services/api';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    // Load initial data
    const loadInitialData = async () => {
      try {
        const [suggestions, health] = await Promise.all([
          getSuggestedQuestions(),
          checkHealth()
        ]);
        setSuggestedQuestions(suggestions);
        setHealthStatus(health);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };

    loadInitialData();

    // Add welcome message
    setMessages([
      {
        id: 'welcome',
        text: `# Welcome to the CSA Shag Archive Assistant! 🕺💃\n\nI'm here to help you explore **35 years** of competitive shag dancing history from the **Competitive Shaggers Association (CSA)** and **National Shag Dance Championship (NSDC)**.\n\nI have access to:\n- **7,869 contest records** from 1990-2025\n- Complete CSA rules and regulations\n- NSDC championship rules\n- Required song lists and bylaws\n\nAsk me anything about:\n- Contest winners and placements\n- Competition divisions and advancement rules\n- Historical trends and statistics\n- Specific dancers or couples\n- Contest locations and dates\n- Judging information\n\nTry one of the suggested questions below or ask your own!`,
        isUser: false,
        timestamp: new Date()
      }
    ]);
  }, []);

  const handleSendMessage = async (message) => {
    setError(null);
    
    // Add user message
    const userMessage = {
      id: Date.now() + '-user',
      text: message,
      isUser: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await askQuestion(message);
      
      // Add assistant response
      const assistantMessage = {
        id: Date.now() + '-assistant',
        text: response.answer,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setError(error.message);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + '-error',
        text: `Sorry, I encountered an error: ${error.message}\n\nPlease try rephrasing your question or try again in a moment.`,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestion = (question) => {
    handleSendMessage(question);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold">CSA Shag Archive Assistant</h1>
          <p className="text-blue-100 text-sm">Your guide to 35 years of competitive shag dancing</p>
          {healthStatus && (
            <div className="text-xs text-blue-100 mt-1">
              {healthStatus.total_records} contest records • {healthStatus.pdf_count} documents loaded
            </div>
          )}
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden flex flex-col max-w-4xl mx-auto w-full">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message.text}
              isUser={message.isUser}
              timestamp={message.timestamp}
            />
          ))}
          
          {/* Suggested Questions (shown when no user messages yet) */}
          {messages.filter(m => m.isUser).length === 0 && suggestedQuestions.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Try asking:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="text-left p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                    disabled={isLoading}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Loading Spinner */}
          {isLoading && <LoadingSpinner />}
          
          {/* Error Display */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-2 text-xs text-gray-600">
        <p>CSA Archive data spans 1990-2025 • Built with 🕺 for the shag community</p>
      </footer>
    </div>
  );\n};\n\nexport default App;