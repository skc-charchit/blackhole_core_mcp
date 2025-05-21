// This script is used by Netlify to inject environment variables into the frontend
const fs = require('fs');
const path = require('path');

// Default MongoDB URI (for local development)
const DEFAULT_MONGODB_URI = 'mongodb://localhost:27017/blackhole';

// Always use empty string for API_BASE_URL to avoid CORS issues
const apiBaseUrl = '';

// Get the RENDER_BACKEND_URL from environment variables or use the default
const renderBackendUrl = process.env.RENDER_BACKEND_URL || 'https://blackhole-core-api.onrender.com';

// Get the MONGODB_URI from environment variables or use the default
const mongodbUri = process.env.MONGODB_URI || DEFAULT_MONGODB_URI;

// Create the content for the env.js file
const envContent = `// This file is auto-generated during deployment
// For local development, use an empty string (same origin)
// For production, use the Netlify proxy to avoid CORS issues
window.API_BASE_URL = ''; // Always use same origin (empty string) to avoid CORS issues

// For debugging, also store the original Render backend URL
window.RENDER_BACKEND_URL = '${renderBackendUrl}';

// MongoDB connection status will be checked at runtime
window.MONGODB_ENABLED = ${!!process.env.MONGODB_URI};

// Log the configuration
console.log('API_BASE_URL set to:', window.API_BASE_URL);
console.log('RENDER_BACKEND_URL set to:', window.RENDER_BACKEND_URL);
console.log('MONGODB_ENABLED:', window.MONGODB_ENABLED);
console.log('Hostname:', window.location.hostname);
console.log('Origin:', window.location.origin);
`;

// Write the content to the env.js file
fs.writeFileSync(path.join(__dirname, 'public', 'env.js'), envContent);

console.log(`Updated env.js with API_BASE_URL: ${apiBaseUrl}`);
console.log(`Updated env.js with RENDER_BACKEND_URL: ${renderBackendUrl}`);
console.log(`MongoDB enabled: ${!!process.env.MONGODB_URI}`);

// Update or create .env file for local development
function updateEnvironmentVariables() {
  console.log('Updating environment variables for local development...');

  try {
    // Check if .env file exists
    const envPath = path.join(__dirname, '.env');
    let envContent = '';

    if (fs.existsSync(envPath)) {
      console.log('Found .env file, reading content...');
      envContent = fs.readFileSync(envPath, 'utf8');
    } else {
      console.log('No .env file found, creating a new one with default values...');
      // Create a default .env file with essential variables
      const defaultEnvContent =
`# MongoDB connection strings
# Netlify Functions MongoDB URI - used by Netlify Functions for MongoDB connection
MONGODB_URI=mongodb://localhost:27017/blackhole

# Render Backend URL - used by Netlify Functions to connect to the Render backend
RENDER_BACKEND_URL=https://blackhole-core-api.onrender.com
`;
      fs.writeFileSync(envPath, defaultEnvContent);
      envContent = defaultEnvContent;
    }

    // Parse existing environment variables
    const envVars = {};
    envContent.split('\n').forEach(line => {
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim();
        envVars[key] = value;
      }
    });

    // Set default values if not already set
    if (!envVars.MONGODB_URI) {
      console.log('Setting default MONGODB_URI in .env file...');
      envVars.MONGODB_URI = DEFAULT_MONGODB_URI;
    }

    if (!envVars.RENDER_BACKEND_URL) {
      console.log('Setting default RENDER_BACKEND_URL in .env file...');
      envVars.RENDER_BACKEND_URL = 'https://blackhole-core-api.onrender.com';
    }

    // Convert environment variables back to string
    const newEnvContent = Object.entries(envVars)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    // Write updated .env file
    fs.writeFileSync(envPath, newEnvContent);
    console.log('Environment variables updated successfully.');

    // Check if running in Netlify environment
    if (process.env.NETLIFY) {
      console.log('Running in Netlify environment.');

      // Check if MONGODB_URI is set in Netlify environment
      if (process.env.MONGODB_URI) {
        console.log('MONGODB_URI is set in Netlify environment.');
      } else {
        console.warn('WARNING: MONGODB_URI is not set in Netlify environment.');
        console.warn('MongoDB connection may not work in production.');
        console.warn('Please set MONGODB_URI in Netlify environment variables.');
      }
    }
  } catch (error) {
    console.error('Error updating environment variables:', error);
  }
}

// Run the environment variable update function
updateEnvironmentVariables();
