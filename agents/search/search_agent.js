/**
 * Search Agent
 * Searches for information in stored documents
 */
const BaseAgent = require('../base_agent');

class SearchAgent extends BaseAgent {
  /**
   * Constructor for the SearchAgent
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    super({
      name: 'SearchAgent',
      description: 'Searches for information in stored documents',
      version: '1.0.0',
      ...options
    });
    
    this.db = options.db || null;
    this.useVectorSearch = options.useVectorSearch || false;
    this.vectorizer = options.vectorizer || null;
    this.maxResults = options.maxResults || 10;
    this.minScore = options.minScore || 0.5;
  }
  
  /**
   * Process a search query
   * @param {Object} input - Input containing search query
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Search results
   */
  async _process(input, context) {
    this.logger.info(`[${this.name}] Processing search query: ${input.query}`);
    
    // Validate database connection
    if (!this.db) {
      throw new Error('Database connection required for search');
    }
    
    // Parse and process the query
    const processedQuery = await this.processQuery(input.query, context);
    
    // Determine search strategy
    let searchResults;
    if (this.useVectorSearch && this.vectorizer) {
      // Vector search (semantic search)
      searchResults = await this.performVectorSearch(processedQuery, input, context);
    } else {
      // Text-based search
      searchResults = await this.performTextSearch(processedQuery, input, context);
    }
    
    // Process and rank the results
    const rankedResults = await this.rankResults(searchResults, processedQuery, context);
    
    // Generate a summary of the results
    const summary = await this.generateSummary(rankedResults, processedQuery, context);
    
    return {
      query: input.query,
      processed_query: processedQuery,
      results: rankedResults,
      summary: summary,
      total_results: rankedResults.length,
      search_type: this.useVectorSearch ? 'vector' : 'text'
    };
  }
  
  /**
   * Process and analyze the search query
   * @param {string} query - Raw search query
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed query
   */
  async processQuery(query, context) {
    // Extract keywords and entities
    const keywords = query.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 2);
    
    // Identify entities (mock implementation)
    const entities = [];
    const entityPatterns = [
      { pattern: /\b\d{4}-\d{2}-\d{2}\b/, type: 'DATE' },
      { pattern: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/, type: 'PERSON' },
      { pattern: /\b[A-Z][a-z]+ (Inc|Corp|LLC|Ltd)\b/, type: 'ORGANIZATION' }
    ];
    
    for (const { pattern, type } of entityPatterns) {
      const matches = query.match(pattern);
      if (matches) {
        for (const match of matches) {
          entities.push({ text: match, type });
        }
      }
    }
    
    // Determine query intent (mock implementation)
    let intent = 'INFORMATION';
    if (query.toLowerCase().includes('how')) {
      intent = 'HOW_TO';
    } else if (query.toLowerCase().includes('what')) {
      intent = 'DEFINITION';
    } else if (query.toLowerCase().includes('when')) {
      intent = 'TIME';
    } else if (query.toLowerCase().includes('where')) {
      intent = 'LOCATION';
    }
    
    return {
      original: query,
      normalized: query.toLowerCase(),
      keywords: keywords,
      entities: entities,
      intent: intent,
      vector: this.vectorizer ? await this.vectorizer.encode(query) : null
    };
  }
  
  /**
   * Perform text-based search
   * @param {Object} processedQuery - Processed query
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Array>} - Search results
   */
  async performTextSearch(processedQuery, input, context) {
    const { keywords, entities } = processedQuery;
    
    // Build the MongoDB query
    const searchQuery = {
      $or: [
        // Search in extracted text
        { 'output.extracted_text': { $regex: processedQuery.normalized, $options: 'i' } },
        
        // Search in keywords
        { 'output.extracted_text': { $in: keywords.map(k => new RegExp(`\\b${k}\\b`, 'i')) } }
      ]
    };
    
    // Add filters from input if provided
    if (input.filters) {
      if (input.filters.agent) {
        searchQuery.agent = input.filters.agent;
      }
      
      if (input.filters.dateRange) {
        searchQuery.created_at = {
          $gte: new Date(input.filters.dateRange.start),
          $lte: new Date(input.filters.dateRange.end)
        };
      }
    }
    
    // Execute the search
    const results = await this.db.collection('agent_results')
      .find(searchQuery)
      .limit(this.maxResults)
      .toArray();
    
    return results.map(result => ({
      ...result,
      score: this.calculateTextScore(result, processedQuery)
    }));
  }
  
  /**
   * Calculate a relevance score for text search results
   * @param {Object} result - Search result
   * @param {Object} processedQuery - Processed query
   * @returns {number} - Relevance score (0-1)
   */
  calculateTextScore(result, processedQuery) {
    const { keywords, entities, normalized } = processedQuery;
    let score = 0;
    
    // Check for exact matches
    if (result.output.extracted_text && result.output.extracted_text.toLowerCase().includes(normalized)) {
      score += 0.5;
    }
    
    // Check for keyword matches
    if (result.output.extracted_text) {
      const text = result.output.extracted_text.toLowerCase();
      const matchedKeywords = keywords.filter(k => text.includes(k));
      score += (matchedKeywords.length / keywords.length) * 0.3;
    }
    
    // Check for entity matches
    if (result.output.analysis && result.output.analysis.entities) {
      const resultEntities = result.output.analysis.entities.map(e => e.text.toLowerCase());
      const matchedEntities = entities.filter(e => resultEntities.includes(e.text.toLowerCase()));
      if (entities.length > 0) {
        score += (matchedEntities.length / entities.length) * 0.2;
      }
    }
    
    return Math.min(1, score);
  }
  
  /**
   * Perform vector-based (semantic) search
   * @param {Object} processedQuery - Processed query
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Array>} - Search results
   */
  async performVectorSearch(processedQuery, input, context) {
    if (!this.vectorizer) {
      throw new Error('Vectorizer required for vector search');
    }
    
    // Check if the collection has a vector search index
    const collections = await this.db.listCollections({ name: 'agent_results' }).toArray();
    const hasVectorIndex = collections.length > 0 && 
                          collections[0].options && 
                          collections[0].options.indexes && 
                          collections[0].options.indexes.some(idx => idx.name === 'vector_index');
    
    if (hasVectorIndex) {
      // Use MongoDB's vector search if available
      return this.performMongoDBVectorSearch(processedQuery, input);
    } else {
      // Fall back to in-memory vector search
      return this.performInMemoryVectorSearch(processedQuery, input);
    }
  }
  
  /**
   * Perform vector search using MongoDB's vector search capability
   * @param {Object} processedQuery - Processed query
   * @param {Object} input - Original input
   * @returns {Promise<Array>} - Search results
   */
  async performMongoDBVectorSearch(processedQuery, input) {
    // Build the MongoDB vector search query
    const searchQuery = {
      $vectorSearch: {
        queryVector: processedQuery.vector,
        path: 'vector_embedding',
        numCandidates: this.maxResults * 10,
        limit: this.maxResults,
        index: 'vector_index',
      }
    };
    
    // Add filters from input if provided
    if (input.filters) {
      if (input.filters.agent) {
        searchQuery.agent = input.filters.agent;
      }
      
      if (input.filters.dateRange) {
        searchQuery.created_at = {
          $gte: new Date(input.filters.dateRange.start),
          $lte: new Date(input.filters.dateRange.end)
        };
      }
    }
    
    // Execute the search
    const results = await this.db.collection('agent_results')
      .aggregate([
        { $match: searchQuery },
        { $project: { score: { $meta: 'vectorSearchScore' }, document: '$$ROOT' } }
      ])
      .toArray();
    
    return results.map(result => ({
      ...result.document,
      score: result.score
    }));
  }
  
  /**
   * Perform in-memory vector search when MongoDB vector search is not available
   * @param {Object} processedQuery - Processed query
   * @param {Object} input - Original input
   * @returns {Promise<Array>} - Search results
   */
  async performInMemoryVectorSearch(processedQuery, input) {
    // Get all documents (with limit for performance)
    const query = {};
    
    // Add filters from input if provided
    if (input.filters) {
      if (input.filters.agent) {
        query.agent = input.filters.agent;
      }
      
      if (input.filters.dateRange) {
        query.created_at = {
          $gte: new Date(input.filters.dateRange.start),
          $lte: new Date(input.filters.dateRange.end)
        };
      }
    }
    
    const documents = await this.db.collection('agent_results')
      .find(query)
      .limit(1000) // Limit for performance
      .toArray();
    
    // Calculate vector for each document if not already present
    const documentsWithVectors = await Promise.all(documents.map(async doc => {
      if (!doc.vector_embedding) {
        // Generate vector from extracted text
        const text = doc.output.extracted_text || '';
        doc.vector_embedding = await this.vectorizer.encode(text);
      }
      return doc;
    }));
    
    // Calculate similarity scores
    const scoredDocuments = documentsWithVectors.map(doc => {
      const score = this.calculateCosineSimilarity(processedQuery.vector, doc.vector_embedding);
      return { ...doc, score };
    });
    
    // Sort by score and take top results
    return scoredDocuments
      .filter(doc => doc.score >= this.minScore)
      .sort((a, b) => b.score - a.score)
      .slice(0, this.maxResults);
  }
  
  /**
   * Calculate cosine similarity between two vectors
   * @param {Array<number>} vec1 - First vector
   * @param {Array<number>} vec2 - Second vector
   * @returns {number} - Cosine similarity (0-1)
   */
  calculateCosineSimilarity(vec1, vec2) {
    if (!vec1 || !vec2 || vec1.length !== vec2.length) {
      return 0;
    }
    
    let dotProduct = 0;
    let mag1 = 0;
    let mag2 = 0;
    
    for (let i = 0; i < vec1.length; i++) {
      dotProduct += vec1[i] * vec2[i];
      mag1 += vec1[i] * vec1[i];
      mag2 += vec2[i] * vec2[i];
    }
    
    mag1 = Math.sqrt(mag1);
    mag2 = Math.sqrt(mag2);
    
    if (mag1 === 0 || mag2 === 0) {
      return 0;
    }
    
    return dotProduct / (mag1 * mag2);
  }
  
  /**
   * Rank and process search results
   * @param {Array} results - Search results
   * @param {Object} processedQuery - Processed query
   * @param {Object} context - Processing context
   * @returns {Promise<Array>} - Ranked results
   */
  async rankResults(results, processedQuery, context) {
    // Filter out low-scoring results
    const filteredResults = results.filter(result => result.score >= this.minScore);
    
    // Sort by score
    const sortedResults = filteredResults.sort((a, b) => b.score - a.score);
    
    // Process each result to extract relevant snippets
    return sortedResults.map(result => {
      // Extract relevant snippets from the text
      const snippets = this.extractRelevantSnippets(result, processedQuery);
      
      return {
        id: result._id,
        agent: result.agent,
        score: result.score,
        snippets: snippets,
        metadata: result.metadata,
        created_at: result.created_at
      };
    });
  }
  
  /**
   * Extract relevant snippets from a document
   * @param {Object} result - Search result
   * @param {Object} processedQuery - Processed query
   * @returns {Array<Object>} - Relevant snippets
   */
  extractRelevantSnippets(result, processedQuery) {
    const text = result.output.extracted_text || '';
    const { keywords, normalized } = processedQuery;
    const snippets = [];
    
    // Split text into sentences
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    // Score each sentence based on query relevance
    for (const sentence of sentences) {
      let score = 0;
      
      // Check for query match
      if (sentence.toLowerCase().includes(normalized)) {
        score += 0.5;
      }
      
      // Check for keyword matches
      for (const keyword of keywords) {
        if (sentence.toLowerCase().includes(keyword)) {
          score += 0.1;
        }
      }
      
      if (score > 0) {
        snippets.push({
          text: sentence.trim(),
          score: score
        });
      }
    }
    
    // Sort snippets by score and take top 3
    return snippets
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }
  
  /**
   * Generate a summary of the search results
   * @param {Array} results - Ranked search results
   * @param {Object} processedQuery - Processed query
   * @param {Object} context - Processing context
   * @returns {Promise<string>} - Summary
   */
  async generateSummary(results, processedQuery, context) {
    if (results.length === 0) {
      return `No results found for query: "${processedQuery.original}"`;
    }
    
    // Count results by agent type
    const agentCounts = {};
    for (const result of results) {
      agentCounts[result.agent] = (agentCounts[result.agent] || 0) + 1;
    }
    
    // Generate summary text
    let summary = `Found ${results.length} results for query: "${processedQuery.original}"\n\n`;
    
    // Add agent breakdown
    summary += 'Results by source:\n';
    for (const [agent, count] of Object.entries(agentCounts)) {
      summary += `- ${agent}: ${count} results\n`;
    }
    
    // Add top result preview
    if (results.length > 0) {
      const topResult = results[0];
      summary += `\nTop result (${Math.round(topResult.score * 100)}% match):\n`;
      
      if (topResult.snippets && topResult.snippets.length > 0) {
        summary += topResult.snippets[0].text;
      }
    }
    
    return summary;
  }
  
  /**
   * Validate the input
   * @param {Object} input - Input to validate
   */
  validateInput(input) {
    super.validateInput(input);
    
    if (!input.query) {
      throw new Error('Search query is required');
    }
    
    if (typeof input.query !== 'string') {
      throw new Error('Search query must be a string');
    }
  }
}

module.exports = SearchAgent;
