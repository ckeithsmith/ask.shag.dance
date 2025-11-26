import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  // Temporarily disable StrictMode to prevent double-invocation of effects causing auth loops
  // <React.StrictMode>
    <App />
  // </React.StrictMode>
);