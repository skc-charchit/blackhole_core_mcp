// A simple mock image processing function that always returns a successful response
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

  // Create a mock response
  const mockResponse = {
    extracted_text: "This is a mock response from the Netlify function. In a real application, this would contain text extracted from an image.",
    agent_result: {
      agent: "ArchiveSearchAgent",
      input: {
        document_text: "This is a mock response from the Netlify function."
      },
      metadata: {
        source_file: "mock_response.txt",
        processed_at: new Date().toISOString()
      },
      output: "No matches found.",
      timestamp: new Date().toISOString()
    }
  };

  // Return the mock response
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify(mockResponse),
  };
};
