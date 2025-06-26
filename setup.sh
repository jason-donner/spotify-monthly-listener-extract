#!/bin/bash

# Spotify Monthly Listener Extract - Production Setup Script
# This script helps prepare your app for production deployment

echo "🎵 Spotify Monthly Listener Extract - Production Setup"
echo "=================================================="

# Check if running in production environment
if [[ "$PORT" != "" ]] || [[ "$AWS_REGION" != "" ]] || [[ "$HEROKU_APP_NAME" != "" ]]; then
    echo "✅ Production environment detected"
    
    # Create necessary directories
    mkdir -p data/results
    mkdir -p logs
    
    # Initialize empty data files if they don't exist
    if [ ! -f "data/results/spotify-monthly-listeners-master.json" ]; then
        echo "[]" > data/results/spotify-monthly-listeners-master.json
        echo "📄 Created empty master data file"
    fi
    
    if [ ! -f "data/results/spotify-followed-artists-master.json" ]; then
        echo "[]" > data/results/spotify-followed-artists-master.json
        echo "📄 Created empty followed artists file"
    fi
    
    if [ ! -f "artist_suggestions.json" ]; then
        echo "[]" > artist_suggestions.json
        echo "💡 Created empty suggestions file"
    fi
    
    if [ ! -f "artist_blacklist.json" ]; then
        echo "[]" > artist_blacklist.json
        echo "🚫 Created empty blacklist file"
    fi
    
    echo "✅ Production setup complete!"
else
    echo "ℹ️  Development environment detected"
fi

# Verify environment variables
echo ""
echo "🔍 Checking environment variables..."

required_vars=("FLASK_SECRET_KEY" "ADMIN_PASSWORD" "SPOTIPY_CLIENT_ID" "SPOTIPY_CLIENT_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    else
        echo "✅ $var is set"
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo ""
    echo "❌ Missing required environment variables:"
    printf "   - %s\n" "${missing_vars[@]}"
    echo ""
    echo "Please set these in your deployment platform's environment variables section."
    exit 1
else
    echo "✅ All required environment variables are set!"
fi

echo ""
echo "🚀 Ready for deployment!"
