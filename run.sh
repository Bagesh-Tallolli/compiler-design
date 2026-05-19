#!/bin/bash
# Semantic Diff Analyzer - Run Script

echo "Starting Semantic Diff Analyzer..."

# Create required folders if they don't exist
mkdir -p .temp_ir
mkdir -p uploads

# Start the backend in the background
echo "Starting backend..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..10}; do
    curl -s http://localhost:8000/api/health > /dev/null
    if [ $? -eq 0 ]; then
        echo "Backend is healthy!"
        break
    fi
    sleep 1
done

# Start the frontend
echo "Starting frontend..."
cd frontend
npm run dev
