#!/bin/bash

# Flogenix Enterprise System Startup Script
# This script starts the complete enterprise claims processing platform

echo "🚀 Starting Flogenix Enterprise Claims Processing Platform..."
echo "=================================================="

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

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    print_status "Detected Windows environment"
    PYTHON_CMD="python"
    PIP_CMD="pip"
    NODE_CMD="npm"
else
    print_status "Detected Unix-like environment"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    NODE_CMD="npm"
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v $PYTHON_CMD &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    print_error "Please run this script from the Flogenix-2 root directory"
    exit 1
fi

print_success "Prerequisites check passed"

# Function to start backend
start_backend() {
    print_status "Setting up backend environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "vev" ]; then
        print_status "Creating Python virtual environment..."
        $PYTHON_CMD -m venv vev
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        source vev/Scripts/activate
    else
        source vev/bin/activate
    fi
    
    # Install backend dependencies
    print_status "Installing Python dependencies..."
    $PIP_CMD install -r requirements_enterprise.txt
    
    # Start the enterprise backend server
    print_status "Starting enterprise backend server on port 8000..."
    $PYTHON_CMD main_enterprise.py &
    BACKEND_PID=$!
    
    cd ..
    
    print_success "Backend server started (PID: $BACKEND_PID)"
}

# Function to start frontend
start_frontend() {
    print_status "Setting up frontend environment..."
    
    cd frontend
    
    # Install frontend dependencies
    print_status "Installing Node.js dependencies..."
    $NODE_CMD install
    
    # Start the React development server
    print_status "Starting React development server on port 5173..."
    $NODE_CMD run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    print_success "Frontend server started (PID: $FRONTEND_PID)"
}

# Function to wait for services
wait_for_services() {
    print_status "Waiting for services to start..."
    
    # Wait for backend
    print_status "Checking backend health..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Backend health check timeout"
        fi
        sleep 2
    done
    
    # Wait for frontend
    print_status "Checking frontend availability..."
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            print_success "Frontend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Frontend availability check timeout"
        fi
        sleep 2
    done
}

# Function to display startup information
show_startup_info() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}🎉 Flogenix Enterprise Platform Started Successfully!${NC}"
    echo "=================================================="
    echo ""
    echo "🌐 Service URLs:"
    echo "   • Frontend (React):     http://localhost:5173"
    echo "   • Backend API:          http://localhost:8000"
    echo "   • API Documentation:    http://localhost:8000/docs"
    echo "   • Interactive API:      http://localhost:8000/redoc"
    echo ""
    echo "🔑 Default Admin Credentials:"
    echo "   • Username: admin"
    echo "   • Password: admin123"
    echo "   • Role: SUPER_ADMIN"
    echo ""
    echo "📚 Quick Start Guide:"
    echo "   1. Open http://localhost:5173 in your browser"
    echo "   2. Login with admin credentials"
    echo "   3. Navigate to Enterprise → Admin Portal"
    echo "   4. Start processing claims with AI agents"
    echo ""
    echo "🤖 Enterprise Features:"
    echo "   • Multi-Agent AI Processing"
    echo "   • Real-time Fraud Detection"
    echo "   • Advanced Analytics Dashboard"
    echo "   • Role-based Access Control"
    echo "   • Comprehensive Audit Trails"
    echo "   • WebSocket Notifications"
    echo ""
    echo "📖 Documentation:"
    echo "   • API Docs: http://localhost:8000/docs"
    echo "   • README: ./README.md"
    echo "   • Integration Guide: ./INTEGRATION_GUIDE.md"
    echo ""
    echo "🛑 To stop the platform:"
    echo "   • Press Ctrl+C to stop this script"
    echo "   • Or run: ./scripts/stop_enterprise.sh"
    echo ""
    echo "=================================================="
}

# Function to handle cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend server..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend server..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining processes
    pkill -f "main_enterprise.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    # Start services
    start_backend
    sleep 3
    start_frontend
    
    # Wait for services to be ready
    wait_for_services
    
    # Show startup information
    show_startup_info
    
    # Keep script running
    print_status "Enterprise platform is running. Press Ctrl+C to stop..."
    while true; do
        sleep 5
        
        # Check if processes are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            cleanup
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            cleanup
        fi
    done
}

# Run main function
main