// MongoDB connection utility for Netlify functions
const mongoose = require('mongoose');

// Cache the database connection to reuse it across function invocations
let cachedDb = null;

/**
 * Connect to MongoDB with retry logic and connection pooling
 * @returns {Promise<mongoose.Connection>} The MongoDB connection
 */
async function connectToDatabase() {
  // If we already have a connection, use it
  if (cachedDb && mongoose.connection.readyState === 1) {
    console.log('Using existing MongoDB connection');
    return cachedDb;
  }

  // Get the MongoDB URI from environment variables
  const MONGODB_URI = process.env.MONGODB_URI;
  
  if (!MONGODB_URI) {
    console.warn('MONGODB_URI environment variable is not set');
    throw new Error('MongoDB connection string not provided');
  }

  try {
    console.log('Connecting to MongoDB...');
    
    // Configure MongoDB connection options
    const options = {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      serverSelectionTimeoutMS: 10000, // Increase timeout for cloud environments
      socketTimeoutMS: 45000, // Increase socket timeout
      connectTimeoutMS: 10000, // Connection timeout
      retryWrites: true,
      maxPoolSize: 10 // Connection pooling
    };

    // Connect to MongoDB
    const connection = await mongoose.connect(MONGODB_URI, options);
    
    // Cache the database connection
    cachedDb = connection;
    
    console.log('MongoDB connected successfully');
    
    // Set up error handling for the connection
    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
      cachedDb = null; // Reset the cache on error
    });
    
    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
      cachedDb = null; // Reset the cache on disconnection
    });
    
    return connection;
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    cachedDb = null; // Reset the cache on error
    throw error;
  }
}

/**
 * Define the PDF document schema
 */
const pdfSchema = new mongoose.Schema({
  filename: {
    type: String,
    required: true
  },
  extracted_text: {
    type: String,
    required: true
  },
  agent_result: {
    type: Object,
    required: true
  },
  created_at: {
    type: Date,
    default: Date.now
  }
}, { timestamps: true });

/**
 * Get the PDF model (create it if it doesn't exist)
 * @returns {mongoose.Model} The PDF model
 */
function getPdfModel() {
  try {
    // Try to get the existing model
    return mongoose.model('Pdf');
  } catch (error) {
    // If the model doesn't exist, create it
    return mongoose.model('Pdf', pdfSchema);
  }
}

/**
 * Save PDF data to MongoDB
 * @param {Object} pdfData - The PDF data to save
 * @returns {Promise<Object>} The saved PDF document
 */
async function savePdfData(pdfData) {
  try {
    // Connect to the database
    await connectToDatabase();
    
    // Get the PDF model
    const PdfModel = getPdfModel();
    
    // Create a new PDF document
    const pdfDocument = new PdfModel({
      filename: pdfData.filename || 'unknown.pdf',
      extracted_text: pdfData.extracted_text || '',
      agent_result: pdfData.agent_result || {}
    });
    
    // Save the document to MongoDB
    const savedDocument = await pdfDocument.save();
    
    console.log(`PDF document saved with ID: ${savedDocument._id}`);
    
    // Return the saved document
    return {
      mongodb_id: savedDocument._id.toString(),
      ...pdfData
    };
  } catch (error) {
    console.error('Error saving PDF data to MongoDB:', error);
    throw error;
  }
}

/**
 * Get the MongoDB connection status
 * @returns {Promise<Object>} The MongoDB connection status
 */
async function getConnectionStatus() {
  try {
    // Try to connect to the database
    await connectToDatabase();
    
    // Return the connection status
    return {
      status: 'connected',
      readyState: mongoose.connection.readyState,
      host: mongoose.connection.host,
      name: mongoose.connection.name
    };
  } catch (error) {
    console.error('Error getting MongoDB connection status:', error);
    
    // Return the error status
    return {
      status: 'disconnected',
      error: error.message
    };
  }
}

module.exports = {
  connectToDatabase,
  savePdfData,
  getConnectionStatus,
  getPdfModel
};
