# Robert's Conversational Agent Makefile

.PHONY: help install dev start test clean

help:  ## Show this help message
	@echo "Robert's Conversational Reception Agent"
	@echo "======================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	python -m pip install -U pip
	pip install -e .

dev:  ## Run in development mode
	python agent.py dev

start:  ## Run in production mode
	python agent.py start

test:  ## Test the agent (when implemented)
	python -m pytest tests/ -v

clean:  ## Clean up cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Quick test scenarios
test-insurance:  ## Quick test for insurance scenario
	@echo "Testing insurance inquiry flow..."
	@echo "Expected: Natural conversation about insurance comparison"

test-solar:  ## Quick test for solar scenario
	@echo "Testing solar support flow..."
	@echo "Expected: Technical diagnostics and specialist routing"

test-interruption:  ## Quick test for interruption handling
	@echo "Testing interruption handling..."
	@echo "Expected: Graceful stop and natural continuation"