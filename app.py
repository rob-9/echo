from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from ai_briefing import AIBriefingSystem
import logging
import json


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///echo.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Get API key from environment variable
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
if not app.config['GEMINI_API_KEY']:
    logger.error("GEMINI_API_KEY environment variable is not set")
    ai_briefing = None
else:
    try:
        # Log API key length for debugging (don't log the actual key)
        api_key = app.config['GEMINI_API_KEY']
        logger.info(f"Found API key with length: {len(api_key)}")
        
        ai_briefing = AIBriefingSystem(api_key)
        logger.info("AI briefing system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI briefing system: {str(e)}", exc_info=True)
        ai_briefing = None

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_seller = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    services = db.relationship('Service', backref='seller', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookmarked_by = db.relationship('Bookmark', backref='service', lazy=True)
    image_url = db.Column(db.String(200))

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='bookmarks')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    services = Service.query.order_by(Service.created_at.desc()).limit(8).all()
    # Get user's bookmarked services if logged in
    bookmarked_service_ids = []
    if current_user.is_authenticated:
        bookmarked_service_ids = [bookmark.service_id for bookmark in current_user.bookmarks]
    return render_template('home.html', services=services, bookmarked_service_ids=bookmarked_service_ids)

@app.route('/services')
def services():
    # Only create test services if none exist
    if Service.query.count() == 0:
        create_test_services()
    
    # Get filter parameters
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'newest')

    # Start with base query
    query = Service.query

    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if min_price is not None:
        query = query.filter(Service.price >= min_price)
    if max_price is not None:
        query = query.filter(Service.price <= max_price)

    # Apply sorting
    if sort == 'price-low':
        query = query.order_by(Service.price.asc())
    elif sort == 'price-high':
        query = query.order_by(Service.price.desc())
    elif sort == 'rating':
        # TODO: Implement rating sorting when rating system is added
        query = query.order_by(Service.created_at.desc())
    else:  # newest
        query = query.order_by(Service.created_at.desc())

    services = query.all()
    
    # Get user's bookmarked services if logged in
    bookmarked_service_ids = []
    if current_user.is_authenticated:
        bookmarked_service_ids = [bookmark.service_id for bookmark in current_user.bookmarks]
    
    return render_template('services.html', 
                         services=services, 
                         selected_category=category,
                         selected_min_price=min_price,
                         selected_max_price=max_price,
                         selected_sort=sort,
                         bookmarked_service_ids=bookmarked_service_ids)

@app.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    # Get user's bookmarked services if logged in
    bookmarked_service_ids = []
    if current_user.is_authenticated:
        bookmarked_service_ids = [bookmark.service_id for bookmark in current_user.bookmarks]
    return render_template('service_detail.html', service=service, bookmarked_service_ids=bookmarked_service_ids)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_seller = 'is_seller' in request.form

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_seller=is_seller
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_seller:
        # Get seller's services
        services = Service.query.filter_by(seller_id=current_user.id).all()
        return render_template('dashboard.html', services=services)
    else:
        # For buyers, show their bookmarked services
        bookmarked_services = Service.query.join(Bookmark).filter(Bookmark.user_id == current_user.id).all()
        return render_template('dashboard.html', bookmarked_services=bookmarked_services)

@app.route('/bookmark/<int:service_id>', methods=['POST'])
@login_required
def toggle_bookmark(service_id):
    service = Service.query.get_or_404(service_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, service_id=service_id).first()
    
    if bookmark:
        db.session.delete(bookmark)
        bookmarked = False
    else:
        bookmark = Bookmark(user_id=current_user.id, service_id=service_id)
        db.session.add(bookmark)
        bookmarked = True
    
    db.session.commit()
    return jsonify({'bookmarked': bookmarked})

# Updated AI Briefing Routes
@app.route('/api/briefing/next-question', methods=['POST'])
@login_required
def get_next_question():
    if not ai_briefing:
        logger.error("AI briefing system is not available - GEMINI_API_KEY may not be set")
        return jsonify({"error": "AI briefing system is not available. Please check server configuration."}), 503
        
    try:
        # Handle empty request body
        if not request.is_json:
            logger.warning("Request is not JSON, trying to proceed anyway")
            data = {}
        else:
            data = request.get_json() or {}
            
        user_input = data.get('user_input')
        logger.debug(f"Received user input: {user_input}")
        
        if not ai_briefing.service_title:
            logger.error("Service title not set before getting questions")
            return jsonify({"error": "Service title must be set before starting the briefing"}), 400
        
        try:
            question = ai_briefing.get_next_question(user_input)
            if not question:
                logger.error("No question generated from AI model")
                return jsonify({"question": "Could you tell me more about your project requirements?"}), 200
                
            return jsonify({"question": question})
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            return jsonify({"question": "What are your key requirements for this project?"}), 200
            
    except Exception as e:
        logger.error(f"Error in next-question endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/briefing/generate-images', methods=['POST'])
@login_required
def generate_images():
    if not ai_briefing:
        logger.error("AI briefing system is not available")
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        requirements = request.json.get('requirements')
        if not requirements:
            logger.error("No requirements provided in request")
            return jsonify({"error": "Requirements are needed to generate images"}), 400
            
        image_urls = ai_briefing.generate_images(requirements)
        return jsonify({'image_urls': image_urls})
    except Exception as e:
        logger.error(f"Error generating images: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error generating images: {str(e)}"}), 500

@app.route('/api/briefing/feedback', methods=['POST'])
@login_required
def process_feedback():
    if not ai_briefing:
        logger.error("AI briefing system is not available")
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        image_url = request.json.get('image_url')
        feedback = request.json.get('feedback')
        
        if not image_url or not feedback:
            logger.error("Missing image_url or feedback in request")
            return jsonify({"error": "Both image_url and feedback are required"}), 400
            
        response = ai_briefing.get_feedback(image_url, feedback)
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing feedback: {str(e)}"}), 500

@app.route('/api/briefing/set-service-title', methods=['POST'])
@login_required
def set_service_title():
    if not ai_briefing:
        logger.error("AI briefing system is not available - GEMINI_API_KEY may not be set")
        return jsonify({"error": "AI briefing system is not available. Please check server configuration."}), 503
        
    try:
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data or 'title' not in data:
            logger.error("No title provided in request")
            return jsonify({"error": "Title is required"}), 400
            
        title = data['title']
        if not title.strip():
            logger.error("Empty title provided")
            return jsonify({"error": "Title cannot be empty"}), 400
            
        try:
            ai_briefing.set_service_title(title)
            logger.info(f"Successfully set service title to: {title}")
            
            # Test the AI system right away to catch any early errors
            test_question = ai_briefing.get_next_question()
            if not test_question:
                logger.error("Failed to get initial question after setting service title")
                return jsonify({"error": "Unable to initialize the AI briefing with this title"}), 500
                
            return jsonify({"success": True, "first_question": test_question})
        except Exception as e:
            logger.error(f"Error setting service title: {str(e)}", exc_info=True)
            return jsonify({"error": f"Error setting service title: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error in set-service-title endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/contact-seller/<int:service_id>', methods=['POST'])
@login_required
def contact_seller(service_id):
    try:
        service = Service.query.get_or_404(service_id)
        seller = User.query.get_or_404(service.seller_id)
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message = data.get('message')
        if not message:
            return jsonify({"error": "Message is required"}), 400
            
        # Here you would typically:
        # 1. Send an email to the seller
        # 2. Store the message in a database
        # 3. Notify the seller
        
        # For now, we'll just return a success response
        return jsonify({
            "success": True,
            "message": "Message sent successfully",
            "seller": {
                "username": seller.username,
                "email": seller.email
            }
        })
        
    except Exception as e:
        logger.error(f"Error in contact-seller endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def create_test_services():
    # Check if test seller exists
    seller = User.query.filter_by(email='designer@example.com').first()
    
    if not seller:
        # Create a test seller if it doesn't exist
        seller = User(
            username='test_designer',
            email='designer@example.com',
            password_hash=generate_password_hash('test123'),
            is_seller=True
        )
        db.session.add(seller)
        db.session.commit()
    else:
        # Clear existing services for this seller
        Service.query.filter_by(seller_id=seller.id).delete()
        db.session.commit()

    # Create test services
    default_image = 'static/images/services/3d-animation.jpg'
    services = [
        # 2D Design Services
        Service(
            title='Custom Logo Design',
            description='Professional logo design with unlimited revisions, source files, and brand guidelines. Perfect for startups and businesses looking to establish their brand identity.',
            price=149,
            category='2d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Social Media Graphics Package',
            description='Complete set of social media graphics including profile pictures, cover photos, and post templates. Optimized for all major platforms.',
            price=89,
            category='2d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Print Design & Layout',
            description='Professional print design services for brochures, business cards, flyers, and more. Includes print-ready files and expert typography.',
            price=129,
            category='2d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        
        # 3D Design Services
        Service(
            title='3D Product Visualization',
            description='High-quality 3D product renders for e-commerce, marketing, and presentations. Includes multiple angles and lighting setups.',
            price=299,
            category='3d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Architectural Visualization',
            description='Photorealistic 3D architectural renders for real estate, interior design, and architectural projects. Includes day and night views.',
            price=399,
            category='3d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Character Design & Modeling',
            description='Custom 3D character design and modeling for games, animations, and digital art. Includes rigging and basic animations.',
            price=349,
            category='3d-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        
        # UI/UX Design Services
        Service(
            title='Website UI/UX Design',
            description='Modern and responsive website design with user experience optimization. Includes wireframes, mockups, and interactive prototypes.',
            price=499,
            category='ui-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Mobile App UI Design',
            description='Native mobile app UI design for iOS and Android. Includes user flows, wireframes, and interactive prototypes.',
            price=399,
            category='ui-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Dashboard Design',
            description='Custom dashboard and admin panel design with data visualization and user-friendly interfaces.',
            price=349,
            category='ui-design',
            seller_id=seller.id,
            image_url=default_image
        ),
        
        # Illustration Services
        Service(
            title='Custom Digital Illustration',
            description='Unique digital illustrations for books, websites, and marketing materials. Includes commercial usage rights.',
            price=199,
            category='illustration',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Character Illustration',
            description='Custom character illustrations for games, books, and branding. Includes multiple poses and expressions.',
            price=249,
            category='illustration',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Infographic Design',
            description='Professional infographic design for data visualization and information sharing. Includes research and content organization.',
            price=299,
            category='illustration',
            seller_id=seller.id,
            image_url=default_image
        ),
        
        # Animation Services
        Service(
            title='2D Animation',
            description='Custom 2D animations for explainer videos, social media, and marketing. Includes storyboard and voice-over integration.',
            price=499,
            category='animation',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='Motion Graphics',
            description='Professional motion graphics for intros, outros, and promotional videos. Includes custom music and sound effects.',
            price=399,
            category='animation',
            seller_id=seller.id,
            image_url=default_image
        ),
        Service(
            title='3D Animation',
            description='High-quality 3D animations for product showcases, architectural walkthroughs, and marketing videos.',
            price=599,
            category='animation',
            seller_id=seller.id,
            image_url=default_image
        )
    ]
    db.session.add_all(services)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)