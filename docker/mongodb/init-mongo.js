// MongoDB initialization script for BlackHole Core MCP
print('🚀 Initializing BlackHole Core MCP Database...');

// Switch to the blackhole_db database
db = db.getSiblingDB('blackhole_db');

// Create application user with read/write permissions
db.createUser({
  user: 'blackhole_user',
  pwd: 'blackhole_pass_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'blackhole_db'
    }
  ]
});

// Create collections with initial structure
print('📊 Creating collections...');

// Agent outputs collection
db.createCollection('agent_outputs');
db.agent_outputs.createIndex({ "timestamp": 1 });
db.agent_outputs.createIndex({ "agent_type": 1 });
db.agent_outputs.createIndex({ "file_path": 1 });

// PDF documents collection
db.createCollection('pdf_documents');
db.pdf_documents.createIndex({ "filename": 1 });
db.pdf_documents.createIndex({ "upload_timestamp": 1 });
db.pdf_documents.createIndex({ "file_hash": 1 }, { unique: true });

// Image documents collection
db.createCollection('image_documents');
db.image_documents.createIndex({ "filename": 1 });
db.image_documents.createIndex({ "upload_timestamp": 1 });
db.image_documents.createIndex({ "file_hash": 1 }, { unique: true });

// Search results collection
db.createCollection('search_results');
db.search_results.createIndex({ "query": 1 });
db.search_results.createIndex({ "timestamp": 1 });

// Vector embeddings collection
db.createCollection('vector_embeddings');
db.vector_embeddings.createIndex({ "document_id": 1 });
db.vector_embeddings.createIndex({ "chunk_index": 1 });

// Conversation history collection
db.createCollection('conversation_history');
db.conversation_history.createIndex({ "session_id": 1 });
db.conversation_history.createIndex({ "timestamp": 1 });

// Insert sample configuration document
print('⚙️ Inserting configuration...');
db.configuration.insertOne({
  _id: 'app_config',
  version: '1.0.0',
  initialized_at: new Date(),
  features: {
    llm_enabled: true,
    ocr_enabled: true,
    vector_search: true,
    conversation_memory: true
  },
  limits: {
    max_file_size_mb: 50,
    max_files_per_user: 100,
    conversation_history_days: 30
  }
});

print('✅ BlackHole Core MCP Database initialized successfully!');
print('📋 Collections created:');
print('   - agent_outputs');
print('   - pdf_documents');
print('   - image_documents');
print('   - search_results');
print('   - vector_embeddings');
print('   - conversation_history');
print('   - configuration');
print('👤 User created: blackhole_user');
print('🔐 Database: blackhole_db');
