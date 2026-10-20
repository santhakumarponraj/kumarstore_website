import functools
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_db, execute_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    """Decorator to require login for specific routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """Decorator to require admin role."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Admin login required.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('user_role') != 'admin':
            flash('Access denied: Administrator privileges required.', 'danger')
            return redirect(url_for('shop.index'))
        return view(**kwargs)
    return wrapped_view

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('shop.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        requested_mode = request.form.get('mode', 'b2c') # b2c or b2b tab preference

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html', requested_mode=requested_mode)

        user = query_db(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            # Establish session
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['view_mode'] = 'b2b' if user['role'] == 'b2b' else 'b2c'

            # Merge guest cart to user cart if session_id existed
            guest_session_id = request.cookies.get('guest_session_id')
            if guest_session_id:
                execute_db(
                    "UPDATE cart SET user_id = %s, session_id = NULL WHERE session_id = %s",
                    (user['id'], guest_session_id)
                )

            flash(f"Welcome back, {user['name']}!", 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('shop.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html', requested_mode=request.args.get('mode', 'b2c'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('shop.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        account_type = request.form.get('account_type', 'b2c') # 'b2c' or 'b2b'
        
        # B2B specific fields
        company_name = request.form.get('company_name', '').strip() if account_type == 'b2b' else None
        gstin = request.form.get('gstin', '').strip().upper() if account_type == 'b2b' else None
        
        # Address fields
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', 'Tamil Nadu').strip()
        pincode = request.form.get('pincode', '').strip()

        # Validation
        if not name or not email or not password or not phone:
            flash('All primary fields (Name, Email, Password, Phone) are required.', 'danger')
            return render_template('auth/register.html', account_type=account_type)

        if account_type == 'b2b' and not company_name:
            flash('Company / Trade Name is mandatory for B2B wholesale accounts.', 'danger')
            return render_template('auth/register.html', account_type='b2b')

        # Check existing user
        existing = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if existing:
            flash('An account with this email already exists. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        password_hash = generate_password_hash(password)
        role = 'b2b' if account_type == 'b2b' else 'b2c'
        is_b2b_verified = True if role == 'b2b' else False

        user_id = execute_db(
            """INSERT INTO users 
               (name, email, password_hash, phone, role, company_name, gstin, is_b2b_verified, address, city, state, pincode)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, email, password_hash, phone, role, company_name, gstin, is_b2b_verified, address, city, state, pincode),
            lastrowid=True
        )

        # Log the user in
        session.clear()
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = role
        session['view_mode'] = role

        flash(f"Account successfully created! You are logged in as {role.upper()}.", 'success')
        return redirect(url_for('shop.index'))

    return render_template('auth/register.html', account_type=request.args.get('mode', 'b2c'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('shop.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        gstin = request.form.get('gstin', '').strip().upper()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()

        execute_db(
            """UPDATE users 
               SET name = %s, phone = %s, company_name = %s, gstin = %s, address = %s, city = %s, state = %s, pincode = %s
               WHERE id = %s""",
            (name, phone, company_name, gstin, address, city, state, pincode, user['id'])
        )
        session['user_name'] = name
        flash('Profile details updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    # Load user's recent orders
    orders = query_db(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 10",
        (user['id'],)
    )

    return render_template('auth/profile.html', user=user, orders=orders)

@auth_bp.route('/upgrade-b2b', methods=['POST'])
@login_required
def upgrade_b2b():
    company_name = request.form.get('company_name', '').strip()
    gstin = request.form.get('gstin', '').strip().upper()

    if not company_name:
        flash('Company / Trade Name is required to activate B2B Wholesale account.', 'danger')
        return redirect(url_for('auth.profile'))

    execute_db(
        """UPDATE users 
           SET role = 'b2b', company_name = %s, gstin = %s, is_b2b_verified = TRUE 
           WHERE id = %s""",
        (company_name, gstin, session['user_id'])
    )
    session['user_role'] = 'b2b'
    session['view_mode'] = 'b2b'
    flash('Congratulations! Your account has been upgraded to B2B Wholesale status.', 'success')
    return redirect(url_for('auth.profile'))
