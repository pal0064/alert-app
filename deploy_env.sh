#!/bin/bash

# Deploy environment variables from .env to Vercel
# Usage: ./deploy_env.sh [environment]
# Environment: production (default), preview, development

ENVIRONMENT=${1:-production}
ENV_FILE="backend/.env"

echo "Deploying environment variables to Vercel ($ENVIRONMENT)..."

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ $ENV_FILE file not found"
    exit 1
fi

# Check if project is linked to Vercel
echo "Checking Vercel project link..."
cd backend
if ! vercel ls > /dev/null 2>&1; then
    echo "Project not linked to Vercel. Linking to existing alert-app project..."
    vercel link --project=alert-app --yes
fi
cd ..

# Source the .env file to load variables
set -a
source "$ENV_FILE"
set +a

# Set each variable individually
if [ -n "$WEBHOOK_URL" ]; then
    echo "Setting WEBHOOK_URL..."
    cd backend && echo "$WEBHOOK_URL" | vercel env add WEBHOOK_URL "$ENVIRONMENT" --force && cd ..
    if [ $? -eq 0 ]; then
        echo "✅ WEBHOOK_URL set"
    else
        echo "❌ Failed to set WEBHOOK_URL"
    fi
else
    echo "⚠️  WEBHOOK_URL not found in .env"
fi

if [ -n "$CHARGER_STATUS_URL" ]; then
    echo "Setting CHARGER_STATUS_URL..."
    cd backend && echo "$CHARGER_STATUS_URL" | vercel env add CHARGER_STATUS_URL "$ENVIRONMENT" --force && cd ..
    if [ $? -eq 0 ]; then
        echo "✅ CHARGER_STATUS_URL set"
    else
        echo "❌ Failed to set CHARGER_STATUS_URL"
    fi
else
    echo "⚠️  CHARGER_STATUS_URL not found in .env"
fi

if [ -n "$SCHEDULE_API_KEY" ]; then
    echo "Setting SCHEDULE_API_KEY..."
    cd backend && echo "$SCHEDULE_API_KEY" | vercel env add SCHEDULE_API_KEY "$ENVIRONMENT" --force && cd ..
    if [ $? -eq 0 ]; then
        echo "✅ SCHEDULE_API_KEY set"
    else
        echo "❌ Failed to set SCHEDULE_API_KEY"
    fi
else
    echo "⚠️  SCHEDULE_API_KEY not found in .env"
fi

if [ -n "$SCHEDULE_JOB_ID" ]; then
    echo "Setting SCHEDULE_JOB_ID..."
    cd backend && echo "$SCHEDULE_JOB_ID" | vercel env add SCHEDULE_JOB_ID "$ENVIRONMENT" --force && cd ..
    if [ $? -eq 0 ]; then
        echo "✅ SCHEDULE_JOB_ID set"
    else
        echo "❌ Failed to set SCHEDULE_JOB_ID"
    fi
else
    echo "⚠️  SCHEDULE_JOB_ID not found in .env"
fi

echo ""
echo "Environment variables deployment complete!"
echo "You can verify by running: vercel env ls"