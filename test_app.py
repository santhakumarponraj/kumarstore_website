import unittest
from app import create_app
from db import query_db

class KumarStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_database_connected(self):
        cats = query_db("SELECT COUNT(*) as cnt FROM categories", one=True)
        self.assertEqual(cats['cnt'], 10, "Should have exactly 10 mandatory categories")

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Kumar Store', response.data)
        self.assertIn(b'Dal and Pulse', response.data)
        self.assertIn(b'Rice', response.data)

    def test_category_page(self):
        response = self.client.get('/category/rice')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Royal Classic Basmati Rice', response.data)

    def test_product_detail(self):
        response = self.client.get('/product/royal-classic-basmati-rice')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Royal Classic Basmati Rice', response.data)
        self.assertIn(b'HSN:', response.data)

    def test_mode_switch(self):
        response = self.client.get('/switch-mode/b2b', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_cart_api(self):
        # Fetch a unit id
        unit = query_db("SELECT id FROM product_units LIMIT 1", one=True)
        self.assertIsNotNone(unit)

        # Add to cart
        res = self.client.post('/api/cart/add', json={'unit_id': unit['id'], 'quantity': 1})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['cart_count'], 1)

        # View Cart page
        cart_page = self.client.get('/cart')
        self.assertEqual(cart_page.status_code, 200)
        self.assertIn(b'Shopping Cart', cart_page.data)

    def test_auth_login(self):
        # Test User Login
        res = self.client.post('/auth/login', data={
            'email': 'user@kumarstore.com',
            'password': 'User@123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ramesh Kumar', res.data)

    def test_admin_access(self):
        # Without login -> redirected
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 302)

        # Login as Admin
        with self.client:
            login_res = self.client.post('/auth/login', data={
                'email': 'admin@kumarstore.com',
                'password': 'Admin@123'
            }, follow_redirects=True)
            self.assertEqual(login_res.status_code, 200)

            admin_dash = self.client.get('/admin/dashboard')
            self.assertEqual(admin_dash.status_code, 200)
            self.assertIn(b'Operations', admin_dash.data)

            admin_prods = self.client.get('/admin/products')
            self.assertEqual(admin_prods.status_code, 200)

            admin_orders = self.client.get('/admin/orders')
            self.assertEqual(admin_orders.status_code, 200)

if __name__ == '__main__':
    unittest.main()
