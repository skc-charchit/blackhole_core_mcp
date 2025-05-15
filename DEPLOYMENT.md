# Deployment Guide for Blackhole Core MCP

This guide will help you deploy both the frontend and backend components of the Blackhole Core MCP application and ensure they connect properly.

## Prerequisites

- A server with Docker installed (for Docker deployment)
- A server with Python 3.8+ installed (for traditional deployment)
- MongoDB (either local or cloud-based like MongoDB Atlas)
- A Netlify account (for frontend deployment)

## Backend Deployment

### Option 1: Using Docker (Recommended)

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

### Option 2: Using the Deployment Script

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd blackhole_core_mcp
   ```

2. **Make the deployment script executable**:
   ```bash
   chmod +x deploy_backend.sh
   ```

3. **Run the deployment script**:
   ```bash
   ./deploy_backend.sh
   ```
   - The script will guide you through the deployment process
   - It will prompt you for MongoDB URI and Netlify URL
   - It will set up a systemd service if run as root

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
     cp .env.production .env
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
   - Leave the build command blank
   - Click "Deploy site"

3. **Update the API_BASE_URL in the frontend**:
   - Edit the `public/index.html` file:
     ```javascript
     // Find this line
     const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
         ? '' // Empty string means same origin on localhost
         : ''; // For Netlify deployment, we'll use a relative URL which will fail gracefully
     
     // Change it to
     const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
         ? '' // Empty string means same origin on localhost
         : 'https://your-backend-server.com'; // Replace with your actual backend URL
     ```
   - Commit and push the changes
   - Redeploy the site on Netlify

4. **Configure environment variables in Netlify**:
   - Go to Site settings > Build & deploy > Environment variables
   - Add `API_BASE_URL` with your backend API URL (e.g., https://your-backend-server.com)
   - Trigger a new deployment for the environment variables to take effect

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

### Backend Issues

1. **MongoDB Connection Issues**:
   - Check the MongoDB URI in the `.env` file
   - Make sure the MongoDB server is running and accessible
   - Check the network settings (firewall, security groups, etc.)
   - Run the MongoDB connection test:
     ```bash
     python -c "from blackhole_core.data_source.mongodb import test_connection; print('MongoDB connection successful!' if test_connection() else 'MongoDB connection failed!')"
     ```

2. **Server Not Starting**:
   - Check the logs:
     ```bash
     # For Docker
     docker-compose logs -f
     
     # For systemd
     journalctl -u blackhole-backend
     
     # For manual deployment
     cat logs/blackhole.log
     ```
   - Make sure all dependencies are installed
   - Check if the port is already in use

### Frontend Issues

1. **CORS Errors**:
   - Check the browser console for CORS errors
   - Make sure the Netlify domain is included in the CORS_ORIGINS in the `.env` file
   - Check that the backend server is properly configured for CORS

2. **API Connection Errors**:
   - Check that the API_BASE_URL is correctly set in the frontend
   - Make sure the backend server is running and accessible
   - Check for any network issues (firewall, security groups, etc.)

## Monitoring and Maintenance

1. **Monitoring the Backend**:
   - Check the logs regularly
   - Set up monitoring tools like Prometheus/Grafana
   - Configure log rotation for production logs

2. **Updating the Application**:
   - Pull the latest changes from the repository
   - Rebuild and restart the containers (for Docker deployment)
   - Restart the service (for traditional deployment)
   - Redeploy the frontend on Netlify

3. **Backing Up MongoDB**:
   - Set up regular backups of your MongoDB database
   - Test the restore process periodically
