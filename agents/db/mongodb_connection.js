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
    serverSelectionTimeoutMS: 10000,
    socketTimeoutMS: 45000,
    connectTimeoutMS: 10000,
    retryWrites: true,
    maxPoolSize: 10
  };
  
  // Merge options
  const connectionOptions = { ...defaultOptions, ...options };
  
  try {
    // Connect to MongoDB
    const connection = await mongoose.connect(uri, connectionOptions);
    
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
    
    // Create indexes
    await createIndexes(mongoose.connection.db);
    
    console.log('Connected to MongoDB');
    
    return connection;
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    cachedConnection = null;
    throw error;
  }
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
