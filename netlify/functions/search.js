// Netlify function to search documents using the BlackHole Agent System
const { connectToMongoDB, getConnectionStatus } = require('../../agents/db/mongodb_connection');
const AgentManager = require('../../agents/agent_manager');

// Initialize MongoDB connection
let db = null;
let agentManager = null;

// Initialize the agent system
async function initializeAgentSystem() {
  if (agentManager) {
    return agentManager;
  }
  
  try {
    // Connect to MongoDB
    const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/blackhole';
    const connection = await connectToMongoDB(MONGODB_URI);
    db = connection.connection.db;
    
    // Create agent manager
    agentManager = new AgentManager({
      db: db,
      logger: console,
      initializeDefaultAgents: true
    });
    
    return agentManager;
  } catch (error) {
    console.error('Error initializing agent system:', error);
    throw error;
  }
}

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
    // Initialize the agent system
    await initializeAgentSystem();
    
    // Parse the request
    let query, filters;
    
    if (event.httpMethod === 'GET') {
      // Get query from query parameters
      query = event.queryStringParameters?.query;
      
      // Parse filters if provided
      if (event.queryStringParameters?.filters) {
        try {
          filters = JSON.parse(event.queryStringParameters.filters);
        } catch (error) {
          console.warn('Error parsing filters:', error);
        }
      }
    } else if (event.httpMethod === 'POST') {
      // Parse the request body
      const body = JSON.parse(event.body);
      query = body.query;
      filters = body.filters;
    } else {
      return {
        statusCode: 405,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Method not allowed',
          message: 'Only GET and POST requests are allowed'
        }),
      };
    }
    
    // Validate the query
    if (!query) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Bad request',
          message: 'Query is required'
        }),
      };
    }
    
    // Search for documents
    const result = await agentManager.search(query, { filters });
    
    // Return the search results
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error searching documents:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Error searching documents',
        message: error.message,
        stack: error.stack
      }),
    };
  }
};
