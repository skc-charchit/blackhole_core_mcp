// Netlify function to proxy requests to the Render backend
const fetch = require('node-fetch');
const FormData = require('form-data');
const busboy = require('busboy');
const { Readable } = require('stream');

// The URL of the Render backend
const RENDER_BACKEND_URL = process.env.RENDER_BACKEND_URL || 'https://blackhole-core-api.onrender.com';

// Parse multipart form data
const parseMultipartForm = event => {
  return new Promise((resolve, reject) => {
    // Create a readable stream from the request body
    const stream = Readable.from([Buffer.from(event.body, 'base64')]);

    // Create a new FormData object
    const formData = new FormData();

    // Parse the multipart form data
    const bb = busboy({
      headers: {
        'content-type': event.headers['content-type'] || event.headers['Content-Type']
      }
    });

    // Handle file fields
    bb.on('file', (name, file, info) => {
      const { filename, encoding, mimeType } = info;
      console.log(`Processing file: ${filename}, mimetype: ${mimeType}`);

      const chunks = [];
      file.on('data', data => chunks.push(data));
      file.on('end', () => {
        const fileBuffer = Buffer.concat(chunks);
        formData.append(name, fileBuffer, {
          filename,
          contentType: mimeType
        });
      });
    });

    // Handle non-file fields
    bb.on('field', (name, value) => {
      console.log(`Processing field: ${name}=${value}`);
      formData.append(name, value);
    });

    // Handle the end of parsing
    bb.on('finish', () => {
      resolve(formData);
    });

    // Handle errors
    bb.on('error', err => {
      reject(new Error(`Error parsing form data: ${err.message}`));
    });

    // Pipe the stream to busboy
    stream.pipe(bb);
  });
};

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

  try {
    // Set up the request options
    const options = {
      method: event.httpMethod,
      headers: {
        'Accept': event.headers['accept'] || 'application/json',
        'Origin': 'https://blackholebody.netlify.app',
      },
    };

    // Handle different content types
    const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';

    // For multipart form data (file uploads)
    if (contentType.includes('multipart/form-data')) {
      console.log('Processing multipart form data');

      try {
        // Parse the multipart form data
        const formData = await parseMultipartForm(event);

        // Use the form data as the request body
        options.body = formData;

        // The headers will be set by the FormData object
        delete options.headers['Content-Type'];
      } catch (formError) {
        console.error('Error parsing form data:', formError);
        return {
          statusCode: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          },
          body: JSON.stringify({
            error: 'Error parsing form data',
            details: formError.message
          }),
        };
      }
    }
    // For JSON data
    else if (contentType.includes('application/json')) {
      options.headers['Content-Type'] = 'application/json';
      if (event.body) {
        options.body = event.body;
      }
    }
    // For other content types
    else if (event.body) {
      options.headers['Content-Type'] = contentType;
      options.body = event.body;
    }

    console.log(`Request options: ${JSON.stringify({
      method: options.method,
      headers: options.headers,
      bodyType: options.body ? typeof options.body : 'none'
    })}`);

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

    // Try to parse the response body as JSON
    let jsonResponse;
    try {
      jsonResponse = JSON.parse(responseBody);
    } catch (e) {
      console.log('Response is not valid JSON:', e.message);
      // If the response is not valid JSON, it might be HTML or some other format
      // In this case, we'll return a JSON error response
      if (responseBody.includes('<html') || responseBody.includes('<!DOCTYPE')) {
        return {
          statusCode: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          },
          body: JSON.stringify({
            error: 'Received HTML response from Render backend',
            details: 'The Render backend returned HTML instead of JSON. This might indicate an error page or redirect.',
            url: fullUrl,
            method: event.httpMethod,
            status: response.status,
          }),
        };
      }
    }

    // Return the response from the Render backend
    return {
      statusCode: response.status,
      headers: {
        'Content-Type': 'application/json',
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
