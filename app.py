from dotenv import load_dotenv
load_dotenv()

import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config.config import config
from src.models import db, User
from src.routes import main_bp, auth_bp, api_bp
from src.routes.websocket_routes import register_websocket_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Determine config
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    if config_name not in config:
        config_name = 'default'
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize SocketIO for real-time communication
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    
    # Register WebSocket handlers
    register_websocket_handlers(socketio)
    
    # Initialize app configuration
    config[config_name].init_app(app)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)