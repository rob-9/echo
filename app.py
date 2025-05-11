from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from ai_briefing import AIBriefingSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///echo.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')  # Get API key from environment variable

# Initialize AI Briefing System
ai_briefing = AIBriefingSystem(app.config['GEMINI_API_KEY'])

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
    return render_template('home.html', services=services)

@app.route('/services')
def services():
    # Get all services if none exist
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
    return render_template('services.html', 
                         services=services, 
                         selected_category=category,
                         selected_min_price=min_price,
                         selected_max_price=max_price,
                         selected_sort=sort)

@app.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    return render_template('service_detail.html', service=service)

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

@app.route('/api/briefing/next-question', methods=['POST'])
@login_required
def get_next_question():
    user_input = request.json.get('user_input')
    question = ai_briefing.get_next_question(user_input)
    return jsonify({'question': question})

@app.route('/api/briefing/generate-images', methods=['POST'])
@login_required
def generate_images():
    requirements = request.json.get('requirements')
    image_urls = ai_briefing.generate_images(requirements)
    return jsonify({'image_urls': image_urls})

@app.route('/api/briefing/feedback', methods=['POST'])
@login_required
def process_feedback():
    image_url = request.json.get('image_url')
    feedback = request.json.get('feedback')
    response = ai_briefing.get_feedback(image_url, feedback)
    return jsonify({'response': response})

def create_test_services():
    # Create a test seller
    seller = User(
        username='test_designer',
        email='designer@example.com',
        password_hash=generate_password_hash('test123'),
        is_seller=True
    )
    db.session.add(seller)
    db.session.commit()

    # Create test services
    services = [
        # Graphics & Design Services
        Service(
            title='Modern UI/UX Design',
            description='Create stunning user interfaces with modern design principles and intuitive user experiences.',
            price=109,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Brand Identity Package',
            description='Complete brand identity design including logo, color palette, and brand guidelines.',
            price=199,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Mobile App Design',
            description='Professional mobile app UI/UX design with wireframes and interactive prototypes.',
            price=99,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='3D Product Visualization',
            description='High-quality 3D product renders and animations for marketing and presentations.',
            price=49,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Web Design Package',
            description='Complete website design with responsive layouts and modern aesthetics.',
            price=99,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Social Media Design',
            description='Custom social media graphics and templates for consistent brand presence.',
            price=79,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Custom Illustration',
            description='Unique hand-drawn illustrations for your brand or project.',
            price=149,
            category='graphics-design',
            seller_id=seller.id
        ),
        Service(
            title='Print Design',
            description='Professional print materials including business cards, brochures, and flyers.',
            price=89,
            category='graphics-design',
            seller_id=seller.id
        ),

        # Digital Marketing Services
        Service(
            title='SEO Optimization',
            description='Improve your website ranking with comprehensive SEO strategies.',
            price=299,
            category='digital-marketing',
            seller_id=seller.id
        ),
        Service(
            title='Social Media Management',
            description='Full-service social media management and content creation.',
            price=399,
            category='digital-marketing',
            seller_id=seller.id
        ),
        Service(
            title='PPC Campaign Management',
            description='Expert management of your Google Ads and social media advertising campaigns.',
            price=499,
            category='digital-marketing',
            seller_id=seller.id
        ),
        Service(
            title='Email Marketing',
            description='Design and implement effective email marketing campaigns.',
            price=199,
            category='digital-marketing',
            seller_id=seller.id
        ),
        Service(
            title='Content Strategy',
            description='Develop a comprehensive content strategy for your brand.',
            price=349,
            category='digital-marketing',
            seller_id=seller.id
        ),

        # Writing & Translation Services
        Service(
            title='Blog Writing',
            description='Engaging blog posts optimized for SEO and reader engagement.',
            price=79,
            category='writing-translation',
            seller_id=seller.id
        ),
        Service(
            title='Technical Writing',
            description='Clear and concise technical documentation and manuals.',
            price=149,
            category='writing-translation',
            seller_id=seller.id
        ),
        Service(
            title='Website Content',
            description='Compelling website copy that converts visitors into customers.',
            price=199,
            category='writing-translation',
            seller_id=seller.id
        ),
        Service(
            title='Translation Services',
            description='Professional translation services in multiple languages.',
            price=129,
            category='writing-translation',
            seller_id=seller.id
        ),

        # Video & Animation Services
        Service(
            title='2D Animation',
            description='Custom 2D animations for your brand or project.',
            price=299,
            category='video-animation',
            seller_id=seller.id
        ),
        Service(
            title='Video Editing',
            description='Professional video editing and post-production services.',
            price=199,
            category='video-animation',
            seller_id=seller.id
        ),
        Service(
            title='Motion Graphics',
            description='Eye-catching motion graphics for your marketing materials.',
            price=249,
            category='video-animation',
            seller_id=seller.id
        ),
        Service(
            title='3D Animation',
            description='High-quality 3D animations for your projects.',
            price=399,
            category='video-animation',
            seller_id=seller.id
        )
    ]
    db.session.add_all(services)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 