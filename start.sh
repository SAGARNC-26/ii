#!/bin/bash

# Smart Vault CCTV System - Startup Script
# This script installs dependencies and starts the application

set -e  # Exit on error

echo "================================================"
echo "  Smart Vault CCTV System - Installation"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi

# Check if MongoDB is running
echo -e "${YELLOW}[2/6] Checking MongoDB connection...${NC}"
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.version()" --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB is running${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB not detected. Starting with Docker...${NC}"
        if command -v docker &> /dev/null; then
            docker run -d -p 27017:27017 --name smartvault-mongodb mongo:latest || echo "MongoDB container already exists or failed to start"
            sleep 3
        else
            echo -e "${RED}Warning: MongoDB not running and Docker not found. Please start MongoDB manually.${NC}"
        fi
    fi
elif command -v mongo &> /dev/null; then
    if mongo --eval "db.version()" --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB is running${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB not running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ MongoDB client not found. Assuming it's running...${NC}"
fi

# Create virtual environment if it doesn't exist
echo -e "${YELLOW}[3/6] Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo -e "${YELLOW}[4/6] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install requirements
echo -e "${YELLOW}[5/6] Installing dependencies (this may take a few minutes)...${NC}"
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Some dependencies failed to install. Check errors above.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}[6/6] Creating project directories...${NC}"
mkdir -p known_faces
mkdir -p models
mkdir -p src/webapp/templates
mkdir -p src/webapp/static
mkdir -p scripts
mkdir -p docs

echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo "================================================"
echo -e "${GREEN}  Installation Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Add authorized face images to known_faces/"
echo "   Example: cp photo.jpg known_faces/Alice_Smith.jpg"
echo ""
echo "2. Sync known faces to database:"
echo "   python src/sync_known_faces.py"
echo ""
echo "3. Start the recognition system:"
echo "   python src/main.py"
echo ""
echo "4. Start the web dashboard (in another terminal):"
echo "   python src/webapp/app.py"
echo "   Access at: http://localhost:5000"
echo ""
echo "5. (Optional) Start with Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "For more information, see README.md"
echo ""
