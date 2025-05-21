/**
 * MongoDB Connection Utility
 * Manages connections to MongoDB for the BlackHole Agent System
 */
const mongoose = require('mongoose');
const { createIndexes } = require('./mongodb_schema');

// Connection cache
let cachedConnection = null;

/**
 * Connect to MongoDB
 * @param {string} uri - MongoDB connection URI
 * @param {Object} options - Connection options
 * @returns {Promise<mongoose.Connection>} - MongoDB connection
 */
async function connectToMongoDB(uri, options = {}) {
  // If we already have a connection, return it
  if (cachedConnection && mongoose.connection.readyState === 1) {
    return cachedConnection;
  }

  // Default options
  const defaultOptions = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    serverSelectionTimeoutMS: 5000, // Reduced timeout
    socketTimeoutMS: 10000, // Reduced timeout
    connectTimeoutMS: 5000, // Reduced timeout
    retryWrites: true,
    maxPoolSize: 5 // Reduced pool size
  };

  // Merge options
  const connectionOptions = { ...defaultOptions, ...options };

  try {
    // Connect to MongoDB with a timeout
    const connectionPromise = mongoose.connect(uri, connectionOptions);

    // Add a timeout to the connection promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('MongoDB connection timeout'));
      }, 5000); // 5 second timeout
    });

    // Race the connection promise against the timeout
    const connection = await Promise.race([connectionPromise, timeoutPromise]);

    // Cache the connection
    cachedConnection = connection;

    // Set up event handlers
    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
      cachedConnection = null;
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
      cachedConnection = null;
    });

    // Create indexes in the background
    setTimeout(() => {
      createIndexes(mongoose.connection.db)
        .then(() => console.log('MongoDB indexes created'))
        .catch(err => console.error('Error creating MongoDB indexes:', err));
    }, 100);

    console.log('Connected to MongoDB');

    return connection;
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    cachedConnection = null;

    // Return a mock connection for fallback
    return {
      connection: {
        db: getMockDb(),
        readyState: 0
      }
    };
  }
}

/**
 * Get a mock database object for fallback
 * @returns {Object} - Mock database object
 */
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

/**
 * Get the MongoDB connection status
 * @returns {Object} - Connection status
 */
function getConnectionStatus() {
  const states = {
    0: 'disconnected',
    1: 'connected',
    2: 'connecting',
    3: 'disconnecting',
    99: 'uninitialized'
  };

  const readyState = mongoose.connection.readyState;

  return {
    status: states[readyState] || 'unknown',
    readyState: readyState,
    host: mongoose.connection.host,
    name: mongoose.connection.name,
    cached: !!cachedConnection
  };
}

/**
 * Close the MongoDB connection
 * @returns {Promise<void>}
 */
async function closeConnection() {
  if (mongoose.connection.readyState !== 0) {
    await mongoose.connection.close();
    cachedConnection = null;
    console.log('MongoDB connection closed');
  }
}

module.exports = {
  connectToMongoDB,
  getConnectionStatus,
  closeConnection
};
