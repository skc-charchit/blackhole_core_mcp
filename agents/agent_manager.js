/**
 * Agent Manager
 * Coordinates multiple agents and manages their interactions
 */
const PDFExtractorAgent = require('./pdf/pdf_extractor_agent');
const ImageOCRAgent = require('./image/image_ocr_agent');
const SearchAgent = require('./search/search_agent');
const LiveDataAgent = require('./live_data/live_data_agent');

class AgentManager {
  /**
   * Constructor for the AgentManager
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = options;
    this.db = options.db || null;
    this.logger = options.logger || console;
    this.agents = new Map();
    
    // Initialize default agents if requested
    if (options.initializeDefaultAgents) {
      this.initializeDefaultAgents();
    }
  }
  
  /**
   * Initialize default agents
   */
  initializeDefaultAgents() {
    this.logger.info('Initializing default agents');
    
    // PDF Extractor Agent
    this.registerAgent('pdf', new PDFExtractorAgent({
      db: this.db,
      logger: this.logger,
      ...this.options.pdfExtractorOptions
    }));
    
    // Image OCR Agent
    this.registerAgent('image', new ImageOCRAgent({
      db: this.db,
      logger: this.logger,
      ...this.options.imageOCROptions
    }));
    
    // Search Agent
    this.registerAgent('search', new SearchAgent({
      db: this.db,
      logger: this.logger,
      ...this.options.searchOptions
    }));
    
    // Live Data Agent
    this.registerAgent('live_data', new LiveDataAgent({
      db: this.db,
      logger: this.logger,
      ...this.options.liveDataOptions
    }));
  }
  
  /**
   * Register an agent
   * @param {string} name - Agent name
   * @param {Object} agent - Agent instance
   */
  registerAgent(name, agent) {
    this.agents.set(name, agent);
    this.logger.info(`Registered agent: ${name}`);
  }
  
  /**
   * Get an agent by name
   * @param {string} name - Agent name
   * @returns {Object} - Agent instance
   */
  getAgent(name) {
    if (!this.agents.has(name)) {
      throw new Error(`Agent not found: ${name}`);
    }
    
    return this.agents.get(name);
  }
  
  /**
   * Process a request using the appropriate agent
   * @param {string} agentName - Agent name
   * @param {Object} input - Input data
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processing result
   */
  async process(agentName, input, context = {}) {
    this.logger.info(`Processing request with agent: ${agentName}`);
    
    const agent = this.getAgent(agentName);
    
    // Add manager reference to context
    const enrichedContext = {
      ...context,
      manager: this
    };
    
    // Process the input
    return await agent.process(input, enrichedContext);
  }
  
  /**
   * Process a document (auto-detect agent)
   * @param {Object} input - Input data
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processing result
   */
  async processDocument(input, context = {}) {
    // Determine the appropriate agent based on the input
    const agentName = this.determineAgent(input);
    
    this.logger.info(`Auto-detected agent: ${agentName}`);
    
    // Process with the determined agent
    return await this.process(agentName, input, context);
  }
  
  /**
   * Determine the appropriate agent for the input
   * @param {Object} input - Input data
   * @returns {string} - Agent name
   */
  determineAgent(input) {
    if (input.file) {
      // Determine by file type
      const filename = input.file.name || '';
      const mimeType = input.file.type || '';
      
      if (filename.toLowerCase().endsWith('.pdf') || mimeType === 'application/pdf') {
        return 'pdf';
      }
      
      if (mimeType.startsWith('image/') || 
          ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'].some(ext => 
            filename.toLowerCase().endsWith(ext))) {
        return 'image';
      }
    }
    
    if (input.query) {
      return 'search';
    }
    
    if (input.source) {
      return 'live_data';
    }
    
    throw new Error('Could not determine appropriate agent for input');
  }
  
  /**
   * Search for information across all stored documents
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Search results
   */
  async search(query, options = {}, context = {}) {
    this.logger.info(`Searching for: ${query}`);
    
    const searchAgent = this.getAgent('search');
    
    return await searchAgent.process({
      query,
      ...options
    }, context);
  }
  
  /**
   * Get live data from external sources
   * @param {string} source - Data source
   * @param {Object} query - Query parameters
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Live data
   */
  async getLiveData(source, query = {}, context = {}) {
    this.logger.info(`Getting live data from: ${source}`);
    
    const liveDataAgent = this.getAgent('live_data');
    
    return await liveDataAgent.process({
      source,
      query
    }, context);
  }
  
  /**
   * Process a multi-step workflow
   * @param {Array} steps - Workflow steps
   * @param {Object} initialInput - Initial input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Workflow result
   */
  async processWorkflow(steps, initialInput, context = {}) {
    this.logger.info(`Processing workflow with ${steps.length} steps`);
    
    let currentInput = initialInput;
    let results = [];
    
    // Process each step in sequence
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      this.logger.info(`Processing workflow step ${i + 1}: ${step.agent}`);
      
      // Process the current step
      const stepResult = await this.process(
        step.agent,
        { ...currentInput, ...step.input },
        { ...context, workflowStep: i, previousResults: results }
      );
      
      // Store the result
      results.push(stepResult);
      
      // Update the input for the next step if a transform function is provided
      if (step.transform) {
        currentInput = step.transform(stepResult, currentInput, results);
      } else {
        // Default transformation: use the output as the next input
        currentInput = {
          ...currentInput,
          ...stepResult
        };
      }
    }
    
    return {
      workflow: {
        steps: steps.map((step, i) => ({
          agent: step.agent,
          result: results[i]
        }))
      },
      finalResult: results[results.length - 1]
    };
  }
  
  /**
   * Store a document in the database
   * @param {Object} document - Document to store
   * @returns {Promise<Object>} - Storage result
   */
  async storeDocument(document) {
    if (!this.db) {
      throw new Error('Database not available');
    }
    
    try {
      const result = await this.db.collection('documents').insertOne({
        ...document,
        created_at: new Date(),
        updated_at: new Date()
      });
      
      this.logger.info(`Stored document with ID: ${result.insertedId}`);
      
      return {
        success: true,
        document_id: result.insertedId,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      this.logger.error(`Error storing document: ${error.message}`);
      
      throw error;
    }
  }
}

module.exports = AgentManager;
