// Netlify function to check MongoDB connection status
const { getConnectionStatus } = require('./utils/mongodb');

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
    // Get the MongoDB connection status
    const status = await getConnectionStatus();
    
    // Return the status
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        mongodb: status.status,
        details: status
      }),
    };
  } catch (error) {
    console.error('Error checking MongoDB status:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        mongodb: 'error',
        error: error.message
      }),
    };
  }
};
