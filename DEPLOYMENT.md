# Deployment Guide for Blackhole Core MCP

This guide will help you deploy both the frontend and backend components of the Blackhole Core MCP application and ensure they connect properly.

## Prerequisites

- A server with Docker installed (for Docker deployment)
- A server with Python 3.8+ installed (for traditional deployment)
- MongoDB (either local or cloud-based like MongoDB Atlas)
- A Netlify account (for frontend deployment)

## Backend Deployment

### Option 1: Using Render (Recommended)

1. **Create a Render account** at https://render.com if you don't have one already.

2. **Connect your GitHub repository** to Render.

3. **Create a new Web Service**:
   - Select your repository
   - Choose "Python" as the environment
   - Set the build command to: `pip install -r requirements.txt`
   - Set the start command to: `python app.py`

4. **Configure environment variables**:
   - PORT: 10000
   - HOST: 0.0.0.0
   - DEBUG: false
   - RENDER: true
   - CORS_ORIGINS: https://blackhole-core.netlify.app,http://localhost:3000,http://localhost:8000
   - MONGO_URI: Your MongoDB connection string
   - MONGO_DB_NAME: blackhole_core
   - MONGO_COLLECTION_NAME: agent_outputs
   - UPLOAD_DIR: /tmp/blackhole_uploads

5. **Deploy the service** and note the URL (e.g., https://blackhole-core-api.onrender.com).

6. **Verify the deployment**:
   - Visit the health check endpoint: `https://your-render-url.onrender.com/api/health`
   - Check the Render logs for any errors

### Option 2: Using Docker

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
     cp .env.render .env
     ```
   - Edit the `.env` file to update the MongoDB URI and CORS settings

5. **Start the server**:
   ```bash
   # For development
   python app.py

   # For production
   gunicorn --bind 0.0.0.0:8000 --workers=4 --timeout=120 app:app
   ```

## Frontend Deployment to Netlify

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

4. **Verify the deployment**:
   - Visit your Netlify site (e.g., https://blackhole-core.netlify.app)
   - Open the browser console (F12) and check that `API_BASE_URL` is correctly set
   - Try using the various features (image processing, PDF processing, etc.)
   - Check the "Results" tab to see if data is being retrieved from MongoDB

## Connecting Frontend to Backend

The frontend and backend need to communicate with each other. Here's how to ensure they're properly connected:

1. **Update CORS settings in the backend**:
   - Make sure your Netlify domain is included in the CORS_ORIGINS in the `.env` file:
     ```
     CORS_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000,http://localhost:8000
     ```

2. **Update API_BASE_URL in the frontend**:
   - Make sure the API_BASE_URL in `public/index.html` points to your backend server:
     ```javascript
     const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
         ? '' // Empty string means same origin on localhost
         : 'https://your-backend-server.com'; // Replace with your actual backend URL
     ```

3. **Test the connection**:
   - Visit your Netlify site
   - Open the browser console (F12) and check for any CORS or connection errors
   - Try using the various features (image processing, PDF processing, etc.)
   - Check the "Results" tab to see if data is being retrieved from MongoDB

## Troubleshooting

### Backend Issues (Render)

1. **MongoDB Connection Issues**:
   - Check the MongoDB URI in the environment variables on Render
   - Make sure the MongoDB Atlas cluster is running and accessible
   - Ensure your IP is whitelisted in MongoDB Atlas
   - Check the Render logs for connection errors

2. **Server Not Starting**:
   - Check the Render logs for errors
   - Make sure all dependencies are listed in requirements.txt
   - Verify that the start command is correct: `python app.py`
   - Check if the Python version on Render is compatible with your code

3. **File Upload Issues**:
   - Remember that Render has an ephemeral filesystem
   - Files uploaded to Render will be lost when the service restarts
   - Make sure the UPLOAD_DIR is set to `/tmp/blackhole_uploads`
   - Consider using cloud storage for persistent files

4. **Slow First Request**:
   - The free tier of Render will spin down after periods of inactivity
   - The first request after inactivity will be slow as the service spins up
   - This is normal behavior for the free tier

### Frontend Issues (Netlify)

1. **CORS Errors**:
   - Check the browser console for CORS errors
   - Make sure the Netlify domain is included in the CORS_ORIGINS on Render
   - Verify that the CORS headers in netlify.toml are correctly configured
   - Check that the backend server is properly configured for CORS

2. **API Connection Errors**:
   - Check that the API_BASE_URL is correctly set in the environment variables on Netlify
   - Make sure the Render backend is running and accessible
   - Try accessing the backend directly to verify it's working
   - Check for any network issues (firewall, security groups, etc.)

3. **Build Errors**:
   - Check the Netlify build logs for errors
   - Make sure the build command is correct: `node update_env.js`
   - Verify that the publish directory is set to `public`
   - Check that the update_env.js script is working correctly

## Monitoring and Maintenance

1. **Monitoring the Backend (Render)**:
   - Check the Render logs regularly
   - Set up Render's built-in monitoring
   - Consider upgrading to a paid plan for better performance and reliability
   - Set up alerts for service outages

2. **Monitoring the Frontend (Netlify)**:
   - Check the Netlify analytics
   - Set up Netlify's built-in monitoring
   - Consider upgrading to a paid plan for better performance and features

3. **Updating the Application**:
   - Push the latest changes to your GitHub repository
   - Render and Netlify will automatically deploy the changes
   - Check the deployment logs for any errors
   - Test the application after deployment

4. **Backing Up MongoDB**:
   - Set up regular backups of your MongoDB Atlas database
   - Use MongoDB Atlas's built-in backup features
   - Test the restore process periodically

5. **Managing Costs**:
   - Monitor your usage of Render and Netlify
   - Stay within the free tier limits if possible
   - Be aware that the free tier of Render has limitations:
     - Services spin down after inactivity
     - Limited compute resources
     - Ephemeral filesystem
   - Consider upgrading to paid plans for production use
