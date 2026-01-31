#!/bin/bash

# Nexus - Production Start Script
# Usage: ./start_production.sh [start|stop|restart|status]

set -e

ACTION="${1:-start}"
WORKERS="${WEB_CONCURRENCY:-4}"
THREADS="${THREADS_PER_WORKER:-4}"
PORT="${PORT:-8000}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[Nexus]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    echo "Please create .env file with required variables."
    echo "See PRODUCTION_DEPLOYMENT.md for configuration."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Redis connection
check_redis() {
    print_message "Checking Redis connection..."
    if [ -n "$REDIS_URL" ]; then
        if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
            print_message "✓ Redis is running"
        else
            print_warning "Redis connection failed!"
            echo "  Falling back to local memory cache (single worker mode)"
            echo "  For production with multiple workers, ensure Redis is running:"
            echo "    sudo systemctl start redis"
        fi
    else
        print_warning "REDIS_URL not set in .env"
        echo "  Using local memory cache (development mode)"
        echo "  For production, install Redis and set REDIS_URL"
    fi
}

# Start production server
start_server() {
    print_message "Starting Nexus in production mode..."
    print_message "Configuration:"
    echo "  Workers: $WORKERS"
    echo "  Threads per worker: $THREADS"
    echo "  Port: $PORT"
    echo "  Total capacity: $((WORKERS * THREADS)) concurrent connections"
    echo ""
    
    check_redis
    
    print_message "Starting Gunicorn..."
    gunicorn -c gunicorn.conf.py config.wsgi:application
}

# Stop server
stop_server() {
    print_message "Stopping Nexus..."
    pkill -f "gunicorn.*config.wsgi" || true
    print_message "Server stopped"
}

# Restart server
restart_server() {
    stop_server
    sleep 2
    start_server
}

# Check status
check_status() {
    print_message "Checking server status..."
    
    if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
        PIDS=$(pgrep -f "gunicorn.*config.wsgi")
        COUNT=$(echo "$PIDS" | wc -l)
        print_message "✓ Server is running"
        echo "  Processes: $COUNT"
        echo "  PIDs: $PIDS"
        
        # Check port
        if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
            print_message "✓ Listening on port $PORT"
        fi
        
        # Check Redis
        check_redis
    else
        print_warning "Server is not running"
    fi
}

# Main script
case "$ACTION" in
    start)
        if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
            print_warning "Server is already running!"
            echo "Use './start_production.sh restart' to restart"
            exit 1
        fi
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Examples:"
        echo "  $0 start    - Start production server"
        echo "  $0 stop     - Stop production server"
        echo "  $0 restart  - Restart production server"
        echo "  $0 status   - Check server status"
        exit 1
        ;;
esac
