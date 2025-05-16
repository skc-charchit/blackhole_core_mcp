// Netlify serverless function to proxy API requests to the Python FastAPI backend
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Function to check if Python is available
async function checkPython() {
  return new Promise((resolve, reject) => {
    const python = spawn('python', ['--version']);
    
    python.on('close', (code) => {
      if (code === 0) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    
    python.on('error', () => {
      resolve(false);
    });
  });
}

// Function to start the FastAPI server
async function startFastAPI() {
  // Path to the main.py file
  const mainPath = path.join(__dirname, 'main.py');
  
  // Check if main.py exists
  if (!fs.existsSync(mainPath)) {
    console.error('main.py not found at', mainPath);
    return null;
  }
  
  // Start the FastAPI server
  const fastapi = spawn('python', [mainPath]);
  
  // Log stdout and stderr
  fastapi.stdout.on('data', (data) => {
    console.log(`FastAPI stdout: ${data}`);
  });
  
  fastapi.stderr.on('data', (data) => {
    console.error(`FastAPI stderr: ${data}`);
  });
  
  // Wait for the server to start
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  return fastapi;
}

// Handler for the Netlify function
exports.handler = async function(event, context) {
  try {
    // Check if Python is available
    const pythonAvailable = await checkPython();
    if (!pythonAvailable) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Python is not available' })
      };
    }
    
    // Start the FastAPI server
    const fastapi = await startFastAPI();
    if (!fastapi) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Failed to start FastAPI server' })
      };
    }
    
    // Forward the request to the FastAPI server
    // This is a simplified example - in a real-world scenario, you would use a proper HTTP client
    // to forward the request to the FastAPI server
    
    // For now, just return a success response
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'FastAPI server started successfully' })
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
