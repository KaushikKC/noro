#!/bin/bash

# noro Agents Setup Script

echo "🚀 Setting up noro SpoonOS Agents..."

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

# Install SpoonOS SDK
echo "📥 Installing SpoonOS SDK..."
pip install spoon-ai-sdk

# Install other dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.template .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY)"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the orchestrator: python orchestrator.py"
echo ""

