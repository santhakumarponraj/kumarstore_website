import unittest
from app import create_app
from db import query_db

class E2ECheckoutTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_full_checkout_and_invoice_journey(self):
        # 1. Login as B2B Wholesale user
        login_res = self.client.post('/auth/login', data={
            'email': 'wholesale@kumarstore.com',
            'password': 'B2B@123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 2. Add Basmati 25kg Master pack to cart
        unit = query_db("SELECT id, moq FROM product_units WHERE unit_name LIKE %s LIMIT 1", ('%25 kg%',), one=True)
        self.assertIsNotNone(unit)

        add_res = self.client.post('/api/cart/add', json={
            'unit_id': unit['id'],
            'quantity': unit['moq']
        })
        self.assertEqual(add_res.status_code, 200)

        # 3. View Checkout page
        co_page = self.client.get('/checkout')
        self.assertEqual(co_page.status_code, 200)
        self.assertIn(b'Complete Your Order', co_page.data)

        # 4. Post Order
        order_post = self.client.post('/checkout', data={
            'shipping_name': 'Sri Krishna Wholesale Mandi',
            'shipping_phone': '9894098765',
            'shipping_address': 'Plot 88, Wholesale Grain Mandi, Koyambedu',
            'shipping_city': 'Chennai',
            'shipping_state': 'Tamil Nadu',
            'shipping_pincode': '600107',
            'buyer_company_name': 'Sri Krishna Wholesale Traders Pvt Ltd',
            'buyer_gstin': '33AAAAA0000A1Z5',
            'payment_method': 'Razorpay'
        }, follow_redirects=True)
        self.assertEqual(order_post.status_code, 200)
        self.assertIn(b'Order Successfully Placed', order_post.data)

        # 5. Fetch latest order from DB
        latest_order = query_db("SELECT * FROM orders ORDER BY id DESC LIMIT 1", one=True)
        self.assertIsNotNone(latest_order)
        self.assertEqual(latest_order['order_type'], 'b2b')
        self.assertEqual(latest_order['payment_status'], 'Paid')

        # 6. Check Tracking Page
        track_page = self.client.get(f"/orders/{latest_order['id']}/track")
        self.assertEqual(track_page.status_code, 200)
        self.assertIn(b'Live Delivery Status', track_page.data)

        # 7. Check Printable GST Invoice
        inv_page = self.client.get(f"/orders/{latest_order['id']}/invoice")
        self.assertEqual(inv_page.status_code, 200)
        self.assertIn(b'TAX INVOICE', inv_page.data)
        self.assertIn(b'00000000000000', inv_page.data)
        self.assertIn(b'33AAAAA0000A1Z5', inv_page.data)
        print("E2E B2B Wholesale checkout, tracking, and GST tax invoice verified successfully!")

if __name__ == '__main__':
    unittest.main()
