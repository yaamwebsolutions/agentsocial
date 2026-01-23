#!/bin/bash

# Agent Twitter Startup Script
# This script starts both the backend and frontend services

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "🚀 Starting Agent Twitter Application"
echo "========================================"

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  Warning: .env file not found!"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup INT TERM

# Start the FastAPI backend
echo ""
echo "📡 Starting FastAPI backend..."
cd backend

# Kill any existing process on port 8000
EXISTING_PID=$(lsof -ti :8000 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo "🧹 Killing existing process on port 8000 (PID: $EXISTING_PID)"
    kill $EXISTING_PID 2>/dev/null
    sleep 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
elif [ -d "packages" ]; then
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/packages"
    echo "✅ Using local packages"
fi

# Start backend in background using uvicorn directly
PYTHONPATH="${PYTHONPATH}:$(pwd)" python -m uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8000} &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start!"
    cleanup
fi

# Start the frontend dev server (optional - comment out if using production build)
echo ""
echo "🌐 Starting frontend development server..."
cd ../app

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

sleep 2

if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
else
    echo "⚠️  Frontend may not have started properly"
fi

# Print status
echo ""
echo "========================================"
echo "✨ Agent Twitter is now running!"
echo "========================================"
echo ""
echo "📍 Services:"
echo "   • Backend API:  http://localhost:${BACKEND_PORT:-8000}"
echo "   • Frontend:     http://localhost:5173"
echo "   • Health Check: http://localhost:${BACKEND_PORT:-8000}/health"
echo "   • Status:       http://localhost:${BACKEND_PORT:-8000}/status"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================"

# Wait for processes
wait
