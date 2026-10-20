# Kumar Store - E-Commerce Grocery Web Application (Dual-Mode B2C & B2B)

A production-ready, customized e-commerce web platform engineered for **"Kumar Store"**, a high-volume South Indian grocery enterprise serving both **Retail Consumers (B2C)** and **Wholesale Mandi Buyers (B2B)**.

---

## 🚀 Key Highlights & Tech Stack

- **Backend**: Python 3.10+ / **Flask** using a clean modular architecture (**Blueprints**: `auth`, `shop`, `admin`, `api`).
- **Database**: **MySQL 8.0+** using **raw direct SQL execution** via `PyMySQL` (Strictly **NO ORM / NO SQLAlchemy**).
- **Security**: 100% Parameterized queries to eliminate SQL injection vulnerabilities; Session-based authentication with `werkzeug.security` password hashing (`scrypt`).
- **Dual-Mode System**:
  - **B2C Mode (Retail)**: Standard consumer retail pricing, small unit packaging (250g, 500g, 1kg, 5kg), standard order limits.
  - **B2B Mode (Wholesale)**: Direct Mandi bulk discount rates, Minimum Order Quantities (MOQ), commercial bulk sacks (25kg, 50kg, 15L tins, master cartons), full GST tax invoice breakdown with Input Tax Credit (ITC).
  - **Admin Dual-Control**: Real-time global mode switch (`HYBRID`, `B2C`, `B2B`) and customer role management.
- **Frontend & Design System**: Mobile-first responsive green & white fresh grocery theme, HTML5, CSS3, Vanilla JavaScript, Bootstrap 5, Bootstrap Icons, with SVG image fallbacks.
- **Mandatory 10 Categories**:
  1. Dal and Pulse
  2. Rice
  3. Flour and Sooji
  4. Masala and Spices
  5. Oil and Food Grains
  6. Snacks and Beverages
  7. Beauty and Hygiene
  8. Detergent and Household Care
  9. Napkins
  10. Other Products

---

## 📁 Folder Structure Overview

```
kumarstore_website/
│
├── .env.example               # Template environment variables
├── .env                       # Local environment configuration
├── requirements.txt           # Python package dependencies
├── config.py                  # Flask configuration & database parameters
├── db.py                      # Raw PyMySQL connector, context managers, dict-cursor helpers
├── schema.sql                 # MySQL DDL (tables, primary/foreign keys, indexes)
├── seed.sql                   # 10 categories, multi-unit products, banners, coupons, reviews
├── init_db.py                 # CLI database schema & seed execution script
├── app.py                     # Flask application factory, context processors, custom filters
├── test_app.py                # Automated unit tests for all routes and APIs
├── test_e2e_checkout.py       # End-to-end B2B/B2C checkout and tax invoice journey test
│
├── blueprints/
│   ├── auth/                  # Authentication & Profile Blueprint
│   │   ├── __init__.py
│   │   └── routes.py          # /login, /register, /logout, /profile, /upgrade-b2b
│   ├── shop/                  # Storefront & Order Fulfillment Blueprint
│   │   ├── __init__.py
│   │   └── routes.py          # /, /category/<slug>, /product/<slug>, /cart, /checkout,
│   │                          # /orders, /orders/<id>/track, /orders/<id>/invoice, /wishlist
│   ├── admin/                 # Admin Operations Dashboard Blueprint
│   │   ├── __init__.py
│   │   └── routes.py          # /admin, /admin/products, /admin/categories, /admin/banners,
│   │                          # /admin/orders, /admin/users, /admin/feedback, /admin/settings
│   └── api/                   # AJAX JSON Endpoints
│       ├── __init__.py
│       └── routes.py          # /api/cart/add, /api/cart/update, /api/cart/remove,
│                              # /api/wishlist/toggle, /api/coupon/apply
│
├── static/
│   ├── css/
│   │   └── style.css          # Green & White fresh grocery design system
│   ├── js/
│   │   ├── main.js            # Live cart badge, variant selector, quantity counter, toasts
│   │   └── admin.js           # Admin table search & status transition helpers
│   ├── img/
│   │   └── fallback.svg       # SVG grocery fallback for missing images
│   └── uploads/               # Directory for user uploaded media
│
└── templates/
    ├── base.html              # Base layout with navbar, alerts, footer, toast container
    ├── 404.html               # Custom 404 Not Found error page
    ├── 500.html               # Custom 500 Server Error page
    ├── components/
    │   ├── navbar.html        # Layer 1 Header / Navbar with search & 10 categories subnav
    │   ├── product_card.html  # Standardized product display card with variant selector
    │   └── footer.html        # Trust badges, 10 categories links, GSTIN & support info
    ├── shop/
    │   ├── index.html         # Layer 1, Layer 2 (Carousel), Layer 3 (Category Showcase)
    │   ├── category.html      # Category products list with sorting & filters
    │   ├── product_detail.html# Multi-unit variants, retail vs wholesale table, reviews
    │   ├── search.html        # Search results page
    │   ├── cart.html          # Interactive cart with MOQ alerts & coupon entry
    │   ├── checkout.html      # Shipping address, B2B GSTIN input, simulated payments
    │   ├── order_success.html # Order confirmation & invoice link
    │   ├── orders.html        # User order history
    │   ├── order_detail.html  # Itemized order breakdown
    │   ├── order_track.html   # Multi-step status indicator (Placed -> Packed -> Shipped...)
    │   ├── invoice.html       # Printable & downloadable GST tax invoice
    │   ├── wishlist.html      # Saved products
    │   └── feedback.html      # Community reviews & feedback form
    ├── auth/
    │   ├── login.html         # B2C / B2B tabbed login with demo accounts helper
    │   ├── register.html      # Registration with dynamic B2B company name & GSTIN
    │   └── profile.html       # Profile editor, address book, B2B upgrade request
    └── admin/
        ├── base.html          # Admin sidebar layout & topbar
        ├── dashboard.html     # Operations KPIs, recent orders, inventory alerts
        ├── products.html      # Products catalog & filter
        ├── product_form.html  # Product editor & unit variant manager
        ├── categories.html    # 10 categories CRUD
        ├── banners.html       # Hero carousel offer banners CRUD
        ├── orders.html        # Order management with live status transitions
        ├── order_view.html    # Itemized order admin view & fulfillment log
        ├── users.html         # Customer accounts & B2B verification panel
        ├── feedback.html      # Customer review moderation
        ├── settings.html      # Global site mode (B2C / B2B / HYBRID) & GSTIN setup
        └── coupons.html       # Discount promo coupons CRUD
```

---

## 🛠️ Local Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0+** running locally or remotely

### 2. Clone / Open Directory
```bash
cd c:\Users\dell\Desktop\Santha\kumarstore_website
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```
*(Dependencies: `Flask`, `PyMySQL`, `python-dotenv`, `cryptography`, `Werkzeug`)*

### 4. Configure Environment Variables (`.env`)
Create or edit the `.env` file in the root directory:
```env
# Flask
SECRET_KEY=kumar_store_super_secret_production_key_2026
FLASK_APP=app.py
DEBUG=True

# MySQL Credentials
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=Admin@123
DB_NAME=kumarstore_db

# Storefront Mode: HYBRID, B2C, or B2B
SITE_MODE=HYBRID
```

### 5. Initialize the Database & Seed Data
Execute the bundled migration and seeding script:
```bash
python init_db.py
```
This automatically:
- Creates the `kumarstore_db` database with `utf8mb4_unicode_ci`.
- Executes `schema.sql` (all 13 relational tables, foreign keys, indexes).
- Executes `seed.sql` (all 10 categories, 23 sample products, 72 unit variants, banners, coupons, reviews, and test accounts).

---

## 🧪 Running Automated Tests

Run the included unit test suite to verify all endpoints, database queries, and B2B/B2C workflows:
```bash
# Core unit test suite (8 tests)
python test_app.py

# End-to-end B2B checkout, tracking, and GST invoice verification test
python test_e2e_checkout.py
```

---

## 🚀 Starting the Web Application

Run the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 🔑 Pre-Configured Demo Accounts

Use these pre-seeded accounts to experience all three system roles:

| Role | Email Address | Password | Features & Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@kumarstore.com` | `Admin@123` | Full access to `/admin` dashboard, inventory, live status transitions, B2C/B2B site mode switch, review moderation. |
| **Retail Consumer (B2C)** | `user@kumarstore.com` | `User@123` | Individual packaging (500g, 1kg), standard prices, wishlist, orders, retail invoices. |
| **Wholesale Mandi (B2B)** | `wholesale@kumarstore.com` | `B2B@123` | Sri Krishna Traders, GSTIN `33AAAAA0000A1Z5`, Mandi bulk packs (25kg, 50kg), wholesale rates, MOQ enforcement, GST tax invoices. |

---

## 💼 Dual-Mode B2C & B2B Architecture

1. **Retail Mode (B2C)**:
   - Evaluates units with `unit_type IN ('B2C', 'BOTH')`.
   - Prices items using `selling_price`.
   - Default Minimum Order Quantity (MOQ) is `1`.
2. **Wholesale Mode (B2B)**:
   - Evaluates units with `unit_type IN ('B2B', 'BOTH')`.
   - Prices items using discounted bulk `b2b_price`.
   - Enforces Minimum Order Quantities (MOQ, e.g. 5 or 10 units for large sacks).
   - Invoices include Seller & Buyer GSTIN, HSN codes, and tax breakdown for 100% Input Tax Credit.
3. **Global Control in Admin Panel (`/admin/settings`)**:
   - `HYBRID`: Retail users see retail prices, B2B logged-in accounts automatically see wholesale prices, and guests can toggle previews.
   - `B2C`: Forces the entire storefront into retail mode.
   - `B2B`: Forces wholesale mandi mode across all catalog views.

---

## 📦 Verified Deliverables Checklist

- [x] **Tech Stack**: Python Flask (Blueprints: `auth`, `shop`, `admin`, `api`), raw `PyMySQL`, strictly **NO ORM**.
- [x] **Database Schema**: `schema.sql` with tables, foreign keys, indexes, and parameterized queries.
- [x] **Seed Data**: `seed.sql` with all **10 mandatory grocery categories**, 23 products, and 72 packaging variants.
- [x] **Layer 1-2-3 Landing Page**:
  - **Layer 1**: Header, Brand Logo, Category dropdown, Search Bar, Live Cart Badge.
  - **Layer 2**: Hero Offer Carousel with promotional banners and promo coupons.
  - **Layer 3**: Category-wise showcase with multi-unit selector cards and "View All" links.
- [x] **Product Display Cards**: Dynamic price updating on variant switch, live stock status badge, discount tag, + / - counter, wishlist heart toggle, static image fallback.
- [x] **Order Tracking**: 5-step status stepper (`Order Placed` -> `Packed` -> `Shipped` -> `Out for Delivery` -> `Delivered`).
- [x] **GST Tax Invoice**: Professional printable tax invoice with HSN codes, Buyer/Seller GSTIN, and tax breakdown.
- [x] **Admin Operations**: Full CRUD for Products, Categories, Banners, Orders, Users, Reviews, and Store Settings.
