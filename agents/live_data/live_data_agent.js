/**
 * Live Data Agent
 * Fetches and processes data from external APIs
 */
const BaseAgent = require('../base_agent');
const fetch = require('node-fetch');

class LiveDataAgent extends BaseAgent {
  /**
   * Constructor for the LiveDataAgent
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    super({
      name: 'LiveDataAgent',
      description: 'Fetches and processes data from external APIs',
      version: '1.0.0',
      ...options
    });
    
    this.apiKeys = options.apiKeys || {};
    this.dataSources = options.dataSources || {};
    this.cacheEnabled = options.cacheEnabled !== undefined ? options.cacheEnabled : true;
    this.cacheTTL = options.cacheTTL || 3600000; // 1 hour in milliseconds
    this.cache = new Map();
  }
  
  /**
   * Process a data request
   * @param {Object} input - Input containing data request
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed data
   */
  async _process(input, context) {
    this.logger.info(`[${this.name}] Processing data request for source: ${input.source}`);
    
    // Check if the requested data source is supported
    if (!this.isSourceSupported(input.source)) {
      throw new Error(`Data source not supported: ${input.source}`);
    }
    
    // Check cache if enabled
    if (this.cacheEnabled) {
      const cachedData = this.checkCache(input);
      if (cachedData) {
        this.logger.info(`[${this.name}] Returning cached data for source: ${input.source}`);
        return {
          ...cachedData,
          cached: true,
          cache_time: cachedData.timestamp
        };
      }
    }
    
    // Fetch data from the source
    const data = await this.fetchData(input, context);
    
    // Process the data
    const processedData = await this.processData(data, input, context);
    
    // Store in cache if enabled
    if (this.cacheEnabled) {
      this.storeInCache(input, processedData);
    }
    
    return {
      source: input.source,
      query: input.query,
      data: processedData,
      timestamp: new Date().toISOString(),
      cached: false
    };
  }
  
  /**
   * Check if a data source is supported
   * @param {string} source - Data source name
   * @returns {boolean} - Whether the source is supported
   */
  isSourceSupported(source) {
    return source in this.dataSources || this.hasBuiltInSupport(source);
  }
  
  /**
   * Check if a data source has built-in support
   * @param {string} source - Data source name
   * @returns {boolean} - Whether the source has built-in support
   */
  hasBuiltInSupport(source) {
    const builtInSources = ['weather', 'news', 'stocks', 'currency'];
    return builtInSources.includes(source.toLowerCase());
  }
  
  /**
   * Check the cache for data
   * @param {Object} input - Input containing data request
   * @returns {Object|null} - Cached data or null if not found
   */
  checkCache(input) {
    const cacheKey = this.getCacheKey(input);
    
    if (this.cache.has(cacheKey)) {
      const cachedItem = this.cache.get(cacheKey);
      
      // Check if the cached item is still valid
      const now = Date.now();
      if (now - cachedItem.cacheTime < this.cacheTTL) {
        return cachedItem.data;
      } else {
        // Remove expired item
        this.cache.delete(cacheKey);
      }
    }
    
    return null;
  }
  
  /**
   * Store data in the cache
   * @param {Object} input - Input containing data request
   * @param {Object} data - Data to cache
   */
  storeInCache(input, data) {
    const cacheKey = this.getCacheKey(input);
    
    this.cache.set(cacheKey, {
      data: {
        source: input.source,
        query: input.query,
        data: data,
        timestamp: new Date().toISOString()
      },
      cacheTime: Date.now()
    });
    
    this.logger.info(`[${this.name}] Stored data in cache for source: ${input.source}`);
  }
  
  /**
   * Generate a cache key for the input
   * @param {Object} input - Input containing data request
   * @returns {string} - Cache key
   */
  getCacheKey(input) {
    return `${input.source}:${JSON.stringify(input.query || {})}`;
  }
  
  /**
   * Fetch data from the source
   * @param {Object} input - Input containing data request
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Fetched data
   */
  async fetchData(input, context) {
    const { source, query } = input;
    
    // Check if we have a custom data source handler
    if (this.dataSources[source]) {
      return await this.dataSources[source].fetch(query, context, this);
    }
    
    // Otherwise, use built-in handlers
    switch (source.toLowerCase()) {
      case 'weather':
        return await this.fetchWeatherData(query, context);
      case 'news':
        return await this.fetchNewsData(query, context);
      case 'stocks':
        return await this.fetchStockData(query, context);
      case 'currency':
        return await this.fetchCurrencyData(query, context);
      default:
        throw new Error(`No handler available for data source: ${source}`);
    }
  }
  
  /**
   * Process the fetched data
   * @param {Object} data - Fetched data
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed data
   */
  async processData(data, input, context) {
    const { source } = input;
    
    // Check if we have a custom data source processor
    if (this.dataSources[source] && this.dataSources[source].process) {
      return await this.dataSources[source].process(data, input, context, this);
    }
    
    // Otherwise, use built-in processors
    switch (source.toLowerCase()) {
      case 'weather':
        return await this.processWeatherData(data, input, context);
      case 'news':
        return await this.processNewsData(data, input, context);
      case 'stocks':
        return await this.processStockData(data, input, context);
      case 'currency':
        return await this.processCurrencyData(data, input, context);
      default:
        // If no specific processor, return the data as is
        return data;
    }
  }
  
  /**
   * Fetch weather data
   * @param {Object} query - Query parameters
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Weather data
   */
  async fetchWeatherData(query, context) {
    const { location } = query;
    
    if (!location) {
      throw new Error('Location is required for weather data');
    }
    
    // Get API key
    const apiKey = this.apiKeys.openweathermap || process.env.OPENWEATHERMAP_API_KEY;
    
    if (!apiKey) {
      // Return mock data if no API key is available
      return this.getMockWeatherData(location);
    }
    
    try {
      // Fetch current weather
      const weatherUrl = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(location)}&appid=${apiKey}&units=metric`;
      const weatherResponse = await fetch(weatherUrl);
      
      if (!weatherResponse.ok) {
        throw new Error(`Weather API error: ${weatherResponse.statusText}`);
      }
      
      const weatherData = await weatherResponse.json();
      
      // Fetch forecast
      const forecastUrl = `https://api.openweathermap.org/data/2.5/forecast?q=${encodeURIComponent(location)}&appid=${apiKey}&units=metric`;
      const forecastResponse = await fetch(forecastUrl);
      
      if (!forecastResponse.ok) {
        throw new Error(`Forecast API error: ${forecastResponse.statusText}`);
      }
      
      const forecastData = await forecastResponse.json();
      
      return {
        current: weatherData,
        forecast: forecastData
      };
    } catch (error) {
      this.logger.error(`[${this.name}] Error fetching weather data: ${error.message}`);
      
      // Fall back to mock data
      return this.getMockWeatherData(location);
    }
  }
  
  /**
   * Get mock weather data
   * @param {string} location - Location name
   * @returns {Object} - Mock weather data
   */
  getMockWeatherData(location) {
    return {
      current: {
        name: location,
        main: {
          temp: 22.5,
          feels_like: 23.2,
          temp_min: 20.1,
          temp_max: 24.8,
          pressure: 1012,
          humidity: 65
        },
        weather: [
          {
            id: 800,
            main: 'Clear',
            description: 'clear sky',
            icon: '01d'
          }
        ],
        wind: {
          speed: 3.6,
          deg: 160
        },
        clouds: {
          all: 5
        },
        dt: Date.now() / 1000,
        sys: {
          country: 'US',
          sunrise: Date.now() / 1000 - 21600,
          sunset: Date.now() / 1000 + 21600
        }
      },
      forecast: {
        list: [
          {
            dt: Date.now() / 1000 + 86400,
            main: {
              temp: 23.1,
              feels_like: 23.8,
              temp_min: 21.2,
              temp_max: 25.3,
              pressure: 1010,
              humidity: 63
            },
            weather: [
              {
                id: 800,
                main: 'Clear',
                description: 'clear sky',
                icon: '01d'
              }
            ]
          },
          {
            dt: Date.now() / 1000 + 172800,
            main: {
              temp: 24.2,
              feels_like: 24.9,
              temp_min: 22.5,
              temp_max: 26.1,
              pressure: 1009,
              humidity: 60
            },
            weather: [
              {
                id: 801,
                main: 'Clouds',
                description: 'few clouds',
                icon: '02d'
              }
            ]
          }
        ],
        city: {
          name: location,
          country: 'US'
        }
      },
      mock: true
    };
  }
  
  /**
   * Process weather data
   * @param {Object} data - Weather data
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed weather data
   */
  async processWeatherData(data, input, context) {
    // Extract the most relevant information
    const current = data.current;
    const forecast = data.forecast;
    
    // Format current weather
    const currentWeather = {
      location: current.name,
      country: current.sys.country,
      temperature: {
        current: current.main.temp,
        feelsLike: current.main.feels_like,
        min: current.main.temp_min,
        max: current.main.temp_max,
        unit: 'celsius'
      },
      conditions: {
        main: current.weather[0].main,
        description: current.weather[0].description,
        icon: current.weather[0].icon
      },
      wind: {
        speed: current.wind.speed,
        direction: current.wind.deg,
        unit: 'm/s'
      },
      humidity: current.main.humidity,
      pressure: current.main.pressure,
      visibility: current.visibility,
      sunrise: new Date(current.sys.sunrise * 1000).toISOString(),
      sunset: new Date(current.sys.sunset * 1000).toISOString(),
      time: new Date(current.dt * 1000).toISOString()
    };
    
    // Format forecast
    const forecastData = forecast.list.slice(0, 5).map(item => ({
      time: new Date(item.dt * 1000).toISOString(),
      temperature: {
        current: item.main.temp,
        feelsLike: item.main.feels_like,
        min: item.main.temp_min,
        max: item.main.temp_max,
        unit: 'celsius'
      },
      conditions: {
        main: item.weather[0].main,
        description: item.weather[0].description,
        icon: item.weather[0].icon
      },
      humidity: item.main.humidity,
      pressure: item.main.pressure
    }));
    
    return {
      current: currentWeather,
      forecast: forecastData,
      mock: data.mock || false
    };
  }
  
  /**
   * Fetch news data
   * @param {Object} query - Query parameters
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - News data
   */
  async fetchNewsData(query, context) {
    // Mock implementation - in a real implementation, you would use a news API
    return {
      articles: [
        {
          title: "Sample News Article 1",
          description: "This is a sample news article about technology.",
          source: "Tech News",
          url: "https://example.com/news/1",
          publishedAt: new Date().toISOString(),
          content: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
        },
        {
          title: "Sample News Article 2",
          description: "This is a sample news article about science.",
          source: "Science Daily",
          url: "https://example.com/news/2",
          publishedAt: new Date(Date.now() - 3600000).toISOString(),
          content: "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        }
      ],
      mock: true
    };
  }
  
  /**
   * Process news data
   * @param {Object} data - News data
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed news data
   */
  async processNewsData(data, input, context) {
    // Just return the articles with some formatting
    return {
      articles: data.articles.map(article => ({
        title: article.title,
        description: article.description,
        source: article.source,
        url: article.url,
        publishedAt: article.publishedAt,
        summary: article.content.substring(0, 100) + '...'
      })),
      mock: data.mock || false
    };
  }
  
  /**
   * Fetch stock data
   * @param {Object} query - Query parameters
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Stock data
   */
  async fetchStockData(query, context) {
    // Mock implementation - in a real implementation, you would use a stock API
    return {
      symbol: query.symbol || 'AAPL',
      price: 150.25,
      change: 2.35,
      changePercent: 1.59,
      volume: 32500000,
      marketCap: 2500000000000,
      mock: true
    };
  }
  
  /**
   * Process stock data
   * @param {Object} data - Stock data
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed stock data
   */
  async processStockData(data, input, context) {
    // Just return the data with some formatting
    return {
      symbol: data.symbol,
      price: {
        current: data.price,
        change: data.change,
        changePercent: data.changePercent,
        currency: 'USD'
      },
      volume: data.volume,
      marketCap: data.marketCap,
      mock: data.mock || false
    };
  }
  
  /**
   * Fetch currency data
   * @param {Object} query - Query parameters
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Currency data
   */
  async fetchCurrencyData(query, context) {
    // Mock implementation - in a real implementation, you would use a currency API
    return {
      base: query.base || 'USD',
      rates: {
        EUR: 0.85,
        GBP: 0.75,
        JPY: 110.25,
        CAD: 1.25,
        AUD: 1.35
      },
      mock: true
    };
  }
  
  /**
   * Process currency data
   * @param {Object} data - Currency data
   * @param {Object} input - Original input
   * @param {Object} context - Processing context
   * @returns {Promise<Object>} - Processed currency data
   */
  async processCurrencyData(data, input, context) {
    // Just return the data with some formatting
    return {
      base: data.base,
      rates: data.rates,
      timestamp: new Date().toISOString(),
      mock: data.mock || false
    };
  }
  
  /**
   * Validate the input
   * @param {Object} input - Input to validate
   */
  validateInput(input) {
    super.validateInput(input);
    
    if (!input.source) {
      throw new Error('Data source is required');
    }
    
    if (typeof input.source !== 'string') {
      throw new Error('Data source must be a string');
    }
  }
}

module.exports = LiveDataAgent;
