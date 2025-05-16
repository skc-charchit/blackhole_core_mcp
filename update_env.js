// This script is used by Netlify to inject environment variables into the frontend
const fs = require('fs');
const path = require('path');

// Get the API_BASE_URL from environment variables or use the Render backend URL
const apiBaseUrl = process.env.API_BASE_URL || 'https://blackhole-core-api.onrender.com';

// Create the content for the env.js file
const envContent = `// This file is auto-generated during deployment
// For local development, use an empty string (same origin)
// For production, use the Render backend URL
window.API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '' // Empty string means same origin on localhost
    : '${apiBaseUrl}'; // Use the Render backend URL in production

console.log('API_BASE_URL set to:', window.API_BASE_URL);
`;

// Write the content to the env.js file
fs.writeFileSync(path.join(__dirname, 'public', 'env.js'), envContent);

console.log(`Updated env.js with API_BASE_URL: ${apiBaseUrl}`);
