// This file contains environment variables for the frontend
// For local development, use an empty string (same origin)
// For production, use the Netlify function URL
window.API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '' // Empty string means same origin on localhost
    : '/.netlify/functions/api'; // Use the Netlify function URL in production

console.log('API_BASE_URL set to:', window.API_BASE_URL);
