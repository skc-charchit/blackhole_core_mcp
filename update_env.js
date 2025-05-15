// This script is used by Netlify to inject environment variables into the frontend
const fs = require('fs');
const path = require('path');

// Get the API_BASE_URL from environment variables
const apiBaseUrl = process.env.API_BASE_URL || '';

// Create the content for the env.js file
const envContent = `// This file is auto-generated during deployment
window.API_BASE_URL = '${apiBaseUrl}';
`;

// Write the content to the env.js file
fs.writeFileSync(path.join(__dirname, 'public', 'env.js'), envContent);

console.log(`Updated env.js with API_BASE_URL: ${apiBaseUrl}`);
