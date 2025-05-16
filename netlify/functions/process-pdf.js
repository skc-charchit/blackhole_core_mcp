// Netlify function to process PDFs without requiring external dependencies
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

  // Only handle POST requests
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Method not allowed',
        message: 'Only POST requests are allowed'
      }),
    };
  }

  try {
    // Parse the multipart form data
    console.log('Parsing multipart form data...');
    const formData = await parseMultipartForm(event);
    console.log('Form data parsed successfully');

    // Try to forward the request to the Render backend first
    try {
      console.log('Forwarding request to Render backend...');
      
      // Set a timeout for the fetch request (10 seconds)
      const controller = new AbortController();
      const timeout = setTimeout(() => {
        controller.abort();
      }, 10000);
      
      try {
        // Make the request to the Render backend
        const response = await fetch(`${RENDER_BACKEND_URL}/api/process-pdf`, {
          method: 'POST',
          body: formData,
          signal: controller.signal
        });
        
        // Clear the timeout
        clearTimeout(timeout);
        
        // If the request was successful, return the response
        if (response.ok) {
          console.log('Render backend processed the PDF successfully');
          const responseBody = await response.text();
          
          return {
            statusCode: response.status,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
            },
            body: responseBody,
          };
        }
        
        // If the request failed, fall back to the mock implementation
        console.log('Render backend failed to process the PDF, falling back to mock implementation');
      } catch (error) {
        // Clear the timeout
        clearTimeout(timeout);
        console.log('Error forwarding request to Render backend:', error.message);
        console.log('Falling back to mock implementation');
      }
    } catch (error) {
      console.log('Error forwarding request to Render backend:', error.message);
      console.log('Falling back to mock implementation');
    }
    
    // Mock implementation - return a response without requiring external dependencies
    console.log('Using mock implementation for PDF processing');
    
    // Create a mock response
    const mockResponse = {
      extracted_text: "PDF text extraction is not available in this environment. External dependencies are required for PDF processing but are not installed on the server.",
      agent_result: {
        agent: "ArchiveSearchAgent",
        input: {
          document_text: "PDF text extraction is not available in this environment."
        },
        metadata: {
          source_file: "mock_response.txt",
          processed_at: new Date().toISOString()
        },
        output: "This is a mock response. The PDF was received successfully, but text extraction is not available in this environment.",
        timestamp: new Date().toISOString()
      }
    };
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(mockResponse),
    };
  } catch (error) {
    console.error('Error processing PDF:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Error processing PDF',
        message: error.message,
        stack: error.stack
      }),
    };
  }
};
