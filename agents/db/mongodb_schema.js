/**
 * MongoDB Schema for the BlackHole Agent System
 * Defines the schema for storing agent results and documents
 */
const mongoose = require('mongoose');

// Schema for agent results
const AgentResultSchema = new mongoose.Schema({
  // Agent information
  agent: {
    type: String,
    required: true,
    index: true
  },
  agent_id: {
    type: String,
    required: true
  },
  
  // Input summary (not the full input to avoid storing large files)
  input: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  
  // Output from the agent
  output: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  
  // Metadata about the processing
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Vector embedding for semantic search
  vector_embedding: {
    type: [Number],
    sparse: true,
    index: false // Will be indexed separately
  },
  
  // Timestamps
  created_at: {
    type: Date,
    default: Date.now,
    index: true
  },
  updated_at: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' }
});

// Schema for documents (PDFs, images, etc.)
const DocumentSchema = new mongoose.Schema({
  // Document information
  title: {
    type: String,
    required: true,
    index: true
  },
  description: {
    type: String
  },
  filename: {
    type: String
  },
  mime_type: {
    type: String
  },
  
  // Document type
  type: {
    type: String,
    enum: ['pdf', 'image', 'text', 'other'],
    required: true,
    index: true
  },
  
  // Document content
  content: {
    type: String,
    required: true
  },
  
  // Structured data extracted from the document
  structured_data: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Metadata about the document
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Analysis of the document
  analysis: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Vector embedding for semantic search
  vector_embedding: {
    type: [Number],
    sparse: true,
    index: false // Will be indexed separately
  },
  
  // References to related documents
  related_documents: [{
    document_id: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Document'
    },
    relationship: {
      type: String
    },
    score: {
      type: Number
    }
  }],
  
  // Timestamps
  created_at: {
    type: Date,
    default: Date.now,
    index: true
  },
  updated_at: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' }
});

// Schema for live data
const LiveDataSchema = new mongoose.Schema({
  // Data source
  source: {
    type: String,
    required: true,
    index: true
  },
  
  // Query used to fetch the data
  query: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  
  // The actual data
  data: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  
  // Whether the data is from cache
  cached: {
    type: Boolean,
    default: false
  },
  
  // When the data was fetched
  fetched_at: {
    type: Date,
    default: Date.now,
    index: true
  },
  
  // When the data expires (for caching)
  expires_at: {
    type: Date,
    index: true
  }
}, {
  timestamps: { createdAt: 'fetched_at' }
});

// Schema for user queries
const UserQuerySchema = new mongoose.Schema({
  // The query text
  query: {
    type: String,
    required: true,
    index: true
  },
  
  // Processed query information
  processed_query: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  
  // Results of the query
  results: [{
    document_id: {
      type: mongoose.Schema.Types.ObjectId,
      refPath: 'results.document_type'
    },
    document_type: {
      type: String,
      enum: ['Document', 'AgentResult', 'LiveData']
    },
    score: {
      type: Number
    },
    snippets: [{
      text: String,
      score: Number
    }]
  }],
  
  // Summary of the results
  summary: {
    type: String
  },
  
  // User feedback on the results
  feedback: {
    rating: {
      type: Number,
      min: 1,
      max: 5
    },
    comments: {
      type: String
    },
    helpful: {
      type: Boolean
    }
  },
  
  // Timestamps
  created_at: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: { createdAt: 'created_at' }
});

// Create models
const AgentResult = mongoose.model('AgentResult', AgentResultSchema);
const Document = mongoose.model('Document', DocumentSchema);
const LiveData = mongoose.model('LiveData', LiveDataSchema);
const UserQuery = mongoose.model('UserQuery', UserQuerySchema);

// Function to create indexes
async function createIndexes(db) {
  // Create text indexes
  await Document.collection.createIndex({ title: 'text', content: 'text' });
  await AgentResult.collection.createIndex({ 'output.extracted_text': 'text' });
  
  // Create vector indexes if supported
  try {
    // Check if vector search is supported
    const buildInfo = await db.command({ buildInfo: 1 });
    const version = parseFloat(buildInfo.version);
    
    if (version >= 5.0) {
      // MongoDB 5.0+ supports vector search
      await Document.collection.createIndex(
        { vector_embedding: "vector" },
        { 
          name: "vector_index",
          vectorSize: 1536, // Adjust based on your embedding size
          vectorSearchOptions: { similarity: "cosine" }
        }
      );
      
      await AgentResult.collection.createIndex(
        { vector_embedding: "vector" },
        { 
          name: "vector_index",
          vectorSize: 1536, // Adjust based on your embedding size
          vectorSearchOptions: { similarity: "cosine" }
        }
      );
    }
  } catch (error) {
    console.warn('Vector search indexes not created:', error.message);
  }
}

module.exports = {
  AgentResult,
  Document,
  LiveData,
  UserQuery,
  createIndexes
};
