from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import Config
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize SocketIO
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',  # Use threading mode for better compatibility
                     logger=True,
                     engineio_logger=True)
    
    with app.app_context():
        # Import blueprints
        from app.auth import auth
        from app.routes import main
        
        # Register blueprints
        app.register_blueprint(auth, url_prefix='/auth')
        app.register_blueprint(main)
        
        return app

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return False
    emit('connected', {'status': 'connected'}, room=str(current_user.id))

@socketio.on('join')
def handle_join(data):
    from flask_login import current_user
    if current_user.is_authenticated:
        room = str(current_user.id)
        join_room(room)
        emit('joined', {'room': room}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    pass

def send_notification(user_id, notification_data):
    """Helper function to send notification via WebSocket"""
    room = str(user_id)
    emit('notification', notification_data, room=room, namespace='/')