#!/bin/bash

# BlackHole Core MCP - Docker Deployment Script
# This script helps deploy the application using Docker Compose

set -e  # Exit on any error

echo "🚀 BlackHole Core MCP - Docker Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.docker .env
    print_warning "Please edit .env file with your actual configuration (especially TOGETHER_API_KEY)"
    print_warning "Then run this script again."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/multimodal/uploaded_pdfs
mkdir -p data/multimodal/uploaded_images
mkdir -p data/multimodal/processed_outputs
mkdir -p uploads
mkdir -p logs

# Set proper permissions
chmod -R 755 data/ uploads/ logs/

print_success "Directories created and permissions set"

# Parse command line arguments
COMMAND=${1:-"up"}

case $COMMAND in
    "up"|"start")
        print_status "Starting BlackHole Core MCP with Docker Compose..."
        docker-compose up -d
        
        print_status "Waiting for services to be healthy..."
        sleep 10
        
        # Check if services are running
        if docker-compose ps | grep -q "Up"; then
            print_success "Services started successfully!"
            echo ""
            echo "🌐 Application URLs:"
            echo "   - BlackHole Core MCP: http://localhost:8000"
            echo "   - API Documentation: http://localhost:8000/docs"
            echo "   - MongoDB Express: http://localhost:8081"
            echo ""
            echo "📋 Default Credentials:"
            echo "   - MongoDB Express: admin / blackhole_admin_2024"
            echo ""
            echo "🔧 Useful Commands:"
            echo "   - View logs: docker-compose logs -f"
            echo "   - Stop services: docker-compose down"
            echo "   - Restart: docker-compose restart"
        else
            print_error "Some services failed to start. Check logs with: docker-compose logs"
            exit 1
        fi
        ;;
        
    "down"|"stop")
        print_status "Stopping BlackHole Core MCP services..."
        docker-compose down
        print_success "Services stopped"
        ;;
        
    "restart")
        print_status "Restarting BlackHole Core MCP services..."
        docker-compose restart
        print_success "Services restarted"
        ;;
        
    "logs")
        print_status "Showing logs..."
        docker-compose logs -f
        ;;
        
    "build")
        print_status "Building BlackHole Core MCP Docker image..."
        docker-compose build --no-cache
        print_success "Build completed"
        ;;
        
    "clean")
        print_status "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup completed"
        ;;
        
    "status")
        print_status "Service status:"
        docker-compose ps
        ;;
        
    "health")
        print_status "Checking service health..."
        echo "🔍 BlackHole App Health:"
        curl -s http://localhost:8000/api/health | jq . || echo "Service not responding"
        echo ""
        echo "🔍 MongoDB Status:"
        docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" || echo "MongoDB not responding"
        ;;
        
    *)
        echo "Usage: $0 {up|down|restart|logs|build|clean|status|health}"
        echo ""
        echo "Commands:"
        echo "  up/start  - Start all services"
        echo "  down/stop - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs      - Show service logs"
        echo "  build     - Rebuild Docker images"
        echo "  clean     - Clean up Docker resources"
        echo "  status    - Show service status"
        echo "  health    - Check service health"
        exit 1
        ;;
esac
