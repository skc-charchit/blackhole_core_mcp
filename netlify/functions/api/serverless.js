// Netlify serverless function to proxy API requests to the Python FastAPI backend
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { URL } = require('url');

// Handler for the Netlify function
exports.handler = async function(event, context) {
  try {
    // Get the path and query parameters from the event
    const path = event.path.replace('/.netlify/functions/api', '');
    const method = event.httpMethod;
    const queryParams = event.queryStringParameters || {};
    const body = event.body ? JSON.parse(event.body) : null;
    
    // Forward the request to the FastAPI server
    const response = await forwardRequest(path, method, queryParams, body);
    
    return {
      statusCode: response.statusCode,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
      },
      body: JSON.stringify(response.body)
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
      },
      body: JSON.stringify({ error: error.message })
    };
  }
};

// Function to forward the request to the FastAPI server
async function forwardRequest(path, method, queryParams, body) {
  // For now, just return a mock response
  // In a real-world scenario, you would use a proper HTTP client
  // to forward the request to the FastAPI server
  
  // Mock responses for different endpoints
  if (path === '/api/health') {
    return {
      statusCode: 200,
      body: {
        'status': 'ok',
        'mongodb': 'connected',
        'mongodb_error': null,
        'timestamp': new Date().toISOString()
      }
    };
  } else if (path === '/api/test') {
    return {
      statusCode: 200,
      body: {
        'message': 'API is working!',
        'timestamp': new Date().toISOString()
      }
    };
  } else if (path === '/api/weather') {
    return {
      statusCode: 200,
      body: {
        'agent': 'LiveDataAgent',
        'input': { 'query': `${queryParams.location || 'London'} weather` },
        'output': {
          'location': queryParams.location || 'London',
          'temperature': '22°C',
          'condition': 'Sunny',
          'humidity': '65%',
          'wind': '10 km/h'
        },
        'timestamp': new Date().toISOString()
      }
    };
  } else if (path === '/api/search' || path === '/api/search-archive') {
    const query = body?.query || queryParams.query || 'default query';
    return {
      statusCode: 200,
      body: {
        'agent': 'ArchiveSearchAgent',
        'input': { 'document_text': query },
        'output': [
          {
            'match_score': 100.0,
            'title': 'Sample Result 1',
            'description': 'This is a sample result for the query.'
          },
          {
            'match_score': 85.0,
            'title': 'Sample Result 2',
            'description': 'This is another sample result for the query.'
          }
        ],
        'timestamp': new Date().toISOString()
      }
    };
  } else if (path === '/run_task') {
    const agent = body?.agent || 'ArchiveSearchAgent';
    const input = body?.input || 'default input';
    return {
      statusCode: 200,
      body: {
        'agent': agent,
        'input': { 'document_text': input },
        'output': {
          'agent': agent,
          'input': { 'document_text': input },
          'output': [
            {
              'match_score': 100.0,
              'title': 'Sample Result 1',
              'description': 'This is a sample result for the task.'
            },
            {
              'match_score': 85.0,
              'title': 'Sample Result 2',
              'description': 'This is another sample result for the task.'
            }
          ],
          'timestamp': new Date().toISOString()
        },
        'timestamp': new Date().toISOString()
      }
    };
  } else {
    return {
      statusCode: 404,
      body: {
        'error': 'Endpoint not found'
      }
    };
  }
}
