// Netlify function to test the environment and configuration
const { autoConnect, getConnectionStatus } = require('./utils/mongodb_connection');

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
    let mongodbStatus = 'not checked';
    try {
      await autoConnect();
      const status = getConnectionStatus();
      mongodbStatus = status.status;
    } catch (mongoError) {
      console.error('Error checking MongoDB status:', mongoError);
      mongodbStatus = 'error';
    }

    // Get environment variables (redact sensitive information)
    const env = {
      NODE_ENV: process.env.NODE_ENV,
      NETLIFY: process.env.NETLIFY,
      CONTEXT: process.env.CONTEXT,
      MONGODB_URI: process.env.MONGODB_URI ? '[REDACTED]' : undefined,
      RENDER_BACKEND_URL: process.env.RENDER_BACKEND_URL ? '[REDACTED]' : undefined
    };

    // Return the test results
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: JSON.stringify({
        status: 'ok',
        message: 'Netlify Function is working!',
        timestamp: new Date().toISOString(),
        mongodb: mongodbStatus,
        env: env,
        runtime: {
          node: process.version,
          platform: process.platform,
          arch: process.arch
        },
        event: {
          path: event.path,
          httpMethod: event.httpMethod,
          headers: event.headers,
          queryStringParameters: event.queryStringParameters,
        }
      }),
    };
  } catch (error) {
    console.error('Error in test function:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: JSON.stringify({
        status: 'error',
        error: error.message
      }),
    };
  }
};
