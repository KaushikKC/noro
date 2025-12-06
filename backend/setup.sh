#!/bin/bash

# PredictX Backend Setup Script

echo "🚀 Setting up PredictX Backend API..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12 or later."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Neo Blockchain Configuration
NEO_RPC_URL=http://localhost:20332
NEO_NETWORK=testnet
NEO_CONTRACT_HASH=0x1974aac54640ec80413e2229003b617daf849a13

# Database
DATABASE_URL=sqlite:///./predictx.db

# LLM API Keys (for agents)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
EOF
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the server: uvicorn main:app --reload"
echo ""

