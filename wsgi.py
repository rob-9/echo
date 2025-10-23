import os
import sys
import logging

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Configure logging for serverless
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Create Flask app instance for Vercel
    config_name = 'production' if os.environ.get('VERCEL') else 'development'
    app = create_app(config_name=config_name)
    
    # Initialize database in serverless environment
    if os.environ.get('VERCEL'):
        with app.app_context():
            from src.models import db
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
                
    logger.info(f"App created successfully with config: {config_name}")
    
except Exception as e:
    logger.error(f"Error creating app: {e}")
    raise

# For Vercel deployment
handler = app

if __name__ == "__main__":
    app.run(debug=True)