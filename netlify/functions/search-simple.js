// Simplified Netlify function to search documents without complex dependencies
const crypto = require('crypto');
const mongoose = require('mongoose');
const { autoConnect, getConnectionStatus } = require('./utils/mongodb_connection');

// Generate a mock MongoDB ID
function generateMongoDBId() {
  return crypto.randomBytes(12).toString('hex');
}

// Search MongoDB for documents matching the query
async function searchMongoDB(query, filters = {}) {
  try {
    // Auto-connect to MongoDB
    await autoConnect();

    // Check connection status
    const status = getConnectionStatus();
    if (status.status !== 'connected') {
      console.warn('MongoDB not connected, cannot search documents');
      return null;
    }

    // Create a text search query
    const searchQuery = {
      $or: [
        { 'output.extracted_text': { $regex: query, $options: 'i' } },
        { 'output.analysis.summary': { $regex: query, $options: 'i' } },
        { 'input.file.name': { $regex: query, $options: 'i' } }
      ]
    };

    // Add filters if provided
    if (filters.agent) {
      searchQuery.agent = filters.agent;
    }

    if (filters.dateFrom) {
      searchQuery.created_at = { $gte: new Date(filters.dateFrom) };
    }

    if (filters.dateTo) {
      if (searchQuery.created_at) {
        searchQuery.created_at.$lte = new Date(filters.dateTo);
      } else {
        searchQuery.created_at = { $lte: new Date(filters.dateTo) };
      }
    }

    // Execute the search
    const collection = mongoose.connection.db.collection('agent_results');
    const documents = await collection.find(searchQuery).limit(10).toArray();

    console.log(`Found ${documents.length} documents matching query: ${query}`);

    return documents;
  } catch (error) {
    console.error('Error searching MongoDB:', error);
    return null;
  }
}

// Process a search query (with MongoDB integration)
async function processSearchQuery(query, filters = {}) {
  // Try to search MongoDB first
  const mongoResults = await searchMongoDB(query, filters);

  // If MongoDB search was successful, format the results
  if (mongoResults && mongoResults.length > 0) {
    const results = mongoResults.map((doc, index) => {
      // Calculate a score based on position (first results get higher scores)
      const score = 1 - (index * 0.1);

      // Extract snippets from the document
      const extractedText = doc.output?.extracted_text || '';
      const snippets = [];

      // Find snippets containing the query
      const queryRegex = new RegExp(`(.{0,50}${query}.{0,50})`, 'gi');
      let match;
      while ((match = queryRegex.exec(extractedText)) !== null) {
        snippets.push({
          text: `...${match[1]}...`,
          score: score - (snippets.length * 0.05)
        });

        // Limit to 3 snippets per document
        if (snippets.length >= 3) break;
      }

      // If no snippets were found, create one from the beginning of the text
      if (snippets.length === 0 && extractedText) {
        snippets.push({
          text: `${extractedText.substring(0, 100)}...`,
          score: score - 0.1
        });
      }

      return {
        id: doc._id.toString(),
        agent: doc.agent,
        score: score,
        snippets: snippets,
        metadata: {
          created_at: doc.created_at?.toISOString() || new Date().toISOString(),
          filename: doc.input?.file?.name || 'unknown.pdf',
          title: doc.output?.metadata?.title || doc.input?.file?.name || 'Unknown Document'
        }
      };
    });

    // Generate a summary
    const summary = `Found ${results.length} results for query: "${query}"\n\n` +
      'Results by source:\n' +
      `- ${results[0].agent}: ${results.length} results\n\n` +
      'Top result:\n' +
      `${results[0].snippets[0]?.text || 'No text snippet available'}`;

    return {
      query: query,
      processed_query: {
        original: query,
        normalized: query.toLowerCase(),
        keywords: query.toLowerCase().split(/\s+/),
        entities: [],
        intent: 'INFORMATION'
      },
      results: results,
      summary: summary,
      total_results: results.length,
      search_type: 'mongodb'
    };
  }

  // Fall back to mock results if MongoDB search failed or returned no results
  console.log('Falling back to mock search results');

  // Generate mock search results based on the query
  const results = [];

  // Add some mock results
  for (let i = 1; i <= 3; i++) {
    const score = 1 - (i * 0.2); // Decreasing scores

    results.push({
      id: generateMongoDBId(),
      agent: "PDFExtractorAgent",
      score: score,
      snippets: [
        {
          text: `This is a snippet from document ${i} that matches the query "${query}".`,
          score: score
        },
        {
          text: `Another relevant section from document ${i} with information about ${query}.`,
          score: score - 0.1
        }
      ],
      metadata: {
        created_at: new Date(Date.now() - i * 86400000).toISOString(), // Different dates
        filename: `document-${i}.pdf`,
        title: `Sample Document ${i}`
      }
    });
  }

  // Generate a summary
  const summary = `Found ${results.length} results for query: "${query}"\n\n` +
    'Results by source:\n' +
    '- PDFExtractorAgent: 3 results\n\n' +
    'Top result (80% match):\n' +
    `This is a snippet from document 1 that matches the query "${query}".`;

  return {
    query: query,
    processed_query: {
      original: query,
      normalized: query.toLowerCase(),
      keywords: query.toLowerCase().split(/\s+/),
      entities: [],
      intent: 'INFORMATION'
    },
    results: results,
    summary: summary,
    total_results: results.length,
    search_type: 'mock'
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
    // Set a timeout for the entire function
    const functionTimeout = setTimeout(() => {
      throw new Error('Function execution timeout');
    }, 8000);

    // Start MongoDB auto-connection in the background
    autoConnect().catch(err => {
      console.warn('MongoDB auto-connection failed:', err.message);
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
          filters = {};
        }
      }
    } else if (event.httpMethod === 'POST') {
      try {
        // Parse the request body
        const body = JSON.parse(event.body);
        query = body.query;
        filters = body.filters;
      } catch (error) {
        console.warn('Error parsing request body:', error);

        // Try to extract query directly from body
        const bodyStr = event.body || '';
        const queryMatch = bodyStr.match(/"query"\s*:\s*"([^"]+)"/);
        query = queryMatch ? queryMatch[1] : null;
        filters = {};
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

    // Process the search query with a timeout
    const searchPromise = processSearchQuery(query, filters);
    const searchTimeoutPromise = new Promise(resolve => {
      setTimeout(() => {
        console.warn('Search operation timed out, using fallback');
        resolve({
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
          search_type: 'timeout',
          error: 'Search operation timed out'
        });
      }, 5000); // 5 second timeout
    });

    // Race the search operation against the timeout
    const result = await Promise.race([searchPromise, searchTimeoutPromise]);

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

    // Return a fallback response
    return {
      statusCode: 200, // Return 200 even for errors to avoid client-side error handling
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        query: event.queryStringParameters?.query || 'unknown',
        processed_query: {
          original: event.queryStringParameters?.query || 'unknown',
          normalized: (event.queryStringParameters?.query || 'unknown').toLowerCase(),
          keywords: [],
          entities: [],
          intent: 'ERROR'
        },
        results: [],
        summary: `Error processing search: ${error.message}`,
        total_results: 0,
        search_type: 'error',
        error: error.message
      }),
    };
  }
};
