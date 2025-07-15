import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Import Bootstrap CSS and JS
import 'bootstrap/dist/css/bootstrap.min.css';

// Import custom styles and the main App component
import './index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
