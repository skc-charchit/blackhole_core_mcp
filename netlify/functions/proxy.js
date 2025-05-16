// Netlify function to proxy requests to the Render backend
const https = require('https');
const http = require('http');
const url = require('url');

// The URL of the Render backend
const RENDER_BACKEND_URL = 'https://blackhole-core-api.onrender.com';

exports.handler = async function(event, context) {
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
  
  // Parse the URL to get the protocol, hostname, and port
  const parsedUrl = url.parse(fullUrl);
  const protocol = parsedUrl.protocol === 'https:' ? https : http;
  
  // Set up the request options
  const options = {
    method: event.httpMethod,
    headers: {
      ...event.headers,
      host: parsedUrl.hostname,
    },
  };
  
  // Remove headers that might cause issues
  delete options.headers['host'];
  delete options.headers['Host'];
  delete options.headers['connection'];
  delete options.headers['Connection'];
  
  // Add the request body if it exists
  const body = event.body ? event.body : null;
  
  try {
    // Make the request to the Render backend
    const response = await new Promise((resolve, reject) => {
      const req = protocol.request(fullUrl, options, (res) => {
        let responseBody = '';
        
        res.on('data', (chunk) => {
          responseBody += chunk;
        });
        
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: responseBody,
          });
        });
      });
      
      req.on('error', (error) => {
        reject(error);
      });
      
      if (body) {
        req.write(body);
      }
      
      req.end();
    });
    
    // Return the response from the Render backend
    return {
      statusCode: response.statusCode,
      headers: {
        'Content-Type': response.headers['content-type'] || 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      },
      body: response.body,
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
