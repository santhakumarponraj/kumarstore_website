import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from blueprints.auth.routes import admin_required
from db import query_db, execute_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Apply admin_required to all routes in admin_bp
@admin_bp.before_request
def check_admin():
    if 'user_id' not in session:
        flash('Admin login required.', 'danger')
        return redirect(url_for('auth.login', next=request.url))
    if session.get('user_role') != 'admin':
        flash('Access denied: Administrator privileges required.', 'danger')
        return redirect(url_for('shop.index'))

# =============================================================
# 1. ADMIN DASHBOARD & KPI ANALYTICS
# =============================================================
@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    # KPI 1: Total Revenue
    rev_row = query_db("SELECT SUM(grand_total) as total_rev FROM orders WHERE payment_status = 'Paid'", one=True)
    total_revenue = float(rev_row['total_rev'] or 0.0)

    # KPI 2: Total Orders
    order_cnt_row = query_db("SELECT COUNT(*) as cnt FROM orders", one=True)
    total_orders = int(order_cnt_row['cnt'] or 0)

    # KPI 3: B2C vs B2B Orders
    b2c_row = query_db("SELECT COUNT(*) as cnt FROM orders WHERE order_type = 'b2c'", one=True)
    b2b_row = query_db("SELECT COUNT(*) as cnt FROM orders WHERE order_type = 'b2b'", one=True)
    b2c_orders = int(b2c_row['cnt'] or 0)
    b2b_orders = int(b2b_row['cnt'] or 0)

    # KPI 4: Users
    user_cnt_row = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
    total_users = int(user_cnt_row['cnt'] or 0)

    # Low Stock Items (< 10 units)
    low_stock_items = query_db(
        """SELECT u.*, p.name as product_name, c.name as category_name
           FROM product_units u
           JOIN products p ON u.product_id = p.id
           JOIN categories c ON p.category_id = c.id
           WHERE u.stock_qty < 10
           ORDER BY u.stock_qty ASC
           LIMIT 8"""
    )

    # Recent Orders
    recent_orders = query_db(
        """SELECT o.*, u.name as customer_name, u.email as customer_email
           FROM orders o
           JOIN users u ON o.user_id = u.id
           ORDER BY o.created_at DESC
           LIMIT 10"""
    )

    # Site mode
    mode_row = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'site_mode'", one=True)
    site_mode = mode_row['setting_value'] if mode_row else 'HYBRID'

    return render_template(
        'admin/dashboard.html',
        total_revenue=total_revenue,
        total_orders=total_orders,
        b2c_orders=b2c_orders,
        b2b_orders=b2b_orders,
        total_users=total_users,
        low_stock_items=low_stock_items,
        recent_orders=recent_orders,
        site_mode=site_mode
    )

# =============================================================
# 2. PRODUCT MANAGEMENT (CRUD)
# =============================================================
@admin_bp.route('/products')
def products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '')

    where_clauses = ["1=1"]
    params = []
    if search:
        where_clauses.append("(p.name LIKE %s OR p.slug LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])
    if category_id and category_id.isdigit():
        where_clauses.append("p.category_id = %s")
        params.append(int(category_id))

    sql = f"""
        SELECT p.*, c.name as category_name, 
               COUNT(u.id) as unit_count,
               MIN(u.selling_price) as min_b2c_price,
               MIN(u.b2b_price) as min_b2b_price
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_units u ON p.id = u.product_id
        WHERE {' AND '.join(where_clauses)}
        GROUP BY p.id
        ORDER BY p.id DESC
    """
    prods = query_db(sql, tuple(params))
    cats = query_db("SELECT * FROM categories ORDER BY name ASC")

    return render_template('admin/products.html', products=prods, categories=cats, search=search, category_id=category_id)

@admin_bp.route('/products/new', methods=['GET', 'POST'])
def product_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower().replace(' ', '-')
        category_id = int(request.form.get('category_id', 1))
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip() or '/static/img/fallback.svg'
        hsn_code = request.form.get('hsn_code', '1006').strip()
        tax_rate = float(request.form.get('tax_rate', 5.0))
        is_featured = bool(request.form.get('is_featured'))
        is_active = bool(request.form.get('is_active', True))

        # Initial unit variant details
        unit_name = request.form.get('unit_name', '1 kg').strip()
        unit_type = request.form.get('unit_type', 'BOTH')
        mrp = float(request.form.get('mrp', 100.0))
        selling_price = float(request.form.get('selling_price', 90.0))
        b2b_price = float(request.form.get('b2b_price', 80.0))
        moq = int(request.form.get('moq', 1))
        stock_qty = int(request.form.get('stock_qty', 100))

        if not name or not slug:
            flash('Product name and slug are required.', 'danger')
            cats = query_db("SELECT * FROM categories ORDER BY name ASC")
            return render_template('admin/product_form.html', categories=cats, product=None)

        # Check existing slug
        existing = query_db("SELECT id FROM products WHERE slug = %s", (slug,), one=True)
        if existing:
            flash(f"A product with slug '{slug}' already exists.", 'danger')
            cats = query_db("SELECT * FROM categories ORDER BY name ASC")
            return render_template('admin/product_form.html', categories=cats, product=None)

        prod_id = execute_db(
            """INSERT INTO products (name, slug, category_id, description, image_url, hsn_code, tax_rate, is_featured, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, slug, category_id, description, image_url, hsn_code, tax_rate, is_featured, is_active),
            lastrowid=True
        )

        # Insert default unit variant
        execute_db(
            """INSERT INTO product_units (product_id, unit_name, unit_type, mrp, selling_price, b2b_price, moq, stock_qty, is_default, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)""",
            (prod_id, unit_name, unit_type, mrp, selling_price, b2b_price, moq, stock_qty)
        )

        flash(f"Product '{name}' created with primary unit variant!", 'success')
        return redirect(url_for('admin.product_edit', id=prod_id))

    cats = query_db("SELECT * FROM categories ORDER BY name ASC")
    return render_template('admin/product_form.html', categories=cats, product=None)

@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
def product_edit(id):
    product = query_db("SELECT * FROM products WHERE id = %s", (id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower().replace(' ', '-')
        category_id = int(request.form.get('category_id', 1))
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip() or '/static/img/fallback.svg'
        hsn_code = request.form.get('hsn_code', '1006').strip()
        tax_rate = float(request.form.get('tax_rate', 5.0))
        is_featured = bool(request.form.get('is_featured'))
        is_active = bool(request.form.get('is_active'))

        execute_db(
            """UPDATE products 
               SET name = %s, slug = %s, category_id = %s, description = %s, image_url = %s, hsn_code = %s, tax_rate = %s, is_featured = %s, is_active = %s
               WHERE id = %s""",
            (name, slug, category_id, description, image_url, hsn_code, tax_rate, is_featured, is_active, id)
        )
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.product_edit', id=id))

    cats = query_db("SELECT * FROM categories ORDER BY name ASC")
    units = query_db("SELECT * FROM product_units WHERE product_id = %s ORDER BY id ASC", (id,))
    return render_template('admin/product_form.html', categories=cats, product=product, units=units)

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
def product_delete(id):
    execute_db("DELETE FROM products WHERE id = %s", (id,))
    flash('Product deleted successfully.', 'info')
    return redirect(url_for('admin.products'))

# =============================================================
# 3. PRODUCT UNIT VARIANTS (B2C & B2B PRICING)
# =============================================================
@admin_bp.route('/products/<int:product_id>/units/new', methods=['POST'])
def unit_add(product_id):
    unit_name = request.form.get('unit_name', '').strip()
    unit_type = request.form.get('unit_type', 'BOTH')
    mrp = float(request.form.get('mrp', 0.0))
    selling_price = float(request.form.get('selling_price', 0.0))
    b2b_price = float(request.form.get('b2b_price', 0.0))
    moq = int(request.form.get('moq', 1))
    stock_qty = int(request.form.get('stock_qty', 0))
    is_default = bool(request.form.get('is_default'))

    if is_default:
        execute_db("UPDATE product_units SET is_default = FALSE WHERE product_id = %s", (product_id,))

    execute_db(
        """INSERT INTO product_units (product_id, unit_name, unit_type, mrp, selling_price, b2b_price, moq, stock_qty, is_default, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
        (product_id, unit_name, unit_type, mrp, selling_price, b2b_price, moq, stock_qty, is_default)
    )
    flash(f"Unit variant '{unit_name}' added!", 'success')
    return redirect(url_for('admin.product_edit', id=product_id))

@admin_bp.route('/units/<int:unit_id>/edit', methods=['POST'])
def unit_edit(unit_id):
    unit = query_db("SELECT * FROM product_units WHERE id = %s", (unit_id,), one=True)
    if not unit:
        flash('Unit not found.', 'danger')
        return redirect(url_for('admin.products'))

    unit_name = request.form.get('unit_name', '').strip()
    unit_type = request.form.get('unit_type', 'BOTH')
    mrp = float(request.form.get('mrp', 0.0))
    selling_price = float(request.form.get('selling_price', 0.0))
    b2b_price = float(request.form.get('b2b_price', 0.0))
    moq = int(request.form.get('moq', 1))
    stock_qty = int(request.form.get('stock_qty', 0))
    is_active = bool(request.form.get('is_active'))

    execute_db(
        """UPDATE product_units 
           SET unit_name = %s, unit_type = %s, mrp = %s, selling_price = %s, b2b_price = %s, moq = %s, stock_qty = %s, is_active = %s
           WHERE id = %s""",
        (unit_name, unit_type, mrp, selling_price, b2b_price, moq, stock_qty, is_active, unit_id)
    )
    flash(f"Unit '{unit_name}' updated successfully!", 'success')
    return redirect(url_for('admin.product_edit', id=unit['product_id']))

@admin_bp.route('/units/<int:unit_id>/delete', methods=['POST'])
def unit_delete(unit_id):
    unit = query_db("SELECT product_id FROM product_units WHERE id = %s", (unit_id,), one=True)
    if unit:
        execute_db("DELETE FROM product_units WHERE id = %s", (unit_id,))
        flash('Unit variant deleted.', 'info')
        return redirect(url_for('admin.product_edit', id=unit['product_id']))
    return redirect(url_for('admin.products'))

# =============================================================
# 4. CATEGORY MANAGEMENT
# =============================================================
@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower().replace(' ', '-')
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        display_order = int(request.form.get('display_order', 0))

        if not name or not slug:
            flash('Category name and slug are required.', 'danger')
        else:
            execute_db(
                """INSERT INTO categories (name, slug, description, image_url, display_order, is_active)
                   VALUES (%s, %s, %s, %s, %s, TRUE)""",
                (name, slug, description, image_url, display_order)
            )
            flash(f"Category '{name}' created!", 'success')
        return redirect(url_for('admin.categories'))

    cats = query_db(
        """SELECT c.*, COUNT(p.id) as product_count
           FROM categories c
           LEFT JOIN products p ON c.id = p.category_id
           GROUP BY c.id
           ORDER BY c.display_order ASC"""
    )
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
def category_delete(id):
    has_prods = query_db("SELECT id FROM products WHERE category_id = %s LIMIT 1", (id,), one=True)
    if has_prods:
        flash('Cannot delete category with associated products. Move products first.', 'danger')
    else:
        execute_db("DELETE FROM categories WHERE id = %s", (id,))
        flash('Category deleted.', 'info')
    return redirect(url_for('admin.categories'))

# =============================================================
# 5. OFFER BANNERS (HERO CAROUSEL)
# =============================================================
@admin_bp.route('/banners', methods=['GET', 'POST'])
def banners():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subtitle = request.form.get('subtitle', '').strip()
        badge_text = request.form.get('badge_text', '').strip()
        coupon_code = request.form.get('coupon_code', '').strip().upper()
        image_url = request.form.get('image_url', '').strip()
        link_url = request.form.get('link_url', '/').strip()
        bg_gradient = request.form.get('bg_gradient', 'linear-gradient(135deg, #059669 0%, #065f46 100%)').strip()
        display_order = int(request.form.get('display_order', 0))

        execute_db(
            """INSERT INTO banners (title, subtitle, badge_text, coupon_code, image_url, link_url, bg_gradient, display_order, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
            (title, subtitle, badge_text, coupon_code, image_url, link_url, bg_gradient, display_order)
        )
        flash(f"Banner '{title}' created!", 'success')
        return redirect(url_for('admin.banners'))

    banner_list = query_db("SELECT * FROM banners ORDER BY display_order ASC")
    return render_template('admin/banners.html', banners=banner_list)

@admin_bp.route('/banners/<int:id>/delete', methods=['POST'])
def banner_delete(id):
    execute_db("DELETE FROM banners WHERE id = %s", (id,))
    flash('Banner deleted.', 'info')
    return redirect(url_for('admin.banners'))

# =============================================================
# 6. ORDER MANAGEMENT & STATUS TRANSITIONS
# =============================================================
@admin_bp.route('/orders')
def orders():
    status = request.args.get('status', '')
    order_type = request.args.get('order_type', '')

    where_clauses = ["1=1"]
    params = []
    if status:
        where_clauses.append("o.order_status = %s")
        params.append(status)
    if order_type:
        where_clauses.append("o.order_type = %s")
        params.append(order_type)

    sql = f"""
        SELECT o.*, u.name as customer_name, u.email as customer_email, u.phone as customer_phone
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY o.created_at DESC
    """
    order_list = query_db(sql, tuple(params))
    return render_template('admin/orders.html', orders=order_list, current_status=status, current_type=order_type)

@admin_bp.route('/orders/<int:id>')
def order_view(id):
    order = query_db(
        """SELECT o.*, u.name as customer_name, u.email as customer_email, u.phone as customer_phone
           FROM orders o
           JOIN users u ON o.user_id = u.id
           WHERE o.id = %s""",
        (id,),
        one=True
    )
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin.orders'))

    items = query_db("SELECT * FROM order_items WHERE order_id = %s", (id,))
    history = query_db("SELECT * FROM order_tracking_history WHERE order_id = %s ORDER BY created_at ASC", (id,))

    return render_template('admin/order_view.html', order=order, items=items, history=history)

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
def order_status_update(id):
    new_status = request.form.get('order_status', '').strip()
    notes = request.form.get('notes', '').strip() or f"Status transitioned to {new_status}."

    valid_statuses = ['Order Placed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered', 'Cancelled']
    if new_status in valid_statuses:
        execute_db("UPDATE orders SET order_status = %s WHERE id = %s", (new_status, id))
        execute_db(
            "INSERT INTO order_tracking_history (order_id, status, notes) VALUES (%s, %s, %s)",
            (id, new_status, notes)
        )
        flash(f"Order #{id} status updated to '{new_status}'!", 'success')
    else:
        flash('Invalid status transition.', 'danger')

    return redirect(url_for('admin.order_view', id=id))

# =============================================================
# 7. USER MANAGEMENT & B2C/B2B ROLES
# =============================================================
@admin_bp.route('/users')
def users():
    role_filter = request.args.get('role', '')
    where_sql = "WHERE role = %s" if role_filter else ""
    params = (role_filter,) if role_filter else ()

    user_list = query_db(
        f"""SELECT u.*, COUNT(o.id) as order_count, SUM(o.grand_total) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            {where_sql}
            GROUP BY u.id
            ORDER BY u.created_at DESC""",
        params
    )
    return render_template('admin/users.html', users=user_list, role_filter=role_filter)

@admin_bp.route('/users/<int:id>/role', methods=['POST'])
def user_update_role(id):
    new_role = request.form.get('role', 'b2c')
    is_verified = bool(request.form.get('is_b2b_verified'))

    if new_role in ('b2c', 'b2b', 'admin'):
        execute_db(
            "UPDATE users SET role = %s, is_b2b_verified = %s WHERE id = %s",
            (new_role, is_verified, id)
        )
        flash(f"User #{id} role updated to {new_role.upper()}.", 'success')
    return redirect(url_for('admin.users'))

# =============================================================
# 8. FEEDBACK & REVIEW MODERATION
# =============================================================
@admin_bp.route('/feedback')
def feedback():
    status = request.args.get('status', 'all')
    where_sql = "WHERE f.status = %s" if status != 'all' else ""
    params = (status,) if status != 'all' else ()

    reviews = query_db(
        f"""SELECT f.*, p.name as product_name, p.slug as product_slug
            FROM feedback f
            LEFT JOIN products p ON f.product_id = p.id
            {where_sql}
            ORDER BY f.created_at DESC""",
        params
    )
    return render_template('admin/feedback.html', reviews=reviews, current_status=status)

@admin_bp.route('/feedback/<int:id>/moderate', methods=['POST'])
def feedback_moderate(id):
    action = request.form.get('action') # approve, reject, delete
    if action == 'approve':
        execute_db("UPDATE feedback SET status = 'approved' WHERE id = %s", (id,))
        flash('Review approved and published.', 'success')
    elif action == 'reject':
        execute_db("UPDATE feedback SET status = 'rejected' WHERE id = %s", (id,))
        flash('Review rejected.', 'info')
    elif action == 'delete':
        execute_db("DELETE FROM feedback WHERE id = %s", (id,))
        flash('Review deleted.', 'warning')
    return redirect(url_for('admin.feedback'))

# =============================================================
# 9. GLOBAL SETTINGS (B2C/B2B/HYBRID MODE SWITCH)
# =============================================================
@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            execute_db(
                """INSERT INTO store_settings (setting_key, setting_value) 
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)""",
                (key, value.strip())
            )
        flash('Store settings saved successfully!', 'success')
        return redirect(url_for('admin.settings'))

    settings_rows = query_db("SELECT setting_key, setting_value FROM store_settings")
    settings_dict = {r['setting_key']: r['setting_value'] for r in settings_rows}

    return render_template('admin/settings.html', settings=settings_dict)

# =============================================================
# 10. COUPONS MANAGEMENT
# =============================================================
@admin_bp.route('/coupons', methods=['GET', 'POST'])
def coupons():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        discount_type = request.form.get('discount_type', 'percentage')
        discount_value = float(request.form.get('discount_value', 0.0))
        min_order_amount = float(request.form.get('min_order_amount', 0.0))
        applicable_mode = request.form.get('applicable_mode', 'both')
        description = request.form.get('description', '').strip()

        if code and discount_value > 0:
            execute_db(
                """INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, applicable_mode, description, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, TRUE)""",
                (code, discount_type, discount_value, min_order_amount, applicable_mode, description)
            )
            flash(f"Coupon '{code}' added successfully!", 'success')
        return redirect(url_for('admin.coupons'))

    coupons_list = query_db("SELECT * FROM coupons ORDER BY id DESC")
    return render_template('admin/coupons.html', coupons=coupons_list)

@admin_bp.route('/coupons/<int:id>/delete', methods=['POST'])
def coupon_delete(id):
    execute_db("DELETE FROM coupons WHERE id = %s", (id,))
    flash('Coupon deleted.', 'info')
    return redirect(url_for('admin.coupons'))
