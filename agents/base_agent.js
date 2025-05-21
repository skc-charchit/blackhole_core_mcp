/**
 * Base Agent class for the BlackHole multi-agent system
 * This serves as the foundation for all specialized agents
 */
class BaseAgent {
  /**
   * Constructor for the BaseAgent class
   * @param {Object} options - Configuration options for the agent
   */
  constructor(options = {}) {
    this.id = options.id || `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.name = options.name || 'BaseAgent';
    this.description = options.description || 'Base agent for the BlackHole system';
    this.version = options.version || '1.0.0';
    this.options = options;
    this.metadata = {
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'initialized'
    };
    this.logger = options.logger || console;
    this.db = options.db || null;
  }

  /**
   * Process input data and return results
   * @param {Object} input - Input data to process
   * @param {Object} context - Additional context for processing
   * @returns {Promise<Object>} - Processing results
   */
  async process(input, context = {}) {
    this.logger.info(`[${this.name}] Processing input`, { agent: this.id });
    
    try {
      // Update metadata
      this.metadata.status = 'processing';
      this.metadata.updated_at = new Date().toISOString();
      
      // Validate input
      this.validateInput(input);
      
      // Process the input (to be implemented by subclasses)
      const result = await this._process(input, context);
      
      // Update metadata
      this.metadata.status = 'completed';
      this.metadata.updated_at = new Date().toISOString();
      
      // Store results if database is available
      if (this.db) {
        await this.storeResults(result, input, context);
      }
      
      return {
        agent: this.name,
        agent_id: this.id,
        input: this.summarizeInput(input),
        output: result,
        metadata: {
          ...this.metadata,
          context_summary: this.summarizeContext(context)
        },
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      // Update metadata
      this.metadata.status = 'error';
      this.metadata.error = error.message;
      this.metadata.updated_at = new Date().toISOString();
      
      this.logger.error(`[${this.name}] Error processing input: ${error.message}`, { 
        agent: this.id,
        error: error.stack 
      });
      
      throw error;
    }
  }
  
  /**
   * Internal processing method to be implemented by subclasses
   * @param {Object} input - Input data to process
   * @param {Object} context - Additional context for processing
   * @returns {Promise<Object>} - Processing results
   */
  async _process(input, context) {
    throw new Error('_process method must be implemented by subclasses');
  }
  
  /**
   * Validate the input data
   * @param {Object} input - Input data to validate
   * @throws {Error} If validation fails
   */
  validateInput(input) {
    if (!input) {
      throw new Error('Input is required');
    }
  }
  
  /**
   * Create a summary of the input for logging and metadata
   * @param {Object} input - Input data to summarize
   * @returns {Object} - Summarized input
   */
  summarizeInput(input) {
    // Default implementation returns a safe version of the input
    // Subclasses should override this to provide a meaningful summary
    if (typeof input === 'object') {
      // Create a shallow copy to avoid modifying the original
      const summary = { ...input };
      
      // Remove potentially large fields
      if (summary.content && summary.content.length > 100) {
        summary.content = `${summary.content.substring(0, 100)}... [${summary.content.length} chars]`;
      }
      
      if (summary.file && summary.file.data) {
        summary.file = {
          ...summary.file,
          data: `[Binary data: ${summary.file.data.length} bytes]`
        };
      }
      
      return summary;
    }
    
    return input;
  }
  
  /**
   * Create a summary of the context for logging and metadata
   * @param {Object} context - Context to summarize
   * @returns {Object} - Summarized context
   */
  summarizeContext(context) {
    // Default implementation returns context keys
    return Object.keys(context);
  }
  
  /**
   * Store results in the database
   * @param {Object} result - Processing results
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Database operation result
   */
  async storeResults(result, input, context) {
    if (!this.db) {
      throw new Error('Database not available');
    }
    
    try {
      const document = {
        agent: this.name,
        agent_id: this.id,
        input: this.summarizeInput(input),
        output: result,
        metadata: {
          ...this.metadata,
          context_summary: this.summarizeContext(context)
        },
        created_at: new Date(),
        updated_at: new Date()
      };
      
      const dbResult = await this.db.collection('agent_results').insertOne(document);
      this.logger.info(`[${this.name}] Stored results in database`, { 
        agent: this.id,
        document_id: dbResult.insertedId 
      });
      
      return dbResult;
    } catch (error) {
      this.logger.error(`[${this.name}] Error storing results: ${error.message}`, { 
        agent: this.id,
        error: error.stack 
      });
      
      // Don't throw the error, just log it
      // This allows the agent to return results even if storage fails
      return { error: error.message };
    }
  }
}

module.exports = BaseAgent;
