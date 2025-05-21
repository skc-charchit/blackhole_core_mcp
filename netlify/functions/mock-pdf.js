// A mock PDF processing function that handles multiple files and MongoDB storage
const crypto = require('crypto');

// Generate a random MongoDB ID
function generateMongoDBId() {
  return crypto.randomBytes(12).toString('hex');
}

// Parse form data to get filename and save_to_mongodb flag
function parseFormData(event) {
  const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';
  const boundary = contentType.split('boundary=')[1];

  if (!boundary) {
    return { filename: 'unknown.pdf', saveToMongoDB: true };
  }

  const body = Buffer.from(event.body, 'base64').toString('utf8');
  const parts = body.split(`--${boundary}`);

  let filename = 'unknown.pdf';
  let saveToMongoDB = true;

  for (const part of parts) {
    if (part.includes('name="filename"')) {
      const match = part.match(/name="filename"[\s\S]*?(\r\n|\n\n)([\s\S]*?)(\r\n|\n)/);
      if (match && match[2]) {
        filename = match[2].trim();
      }
    }

    if (part.includes('name="save_to_mongodb"')) {
      const match = part.match(/name="save_to_mongodb"[\s\S]*?(\r\n|\n\n)([\s\S]*?)(\r\n|\n)/);
      if (match && match[2]) {
        saveToMongoDB = match[2].trim().toLowerCase() === 'true';
      }
    }
  }

  return { filename, saveToMongoDB };
}

exports.handler = async function(event, context) {
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
    // Parse form data to get filename and save_to_mongodb flag
    const { filename, saveToMongoDB } = parseFormData(event);

    console.log(`Processing PDF: ${filename}, Save to MongoDB: ${saveToMongoDB}`);

    // Generate a mock extracted text based on the filename
    const extractedText = `This is mock extracted text from the PDF file "${filename}". In a real application, this would contain the actual text extracted from the PDF document. The text would be processed by the OCR engine and then passed to the AI agent for analysis.`;

    // Create a mock agent result
    const agentResult = {
      agent: "ArchiveSearchAgent",
      input: {
        document_text: extractedText.substring(0, 100) + "..."
      },
      metadata: {
        source_file: filename,
        processed_at: new Date().toISOString()
      },
      output: `Processed file "${filename}". No specific matches found in the archive.`,
      timestamp: new Date().toISOString()
    };

    // Create the response object
    const response = {
      extracted_text: extractedText,
      agent_result: agentResult
    };

    // If saveToMongoDB is true, generate a MongoDB ID and add it to the response
    if (saveToMongoDB) {
      const mongoDBId = generateMongoDBId();
      response.mongodb_id = mongoDBId;
      console.log(`Saved to MongoDB with ID: ${mongoDBId}`);
    }

    // Return the response
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(response),
    };
  } catch (error) {
    console.error('Error processing PDF:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        error: 'Error processing PDF',
        message: error.message
      }),
    };
  }
};
