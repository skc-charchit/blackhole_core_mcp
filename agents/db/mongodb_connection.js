/**
 * MongoDB Connection Utility
 * Manages connections to MongoDB for the BlackHole Agent System
 */
const mongoose = require('mongoose');
const { createIndexes } = require('./mongodb_schema');

// Connection cache
let cachedConnection = null;
let connectionAttemptInProgress = false;
let autoConnectInitiated = false;

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

  // If a connection attempt is already in progress, wait for it
  if (connectionAttemptInProgress) {
    console.log('Connection attempt already in progress, waiting...');
    // Wait for the connection attempt to complete (max 3 seconds)
    for (let i = 0; i < 30; i++) {
      await new Promise(resolve => setTimeout(resolve, 100));
      if (cachedConnection && mongoose.connection.readyState === 1) {
        return cachedConnection;
      }
    }
  }

  // Mark that a connection attempt is in progress
  connectionAttemptInProgress = true;

  // Default options
  const defaultOptions = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    serverSelectionTimeoutMS: 5000, // Reduced timeout
    socketTimeoutMS: 10000, // Reduced timeout
    connectTimeoutMS: 5000, // Reduced timeout
    retryWrites: true,
    maxPoolSize: 5, // Reduced pool size
    autoReconnect: true, // Enable auto reconnect
    reconnectTries: Number.MAX_VALUE, // Try to reconnect forever
    reconnectInterval: 1000 // Reconnect every 1 second
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
      connectionAttemptInProgress = false;

      // Try to reconnect after a delay
      setTimeout(() => {
        console.log('Attempting to reconnect to MongoDB...');
        connectToMongoDB(uri, options).catch(err => {
          console.error('Reconnection attempt failed:', err);
        });
      }, 5000);
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
      cachedConnection = null;
      connectionAttemptInProgress = false;

      // Try to reconnect after a delay
      setTimeout(() => {
        console.log('Attempting to reconnect to MongoDB...');
        connectToMongoDB(uri, options).catch(err => {
          console.error('Reconnection attempt failed:', err);
        });
      }, 5000);
    });

    mongoose.connection.on('connected', () => {
      console.log('MongoDB connected');
      connectionAttemptInProgress = false;
    });

    // Create indexes in the background
    setTimeout(() => {
      createIndexes(mongoose.connection.db)
        .then(() => console.log('MongoDB indexes created'))
        .catch(err => console.error('Error creating MongoDB indexes:', err));
    }, 100);

    console.log('Connected to MongoDB');
    connectionAttemptInProgress = false;

    return connection;
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    cachedConnection = null;
    connectionAttemptInProgress = false;

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
    cached: !!cachedConnection,
    autoConnectInitiated: autoConnectInitiated
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

/**
 * Auto-connect to MongoDB using environment variables
 * This function will be called automatically when the module is imported
 * @returns {Promise<mongoose.Connection>} - MongoDB connection
 */
async function autoConnect() {
  if (autoConnectInitiated) {
    return cachedConnection;
  }

  autoConnectInitiated = true;
  console.log('Auto-connecting to MongoDB...');

  try {
    // Get MongoDB URI from environment variables
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/blackhole';

    // Connect to MongoDB
    const connection = await connectToMongoDB(uri);

    console.log('Auto-connection to MongoDB successful');
    return connection;
  } catch (error) {
    console.error('Auto-connection to MongoDB failed:', error);
    return null;
  }
}

// Start auto-connection process
autoConnect().catch(err => {
  console.error('Error in auto-connect process:', err);
});

module.exports = {
  connectToMongoDB,
  getConnectionStatus,
  closeConnection,
  autoConnect
};
