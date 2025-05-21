// Simplified Netlify function to fetch live data without complex dependencies

// Get mock weather data
function getMockWeatherData(location) {
  return {
    current: {
      location: location || 'Unknown',
      country: 'US',
      temperature: {
        current: 22.5,
        feelsLike: 23.2,
        min: 20.1,
        max: 24.8,
        unit: 'celsius'
      },
      conditions: {
        main: 'Clear',
        description: 'clear sky',
        icon: '01d'
      },
      wind: {
        speed: 3.6,
        direction: 160,
        unit: 'm/s'
      },
      humidity: 65,
      pressure: 1012,
      visibility: 10000,
      sunrise: new Date(Date.now() - 21600000).toISOString(),
      sunset: new Date(Date.now() + 21600000).toISOString(),
      time: new Date().toISOString()
    },
    forecast: [
      {
        time: new Date(Date.now() + 86400000).toISOString(),
        temperature: {
          current: 23.1,
          feelsLike: 23.8,
          min: 21.2,
          max: 25.3,
          unit: 'celsius'
        },
        conditions: {
          main: 'Clear',
          description: 'clear sky',
          icon: '01d'
        },
        humidity: 63,
        pressure: 1010
      },
      {
        time: new Date(Date.now() + 172800000).toISOString(),
        temperature: {
          current: 24.2,
          feelsLike: 24.9,
          min: 22.5,
          max: 26.1,
          unit: 'celsius'
        },
        conditions: {
          main: 'Clouds',
          description: 'few clouds',
          icon: '02d'
        },
        humidity: 60,
        pressure: 1009
      }
    ],
    mock: true
  };
}

// Get mock news data
function getMockNewsData() {
  return {
    articles: [
      {
        title: "Sample News Article 1",
        description: "This is a sample news article about technology.",
        source: "Tech News",
        url: "https://example.com/news/1",
        publishedAt: new Date().toISOString(),
        summary: "Lorem ipsum dolor sit amet, consectetur adipiscing elit..."
      },
      {
        title: "Sample News Article 2",
        description: "This is a sample news article about science.",
        source: "Science Daily",
        url: "https://example.com/news/2",
        publishedAt: new Date(Date.now() - 3600000).toISOString(),
        summary: "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua..."
      }
    ],
    mock: true
  };
}

// Get mock stock data
function getMockStockData(symbol) {
  return {
    symbol: symbol || 'AAPL',
    price: {
      current: 150.25,
      change: 2.35,
      changePercent: 1.59,
      currency: 'USD'
    },
    volume: 32500000,
    marketCap: 2500000000000,
    mock: true
  };
}

// Get mock currency data
function getMockCurrencyData(base) {
  return {
    base: base || 'USD',
    rates: {
      EUR: 0.85,
      GBP: 0.75,
      JPY: 110.25,
      CAD: 1.25,
      AUD: 1.35
    },
    timestamp: new Date().toISOString(),
    mock: true
  };
}

// Process a live data request (mock implementation)
function processLiveDataRequest(source, query = {}) {
  switch (source.toLowerCase()) {
    case 'weather':
      return {
        source: 'weather',
        query: query,
        data: getMockWeatherData(query.location),
        timestamp: new Date().toISOString(),
        cached: false
      };
    case 'news':
      return {
        source: 'news',
        query: query,
        data: getMockNewsData(),
        timestamp: new Date().toISOString(),
        cached: false
      };
    case 'stocks':
      return {
        source: 'stocks',
        query: query,
        data: getMockStockData(query.symbol),
        timestamp: new Date().toISOString(),
        cached: false
      };
    case 'currency':
      return {
        source: 'currency',
        query: query,
        data: getMockCurrencyData(query.base),
        timestamp: new Date().toISOString(),
        cached: false
      };
    default:
      return {
        source: source,
        query: query,
        data: {
          message: `Data source '${source}' is not supported.`
        },
        timestamp: new Date().toISOString(),
        cached: false,
        error: 'unsupported_source'
      };
  }
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

  try {
    // Set a timeout for the entire function
    const functionTimeout = setTimeout(() => {
      throw new Error('Function execution timeout');
    }, 8000);
    
    // Parse the request
    let source, query;
    
    if (event.httpMethod === 'GET') {
      // Get source and query from query parameters
      source = event.queryStringParameters?.source;
      
      // Parse query if provided
      if (event.queryStringParameters?.query) {
        try {
          query = JSON.parse(event.queryStringParameters.query);
        } catch (error) {
          // If parsing fails, use the query string as is
          query = { location: event.queryStringParameters.query };
        }
      } else {
        // If no query is provided, create a default one
        query = event.queryStringParameters?.location ? 
          { location: event.queryStringParameters.location } : 
          {};
      }
    } else if (event.httpMethod === 'POST') {
      try {
        // Parse the request body
        const body = JSON.parse(event.body);
        source = body.source;
        query = body.query || {};
      } catch (error) {
        console.warn('Error parsing request body:', error);
        
        // Try to extract source directly from body
        const bodyStr = event.body || '';
        const sourceMatch = bodyStr.match(/"source"\s*:\s*"([^"]+)"/);
        source = sourceMatch ? sourceMatch[1] : null;
        query = {};
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
    
    // Validate the source
    if (!source) {
      clearTimeout(functionTimeout);
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify({
          error: 'Bad request',
          message: 'Data source is required'
        }),
      };
    }
    
    // Process the live data request
    const result = processLiveDataRequest(source, query);
    
    // Clear the function timeout
    clearTimeout(functionTimeout);
    
    // Return the data
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error fetching live data:', error);
    
    // Return a fallback response
    return {
      statusCode: 200, // Return 200 even for errors to avoid client-side error handling
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify({
        source: event.queryStringParameters?.source || 'unknown',
        query: {},
        data: {
          message: `Error fetching data: ${error.message}`
        },
        timestamp: new Date().toISOString(),
        cached: false,
        error: error.message
      }),
    };
  }
};
