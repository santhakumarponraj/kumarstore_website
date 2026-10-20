import datetime
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from db import query_db, execute_db, get_db_cursor
from blueprints.auth.routes import login_required

shop_bp = Blueprint('shop', __name__)

def get_session_id():
    """Generates or retrieves guest session ID from cookie/session."""
    if 'guest_session_id' not in session:
        session['guest_session_id'] = str(uuid.uuid4())
    return session['guest_session_id']

def resolve_active_mode():
    """Resolves active storefront mode based on site settings and user session."""
    # Check global store setting
    setting = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'site_mode'", one=True)
    site_mode = setting['setting_value'].upper() if setting else 'HYBRID'

    if site_mode == 'B2C':
        return 'b2c'
    if site_mode == 'B2B':
        return 'b2b'

    # Hybrid mode: respect logged-in user role or session view_mode
    if 'user_role' in session:
        if session['user_role'] == 'b2b':
            return 'b2b'
        elif session['user_role'] == 'b2c':
            return 'b2c'

    # Guest user or admin
    return session.get('view_mode', 'b2c').lower()

def enrich_products_with_units(products, active_mode):
    """Fetches unit variants for each product according to active B2C/B2B mode."""
    if not products:
        return []

    product_ids = [p['id'] for p in products]
    placeholders = ','.join(['%s'] * len(product_ids))

    # In B2C mode: fetch units where unit_type IN ('B2C', 'BOTH')
    # In B2B mode: fetch units where unit_type IN ('B2B', 'BOTH')
    target_types = ('B2B', 'BOTH') if active_mode == 'b2b' else ('B2C', 'BOTH')
    type_placeholders = ','.join(['%s'] * len(target_types))

    query = f"""
        SELECT * FROM product_units 
        WHERE product_id IN ({placeholders}) 
          AND unit_type IN ({type_placeholders}) 
          AND is_active = TRUE 
        ORDER BY product_id, is_default DESC, selling_price ASC
    """
    params = product_ids + list(target_types)
    all_units = query_db(query, tuple(params))

    units_by_product = {}
    for u in all_units:
        p_id = u['product_id']
        if p_id not in units_by_product:
            units_by_product[p_id] = []
        units_by_product[p_id].append(u)

    enriched = []
    for p in products:
        p_copy = dict(p)
        p_units = units_by_product.get(p['id'], [])
        p_copy['units'] = p_units
        p_copy['default_unit'] = p_units[0] if p_units else None
        
        # Check wishlist status if user is logged in
        p_copy['in_wishlist'] = False
        if 'user_id' in session:
            wish = query_db(
                "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
                (session['user_id'], p['id']),
                one=True
            )
            p_copy['in_wishlist'] = bool(wish)

        enriched.append(p_copy)

    return enriched

# =============================================================
# 1. LANDING PAGE (Layer 1 Navbar, Layer 2 Offer Zone, Layer 3 Showcase)
# =============================================================
@shop_bp.route('/')
def index():
    active_mode = resolve_active_mode()

    # Layer 2: Hero Carousel Offer Banners
    banners = query_db(
        "SELECT * FROM banners WHERE is_active = TRUE ORDER BY display_order ASC"
    )

    # Layer 3: Category-Wise Showcase
    # Fetch all 10 active categories
    categories = query_db(
        "SELECT * FROM categories WHERE is_active = TRUE ORDER BY display_order ASC"
    )

    # Fetch top products for each category
    category_showcase = []
    for cat in categories:
        products = query_db(
            """SELECT p.*, c.name as category_name, c.slug as category_slug 
               FROM products p
               JOIN categories c ON p.category_id = c.id
               WHERE p.category_id = %s AND p.is_active = TRUE
               ORDER BY p.is_featured DESC, p.id ASC
               LIMIT 4""",
            (cat['id'],)
        )
        if products:
            enriched_prods = enrich_products_with_units(products, active_mode)
            category_showcase.append({
                'category': cat,
                'products': enriched_prods
            })

    # Top featured deals
    featured_products = query_db(
        """SELECT p.*, c.name as category_name, c.slug as category_slug
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.is_featured = TRUE AND p.is_active = TRUE
           ORDER BY p.id DESC
           LIMIT 8"""
    )
    enriched_featured = enrich_products_with_units(featured_products, active_mode)

    return render_template(
        'shop/index.html',
        banners=banners,
        category_showcase=category_showcase,
        featured_products=enriched_featured,
        active_mode=active_mode
    )

# =============================================================
# 2. CATEGORY PRODUCTS LISTING
# =============================================================
@shop_bp.route('/category/<slug>')
def category_products(slug):
    active_mode = resolve_active_mode()
    category = query_db("SELECT * FROM categories WHERE slug = %s", (slug,), one=True)
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('shop.index'))

    sort = request.args.get('sort', 'featured')
    order_clause = "p.is_featured DESC, p.id DESC"
    if sort == 'price_low':
        order_clause = "min_price ASC"
    elif sort == 'price_high':
        order_clause = "min_price DESC"
    elif sort == 'name':
        order_clause = "p.name ASC"

    price_col = "u.b2b_price" if active_mode == 'b2b' else "u.selling_price"

    products = query_db(
        f"""SELECT p.*, c.name as category_name, c.slug as category_slug,
                   MIN({price_col}) as min_price
            FROM products p
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_units u ON p.id = u.product_id
            WHERE p.category_id = %s AND p.is_active = TRUE
            GROUP BY p.id
            ORDER BY {order_clause}""",
        (category['id'],)
    )

    enriched_products = enrich_products_with_units(products, active_mode)

    return render_template(
        'shop/category.html',
        category=category,
        products=enriched_products,
        current_sort=sort,
        active_mode=active_mode
    )

# =============================================================
# 3. PRODUCT DETAIL PAGE
# =============================================================
@shop_bp.route('/product/<slug>')
def product_detail(slug):
    active_mode = resolve_active_mode()
    product = query_db(
        """SELECT p.*, c.name as category_name, c.slug as category_slug
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.slug = %s AND p.is_active = TRUE""",
        (slug,),
        one=True
    )
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop.index'))

    # Fetch all units (both B2C and B2B so the user can see all variants)
    units = query_db(
        """SELECT * FROM product_units 
           WHERE product_id = %s AND is_active = TRUE 
           ORDER BY is_default DESC, selling_price ASC""",
        (product['id'],)
    )

    # Check wishlist
    in_wishlist = False
    if 'user_id' in session:
        wish = query_db(
            "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
            (session['user_id'], product['id']),
            one=True
        )
        in_wishlist = bool(wish)

    # Reviews
    reviews = query_db(
        """SELECT * FROM feedback 
           WHERE product_id = %s AND status = 'approved' 
           ORDER BY created_at DESC""",
        (product['id'],)
    )

    # Related products
    related = query_db(
        """SELECT p.*, c.name as category_name, c.slug as category_slug
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.category_id = %s AND p.id != %s AND p.is_active = TRUE
           LIMIT 4""",
        (product['category_id'], product['id'])
    )
    enriched_related = enrich_products_with_units(related, active_mode)

    return render_template(
        'shop/product_detail.html',
        product=product,
        units=units,
        in_wishlist=in_wishlist,
        reviews=reviews,
        related=enriched_related,
        active_mode=active_mode
    )

# =============================================================
# 4. PRODUCT REVIEW SUBMISSION
# =============================================================
@shop_bp.route('/product/<int:product_id>/review', methods=['POST'])
def submit_review(product_id):
    product = query_db("SELECT id, slug FROM products WHERE id = %s", (product_id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop.index'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    rating = int(request.form.get('rating', 5))
    subject = request.form.get('subject', '').strip()
    comment = request.form.get('comment', '').strip()
    user_id = session.get('user_id')

    if not name or not email or not comment:
        flash('Please complete all review fields.', 'danger')
        return redirect(url_for('shop.product_detail', slug=product['slug']))

    execute_db(
        """INSERT INTO feedback (user_id, product_id, name, email, rating, subject, comment, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved')""",
        (user_id, product_id, name, email, rating, subject, comment)
    )
    flash('Thank you! Your verified review has been published.', 'success')
    return redirect(url_for('shop.product_detail', slug=product['slug']))

# =============================================================
# 5. SEARCH
# =============================================================
@shop_bp.route('/search')
def search():
    active_mode = resolve_active_mode()
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', '')

    where_clauses = ["p.is_active = TRUE"]
    params = []

    if q:
        where_clauses.append("(p.name LIKE %s OR p.description LIKE %s OR c.name LIKE %s)")
        wildcard = f"%{q}%"
        params.extend([wildcard, wildcard, wildcard])

    if category_id and category_id.isdigit():
        where_clauses.append("p.category_id = %s")
        params.append(int(category_id))

    sql = f"""
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY p.id DESC
        LIMIT 50
    """
    products = query_db(sql, tuple(params))
    enriched = enrich_products_with_units(products, active_mode)

    return render_template(
        'shop/search.html',
        query=q,
        category_id=category_id,
        products=enriched,
        active_mode=active_mode
    )

# =============================================================
# 6. MODE SWITCHER (B2C Retail <-> B2B Wholesale)
# =============================================================
@shop_bp.route('/switch-mode/<mode>')
def switch_mode(mode):
    mode = mode.lower()
    if mode in ('b2c', 'b2b'):
        session['view_mode'] = mode
        flash(f"Switched view to {'B2B Wholesale' if mode == 'b2b' else 'B2C Retail'} pricing.", 'info')

    ref = request.referrer
    if ref and ('/' in ref):
        return redirect(ref)
    return redirect(url_for('shop.index'))

# =============================================================
# 7. SHOPPING CART VIEW
# =============================================================
@shop_bp.route('/cart')
def cart():
    active_mode = resolve_active_mode()
    user_id = session.get('user_id')
    guest_id = session.get('guest_session_id')

    if user_id:
        cart_rows = query_db(
            """SELECT c.id as cart_id, c.quantity, c.mode,
                      p.id as product_id, p.name as product_name, p.slug as product_slug, p.image_url, p.hsn_code, p.tax_rate,
                      u.id as unit_id, u.unit_name, u.mrp, u.selling_price, u.b2b_price, u.moq, u.stock_qty, u.unit_type
               FROM cart c
               JOIN products p ON c.product_id = p.id
               JOIN product_units u ON c.unit_id = u.id
               WHERE c.user_id = %s
               ORDER BY c.id DESC""",
            (user_id,)
        )
    else:
        cart_rows = query_db(
            """SELECT c.id as cart_id, c.quantity, c.mode,
                      p.id as product_id, p.name as product_name, p.slug as product_slug, p.image_url, p.hsn_code, p.tax_rate,
                      u.id as unit_id, u.unit_name, u.mrp, u.selling_price, u.b2b_price, u.moq, u.stock_qty, u.unit_type
               FROM cart c
               JOIN products p ON c.product_id = p.id
               JOIN product_units u ON c.unit_id = u.id
               WHERE c.session_id = %s
               ORDER BY c.id DESC""",
            (guest_id,)
        )

    # Compute calculations
    total_mrp = 0.0
    subtotal = 0.0
    items = []
    moq_errors = []

    for item in cart_rows:
        # Determine applicable unit price
        is_b2b_item = (item['mode'] == 'b2b')
        unit_price = float(item['b2b_price']) if is_b2b_item else float(item['selling_price'])
        mrp = float(item['mrp'])
        qty = int(item['quantity'])
        moq = int(item['moq'])

        if is_b2b_item and qty < moq:
            moq_errors.append(f"{item['product_name']} ({item['unit_name']}) requires a Minimum Order Quantity of {moq} for B2B Wholesale.")

        line_mrp = mrp * qty
        line_total = unit_price * qty
        total_mrp += line_mrp
        subtotal += line_total

        item_dict = dict(item)
        item_dict['unit_price'] = unit_price
        item_dict['line_total'] = line_total
        item_dict['line_mrp'] = line_mrp
        items.append(item_dict)

    # Coupon discount calculation
    coupon_discount = 0.0
    applied_coupon = session.get('applied_coupon')
    if applied_coupon and subtotal > 0:
        if subtotal >= float(applied_coupon['min_order_amount']):
            if applied_coupon['discount_type'] == 'percentage':
                coupon_discount = (subtotal * float(applied_coupon['discount_value'])) / 100.0
            else:
                coupon_discount = float(applied_coupon['discount_value'])
        else:
            session.pop('applied_coupon', None)
            applied_coupon = None

    # Delivery calculation
    setting_free = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'free_shipping_threshold'", one=True)
    setting_fee = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'standard_shipping_fee'", one=True)
    free_threshold = float(setting_free['setting_value']) if setting_free else 1000.0
    std_shipping = float(setting_fee['setting_value']) if setting_fee else 50.0

    delivery_fee = 0.0 if (subtotal >= free_threshold or subtotal == 0) else std_shipping
    grand_total = max(0.0, subtotal - coupon_discount + delivery_fee)

    return render_template(
        'shop/cart.html',
        items=items,
        total_mrp=total_mrp,
        subtotal=subtotal,
        coupon_discount=coupon_discount,
        applied_coupon=applied_coupon,
        delivery_fee=delivery_fee,
        grand_total=grand_total,
        free_threshold=free_threshold,
        moq_errors=moq_errors,
        active_mode=active_mode
    )

# =============================================================
# 8. CHECKOUT
# =============================================================
@shop_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    active_mode = resolve_active_mode()
    user_id = session.get('user_id')

    # Require login for checkout
    if not user_id:
        flash('Please login or register to proceed with secure checkout.', 'info')
        return redirect(url_for('auth.login', next=url_for('shop.checkout')))

    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)

    # Fetch user cart items
    cart_items = query_db(
        """SELECT c.id as cart_id, c.quantity, c.mode,
                  p.id as product_id, p.name as product_name, p.hsn_code, p.tax_rate,
                  u.id as unit_id, u.unit_name, u.mrp, u.selling_price, u.b2b_price, u.moq, u.stock_qty
           FROM cart c
           JOIN products p ON c.product_id = p.id
           JOIN product_units u ON c.unit_id = u.id
           WHERE c.user_id = %s""",
        (user_id,)
    )

    if not cart_items:
        flash('Your cart is empty. Add items before checking out.', 'warning')
        return redirect(url_for('shop.cart'))

    # Calculate totals
    subtotal = 0.0
    total_mrp = 0.0
    tax_amount = 0.0
    has_b2b = False

    for item in cart_items:
        is_b2b = (item['mode'] == 'b2b')
        if is_b2b:
            has_b2b = True
        price = float(item['b2b_price']) if is_b2b else float(item['selling_price'])
        qty = int(item['quantity'])
        tax_rate = float(item['tax_rate'])
        
        line_price = price * qty
        subtotal += line_price
        total_mrp += float(item['mrp']) * qty
        tax_amount += (line_price * tax_rate) / 100.0

    # Coupon
    coupon_discount = 0.0
    applied_coupon = session.get('applied_coupon')
    if applied_coupon and subtotal >= float(applied_coupon['min_order_amount']):
        if applied_coupon['discount_type'] == 'percentage':
            coupon_discount = (subtotal * float(applied_coupon['discount_value'])) / 100.0
        else:
            coupon_discount = float(applied_coupon['discount_value'])

    # Delivery
    setting_free = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'free_shipping_threshold'", one=True)
    setting_fee = query_db("SELECT setting_value FROM store_settings WHERE setting_key = 'standard_shipping_fee'", one=True)
    free_threshold = float(setting_free['setting_value']) if setting_free else 1000.0
    delivery_fee = 0.0 if subtotal >= free_threshold else (float(setting_fee['setting_value']) if setting_fee else 50.0)
    grand_total = max(0.0, subtotal - coupon_discount + delivery_fee)

    if request.method == 'POST':
        shipping_name = request.form.get('shipping_name', '').strip()
        shipping_phone = request.form.get('shipping_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        shipping_city = request.form.get('shipping_city', '').strip()
        shipping_state = request.form.get('shipping_state', 'Tamil Nadu').strip()
        shipping_pincode = request.form.get('shipping_pincode', '').strip()
        buyer_company_name = request.form.get('buyer_company_name', '').strip()
        buyer_gstin = request.form.get('buyer_gstin', '').strip().upper()
        payment_method = request.form.get('payment_method', 'COD')

        if not shipping_name or not shipping_phone or not shipping_address or not shipping_city or not shipping_pincode:
            flash('Please fill in all mandatory shipping address fields.', 'danger')
            return render_template('shop/checkout.html', user=user, cart_items=cart_items, subtotal=subtotal, total_mrp=total_mrp, discount=coupon_discount, delivery_fee=delivery_fee, grand_total=grand_total, has_b2b=has_b2b)

        # Generate unique order number (e.g. KMR-20261020-ABCD)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:4].upper()
        order_number = f"KMR-{date_str}-{rand_str}"
        order_type = 'b2b' if has_b2b or user['role'] == 'b2b' else 'b2c'

        # Payment status simulation: If online (Razorpay/Stripe placeholder), simulated as Paid
        payment_status = 'Paid' if payment_method in ('Razorpay', 'Stripe') else 'Pending'
        payment_ref = f"PAY_{uuid.uuid4().hex[:12].upper()}" if payment_method in ('Razorpay', 'Stripe') else None

        # Insert order
        order_id = execute_db(
            """INSERT INTO orders 
               (order_number, user_id, order_type, total_mrp, subtotal, discount_amount, coupon_code, tax_amount, delivery_fee, grand_total, payment_status, payment_method, payment_ref, order_status, shipping_name, shipping_phone, shipping_address, shipping_city, shipping_state, shipping_pincode, buyer_company_name, buyer_gstin)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Order Placed', %s, %s, %s, %s, %s, %s, %s, %s)""",
            (order_number, user_id, order_type, total_mrp, subtotal, coupon_discount, applied_coupon['code'] if applied_coupon else None, tax_amount, delivery_fee, grand_total, payment_status, payment_method, payment_ref, shipping_name, shipping_phone, shipping_address, shipping_city, shipping_state, shipping_pincode, buyer_company_name or user.get('company_name'), buyer_gstin or user.get('gstin')),
            lastrowid=True
        )

        # Insert itemized order items
        for item in cart_items:
            is_b2b_item = (item['mode'] == 'b2b')
            unit_price = float(item['b2b_price']) if is_b2b_item else float(item['selling_price'])
            qty = int(item['quantity'])
            item_total = unit_price * qty

            execute_db(
                """INSERT INTO order_items 
                   (order_id, product_id, unit_id, product_name, unit_name, quantity, unit_price, mrp, total_price, tax_rate, hsn_code)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (order_id, item['product_id'], item['unit_id'], item['product_name'], item['unit_name'], qty, unit_price, item['mrp'], item_total, item['tax_rate'], item['hsn_code'])
            )

            # Reduce stock
            execute_db(
                "UPDATE product_units SET stock_qty = GREATEST(0, stock_qty - %s) WHERE id = %s",
                (qty, item['unit_id'])
            )

        # Insert initial tracking entry
        execute_db(
            "INSERT INTO order_tracking_history (order_id, status, notes) VALUES (%s, 'Order Placed', 'Order received and confirmed by Kumar Store system.')",
            (order_id,)
        )

        # Clear cart & coupon
        execute_db("DELETE FROM cart WHERE user_id = %s", (user_id,))
        session.pop('applied_coupon', None)

        flash(f'Thank you! Your order {order_number} has been placed successfully.', 'success')
        return redirect(url_for('shop.order_success', order_number=order_number))

    return render_template(
        'shop/checkout.html',
        user=user,
        cart_items=cart_items,
        subtotal=subtotal,
        total_mrp=total_mrp,
        discount=coupon_discount,
        delivery_fee=delivery_fee,
        grand_total=grand_total,
        has_b2b=has_b2b,
        active_mode=active_mode
    )

# =============================================================
# 9. ORDER SUCCESS CONFIRMATION
# =============================================================
@shop_bp.route('/order-success/<order_number>')
def order_success(order_number):
    order = query_db(
        "SELECT * FROM orders WHERE order_number = %s",
        (order_number,),
        one=True
    )
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop.index'))

    return render_template('shop/order_success.html', order=order)

# =============================================================
# 10. USER ORDERS LIST & DETAILS
# =============================================================
@shop_bp.route('/orders')
@login_required
def orders():
    user_orders = query_db(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC",
        (session['user_id'],)
    )
    return render_template('shop/orders.html', orders=user_orders)

@shop_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = query_db(
        "SELECT * FROM orders WHERE id = %s AND (user_id = %s OR %s = 'admin')",
        (order_id, session['user_id'], session.get('user_role')),
        one=True
    )
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop.orders'))

    items = query_db(
        "SELECT * FROM order_items WHERE order_id = %s",
        (order_id,)
    )

    history = query_db(
        "SELECT * FROM order_tracking_history WHERE order_id = %s ORDER BY created_at ASC",
        (order_id,)
    )

    return render_template('shop/order_detail.html', order=order, items=items, history=history)

# =============================================================
# 11. DELIVERY TRACKING SCREEN
# =============================================================
@shop_bp.route('/orders/<int:order_id>/track')
@login_required
def order_track(order_id):
    order = query_db(
        "SELECT * FROM orders WHERE id = %s AND (user_id = %s OR %s = 'admin')",
        (order_id, session['user_id'], session.get('user_role')),
        one=True
    )
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('shop.orders'))

    tracking_steps = [
        {'name': 'Order Placed', 'icon': 'bi-receipt'},
        {'name': 'Packed', 'icon': 'bi-box-seam'},
        {'name': 'Shipped', 'icon': 'bi-truck'},
        {'name': 'Out for Delivery', 'icon': 'bi-bicycle'},
        {'name': 'Delivered', 'icon': 'bi-check2-circle'}
    ]

    history = query_db(
        "SELECT * FROM order_tracking_history WHERE order_id = %s ORDER BY created_at ASC",
        (order_id,)
    )

    # Determine current step index
    status_order = ['Order Placed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered']
    current_status = order['order_status']
    current_idx = status_order.index(current_status) if current_status in status_order else 0

    return render_template(
        'shop/order_track.html',
        order=order,
        steps=tracking_steps,
        history=history,
        current_idx=current_idx
    )

# =============================================================
# 12. TAX INVOICE (GST COMPLIANT, PRINTABLE)
# =============================================================
@shop_bp.route('/orders/<int:order_id>/invoice')
@login_required
def order_invoice(order_id):
    order = query_db(
        "SELECT * FROM orders WHERE id = %s AND (user_id = %s OR %s = 'admin')",
        (order_id, session['user_id'], session.get('user_role')),
        one=True
    )
    if not order:
        flash('Invoice not available.', 'danger')
        return redirect(url_for('shop.orders'))

    items = query_db("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    
    # Fetch store details from settings
    store_info = {}
    rows = query_db("SELECT setting_key, setting_value FROM store_settings")
    for r in rows:
        store_info[r['setting_key']] = r['setting_value']

    return render_template('shop/invoice.html', order=order, items=items, store=store_info)

# =============================================================
# 13. WISHLIST VIEW
# =============================================================
@shop_bp.route('/wishlist')
@login_required
def wishlist():
    active_mode = resolve_active_mode()
    products = query_db(
        """SELECT p.*, c.name as category_name, c.slug as category_slug
           FROM wishlist w
           JOIN products p ON w.product_id = p.id
           JOIN categories c ON p.category_id = c.id
           WHERE w.user_id = %s
           ORDER BY w.created_at DESC""",
        (session['user_id'],)
    )
    enriched = enrich_products_with_units(products, active_mode)
    return render_template('shop/wishlist.html', products=enriched, active_mode=active_mode)

# =============================================================
# 14. STORE FEEDBACK & CONTACT
# =============================================================
@shop_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        rating = int(request.form.get('rating', 5))
        subject = request.form.get('subject', '').strip()
        comment = request.form.get('comment', '').strip()
        user_id = session.get('user_id')

        if not name or not email or not comment:
            flash('Please enter your name, email, and feedback message.', 'danger')
            return render_template('shop/feedback.html')

        execute_db(
            """INSERT INTO feedback (user_id, product_id, name, email, rating, subject, comment, status)
               VALUES (%s, NULL, %s, %s, %s, %s, %s, 'approved')""",
            (user_id, name, email, rating, subject, comment)
        )
        flash('Thank you for your valuable feedback! We truly appreciate your support.', 'success')
        return redirect(url_for('shop.index'))

    # Load recent approved general feedback
    store_reviews = query_db(
        "SELECT * FROM feedback WHERE product_id IS NULL AND status = 'approved' ORDER BY created_at DESC LIMIT 10"
    )
    return render_template('shop/feedback.html', reviews=store_reviews)
