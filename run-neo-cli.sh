#!/bin/bash

# Neo-CLI Runner Script
# This script helps you run Neo-CLI easily

NEO_CLI_DIR="/Users/kaushikk/Documents/hackathons/SpoonOS neo Hack/PredictX/neo-node/src/Neo.CLI/bin/Release/net10.0/osx-arm64/publish"
CONTRACT_DIR="/Users/kaushikk/Documents/hackathons/SpoonOS neo Hack/PredictX/contracts/bin/sc"

cd "$NEO_CLI_DIR"

echo "═══════════════════════════════════════════════════════════"
echo "  Neo-CLI Helper Script"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📍 Neo-CLI Location:"
echo "   $NEO_CLI_DIR"
echo ""
echo "📄 Contract Files:"
echo "   $CONTRACT_DIR"
echo ""

# Check if contract files exist
if [ -f "$CONTRACT_DIR/PredictXMarket.nef" ]; then
    echo "✅ Contract files found!"
    echo "   - PredictXMarket.nef"
    echo "   - PredictXMarket.manifest.json"
    echo ""
fi

echo "⚠️  IMPORTANT: Use './neo-cli' NOT 'neo'"
echo ""
echo "📋 Quick Commands:"
echo "   1. Start Neo-CLI:        ./neo-cli"
echo "   2. Create wallet:        neo> create wallet wallet.json"
echo "   3. Open wallet:          neo> open wallet wallet.json"
echo "   4. Show wallet:          neo> show wallet"
echo "   5. Deploy contract:      neo> deploy <nef> <manifest>"
echo ""
echo "🌐 TestNet Setup:"
echo "   - Get test GAS: https://neoline.io/faucet"
echo "   - Use your wallet address from 'create wallet'"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if running with arguments (non-interactive)
if [ $# -gt 0 ]; then
    echo "Running: ./neo-cli $@"
    ./neo-cli "$@"
    exit $?
fi

# Interactive mode
echo "Starting Neo-CLI in interactive mode..."
echo "Type 'help' for available commands, 'exit' to quit"
echo ""
echo "───────────────────────────────────────────────────────────"
echo ""

# Run Neo-CLI interactively
./neo-cli

