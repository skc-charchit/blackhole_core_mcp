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
    // Initialize the agent system
    await initializeAgentSystem();
    
    // Parse the multipart form data
    console.log('Parsing multipart form data...');
    const { formData, fields, fileData } = await parseMultipartForm(event);
    console.log('Form data parsed successfully');
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
    
    // Process the document with the appropriate agent
    let result;
    if (fields.documentType === 'pdf') {
      // Process with PDF Extractor Agent
      result = await agentManager.process('pdf', input);
    } else if (fields.documentType === 'image') {
      // Process with Image OCR Agent
      result = await agentManager.process('image', input);
    } else if (fields.query) {
      // Process with Search Agent
      result = await agentManager.process('search', input);
    } else {
      // Auto-detect the agent
      result = await agentManager.processDocument(input);
    }
    
    // Save to MongoDB if requested
    if (fields.saveToMongoDB && db) {
      try {
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
        
        const dbResult = await collection.insertOne(document);
        console.log(`Stored result in MongoDB with ID: ${dbResult.insertedId}`);
        
        // Add MongoDB ID to the result
        result.mongodb_id = dbResult.insertedId.toString();
      } catch (mongoError) {
        console.error('Error saving to MongoDB:', mongoError);
      }
    }
    
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
