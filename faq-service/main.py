#!/usr/bin/env python3
import os
import logging
from app import create_app

env = os.getenv('FLASK_ENV', 'development')
app = create_app()

if __name__ == '__main__':
    logging.info(f"Starting FAQ Service in {env} mode...")
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5001)
    debug = app.config.get('DEBUG', False)
    
    app.run(host=host, port=port, debug=debug)
