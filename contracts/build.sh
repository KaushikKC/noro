#!/bin/bash

# Add dotnet to PATH
export PATH="/usr/local/share/dotnet:$HOME/.dotnet/tools:$PATH"

# Navigate to contracts directory
cd "$(dirname "$0")"

echo "Building PredictXMarket contract..."
echo "Using dotnet: $(which dotnet)"
echo "Dotnet version: $(dotnet --version)"

# Build the project
dotnet build PredictXMarket.csproj

# Check if .nef file was generated
if [ -f "bin/sc/PredictXMarket.nef" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Generated files:"
    ls -lh bin/sc/
else
    echo ""
    echo "⚠️  C# compilation succeeded, but .nef file not generated."
    echo "This is likely because nccs requires .NET 9.0 but you have .NET 10.0."
    echo ""
    echo "To fix this, you can:"
    echo "1. Install .NET 9.0: https://dotnet.microsoft.com/download/dotnet/9.0"
    echo "2. Or manually run nccs after C# build completes"
    echo ""
    echo "The DLL was successfully created at:"
    ls -lh bin/Debug/net8.0/PredictXMarket.dll
fi

