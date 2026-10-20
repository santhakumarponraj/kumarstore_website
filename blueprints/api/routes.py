import uuid
from flask import Blueprint, request, jsonify, session
from db import query_db, execute_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_or_create_session_id():
    if 'guest_session_id' not in session:
        session['guest_session_id'] = str(uuid.uuid4())
    return session['guest_session_id']

def get_current_cart_count():
    user_id = session.get('user_id')
    guest_id = session.get('guest_session_id')
    if user_id:
        res = query_db("SELECT SUM(quantity) as cnt FROM cart WHERE user_id = %s", (user_id,), one=True)
    elif guest_id:
        res = query_db("SELECT SUM(quantity) as cnt FROM cart WHERE session_id = %s", (guest_id,), one=True)
    else:
        return 0
    return int(res['cnt']) if (res and res['cnt']) else 0

@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json() or {}
    unit_id = data.get('unit_id')
    quantity = int(data.get('quantity', 1))

    if not unit_id or quantity <= 0:
        return jsonify({'success': False, 'error': 'Invalid unit or quantity'}), 400

    unit = query_db(
        """SELECT u.*, p.name as product_name, p.id as product_id, p.is_active as prod_active 
           FROM product_units u
           JOIN products p ON u.product_id = p.id
           WHERE u.id = %s AND u.is_active = TRUE AND p.is_active = TRUE""",
        (unit_id,),
        one=True
    )

    if not unit:
        return jsonify({'success': False, 'error': 'Product unit not found or inactive'}), 404

    # Determine mode: user role or session view_mode
    mode = session.get('view_mode', 'b2c').lower()
    if session.get('user_role') == 'b2b':
        mode = 'b2b'

    # MOQ check for wholesale mode
    if mode == 'b2b' and quantity < unit['moq']:
        return jsonify({
            'success': False,
            'error': f"Minimum Order Quantity for B2B Wholesale is {unit['moq']} units."
        }), 400

    # Stock check
    if unit['stock_qty'] <= 0:
        return jsonify({'success': False, 'error': 'This item is currently out of stock'}), 400

    user_id = session.get('user_id')
    guest_id = get_or_create_session_id()

    # Check if item with same unit and mode already exists in cart
    if user_id:
        existing = query_db(
            "SELECT id, quantity FROM cart WHERE user_id = %s AND unit_id = %s AND mode = %s",
            (user_id, unit_id, mode),
            one=True
        )
        if existing:
            new_qty = existing['quantity'] + quantity
            execute_db("UPDATE cart SET quantity = %s WHERE id = %s", (new_qty, existing['id']))
        else:
            execute_db(
                "INSERT INTO cart (user_id, product_id, unit_id, quantity, mode) VALUES (%s, %s, %s, %s, %s)",
                (user_id, unit['product_id'], unit_id, quantity, mode)
            )
    else:
        existing = query_db(
            "SELECT id, quantity FROM cart WHERE session_id = %s AND unit_id = %s AND mode = %s",
            (guest_id, unit_id, mode),
            one=True
        )
        if existing:
            new_qty = existing['quantity'] + quantity
            execute_db("UPDATE cart SET quantity = %s WHERE id = %s", (new_qty, existing['id']))
        else:
            execute_db(
                "INSERT INTO cart (session_id, product_id, unit_id, quantity, mode) VALUES (%s, %s, %s, %s, %s)",
                (guest_id, unit['product_id'], unit_id, quantity, mode)
            )

    cart_count = get_current_cart_count()
    return jsonify({
        'success': True,
        'message': f"Added {quantity} x {unit['product_name']} ({unit['unit_name']}) to cart",
        'cart_count': cart_count,
        'unit_id': unit_id,
        'quantity': new_qty if existing else quantity
    })

@api_bp.route('/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json() or {}
    cart_id = data.get('cart_id')
    unit_id = data.get('unit_id')
    quantity = int(data.get('quantity', 1))

    user_id = session.get('user_id')
    guest_id = session.get('guest_session_id')

    if cart_id:
        item = query_db(
            """SELECT c.*, u.moq, u.stock_qty 
               FROM cart c 
               JOIN product_units u ON c.unit_id = u.id 
               WHERE c.id = %s""",
            (cart_id,),
            one=True
        )
    elif unit_id:
        if user_id:
            item = query_db(
                """SELECT c.*, u.moq, u.stock_qty 
                   FROM cart c 
                   JOIN product_units u ON c.unit_id = u.id 
                   WHERE c.unit_id = %s AND c.user_id = %s""",
                (unit_id, user_id),
                one=True
            )
        else:
            item = query_db(
                """SELECT c.*, u.moq, u.stock_qty 
                   FROM cart c 
                   JOIN product_units u ON c.unit_id = u.id 
                   WHERE c.unit_id = %s AND c.session_id = %s""",
                (unit_id, guest_id),
                one=True
            )
    else:
        return jsonify({'success': False, 'error': 'Invalid request parameters'}), 400

    if not item:
        return jsonify({'success': False, 'error': 'Cart item not found'}), 404

    # If quantity is <= 0: delete item from cart
    if quantity <= 0:
        execute_db("DELETE FROM cart WHERE id = %s", (item['id'],))
        return jsonify({
            'success': True,
            'removed': True,
            'message': 'Item removed from cart',
            'cart_count': get_current_cart_count()
        })

    # Enforce MOQ if mode is B2B
    if item['mode'] == 'b2b' and quantity < item['moq']:
        return jsonify({
            'success': False,
            'error': f"Minimum Order Quantity for B2B is {item['moq']}.",
            'min_qty': item['moq']
        }), 400

    execute_db("UPDATE cart SET quantity = %s WHERE id = %s", (quantity, item['id']))
    return jsonify({
        'success': True,
        'quantity': quantity,
        'message': 'Cart quantity updated',
        'cart_count': get_current_cart_count()
    })

@api_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json() or {}
    cart_id = data.get('cart_id')
    unit_id = data.get('unit_id')
    user_id = session.get('user_id')
    guest_id = session.get('guest_session_id')

    if cart_id:
        execute_db("DELETE FROM cart WHERE id = %s", (cart_id,))
    elif unit_id:
        if user_id:
            execute_db("DELETE FROM cart WHERE unit_id = %s AND user_id = %s", (unit_id, user_id))
        elif guest_id:
            execute_db("DELETE FROM cart WHERE unit_id = %s AND session_id = %s", (unit_id, guest_id))
    else:
        return jsonify({'success': False, 'error': 'Invalid cart ID or unit ID'}), 400

    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': get_current_cart_count()
    })

@api_bp.route('/cart/count', methods=['GET'])
def cart_count():
    return jsonify({'count': get_current_cart_count()})

@api_bp.route('/wishlist/toggle', methods=['POST'])
def toggle_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'redirect': '/auth/login'}), 401

    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID required'}), 400

    user_id = session['user_id']
    existing = query_db(
        "SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
        one=True
    )

    if existing:
        execute_db("DELETE FROM wishlist WHERE id = %s", (existing['id'],))
        in_wishlist = False
    else:
        execute_db("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
        in_wishlist = True

    count_res = query_db("SELECT COUNT(*) as cnt FROM wishlist WHERE user_id = %s", (user_id,), one=True)
    wishlist_count = count_res['cnt'] if count_res else 0

    return jsonify({
        'success': True,
        'in_wishlist': in_wishlist,
        'wishlist_count': wishlist_count
    })

@api_bp.route('/coupon/apply', methods=['POST'])
def apply_coupon():
    data = request.get_json() or {}
    code = data.get('coupon_code', '').strip().upper()
    if not code:
        return jsonify({'success': False, 'error': 'Coupon code is required'}), 400

    coupon = query_db(
        "SELECT * FROM coupons WHERE code = %s AND is_active = TRUE",
        (code,),
        one=True
    )
    if not coupon:
        return jsonify({'success': False, 'error': 'Invalid or expired coupon code'}), 400

    mode = session.get('view_mode', 'b2c').lower()
    app_mode = coupon['applicable_mode'].lower()
    if app_mode != 'both' and app_mode != mode:
        return jsonify({'success': False, 'error': f"Coupon '{code}' is valid only for {app_mode.upper()} mode"}), 400

    # Store coupon in session
    session['applied_coupon'] = {
        'id': coupon['id'],
        'code': coupon['code'],
        'discount_type': coupon['discount_type'],
        'discount_value': float(coupon['discount_value']),
        'min_order_amount': float(coupon['min_order_amount']),
        'description': coupon['description']
    }

    return jsonify({
        'success': True,
        'message': f"Coupon '{code}' applied successfully!",
        'coupon': session['applied_coupon']
    })

@api_bp.route('/product-unit-info/<int:unit_id>', methods=['GET'])
def unit_info(unit_id):
    unit = query_db("SELECT * FROM product_units WHERE id = %s", (unit_id,), one=True)
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    return jsonify(dict(unit))
