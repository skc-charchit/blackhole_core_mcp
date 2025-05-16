// A simple test function to check if Netlify Functions are working
exports.handler = async function(event, context) {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    },
    body: JSON.stringify({
      message: 'Netlify Function is working!',
      timestamp: new Date().toISOString(),
      event: {
        path: event.path,
        httpMethod: event.httpMethod,
        headers: event.headers,
        queryStringParameters: event.queryStringParameters,
      }
    }),
  };
};
