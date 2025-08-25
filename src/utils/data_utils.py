from werkzeug.security import generate_password_hash
from src.models import db, User, Service


def create_test_services():
    """Create test services for the application"""
    seller = User.query.filter_by(email='designer@example.com').first()
    
    if not seller:
        seller = User(
            username='test_designer',
            email='designer@example.com',
            password_hash=generate_password_hash('test123'),
            is_seller=True
        )
        db.session.add(seller)
        db.session.commit()
    else:
        Service.query.filter_by(seller_id=seller.id).delete()
        db.session.commit()

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