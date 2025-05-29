// Netlify function to fetch live data using the BlackHole Agent System
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

    // Create a fallback agent manager with no DB
    agentManager = new AgentManager({
      logger: console,
      initializeDefaultAgents: true,
      liveDataOptions: {
        apiKeys: {
          openweathermap: process.env.OPENWEATHERMAP_API_KEY,
          newsapi: process.env.NEWSAPI_API_KEY,
          alphavantage: process.env.ALPHAVANTAGE_API_KEY
        },
        cacheEnabled: false // Disable cache without DB
      }
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
    let source, query;

    if (event.httpMethod === 'GET') {
      // Get source and query from query parameters
      source = event.queryStringParameters?.source;

      // Parse query if provided
      if (event.queryStringParameters?.query) {
        try {
          const parsePromise = async () => JSON.parse(event.queryStringParameters.query);
          const parseTimeoutPromise = new Promise((_, reject) => {
            setTimeout(() => {
              reject(new Error('Query parsing timeout'));
            }, 1000); // 1 second timeout
          });

          query = await Promise.race([parsePromise(), parseTimeoutPromise])
            .catch(error => {
              console.warn('Query parsing timed out, using fallback:', error.message);
              // Use the query string as is
              return { location: event.queryStringParameters.query };
            });
        } catch (error) {
          // If parsing fails, use the query string as is
          query = { location: event.queryStringParameters.query };
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

        const body = await Promise.race([parsePromise(), parseTimeoutPromise])
          .catch(error => {
            console.warn('Request body parsing timed out, using fallback:', error.message);
            // Extract source and query directly from body as fallback
            const bodyStr = event.body || '';
            const sourceMatch = bodyStr.match(/"source"\s*:\s*"([^"]+)"/);
            const queryMatch = bodyStr.match(/"query"\s*:\s*(\{[^}]+\})/);

            return {
              source: sourceMatch ? sourceMatch[1] : null,
              query: queryMatch ? JSON.parse(queryMatch[1]) : { location: 'unknown' }
            };
          });

        source = body.source;
        query = body.query;
      } catch (parseError) {
        console.warn('Error parsing request body:', parseError);
        // Extract source directly from body as fallback
        const bodyStr = event.body || '';
        const sourceMatch = bodyStr.match(/"source"\s*:\s*"([^"]+)"/);
        source = sourceMatch ? sourceMatch[1] : null;
        query = { location: 'unknown' };
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

    // Validate the source
    if (!source) {
      clearTimeout(functionTimeout);
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

    // Fetch live data with timeout
    const fetchPromise = agentManager.getLiveData(source, query);
    const fetchTimeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Live data fetch timeout'));
      }, 5000); // 5 second timeout
    });

    const result = await Promise.race([fetchPromise, fetchTimeoutPromise])
      .catch(error => {
        console.warn('Live data fetch timed out, using fallback:', error.message);
        // Return mock data based on the source
        if (source === 'weather') {
          return {
            source: 'weather',
            query: query,
            data: {
              current: {
                location: query.location || 'Unknown',
                country: 'Unknown',
                temperature: {
                  current: 22.5,
                  feelsLike: 23.2,
                  min: 20.1,
                  max: 24.8,
                  unit: 'celsius'
                },
                conditions: {
                  main: 'Clear',
                  description: 'clear sky',
                  icon: '01d'
                },
                humidity: 65,
                pressure: 1012,
                time: new Date().toISOString()
              },
              forecast: [],
              mock: true
            },
            timestamp: new Date().toISOString(),
            cached: false,
            error: 'timeout'
          };
        } else {
          return {
            source: source,
            query: query,
            data: {
              message: `Data for ${source} is not available due to a timeout.`
            },
            timestamp: new Date().toISOString(),
            cached: false,
            error: 'timeout'
          };
        }
      });

    // Clear the function timeout
    clearTimeout(functionTimeout);

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
