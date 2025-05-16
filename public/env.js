// This file contains environment variables for the frontend
// For local development, use an empty string (same origin)
// For production, use the Netlify proxy to avoid CORS issues
window.API_BASE_URL = '';  // Always use same origin (empty string) to avoid CORS issues

// For debugging, also store the original Render backend URL
window.RENDER_BACKEND_URL = 'https://blackhole-core-api.onrender.com';

// Log the configuration
console.log('API_BASE_URL set to:', window.API_BASE_URL);
console.log('RENDER_BACKEND_URL set to:', window.RENDER_BACKEND_URL);
console.log('Hostname:', window.location.hostname);
console.log('Origin:', window.location.origin);
