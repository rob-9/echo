from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db, User, Service, Bookmark

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_seller = 'is_seller' in request.form

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_seller=is_seller
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Invalid username or password')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_seller:
        services = Service.query.filter_by(seller_id=current_user.id).all()
        return render_template('dashboard.html', services=services)
    else:
        bookmarked_services = Service.query.join(Bookmark).filter(Bookmark.user_id == current_user.id).all()
        return render_template('dashboard.html', bookmarked_services=bookmarked_services)


@auth_bp.route('/bookmark/<int:service_id>', methods=['POST'])
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