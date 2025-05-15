# Netlify Deployment for Blackhole Core MCP

This document provides information about the Netlify deployment configuration for the Blackhole Core MCP project.

## Deployment Structure

- `netlify.toml`: Main configuration file for Netlify
- `build.sh`: Build script that prepares the project for deployment
- `requirements-netlify.txt`: Python dependencies for the Netlify deployment
- `netlify/functions/api.py`: FastAPI application adapted for Netlify Functions
- `dist/`: Directory containing static files for the frontend

## Environment Variables

The following environment variables should be set in the Netlify dashboard:

- `MONGO_URI`: Connection string for MongoDB (if using MongoDB)
- Any other environment variables required by your application

## Deployment Process

1. Netlify will run the build script specified in `netlify.toml`
2. The build script will create the `dist` directory and copy static files
3. Python dependencies will be installed from `requirements-netlify.txt`
4. The FastAPI application will be deployed as a serverless function

## API Endpoints

- `/.netlify/functions/api`: Base endpoint for the API
- `/.netlify/functions/api/run_task`: Endpoint for running agent tasks

## Local Development

To run the project locally with Netlify CLI:

1. Install Netlify CLI: `npm install -g netlify-cli`
2. Run `netlify dev` to start the development server

## Troubleshooting

If you encounter issues with the deployment:

1. Check the Netlify deployment logs
2. Verify that all required environment variables are set
3. Make sure the `dist` directory is being created correctly
4. Check that the Python dependencies are being installed correctly
