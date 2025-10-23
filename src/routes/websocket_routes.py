from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from src.services.ai_service import AIBriefingService
import logging
import asyncio
import threading

logger = logging.getLogger(__name__)

def register_websocket_handlers(socketio):
    """Register WebSocket event handlers for real-time image generation"""
    
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            logger.info(f"User {current_user.username} connected via WebSocket")
            emit('status', {'message': 'Connected to real-time image generation'})
        else:
            logger.warning("Unauthenticated user attempted WebSocket connection")
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            logger.info(f"User {current_user.username} disconnected from WebSocket")
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """Join a specific briefing session room for real-time updates"""
        if not current_user.is_authenticated:
            return
            
        session_id = data.get('session_id', f"user_{current_user.id}")
        join_room(session_id)
        logger.info(f"User {current_user.username} joined session {session_id}")
        emit('status', {'message': f'Joined session {session_id}'})
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """Leave a briefing session room"""
        if not current_user.is_authenticated:
            return
            
        session_id = data.get('session_id', f"user_{current_user.id}")
        leave_room(session_id)
        logger.info(f"User {current_user.username} left session {session_id}")
    
    @socketio.on('start_realtime_generation')
    def handle_realtime_generation(data):
        """Start real-time image generation with live updates"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        try:
            requirements = data.get('requirements')
            session_id = data.get('session_id', f"user_{current_user.id}")
            
            if not requirements:
                emit('error', {'message': 'Requirements needed for image generation'})
                return
            
            # Emit generation started
            emit('generation_started', {
                'message': 'Starting real-time image generation...',
                'session_id': session_id
            }, room=session_id)
            
            # Start generation in background thread
            def generate_images_async():
                try:
                    ai_service = AIBriefingService()
                    
                    # Emit progress updates
                    socketio.emit('generation_progress', {
                        'status': 'Initializing AWS Bedrock connection...',
                        'progress': 20
                    }, room=session_id)
                    
                    socketio.emit('generation_progress', {
                        'status': 'Processing requirements with AI...',
                        'progress': 40
                    }, room=session_id)
                    
                    # Generate images
                    image_urls = ai_service.generate_images(requirements)
                    
                    socketio.emit('generation_progress', {
                        'status': 'Generating concept images...',
                        'progress': 80
                    }, room=session_id)
                    
                    # Convert to web URLs
                    web_urls = []
                    for url in image_urls:
                        if url.startswith("generated_images/"):
                            web_urls.append("/" + url)
                        else:
                            web_urls.append(url)
                    
                    # Emit completion
                    socketio.emit('generation_complete', {
                        'images': web_urls,
                        'progress': 100,
                        'message': 'Image generation completed!'
                    }, room=session_id)
                    
                except Exception as e:
                    logger.error(f"Error in real-time generation: {str(e)}")
                    socketio.emit('generation_error', {
                        'error': str(e),
                        'message': 'Failed to generate images'
                    }, room=session_id)
            
            # Start background thread
            thread = threading.Thread(target=generate_images_async)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Error starting real-time generation: {str(e)}")
            emit('error', {'message': f'Failed to start generation: {str(e)}'})
    
    @socketio.on('realtime_feedback')
    def handle_realtime_feedback(data):
        """Handle real-time feedback on generated images"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        try:
            image_url = data.get('image_url')
            feedback = data.get('feedback')
            session_id = data.get('session_id', f"user_{current_user.id}")
            
            if not image_url or not feedback:
                emit('error', {'message': 'Image URL and feedback required'})
                return
            
            def process_feedback_async():
                try:
                    ai_service = AIBriefingService()
                    
                    # Emit feedback processing started
                    socketio.emit('feedback_processing', {
                        'message': 'Processing your feedback...',
                        'progress': 25
                    }, room=session_id)
                    
                    # Process feedback
                    response = ai_service.get_feedback(image_url, feedback)
                    
                    socketio.emit('feedback_processing', {
                        'message': 'Generating improved version...',
                        'progress': 75
                    }, room=session_id)
                    
                    # Generate new image based on feedback
                    new_requirements = response + " " + feedback
                    new_images = ai_service.generate_images(new_requirements)
                    
                    new_image_url = None
                    if new_images:
                        new_image_url = new_images[0]
                        if new_image_url.startswith("generated_images/"):
                            new_image_url = "/" + new_image_url
                    
                    # Emit results
                    socketio.emit('feedback_complete', {
                        'response': response,
                        'new_image_url': new_image_url,
                        'progress': 100
                    }, room=session_id)
                    
                except Exception as e:
                    logger.error(f"Error processing real-time feedback: {str(e)}")
                    socketio.emit('feedback_error', {
                        'error': str(e),
                        'message': 'Failed to process feedback'
                    }, room=session_id)
            
            # Start background thread
            thread = threading.Thread(target=process_feedback_async)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Error handling real-time feedback: {str(e)}")
            emit('error', {'message': f'Failed to process feedback: {str(e)}'})