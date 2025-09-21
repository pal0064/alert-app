# Makefile for EV Charger Alert App (Frontend & Backend)

.PHONY: help install install-api install-streamlit dev streamlit deploy preview logs env-check clean setup

# Default target
help:
	@echo "EV Charger Alert App - Frontend & Backend"
	@echo ""
	@echo "Available commands:"
	@echo "  install          - Install all dependencies for development"
	@echo "  install-api      - Install only FastAPI dependencies"
	@echo "  install-streamlit - Install only Streamlit dependencies"
	@echo "  dev              - Run FastAPI development server locally"
	@echo "  streamlit        - Run Streamlit frontend app"
	@echo "  deploy           - Deploy backend to Vercel with environment variables"
	@echo "  preview          - Deploy backend to Vercel preview"
	@echo "  logs             - View Vercel deployment logs"
	@echo "  clean            - Clean build artifacts"
	@echo "  setup            - Initial setup (install Vercel CLI)"
	@echo ""

# Install dependencies
install:
	@echo "Installing all dependencies for development..."
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pip install -r requirements.txt
	@echo "All dependencies installed!"

# Install only FastAPI dependencies
install-api:
	@echo "Installing FastAPI dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "FastAPI dependencies installed!"

# Install only Streamlit dependencies
install-streamlit:
	@echo "Installing Streamlit dependencies..."
	cd frontend && pip install -r requirements.txt
	@echo "Streamlit dependencies installed!"

# Install Vercel CLI
setup:
	@echo "Installing Vercel CLI..."
	npm install -g vercel
	@echo "Vercel CLI installed!"
	@echo "Run 'vercel login' to authenticate"

# Run development server
dev:
	@echo "Starting FastAPI development server..."
	cd backend && uvicorn api.index:app --reload --host 0.0.0.0 --port 8000

# Run Streamlit app
streamlit:
	@echo "Starting Streamlit frontend app..."
	cd frontend && streamlit run streamlit_app.py --server.port 8501

# Deploy to Vercel production with environment variables
deploy:
	@echo "Deploying backend to Vercel production..."
	@echo "Linking to existing alert-app project..."
	@cd backend && vercel link --project=alert-app --yes || true
	@echo "Setting environment variables from .env file..."
	@chmod +x deploy_env.sh
	@./deploy_env.sh production
	@echo "Deploying application..."
	cd backend && vercel --prod
	@echo "Deployment complete!"
	@echo "Check your app at your Vercel URL"

# Deploy to Vercel preview
preview:
	@echo "Deploying backend to Vercel preview..."
	cd backend && vercel
	@echo "Preview deployment complete!"

# View deployment logs
logs:
	@echo "Fetching Vercel logs..."
	vercel logs

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	rm -rf backend/__pycache__
	rm -rf frontend/__pycache__
	rm -rf .vercel
	rm -rf backend/*.pyc
	rm -rf frontend/*.pyc
	find . -type d -name "__pycache__" -delete
	@echo "Cleanup complete!"