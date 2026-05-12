#!/usr/bin/env python3
"""
Auth Service - Main Entry Point
AI University FAQ Assistant - Authentication & Authorization Service
"""

import os
import logging
from app import create_app

# Get environment
env = os.getenv('FLASK_ENV', 'development')

# Create application
app = create_app()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    logger.info(f"Starting Auth Service in {env} mode...")
    
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Running on http://{host}:{port}")
    
    app.run(host=host, port=port, debug=debug)
