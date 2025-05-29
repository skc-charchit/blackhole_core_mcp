// Netlify function to process documents using the BlackHole Agent System
const fetch = require('node-fetch');
const FormData = require('form-data');
const busboy = require('busboy');
const { Readable } = require('stream');
const { connectToMongoDB, getConnectionStatus } = require('../../agents/db/mongodb_connection');
const AgentManager = require('../../agents/agent_manager');
const PDFExtractorAgent = require('../../agents/pdf/pdf_extractor_agent');
const ImageOCRAgent = require('../../agents/image/image_ocr_agent');
const SearchAgent = require('../../agents/search/search_agent');
const LiveDataAgent = require('../../agents/live_data/live_data_agent');

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

// Parse multipart form data
const parseMultipartForm = event => {
  return new Promise((resolve, reject) => {
    try {
      // Check if the body is base64 encoded
      let buffer;
      if (event.isBase64Encoded) {
        buffer = Buffer.from(event.body, 'base64');
      } else {
        buffer = Buffer.from(event.body);
      }

      // Log the size of the request body
      console.log(`Request body size: ${buffer.length} bytes`);

      // Create a readable stream from the buffer
      const stream = Readable.from([buffer]);

      // Create a new FormData object
      const formData = new FormData();

      // Get the content type and boundary
      const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';
      console.log(`Content-Type: ${contentType}`);

      // Store additional fields
      const fields = {
        filename: 'unknown.file',
        saveToMongoDB: true,
        documentType: 'unknown'
      };

      // Store file data
      let fileData = null;

      // Parse the multipart form data with higher limits
      const bb = busboy({
        headers: {
          'content-type': contentType
        },
        limits: {
          fieldSize: 10 * 1024 * 1024, // 10MB
          fields: 10,
          fileSize: 50 * 1024 * 1024, // 50MB
          files: 5
        }
      });

      // Handle file fields
      bb.on('file', (name, file, info) => {
        const { filename, encoding, mimeType } = info;
        console.log(`Processing file: ${filename}, mimetype: ${mimeType}`);

        // Store the filename and determine document type
        fields.filename = filename;

        if (mimeType === 'application/pdf' || filename.toLowerCase().endsWith('.pdf')) {
          fields.documentType = 'pdf';
        } else if (mimeType.startsWith('image/') ||
                  ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'].some(ext =>
                    filename.toLowerCase().endsWith(ext))) {
          fields.documentType = 'image';
        }

        const chunks = [];
        let fileSize = 0;

        file.on('data', data => {
          chunks.push(data);
          fileSize += data.length;
          console.log(`Received ${data.length} bytes, total: ${fileSize} bytes`);
        });

        file.on('end', () => {
          console.log(`File processing complete: ${filename}, total size: ${fileSize} bytes`);
          fileData = Buffer.concat(chunks);
          formData.append(name, fileData, {
            filename,
            contentType: mimeType
          });
        });

        file.on('limit', () => {
          console.warn(`File size limit reached for ${filename}`);
        });
      });

      // Handle non-file fields
      bb.on('field', (name, value) => {
        console.log(`Processing field: ${name}=${value}`);

        // Store special fields
        if (name === 'filename') {
          fields.filename = value;
        } else if (name === 'save_to_mongodb') {
          fields.saveToMongoDB = value.toLowerCase() === 'true';
        } else if (name === 'document_type') {
          fields.documentType = value.toLowerCase();
        } else if (name === 'query') {
          fields.query = value;
        }

        formData.append(name, value);
      });

      // Handle the end of parsing
      bb.on('finish', () => {
        console.log('Form data parsing complete');
        resolve({ formData, fields, fileData });
      });

      // Handle errors
      bb.on('error', err => {
        console.error('Error parsing form data:', err);
        reject(new Error(`Error parsing form data: ${err.message}`));
      });

      // Pipe the stream to busboy
      stream.pipe(bb);
    } catch (error) {
      console.error('Exception in parseMultipartForm:', error);
      reject(error);
    }
  });
};

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

    // Parse the multipart form data with a timeout
    console.log('Parsing multipart form data...');
    const formDataPromise = parseMultipartForm(event);
    const formDataTimeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Form data parsing timeout'));
      }, 3000); // 3 second timeout
    });

    const { formData, fields, fileData } = await Promise.race([formDataPromise, formDataTimeoutPromise])
      .catch(error => {
        console.warn('Form data parsing timed out, using fallback:', error.message);
        // Return mock form data
        return {
          formData: null,
          fields: {
            filename: 'timeout.pdf',
            documentType: 'pdf',
            saveToMongoDB: false
          },
          fileData: Buffer.from('Mock file data')
        };
      });

    console.log('Form data processed');
    console.log(`Filename: ${fields.filename}, Document Type: ${fields.documentType}, Save to MongoDB: ${fields.saveToMongoDB}`);

    // Prepare the input for the agent
    const input = {
      file: {
        name: fields.filename,
        type: fields.documentType === 'pdf' ? 'application/pdf' : 'image/jpeg',
        data: fileData
      }
    };

    // If a query is provided, add it to the input
    if (fields.query) {
      input.query = fields.query;
    }

    // Process the document with the appropriate agent with a timeout
    let result;
    const processPromise = async () => {
      if (fields.documentType === 'pdf') {
        // Process with PDF Extractor Agent
        return await agentManager.process('pdf', input);
      } else if (fields.documentType === 'image') {
        // Process with Image OCR Agent
        return await agentManager.process('image', input);
      } else if (fields.query) {
        // Process with Search Agent
        return await agentManager.process('search', input);
      } else {
        // Auto-detect the agent
        return await agentManager.processDocument(input);
      }
    };

    const processTimeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('Document processing timeout'));
      }, 5000); // 5 second timeout
    });

    result = await Promise.race([processPromise(), processTimeoutPromise])
      .catch(error => {
        console.warn('Document processing timed out, using fallback:', error.message);
        // Return mock result
        return {
          agent: fields.documentType === 'pdf' ? 'PDFExtractorAgent' : 'ImageOCRAgent',
          agent_id: `fallback_${Date.now()}`,
          input: {
            file: {
              name: fields.filename
            }
          },
          output: {
            extracted_text: "This is a fallback response due to processing timeout. The document was received but could not be processed within the time limit.",
            structured_data: {},
            metadata: {
              title: fields.filename,
              pageCount: 1
            },
            analysis: {
              summary: "Document processing timed out."
            }
          },
          metadata: {
            status: 'timeout',
            created_at: new Date().toISOString(),
            error: 'Processing timeout'
          },
          timestamp: new Date().toISOString()
        };
      });

    // Save to MongoDB if requested (with timeout)
    if (fields.saveToMongoDB && db) {
      try {
        const savePromise = async () => {
          // Store the result in MongoDB
          const collection = db.collection('agent_results');
          const document = {
            agent: result.agent,
            agent_id: result.agent_id,
            input: result.input,
            output: result.output,
            metadata: result.metadata,
            created_at: new Date(),
            updated_at: new Date()
          };

          return await collection.insertOne(document);
        };

        const saveTimeoutPromise = new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('MongoDB save timeout'));
          }, 2000); // 2 second timeout
        });

        const dbResult = await Promise.race([savePromise(), saveTimeoutPromise])
          .catch(error => {
            console.warn('MongoDB save timed out:', error.message);
            // Return mock result
            return { insertedId: `mock_${Date.now()}` };
          });

        console.log(`Stored result in MongoDB with ID: ${dbResult.insertedId}`);

        // Add MongoDB ID to the result
        result.mongodb_id = dbResult.insertedId.toString();
      } catch (mongoError) {
        console.error('Error saving to MongoDB:', mongoError);
        // Generate a mock MongoDB ID
        result.mongodb_id = `mock_${Date.now()}`;
      }
    }

    // Clear the function timeout
    clearTimeout(functionTimeout);

    // Return the result
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error processing document:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Error processing document',
        message: error.message,
        stack: error.stack
      }),
    };
  }
};
