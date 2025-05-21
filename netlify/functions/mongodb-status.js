// Netlify function to check MongoDB connection status
const mongoose = require('mongoose');
const { autoConnect, getConnectionStatus } = require('../agents/db/mongodb_connection');

exports.handler = async function(event, context) {
  // Make the database connection reusable across function invocations
  context.callbackWaitsForEmptyEventLoop = false;

  // Handle OPTIONS requests for CORS
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Max-Age': '86400',
      },
      body: '',
    };
  }

  try {
    // Try to auto-connect to MongoDB
    await autoConnect();

    // Get the MongoDB connection status
    const status = getConnectionStatus();

    // Get environment variables (redact sensitive information)
    const env = {
      MONGODB_URI: process.env.MONGODB_URI ? '[REDACTED]' : undefined,
      NODE_ENV: process.env.NODE_ENV,
      NETLIFY: process.env.NETLIFY,
      CONTEXT: process.env.CONTEXT
    };

    // Return the status
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        mongodb: status.status,
        details: status,
        env: env,
        timestamp: new Date().toISOString()
      }),
    };
  } catch (error) {
    console.error('Error checking MongoDB status:', error);

    return {
      statusCode: 200, // Return 200 even for errors
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        mongodb: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      }),
    };
  }
};
