# Deployment Guide for Blackhole Core MCP (FastAPI Version)

This guide will help you deploy both the frontend and backend components of the Blackhole Core MCP application and ensure they connect properly.

## Prerequisites

- A server with Docker installed (for Docker deployment)
- A server with Python 3.8+ installed (for traditional deployment)
- MongoDB (either local or cloud-based like MongoDB Atlas)
- A Netlify account (for frontend deployment)

## Backend Deployment

### Option 1: Using Docker

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd blackhole_core_mcp
   ```

2. **Configure environment variables**:
   - Copy the production environment file:
     ```bash
     cp .env.production .env
     ```
   - Edit the `.env` file to update the MongoDB URI and CORS settings:
     ```
     MONGO_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/blackhole_db
     CORS_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000,http://localhost:8000
     ```

3. **Build and start the containers**:
   ```bash
   docker-compose up -d
   ```

4. **Verify the deployment**:
   - Check if the containers are running:
     ```bash
     docker-compose ps
     ```
   - Check the logs:
     ```bash
     docker-compose logs -f
     ```
   - Test the API:
     ```bash
     curl http://localhost:8000/api/health
     ```

### Option 3: Manual Deployment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd blackhole_core_mcp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy the production environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file to update the MongoDB URI and CORS settings

5. **Start the server**:
   ```bash
   # For development
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

   # Or use the provided scripts
   # On Linux/Mac:
   ./start.sh

   # On Windows:
   start.bat

   # For production
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

## Deployment Setup (Render Backend + Netlify Frontend)

This project is configured for deployment with the backend on Render and the frontend on Netlify:

### Backend Deployment (Render)

1. **Push your code to a Git repository** (GitHub, GitLab, or Bitbucket)

2. **Log in to Render and create a new Web Service**:
   - Click "New Web Service"
   - Select your repository
   - Configure the deployment settings:
     - Build command: `pip install -r requirements.txt`
     - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Click "Create Web Service"

3. **Configure environment variables in Render**:
   - Go to the Environment tab
   - Add the following environment variables:
     - `MONGO_URI`: Your MongoDB connection string
     - `CORS_ORIGINS`: `*` (or your specific origins including your Netlify domain)
   - Click "Save Changes"

4. **Verify the backend deployment**:
   - Visit your Render URL (e.g., https://blackhole-core-api.onrender.com)
   - Check that the API is responding correctly
   - Test the API endpoints using a tool like Postman or curl

### Frontend Deployment (Netlify)

1. **Push your code to a Git repository** (GitHub, GitLab, or Bitbucket)

2. **Log in to Netlify and create a new site**:
   - Click "New site from Git"
   - Select your repository
   - Set the publish directory to `public` (not `dist`)
   - Set the build command to `node update_env.js`
   - Click "Deploy site"

3. **Configure environment variables in Netlify**:
   - Go to Site settings > Build & deploy > Environment variables
   - Add `API_BASE_URL` with your Render backend URL (e.g., https://blackhole-core-api.onrender.com)
   - Trigger a new deployment for the environment variables to take effect

4. **Verify the frontend deployment**:
   - Visit your Netlify site (e.g., https://blackholebody.netlify.app)
   - Open the browser console (F12) and check that `API_BASE_URL` is correctly set to your Render backend URL
   - Try using the various features (image processing, PDF processing, etc.)
   - Check the "Results" tab to see if data is being retrieved from MongoDB

## Connecting Frontend to Backend

When deploying with Render for the backend and Netlify for the frontend, here's how the connection works:

1. **CORS settings**:
   - The Render backend has CORS configured to allow requests from your Netlify domain
   - This is set in the `main.py` file and through the `CORS_ORIGINS` environment variable
   - The Netlify domain (blackholebody.netlify.app) is explicitly added to the allowed origins

2. **API_BASE_URL configuration**:
   - The `env.js` file is automatically updated during deployment
   - It sets `API_BASE_URL` to your Render backend URL (e.g., https://blackhole-core-api.onrender.com) when running on Netlify
   - It sets `API_BASE_URL` to an empty string (same origin) when running locally
   - This ensures that the frontend uses the correct API URL in all environments

3. **Testing the connection**:
   - Visit your Netlify site (e.g., https://blackholebody.netlify.app)
   - Open the browser console (F12) and check for any CORS or connection errors
   - Try using the various features (image processing, PDF processing, etc.)
   - Check the "Results" tab to see if data is being retrieved from MongoDB

4. **Local development**:
   - When running locally, the frontend will connect to the local backend
   - Start the backend with `uvicorn main:app --host 0.0.0.0 --port 8000`
   - The frontend will automatically use the local backend API

## Troubleshooting

### Backend Issues

1. **MongoDB Connection Issues**:
   - Check the MongoDB URI in the environment variables
   - Make sure the MongoDB server is running and accessible
   - Ensure your IP is whitelisted if using MongoDB Atlas
   - Check the server logs for connection errors

2. **Server Not Starting**:
   - Check the server logs for errors
   - Make sure all dependencies are listed in requirements.txt
   - Verify that the start command is correct
   - Check if the Python version is compatible with your code

3. **File Upload Issues**:
   - Make sure the UPLOAD_DIR exists and is writable
   - Check the file permissions
   - Consider using cloud storage for persistent files

### Frontend Issues (Netlify)

1. **CORS Errors**:
   - Check the browser console for CORS errors
   - Make sure the Netlify domain is included in the CORS_ORIGINS in your backend
   - Verify that the CORS headers in netlify.toml are correctly configured
   - Check that the backend server is properly configured for CORS

2. **API Connection Errors**:
   - Check that the API_BASE_URL is correctly set in the environment variables on Netlify
   - Make sure the backend server is running and accessible
   - Try accessing the backend directly to verify it's working
   - Check for any network issues (firewall, security groups, etc.)

3. **Build Errors**:
   - Check the Netlify build logs for errors
   - Make sure the build command is correct: `node update_env.js`
   - Verify that the publish directory is set to `public`
   - Check that the update_env.js script is working correctly

## Monitoring and Maintenance

1. **Monitoring the Backend**:
   - Check the server logs regularly
   - Set up monitoring tools like Prometheus/Grafana
   - Configure log rotation for production logs
   - Set up alerts for service outages

2. **Monitoring the Frontend (Netlify)**:
   - Check the Netlify analytics
   - Set up Netlify's built-in monitoring
   - Consider upgrading to a paid plan for better performance and features

3. **Updating the Application**:
   - Push the latest changes to your GitHub repository
   - Netlify will automatically deploy the frontend changes
   - Update your backend server with the latest changes
   - Test the application after deployment

4. **Backing Up MongoDB**:
   - Set up regular backups of your MongoDB database
   - If using MongoDB Atlas, use its built-in backup features
   - Test the restore process periodically

5. **Managing Costs**:
   - Monitor your usage of hosting services
   - Stay within the free tier limits if possible
   - Consider upgrading to paid plans for production use
