// This file contains environment variables for the frontend
// For local development, use an empty string (same origin)
// For production, use the actual backend URL
window.API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '' // Empty string means same origin on localhost
    : 'https://blackhole-core-api.onrender.com'; // Use Render URL for production

console.log('API_BASE_URL set to:', window.API_BASE_URL);
