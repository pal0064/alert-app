#!/usr/bin/env bash
set -euo pipefail

# Usage: check_alert.sh [URL]
URL="${1:-http://localhost:8501/?api=check_alert}"

tmpbody=$(mktemp)
trap 'rm -f "$tmpbody"' EXIT

echo "Loading $URL with headless browser at $(date)"

# Detect OS and install browser if needed
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
else
  echo "::error::Unsupported OS: $OSTYPE"
  exit 1
fi

echo "Detected OS: $OS"

# Try to find an available browser on the runner
BROWSER=""
for cmd in chromium-browser google-chrome-stable google-chrome chromium; do
  if command -v "$cmd" >/dev/null 2>&1; then
    BROWSER="$cmd"
    break
  fi
done

# Check for macOS Chrome specifically
if [[ -z "$BROWSER" && "$OS" == "macos" ]]; then
  CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  if [[ -x "$CHROME_PATH" ]]; then
    BROWSER="$CHROME_PATH"
  fi
fi

# Install browser if not found
if [[ -z "$BROWSER" ]]; then
  echo "No browser found. Installing browser for $OS..."
  
  if [[ "$OS" == "linux" ]]; then
    # Ubuntu/Debian - install chromium
    echo "Installing chromium-browser on Ubuntu..."
    sudo apt-get update -qq
    sudo apt-get install -y chromium-browser
    BROWSER="chromium-browser"
  elif [[ "$OS" == "macos" ]]; then
    # macOS - check if Chrome already exists before installing
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [[ -x "$CHROME_PATH" ]]; then
      echo "Google Chrome already installed at $CHROME_PATH"
      BROWSER="$CHROME_PATH"
    else
      echo "Installing Google Chrome on macOS..."
      if ! command -v brew >/dev/null 2>&1; then
        echo "::error::Homebrew not found. Please install Homebrew first."
        exit 1
      fi
      brew install --cask google-chrome
      BROWSER="$CHROME_PATH"
    fi
  fi
  
  # Verify installation
  if ! command -v "$BROWSER" >/dev/null 2>&1 && [[ ! -x "$BROWSER" ]]; then
    echo "::error::Failed to install or find browser after installation"
    exit 1
  fi
fi

echo "Using browser: $BROWSER"

# Use headless browser to load the URL and wait for completion
echo "Loading page with headless browser..."
if "$BROWSER" --headless --disable-gpu --no-sandbox --virtual-time-budget=15000 "$URL" > /dev/null 2>&1; then
  echo "✅ Successfully loaded URL and waited for page completion"
else
  echo "::warning::First attempt failed, trying again..."
  if "$BROWSER" --headless --disable-gpu --no-sandbox --virtual-time-budget=20000 "$URL" > /dev/null 2>&1; then
    echo "✅ Successfully loaded URL on second attempt"
  else
    echo "::error::Failed to load URL after multiple attempts"
    exit 2
  fi
fi

exit 0
