// This script is used by Netlify to inject environment variables into the frontend
const fs = require('fs');
const path = require('path');

// Always use empty string for API_BASE_URL to avoid CORS issues
const apiBaseUrl = '';

// Get the RENDER_BACKEND_URL from environment variables or use the default
const renderBackendUrl = process.env.RENDER_BACKEND_URL || 'https://blackhole-core-api.onrender.com';

// Create the content for the env.js file
const envContent = `// This file is auto-generated during deployment
// For local development, use an empty string (same origin)
// For production, use the Netlify proxy to avoid CORS issues
window.API_BASE_URL = ''; // Always use same origin (empty string) to avoid CORS issues

// For debugging, also store the original Render backend URL
window.RENDER_BACKEND_URL = '${renderBackendUrl}';

// Log the configuration
console.log('API_BASE_URL set to:', window.API_BASE_URL);
console.log('RENDER_BACKEND_URL set to:', window.RENDER_BACKEND_URL);
console.log('Hostname:', window.location.hostname);
console.log('Origin:', window.location.origin);
`;

// Write the content to the env.js file
fs.writeFileSync(path.join(__dirname, 'public', 'env.js'), envContent);

console.log(`Updated env.js with API_BASE_URL: ${apiBaseUrl}`);
console.log(`Updated env.js with RENDER_BACKEND_URL: ${renderBackendUrl}`);
