// Netlify function to search documents using the BlackHole Agent System
const { connectToMongoDB, getConnectionStatus } = require('../../agents/db/mongodb_connection');
const AgentManager = require('../../agents/agent_manager');

// Initialize MongoDB connection
let db = null;
let agentManager = null;

// Initialize the agent system with timeout
async function initializeAgentSystem() {
  if (agentManager) {
    return agentManager;
  }

  try {
    // Connect to MongoDB with a timeout
    const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/blackhole';

    // Create a promise that resolves with the connection
    const connectionPromise = connectToMongoDB(MONGODB_URI);

    // Create a promise that rejects after a timeout
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Agent system initialization timeout'));
      }, 3000); // 3 second timeout
    });

    // Race the connection promise against the timeout
    const connection = await Promise.race([connectionPromise, timeoutPromise])
      .catch(error => {
        console.warn('MongoDB connection timed out, using mock DB:', error.message);
        // Return a mock connection
        return { connection: { db: getMockDb() } };
      });

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

    // Create a fallback agent manager with no DB
    agentManager = new AgentManager({
      logger: console,
      initializeDefaultAgents: true
    });

    return agentManager;
  }
}

// Get a mock database object for fallback
function getMockDb() {
  return {
    collection: (name) => ({
      find: () => ({
        limit: () => ({
          toArray: async () => []
        })
      }),
      findOne: async () => null,
      insertOne: async () => ({ insertedId: `mock_${Date.now()}` }),
      createIndex: async () => null
    }),
    listCollections: () => ({
      toArray: async () => []
    }),
    command: async () => ({ ok: 1 })
  };
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
    // Start a timeout for the entire function
    const functionTimeout = setTimeout(() => {
      throw new Error('Function execution timeout');
    }, 8000); // 8 second timeout (Netlify limit is 10s)

    // Initialize the agent system with a timeout
    const agentSystemPromise = initializeAgentSystem();
    const agentSystemTimeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Agent system initialization timeout'));
      }, 3000); // 3 second timeout
    });

    await Promise.race([agentSystemPromise, agentSystemTimeoutPromise])
      .catch(error => {
        console.warn('Agent system initialization timed out, using fallback:', error.message);
      });

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
      // Parse the request body with timeout
      try {
        const parsePromise = async () => JSON.parse(event.body);
        const parseTimeoutPromise = new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('Request body parsing timeout'));
          }, 1000); // 1 second timeout
        });

        const body = await Promise.race([parsePromise(), parseTimeoutPromise]);
        query = body.query;
        filters = body.filters;
      } catch (parseError) {
        console.warn('Error parsing request body:', parseError);
        // Extract query directly from body as fallback
        const bodyStr = event.body || '';
        const queryMatch = bodyStr.match(/"query"\s*:\s*"([^"]+)"/);
        query = queryMatch ? queryMatch[1] : null;
      }
    } else {
      clearTimeout(functionTimeout);
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
      clearTimeout(functionTimeout);
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

    // Search for documents with timeout
    const searchPromise = agentManager.search(query, { filters });
    const searchTimeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Search timeout'));
      }, 5000); // 5 second timeout
    });

    const result = await Promise.race([searchPromise, searchTimeoutPromise])
      .catch(error => {
        console.warn('Search timed out, using fallback:', error.message);
        // Return mock search results
        return {
          query: query,
          processed_query: {
            original: query,
            normalized: query.toLowerCase(),
            keywords: query.toLowerCase().split(/\s+/),
            entities: [],
            intent: 'INFORMATION'
          },
          results: [],
          summary: `The search for "${query}" timed out. Please try a more specific query or try again later.`,
          total_results: 0,
          search_type: 'text',
          error: 'timeout'
        };
      });

    // Clear the function timeout
    clearTimeout(functionTimeout);

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
