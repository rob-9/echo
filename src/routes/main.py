from flask import Blueprint, render_template, request, send_from_directory, jsonify
from flask_login import current_user
from src.models import Service, Bookmark
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    from src.utils.data_utils import create_test_services
    
    try:
        # Ensure we have test data
        if Service.query.count() == 0:
            create_test_services()
        
        services = Service.query.order_by(Service.created_at.desc()).limit(8).all()
    except Exception as e:
        print(f"Error loading services: {e}")
        services = []
        
    bookmarked_service_ids = []
    if current_user.is_authenticated:
        try:
            bookmarked_service_ids = [bookmark.service_id for bookmark in current_user.bookmarks]
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            
    return render_template('home.html', services=services, bookmarked_service_ids=bookmarked_service_ids)


@main_bp.route('/services')
def services():
    from src.utils.data_utils import create_test_services
    
    # Always create test services in serverless environment (in-memory DB)
    try:
        if Service.query.count() == 0:
            create_test_services()
    except Exception as e:
        # Log error but don't crash the app
        print(f"Error creating test services: {e}")
    
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
        query = query.order_by(Service.created_at.desc())
    else:  # newest
        query = query.order_by(Service.created_at.desc())

    services = query.all()
    
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


@main_bp.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    bookmarked_service_ids = []
    if current_user.is_authenticated:
        bookmarked_service_ids = [bookmark.service_id for bookmark in current_user.bookmarks]
    return render_template('service_detail.html', service=service, bookmarked_service_ids=bookmarked_service_ids)


@main_bp.route('/generated_images/<path:filename>')
def generated_image(filename):
    return send_from_directory('generated_images', filename)


@main_bp.route('/health')
def health():
    """Health check endpoint for Vercel"""
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel' if os.environ.get('VERCEL') else 'local',
        'database': 'in-memory' if os.environ.get('VERCEL') else 'file'
    })