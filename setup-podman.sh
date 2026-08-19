#!/bin/bash

# Setup script for FAIRweaver Podman deployment
# Run this script to configure your environment before first deployment

set -e

echo "FAIRweaver Podman Setup"
echo "======================="
echo ""

CONTAINER_ENGINE=""

# Check if podman is installed
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
    echo "✓ podman found: $(podman --version)"

    # Check if podman-compose is installed
    if ! command -v podman-compose &> /dev/null; then
        echo "❌ Error: podman-compose is not installed"
        echo "   Install it with: sudo apt install podman-compose"
        exit 1
    fi
    echo "✓ podman-compose found: $(podman-compose --version)"

# Check if docker-compose is installed (as fallback)
elif command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    CONTAINER_ENGINE="docker"
    echo "⚠️  podman not found, using docker as fallback"
    echo "✓ docker found: $(docker --version)"
    echo "✓ docker-compose found: $(docker-compose --version)"
    echo "⚠️  Note: For remote deployment, podman is recommended"

else
    echo "❌ Error: No container engine found"
    echo "   Install podman: sudo apt install podman podman-compose"
    echo "   Or install docker: sudo apt install docker.io docker-compose"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Creating from example..."
    cp .env.example .env
    echo "✓ Created .env file from example"
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
else
    echo "✓ .env file found"
fi

# Check if required environment variables are set
# Use a safer method to load .env file that handles spaces properly
set -a
source .env || true
set +a

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY is not set in .env"
    exit 1
fi

echo "✓ OPENAI_API_KEY is configured"

# Check if podman server credentials are set
if [ -z "$PODMAN_SERVER_HOST" ] || [ -z "$PODMAN_SERVER_USER" ] || [ -z "$PODMAN_SERVER_PASSWORD" ]; then
    echo "❌ Error: Podman server credentials not set in .env"
    echo "   Please add PODMAN_SERVER_HOST, PODMAN_SERVER_USER, and PODMAN_SERVER_PASSWORD"
    exit 1
fi

echo "✓ Podman server credentials configured"
echo "  Host: $PODMAN_SERVER_HOST"
echo "  User: $PODMAN_SERVER_USER"

# Check network connectivity to podman server
echo ""
echo "Testing connection to $PODMAN_SERVER_HOST..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes ${PODMAN_SERVER_USER}@${PODMAN_SERVER_HOST} "podman --version" 2>/dev/null; then
    echo "✓ Can connect to podman server"
else
    echo "⚠️  Warning: Cannot connect to podman server via SSH"
    echo "   You may need to set up SSH keys or password authentication"
fi

echo ""
echo "Setup complete! You can now deploy FAIRweaver:"
echo "  Development: ./run-podman.sh dev start"
echo "  Production:  ./run-podman.sh prod start"
echo ""
echo "To manage pods:"
echo "  Status: ./run-podman.sh <dev|prod> status"
echo "  Logs:   ./run-podman.sh <dev|prod> logs"
echo "  Stop:   ./run-podman.sh <dev|prod> stop"