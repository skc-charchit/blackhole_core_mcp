#!/bin/bash
# Deployment script for Blackhole Core MCP Backend

# Exit on error
set -e

# Print commands
set -x

echo "Starting deployment of Blackhole Core MCP Backend..."

# Check if running as root (not recommended)
if [ "$(id -u)" = "0" ]; then
    echo "Warning: Running as root is not recommended. Consider using a non-root user."
fi

# Create necessary directories
mkdir -p uploads logs temp processed public

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing Python 3..."
    
    # Check the OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y python3 python3-pip python3-venv
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        yum install -y python3 python3-pip
    else
        echo "Unsupported OS. Please install Python 3 manually."
        exit 1
    fi
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists, if not, copy from .env.production
if [ ! -f .env ]; then
    echo "Creating .env file from .env.production..."
    cp .env.production .env
    
    # Prompt for MongoDB URI
    read -p "Enter your MongoDB URI (leave blank to use default): " mongo_uri
    if [ ! -z "$mongo_uri" ]; then
        # Replace MongoDB URI in .env file
        sed -i "s|MONGO_URI=.*|MONGO_URI=$mongo_uri|g" .env
    fi
    
    # Prompt for Netlify URL
    read -p "Enter your Netlify app URL (e.g., https://your-app.netlify.app): " netlify_url
    if [ ! -z "$netlify_url" ]; then
        # Update CORS_ORIGINS in .env file
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=$netlify_url,http://localhost:3000,http://localhost:8000|g" .env
    fi
fi

# Test MongoDB connection
echo "Testing MongoDB connection..."
python -c "from blackhole_core.data_source.mongodb import test_connection; print('MongoDB connection successful!' if test_connection() else 'MongoDB connection failed!')"

# Check if MongoDB connection was successful
if ! python -c "from blackhole_core.data_source.mongodb import test_connection; exit(0 if test_connection() else 1)"; then
    echo "MongoDB connection failed. Please check your MongoDB URI in the .env file."
    echo "You can continue with deployment, but the application may not work properly."
    read -p "Continue with deployment? (y/n): " continue_deploy
    if [ "$continue_deploy" != "y" ]; then
        echo "Deployment aborted."
        exit 1
    fi
fi

# Set up systemd service for production (if running as root)
if [ "$(id -u)" = "0" ]; then
    echo "Setting up systemd service..."
    cat > /etc/systemd/system/blackhole-backend.service << EOL
[Unit]
Description=Blackhole Core MCP Backend
After=network.target

[Service]
User=$(logname)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:8000 app:app
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=blackhole-backend
Environment="PATH=$(pwd)/venv/bin"

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd and enable/start the service
    systemctl daemon-reload
    systemctl enable blackhole-backend
    systemctl start blackhole-backend
    
    echo "Systemd service installed and started. Check status with: systemctl status blackhole-backend"
else
    # Start the server directly if not running as root
    echo "Starting the server..."
    echo "You can use one of the following methods to run the server:"
    echo "1. Direct Python: python app.py"
    echo "2. Gunicorn (recommended for production): gunicorn --bind 0.0.0.0:8000 app:app"
    echo "3. Screen session (to keep running after logout): screen -S blackhole -dm gunicorn --bind 0.0.0.0:8000 app:app"
    
    # Ask which method to use
    read -p "Choose a method (1/2/3): " start_method
    
    case $start_method in
        1)
            python app.py
            ;;
        2)
            gunicorn --bind 0.0.0.0:8000 app:app
            ;;
        3)
            # Check if screen is installed
            if ! command -v screen &> /dev/null; then
                echo "Screen is not installed. Installing screen..."
                if [ -f /etc/debian_version ]; then
                    apt-get update
                    apt-get install -y screen
                elif [ -f /etc/redhat-release ]; then
                    yum install -y screen
                else
                    echo "Unsupported OS. Please install screen manually."
                    exit 1
                fi
            fi
            
            screen -S blackhole -dm gunicorn --bind 0.0.0.0:8000 app:app
            echo "Server started in screen session. Attach with: screen -r blackhole"
            ;;
        *)
            echo "Invalid option. Please run the server manually."
            ;;
    esac
fi

echo "Deployment completed successfully!"
echo "Your backend server should now be running and connected to MongoDB."
echo "Make sure to update the API_BASE_URL in your frontend to point to this server."
