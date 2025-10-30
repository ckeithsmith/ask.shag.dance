import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import LoadingSpinner from './components/LoadingSpinner';
import * as api from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      const response = await api.askQuestion(userMessage);
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.answer || response,  // Handle both {answer: "..."} and direct string responses
        sender: 'assistant',
        timestamp: new Date()
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

  return (
    <div className="App flex flex-col min-h-screen">
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
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 pb-4">
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

        {/* Chat Input */}
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-2 text-xs text-gray-600">
        <p>CSA Archive data spans 1990-2025 • Built with 🕺 for the shag community</p>
      </footer>
    </div>
  );
}

export default App;