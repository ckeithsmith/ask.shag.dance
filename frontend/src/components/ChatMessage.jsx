import React from 'react';
import ReactMarkdown from 'react-markdown';
import FeedbackButton from './FeedbackButton';

const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-2xl px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : message.isError 
            ? 'bg-red-100 text-red-800 rounded-bl-none border border-red-200'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        }`}
      >
        {isUser ? (
          <p className="text-sm">{message.text}</p>
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              components={{
                // Custom table styling
                table: ({node, ...props}) => (
                  <table className="min-w-full table-auto border-collapse border border-gray-300 text-xs" {...props} />
                ),
                thead: ({node, ...props}) => (
                  <thead className="bg-gray-50" {...props} />
                ),
                th: ({node, ...props}) => (
                  <th className="border border-gray-300 px-2 py-1 text-left font-semibold" {...props} />
                ),
                td: ({node, ...props}) => (
                  <td className="border border-gray-300 px-2 py-1" {...props} />
                ),
                // Style headings
                h1: ({node, ...props}) => (
                  <h1 className="text-lg font-bold mb-2 text-gray-800" {...props} />
                ),
                h2: ({node, ...props}) => (
                  <h2 className="text-md font-semibold mb-2 text-gray-700" {...props} />
                ),
                h3: ({node, ...props}) => (
                  <h3 className="text-sm font-semibold mb-1 text-gray-700" {...props} />
                ),
                // Style lists
                ul: ({node, ...props}) => (
                  <ul className="list-disc list-inside mb-2" {...props} />
                ),
                ol: ({node, ...props}) => (
                  <ol className="list-decimal list-inside mb-2" {...props} />
                ),
                li: ({node, ...props}) => (
                  <li className="mb-1" {...props} />
                ),
              }}
            >
              {message.text ? String(message.text) : 'Loading...'}
            </ReactMarkdown>
          </div>
        )}
        {message.timestamp && (
          <div className={`text-xs mt-1 opacity-70 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
            {message.timestamp.toLocaleTimeString()}
            {message.responseTime && (
              <span className="ml-2">({message.responseTime}ms)</span>
            )}
          </div>
        )}
        
        {/* Feedback Button for Assistant Messages */}
        {!isUser && !message.isError && message.queryId && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <FeedbackButton messageId={message.queryId} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;