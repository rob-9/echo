import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///echo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else 'static/uploads'
    
    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Generated images directory - use tmp for serverless
    GENERATED_IMAGES_DIR = '/tmp/generated_images' if os.environ.get('VERCEL') else 'generated_images'
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        try:
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(Config.GENERATED_IMAGES_DIR, exist_ok=True)
        except (OSError, PermissionError):
            # In serverless environments, we might not have write permissions
            pass

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}