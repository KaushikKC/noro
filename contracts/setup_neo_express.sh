#!/bin/bash
# Setup script for Neo Express local blockchain

set -e

echo "=========================================="
echo "Neo Express Setup for Local Testing"
echo "=========================================="
echo ""

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "❌ .NET SDK not found. Please install .NET SDK 8.0+ first:"
    echo "   https://dotnet.microsoft.com/download"
    exit 1
fi

echo "✅ .NET SDK found: $(dotnet --version)"
echo ""

# Check if Neo Express is installed
if ! command -v neo-express &> /dev/null; then
    echo "📦 Installing Neo Express..."
    dotnet tool install --global Neo.Express
    echo "✅ Neo Express installed"
else
    echo "✅ Neo Express already installed: $(neo-express --version)"
fi

echo ""

# Create Neo Express instance if it doesn't exist
if [ ! -f "predictx.neo-express.json" ]; then
    echo "📝 Creating Neo Express instance..."
    neo-express create predictx
    echo "✅ Neo Express instance created: predictx.neo-express.json"
else
    echo "✅ Neo Express instance already exists: predictx.neo-express.json"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the local blockchain:"
echo "  neo-express run predictx"
echo ""
echo "To test the contract:"
echo "  python3 test_contract_simple.py --rpc-url http://localhost:20332 --contract-hash <CONTRACT_HASH>"
echo ""
echo "Note: You'll need to deploy the contract first using NeoNova.space or Neo-CLI"
echo "      with the local blockchain running."

