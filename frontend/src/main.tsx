import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Import directly from Django static directory relative to frontend/src/main.tsx
import '../../static/css/design/tokens.css';
import '../../static/css/design/components.css';
import '../../static/css/app.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);