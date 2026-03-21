#!/bin/bash
# setup.sh — interactive setup script for the Forumbee MCP server
#
# This script collects your Forumbee credentials and writes them to a .env
# file so the MCP server knows how to connect to your community.
#
# Note: This script has not been tested on Windows. Windows users should
# create the .env file manually by copying .env.example and filling it in.

set -e  # Stop immediately if any command fails

echo ""
echo "Forumbee MCP Server Setup"
echo "========================="
echo ""

# Check that uv is installed before going any further
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Install it from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Prompt for the Forumbee community domain (e.g. thepondhoa.forumbee.com)
read -p "Enter your Forumbee community domain (e.g. thepondhoa.forumbee.com): " domain

# Prompt for the API token — the input is hidden so it doesn't appear on screen
read -s -p "Enter your Forumbee API token: " token
echo ""  # Print a newline after the hidden input

# Basic validation — make sure neither field was left blank
if [ -z "$domain" ]; then
    echo "Error: domain cannot be empty."
    exit 1
fi
if [ -z "$token" ]; then
    echo "Error: API token cannot be empty."
    exit 1
fi

# Determine the directory this script lives in so we can write .env next to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Warn if a .env already exists and ask before overwriting
if [ -f "$ENV_FILE" ]; then
    read -p ".env already exists. Overwrite? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted. Existing .env was not changed."
        exit 0
    fi
fi

# Write the .env file
cat > "$ENV_FILE" <<EOF
FORUMBEE_DOMAIN=$domain
FORUMBEE_API_TOKEN=$token
EOF

echo ""
echo ".env written to $ENV_FILE"
echo ""

# Install dependencies via uv
echo "Installing dependencies..."
uv sync --project "$SCRIPT_DIR"
echo ""
echo "Setup complete. You can now configure your MCP client to run the server."
echo "See the README for Claude Code and Claude Desktop configuration examples."
echo ""
