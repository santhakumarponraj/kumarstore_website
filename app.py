import datetime
from flask import Flask, render_template, session, request
from config import Config
from db import query_db
from blueprints.auth import auth_bp
from blueprints.shop import shop_bp
from blueprints.admin import admin_bp
from blueprints.api import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    app.register_blueprint(shop_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # ---------------------------------------------------------
    # Context Processors - Global Template Context
    # ---------------------------------------------------------
    @app.context_processor
    def inject_global_data():
        # 1. Current user object
        user = None
        if 'user_id' in session:
            user = query_db(
                "SELECT id, name, email, phone, role, company_name, gstin, is_b2b_verified FROM users WHERE id = %s",
                (session['user_id'],),
                one=True
            )

        # 2. Store settings & Global Mode
        store_settings_rows = query_db("SELECT setting_key, setting_value FROM store_settings")
        store_settings = {r['setting_key']: r['setting_value'] for r in store_settings_rows} if store_settings_rows else {}
        global_site_mode = store_settings.get('site_mode', 'HYBRID').upper()

        # 3. Active Storefront Mode resolution
        if global_site_mode == 'B2C':
            active_mode = 'b2c'
        elif global_site_mode == 'B2B':
            active_mode = 'b2b'
        else:
            # Hybrid mode
            if user and user.get('role') == 'b2b':
                active_mode = 'b2b'
            elif user and user.get('role') == 'b2c':
                active_mode = 'b2c'
            else:
                active_mode = session.get('view_mode', 'b2c').lower()

        # 4. Mandatory 10 Categories for Layer 1 Navbar
        categories = query_db(
            "SELECT * FROM categories WHERE is_active = TRUE ORDER BY display_order ASC"
        )

        # 5. Live Cart Count
        cart_count = 0
        user_id = session.get('user_id')
        guest_id = session.get('guest_session_id')
        if user_id:
            cart_res = query_db("SELECT SUM(quantity) as cnt FROM cart WHERE user_id = %s", (user_id,), one=True)
            cart_count = int(cart_res['cnt']) if (cart_res and cart_res['cnt']) else 0
        elif guest_id:
            cart_res = query_db("SELECT SUM(quantity) as cnt FROM cart WHERE session_id = %s", (guest_id,), one=True)
            cart_count = int(cart_res['cnt']) if (cart_res and cart_res['cnt']) else 0

        # 6. Live Wishlist Count
        wishlist_count = 0
        if user_id:
            wish_res = query_db("SELECT COUNT(*) as cnt FROM wishlist WHERE user_id = %s", (user_id,), one=True)
            wishlist_count = int(wish_res['cnt']) if wish_res else 0

        return dict(
            current_user=user,
            active_mode=active_mode,
            global_site_mode=global_site_mode,
            all_categories=categories,
            store_settings=store_settings,
            cart_count=cart_count,
            wishlist_count=wishlist_count,
            current_year=datetime.datetime.now().year
        )

    # ---------------------------------------------------------
    # Custom Jinja Filters
    # ---------------------------------------------------------
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            val = float(value)
            return f"₹ {val:,.2f}"
        except (ValueError, TypeError):
            return "₹ 0.00"

    @app.template_filter('format_date')
    def format_date_filter(value, fmt='%d %b %Y, %I:%M %p'):
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime(fmt)
        return str(value)

    @app.template_filter('discount_pct')
    def discount_pct_filter(mrp, selling):
        try:
            m = float(mrp)
            s = float(selling)
            if m > s and m > 0:
                return round(((m - s) / m) * 100)
            return 0
        except (ValueError, TypeError):
            return 0

    # ---------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
