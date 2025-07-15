// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true,
    },
  },
});
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
