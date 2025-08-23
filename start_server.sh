#!/bin/bash

echo "🚀 Starting Spam Call Detector Python Server..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo ""
echo "✅ Server starting..."
echo "📱 Android app should connect to: ws://$LOCAL_IP:8765/stream"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the server
python3 python_server.py
