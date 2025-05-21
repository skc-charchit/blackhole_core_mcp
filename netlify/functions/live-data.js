// Netlify function to fetch live data using the BlackHole Agent System
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
      initializeDefaultAgents: true,
      liveDataOptions: {
        apiKeys: {
          openweathermap: process.env.OPENWEATHERMAP_API_KEY,
          newsapi: process.env.NEWSAPI_API_KEY,
          alphavantage: process.env.ALPHAVANTAGE_API_KEY
        },
        cacheEnabled: true,
        cacheTTL: 3600000 // 1 hour
      }
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
    let source, query;
    
    if (event.httpMethod === 'GET') {
      // Get source and query from query parameters
      source = event.queryStringParameters?.source;
      
      // Parse query if provided
      if (event.queryStringParameters?.query) {
        try {
          query = JSON.parse(event.queryStringParameters.query);
        } catch (error) {
          // If parsing fails, use the query string as is
          query = { location: event.queryStringParameters.query };
        }
      }
    } else if (event.httpMethod === 'POST') {
      // Parse the request body
      const body = JSON.parse(event.body);
      source = body.source;
      query = body.query;
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
    
    // Validate the source
    if (!source) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Bad request',
          message: 'Data source is required'
        }),
      };
    }
    
    // Fetch live data
    const result = await agentManager.getLiveData(source, query);
    
    // Return the data
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error fetching live data:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Error fetching live data',
        message: error.message,
        stack: error.stack
      }),
    };
  }
};
