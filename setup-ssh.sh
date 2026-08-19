#!/bin/bash

# SSH Key Setup for Podman Remote Access
# Run this script to set up passwordless SSH access to remote podman server

set -e

REMOTE_USER="brizuela"
REMOTE_HOST="dmz-web-140.ipk-gatersleben.de"
KEY_TYPE="${KEY_TYPE:-ed25519}"
KEY_COMMENT="fairweaver@local"

echo "SSH Key Setup for Podman Remote Access"
echo "========================================"
echo ""

# Check if SSH key already exists
if [ -f "$HOME/.ssh/id_${KEY_TYPE}" ]; then
    echo "✓ SSH key found: $HOME/.ssh/id_${KEY_TYPE}"
    read -p "Use existing key? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" != "y" ]; then
        echo "Cancelling..."
        exit 1
    fi
else
    echo "Generating new SSH key ($KEY_TYPE)..."
    ssh-keygen -t "$KEY_TYPE" -C "$KEY_COMMENT"
    echo "✓ SSH key generated"
fi

# Test SSH connection
echo ""
echo "Testing SSH connection to ${REMOTE_USER}@${REMOTE_HOST}..."

if ssh -o ConnectTimeout=10 -o BatchMode=no "${REMOTE_USER}@${REMOTE_HOST}" "echo 'Connected to remote server'" 2>&1 | grep -q "Connected to remote server"; then
    echo "⚠️  Password authentication is working"
    echo "   For passwordless access, we'll copy your public key"

    # Copy public key to remote server
    echo ""
    echo "Copying SSH public key to remote server..."
    if ssh-copy-id -i "$HOME/.ssh/id_${KEY_TYPE}.pub" "${REMOTE_USER}@${REMOTE_HOST}"; then
        echo "✓ SSH public key copied successfully"
    else
        echo "❌ Failed to copy SSH key"
        echo "   Please manually copy the public key:"
        echo "   ssh-copy-id -i $HOME/.ssh/id_${KEY_TYPE}.pub ${REMOTE_USER}@${REMOTE_HOST}"
        exit 1
    fi

    # Test passwordless authentication
    echo ""
    echo "Testing passwordless SSH connection..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "${REMOTE_USER}@${REMOTE_HOST}" "podman --version"; then
        echo "✓ Passwordless SSH access configured"
        echo "✓ Podman is available on remote server: $(ssh ${REMOTE_USER}@${REMOTE_HOST} 'podman --version')"
    else
        echo "❌ Passwordless SSH still not working"
        echo "   You may need to manually configure SSH agent or check permissions"
        exit 1
    fi

else
    echo "❌ Cannot connect to remote server"
    echo "   Please check:"
    echo "   1. Remote server is reachable: ping ${REMOTE_HOST}"
    echo "   2. Username is correct: ${REMOTE_USER}@${REMOTE_HOST}"
    echo "   3. Password is correct (you may be prompted for it)"
    exit 1
fi

echo ""
echo "Setup complete! You can now use passwordless SSH for:"
echo "  - Remote Podman management"
echo "  - Automated deployment via ./run-podman.sh"
echo ""
echo "To test SSH connection:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST}"