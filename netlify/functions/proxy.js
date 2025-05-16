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
    try {
      // Check if the body is base64 encoded
      let buffer;
      if (event.isBase64Encoded) {
        buffer = Buffer.from(event.body, 'base64');
      } else {
        buffer = Buffer.from(event.body);
      }

      // Log the size of the request body
      console.log(`Request body size: ${buffer.length} bytes`);

      // Create a readable stream from the buffer
      const stream = Readable.from([buffer]);

      // Create a new FormData object
      const formData = new FormData();

      // Get the content type and boundary
      const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';
      console.log(`Content-Type: ${contentType}`);

      // Parse the multipart form data with higher limits
      const bb = busboy({
        headers: {
          'content-type': contentType
        },
        limits: {
          fieldSize: 10 * 1024 * 1024, // 10MB
          fields: 10,
          fileSize: 50 * 1024 * 1024, // 50MB
          files: 5
        }
      });

      // Handle file fields
      bb.on('file', (name, file, info) => {
        const { filename, encoding, mimeType } = info;
        console.log(`Processing file: ${filename}, mimetype: ${mimeType}`);

        const chunks = [];
        let fileSize = 0;

        file.on('data', data => {
          chunks.push(data);
          fileSize += data.length;
          console.log(`Received ${data.length} bytes, total: ${fileSize} bytes`);
        });

        file.on('end', () => {
          console.log(`File processing complete: ${filename}, total size: ${fileSize} bytes`);
          const fileBuffer = Buffer.concat(chunks);
          formData.append(name, fileBuffer, {
            filename,
            contentType: mimeType
          });
        });

        file.on('limit', () => {
          console.warn(`File size limit reached for ${filename}`);
        });
      });

      // Handle non-file fields
      bb.on('field', (name, value) => {
        console.log(`Processing field: ${name}=${value}`);
        formData.append(name, value);
      });

      // Handle the end of parsing
      bb.on('finish', () => {
        console.log('Form data parsing complete');
        resolve(formData);
      });

      // Handle errors
      bb.on('error', err => {
        console.error('Error parsing form data:', err);
        reject(new Error(`Error parsing form data: ${err.message}`));
      });

      // Pipe the stream to busboy
      stream.pipe(bb);
    } catch (error) {
      console.error('Exception in parseMultipartForm:', error);
      reject(error);
    }
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

    // Set a timeout for the fetch request (30 seconds)
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      controller.abort();
    }, 30000);

    let response;
    let responseBody;

    try {
      // Add the signal to the options
      options.signal = controller.signal;

      // Make the request to the Render backend
      console.log('Sending request to Render backend...');
      response = await fetch(fullUrl, options);
      console.log('Received response from Render backend');

      // Get the response body
      console.log('Reading response body...');
      responseBody = await response.text();
      console.log('Response body read complete');

      // Clear the timeout
      clearTimeout(timeout);
    } catch (fetchError) {
      // Clear the timeout
      clearTimeout(timeout);

      // Check if the error is due to timeout
      if (fetchError.name === 'AbortError') {
        throw new Error('Request timed out after 30 seconds');
      }

      // Re-throw the error
      throw fetchError;
    }

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
