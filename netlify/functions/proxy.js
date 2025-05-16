// Netlify function to proxy requests to the Render backend
const fetch = require('node-fetch');

// The URL of the Render backend
const RENDER_BACKEND_URL = process.env.RENDER_BACKEND_URL || 'https://blackhole-core-api.onrender.com';

exports.handler = async function(event, context) {
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

  // Get the path and query parameters from the event
  const path = event.path.replace('/.netlify/functions/proxy', '');
  const queryParams = event.queryStringParameters || {};
  const queryString = Object.keys(queryParams).length > 0
    ? '?' + Object.keys(queryParams)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(queryParams[key])}`)
        .join('&')
    : '';

  // Construct the full URL to the Render backend
  const fullUrl = `${RENDER_BACKEND_URL}${path}${queryString}`;

  console.log(`Proxying request to: ${fullUrl}`);
  console.log(`Method: ${event.httpMethod}`);
  console.log(`Headers: ${JSON.stringify(event.headers)}`);
  console.log(`Body: ${event.body || 'none'}`);

  try {
    // Set up the request options
    const options = {
      method: event.httpMethod,
      headers: {
        'Content-Type': event.headers['content-type'] || 'application/json',
        'Accept': event.headers['accept'] || 'application/json',
      },
    };

    // Add the request body if it exists
    if (event.body) {
      options.body = event.body;
    }

    // Make the request to the Render backend
    const response = await fetch(fullUrl, options);

    // Get the response body
    const responseBody = await response.text();

    // Get the response headers
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    console.log(`Response status: ${response.status}`);
    console.log(`Response headers: ${JSON.stringify(responseHeaders)}`);
    console.log(`Response body: ${responseBody.substring(0, 200)}${responseBody.length > 200 ? '...' : ''}`);

    // Return the response from the Render backend
    return {
      statusCode: response.status,
      headers: {
        'Content-Type': responseHeaders['content-type'] || 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: responseBody,
    };
  } catch (error) {
    console.error('Error proxying request:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: JSON.stringify({
        error: 'Error proxying request to Render backend',
        details: error.message,
        url: fullUrl,
        method: event.httpMethod,
      }),
    };
  }
};
