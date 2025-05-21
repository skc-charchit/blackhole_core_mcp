/**
 * Image OCR Agent
 * Extracts text from images using OCR
 */
const BaseAgent = require('../base_agent');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class ImageOCRAgent extends BaseAgent {
  /**
   * Constructor for the ImageOCRAgent
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    super({
      name: 'ImageOCRAgent',
      description: 'Extracts text from images using OCR',
      version: '1.0.0',
      ...options
    });
    
    this.tempDir = options.tempDir || 'temp';
    this.ocrEngine = options.ocrEngine || null;
    this.preProcessors = options.preProcessors || [];
    this.supportedFormats = options.supportedFormats || ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'];
  }
  
  /**
   * Process an image
   * @param {Object} input - Input containing image data
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - OCR results
   */
  async _process(input, context) {
    this.logger.info(`[${this.name}] Processing image`);
    
    // Extract image data from input
    const imageData = await this.extractImageData(input);
    
    // Determine image format
    const format = this.determineImageFormat(input, imageData);
    
    // Pre-process the image for better OCR results
    const processedImageData = await this.preProcessImage(imageData, format, context);
    
    // Perform OCR on the image
    const ocrResult = await this.performOCR(processedImageData, format, context);
    
    // Post-process the OCR result
    const processedResult = await this.postProcessOCR(ocrResult, context);
    
    // Analyze the extracted text
    const analysis = await this.analyzeText(processedResult.text, context);
    
    return {
      extracted_text: processedResult.text,
      confidence: processedResult.confidence,
      regions: processedResult.regions,
      analysis: analysis,
      image_metadata: {
        format: format,
        pre_processed: this.preProcessors.length > 0,
        size: imageData ? imageData.length : 0
      }
    };
  }
  
  /**
   * Extract image data from the input
   * @param {Object} input - Input object
   * @returns {Promise<Buffer>} - Image data as a buffer
   */
  async extractImageData(input) {
    // Handle different input formats
    if (input.file && input.file.data) {
      // Direct file data
      return Buffer.from(input.file.data);
    } else if (input.file && input.file.path) {
      // File path
      return await fs.readFile(input.file.path);
    } else if (input.url) {
      // URL to an image
      throw new Error('URL-based image extraction not implemented yet');
    } else if (input.text) {
      // This is already extracted text, no need to process
      return null;
    } else {
      throw new Error('Invalid input: No image data, file path, or URL provided');
    }
  }
  
  /**
   * Determine the format of the image
   * @param {Object} input - Original input
   * @param {Buffer} imageData - Image data
   * @returns {string} - Image format
   */
  determineImageFormat(input, imageData) {
    // Try to get format from input
    if (input.file && input.file.name) {
      const ext = path.extname(input.file.name).toLowerCase().substring(1);
      if (this.supportedFormats.includes(ext)) {
        return ext;
      }
    }
    
    if (input.file && input.file.type) {
      const mimeFormat = input.file.type.split('/')[1];
      if (this.supportedFormats.includes(mimeFormat)) {
        return mimeFormat;
      }
    }
    
    // Default to jpeg
    return 'jpeg';
  }
  
  /**
   * Pre-process the image for better OCR results
   * @param {Buffer} imageData - Image data
   * @param {string} format - Image format
   * @param {Object} context - Processing context
   * @returns {Promise<Buffer>} - Processed image data
   */
  async preProcessImage(imageData, format, context) {
    if (!imageData) {
      return null;
    }
    
    if (this.preProcessors.length === 0) {
      return imageData;
    }
    
    // Apply each pre-processor in sequence
    let processedData = imageData;
    for (const processor of this.preProcessors) {
      processedData = await processor.process(processedData, format, context);
    }
    
    return processedData;
  }
  
  /**
   * Perform OCR on the image
   * @param {Buffer} imageData - Image data
   * @param {string} format - Image format
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - OCR result
   */
  async performOCR(imageData, format, context) {
    if (!imageData) {
      return { text: '', confidence: 0, regions: [] };
    }
    
    // If we have a custom OCR engine, use it
    if (this.ocrEngine) {
      return await this.ocrEngine.recognize(imageData, format, context);
    }
    
    // Otherwise, use a mock implementation
    this.logger.warn(`[${this.name}] Using mock OCR implementation`);
    
    // Save the image to a temporary file for processing
    const tempFilePath = await this.saveTempFile(imageData, format);
    
    // Mock OCR result - in a real implementation, you would use Tesseract or another OCR engine
    const mockResult = {
      text: `This is mock extracted text from an image.
      
The BlackHole system can extract text from images using OCR technology.
      
Sample data:
- Item 1
- Item 2
- Item 3

For more information, visit example.com`,
      confidence: 0.85,
      regions: [
        {
          boundingBox: { x: 10, y: 10, width: 500, height: 100 },
          text: "This is mock extracted text from an image.",
          confidence: 0.9
        },
        {
          boundingBox: { x: 10, y: 120, width: 500, height: 100 },
          text: "The BlackHole system can extract text from images using OCR technology.",
          confidence: 0.85
        },
        {
          boundingBox: { x: 10, y: 230, width: 500, height: 150 },
          text: "Sample data:\n- Item 1\n- Item 2\n- Item 3",
          confidence: 0.8
        }
      ]
    };
    
    // Clean up the temporary file
    try {
      await fs.unlink(tempFilePath);
    } catch (error) {
      this.logger.error(`[${this.name}] Error deleting temporary file: ${error.message}`);
    }
    
    return mockResult;
  }
  
  /**
   * Post-process the OCR result
   * @param {Object} ocrResult - OCR result
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed OCR result
   */
  async postProcessOCR(ocrResult, context) {
    // Apply text corrections and improvements
    let processedText = ocrResult.text;
    
    // Remove common OCR errors
    processedText = processedText.replace(/[|]l/g, 'I'); // Replace |l with I
    processedText = processedText.replace(/rn/g, 'm');   // Replace rn with m
    
    // Fix spacing issues
    processedText = processedText.replace(/\s+/g, ' ');  // Replace multiple spaces with a single space
    
    // Update the OCR result
    return {
      ...ocrResult,
      text: processedText,
      post_processed: true
    };
  }
  
  /**
   * Analyze the extracted text
   * @param {string} text - Extracted text
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Analysis results
   */
  async analyzeText(text, context) {
    // Mock implementation - in a real implementation, you would use NLP or other analysis
    return {
      summary: "This text contains information about the BlackHole system's OCR capabilities.",
      language: "en",
      wordCount: text.split(/\s+/).length,
      entities: [
        { type: "ORGANIZATION", text: "BlackHole", count: 1 },
        { type: "TECHNOLOGY", text: "OCR", count: 1 }
      ],
      sentiment: {
        score: 0.1,
        magnitude: 0.3,
        label: "neutral"
      }
    };
  }
  
  /**
   * Save data to a temporary file
   * @param {Buffer} data - Data to save
   * @param {string} extension - File extension
   * @returns {Promise<string>} - Path to the temporary file
   */
  async saveTempFile(data, extension) {
    // Create temp directory if it doesn't exist
    try {
      await fs.mkdir(this.tempDir, { recursive: true });
    } catch (error) {
      if (error.code !== 'EEXIST') {
        throw error;
      }
    }
    
    // Generate a unique filename
    const filename = `${Date.now()}_${crypto.randomBytes(8).toString('hex')}.${extension}`;
    const filePath = path.join(this.tempDir, filename);
    
    // Write the data to the file
    await fs.writeFile(filePath, data);
    
    return filePath;
  }
  
  /**
   * Validate the input
   * @param {Object} input - Input to validate
   */
  validateInput(input) {
    super.validateInput(input);
    
    if (!input.file && !input.url && !input.text) {
      throw new Error('Input must contain file, url, or text');
    }
  }
}

module.exports = ImageOCRAgent;
