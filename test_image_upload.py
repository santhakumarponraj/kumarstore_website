import os
import io
import unittest
from app import create_app
from config import Config
from db import query_db, execute_db

class ImageUploadTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.uploaded_files_to_clean = []
        self.created_product_id = None
        self.created_cat_id = None
        self.created_banner_id = None

        # Admin login
        res = self.client.post('/auth/login', data={
            'email': 'admin@kumarstore.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def tearDown(self):
        # Clean up database records
        if self.created_product_id:
            execute_db("DELETE FROM product_units WHERE product_id = %s", (self.created_product_id,))
            execute_db("DELETE FROM products WHERE id = %s", (self.created_product_id,))
        if self.created_cat_id:
            execute_db("DELETE FROM categories WHERE id = %s", (self.created_cat_id,))
        if self.created_banner_id:
            execute_db("DELETE FROM banners WHERE id = %s", (self.created_banner_id,))

        # Clean up files created in static/uploads
        for rel_path in self.uploaded_files_to_clean:
            cleaned = rel_path.lstrip('/')
            full_path = os.path.join(self.app.root_path, cleaned)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except OSError:
                    pass

    def test_local_product_image_upload_and_edit(self):
        # 1. Create a dummy image payload
        dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        file_data = (io.BytesIO(dummy_png), 'test_premium_rice.png')

        # 2. POST to /admin/products/new
        res = self.client.post('/admin/products/new', data={
            'name': 'Test Uploaded Premium Rice',
            'slug': 'test-uploaded-premium-rice',
            'category_id': 2, # Rice
            'description': 'Delicious organic harvest test grain.',
            'image_file': file_data,
            'hsn_code': '1006',
            'tax_rate': '5.0',
            'is_featured': '1',
            'is_active': '1',
            'unit_name': '1 kg',
            'unit_type': 'BOTH',
            'mrp': '150.00',
            'selling_price': '130.00',
            'b2b_price': '115.00',
            'stock_qty': '80'
        }, content_type='multipart/form-data', follow_redirects=False)

        self.assertEqual(res.status_code, 302, f"Expected redirect after product creation, got {res.status_code}")
        
        # 3. Query DB to verify product was created with local uploaded image path
        prod = query_db("SELECT * FROM products WHERE slug = 'test-uploaded-premium-rice'", one=True)
        self.assertIsNotNone(prod, "Product record should exist in DB")
        self.created_product_id = prod['id']

        img_url = prod['image_url']
        self.assertTrue(img_url.startswith('/static/uploads/products/'), f"Expected local upload path, got: {img_url}")
        self.assertTrue(img_url.endswith('test_premium_rice.png'), f"Filename should match: {img_url}")
        self.uploaded_files_to_clean.append(img_url)

        # 4. Check file exists on filesystem
        full_disk_path = os.path.join(self.app.root_path, img_url.lstrip('/'))
        self.assertTrue(os.path.exists(full_disk_path), f"File should exist on disk at {full_disk_path}")

        # 5. Check that Flask static endpoint can serve the uploaded image
        serve_res = self.client.get(img_url)
        self.assertEqual(serve_res.status_code, 200, "Flask should serve the uploaded image statically")
        self.assertEqual(serve_res.data, dummy_png)
        serve_res.close()

        # 6. Test updating product with a second uploaded image
        dummy_png_v2 = dummy_png + b'\x00\x00'
        file_data_v2 = (io.BytesIO(dummy_png_v2), 'test_rice_updated.png')

        res_edit = self.client.post(f"/admin/products/{self.created_product_id}/edit", data={
            'name': 'Test Uploaded Premium Rice (Updated)',
            'slug': 'test-uploaded-premium-rice',
            'category_id': 2,
            'description': 'Updated grain description',
            'image_file': file_data_v2,
            'hsn_code': '1006',
            'tax_rate': '5.0',
            'is_active': '1'
        }, content_type='multipart/form-data', follow_redirects=False)

        self.assertEqual(res_edit.status_code, 302)

        prod_updated = query_db("SELECT * FROM products WHERE id = %s", (self.created_product_id,), one=True)
        new_img_url = prod_updated['image_url']
        self.assertTrue(new_img_url.startswith('/static/uploads/products/'))
        self.assertTrue(new_img_url.endswith('test_rice_updated.png'))
        self.uploaded_files_to_clean.append(new_img_url)

        full_disk_path_v2 = os.path.join(self.app.root_path, new_img_url.lstrip('/'))
        self.assertTrue(os.path.exists(full_disk_path_v2))

    def test_local_category_and_banner_image_upload(self):
        dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        # 1. Test Category upload
        cat_file = (io.BytesIO(dummy_png), 'test_category.png')
        res_cat = self.client.post('/admin/categories', data={
            'name': 'Test Upload Category',
            'slug': 'test-upload-category',
            'description': 'Category with uploaded icon',
            'display_order': 20,
            'image_file': cat_file
        }, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res_cat.status_code, 302)

        cat = query_db("SELECT * FROM categories WHERE slug = 'test-upload-category'", one=True)
        self.assertIsNotNone(cat)
        self.created_cat_id = cat['id']
        self.assertTrue(cat['image_url'].startswith('/static/uploads/categories/'))
        self.assertTrue(cat['image_url'].endswith('test_category.png'))
        self.uploaded_files_to_clean.append(cat['image_url'])

        # 2. Test Banner upload
        banner_file = (io.BytesIO(dummy_png), 'test_banner.png')
        res_banner = self.client.post('/admin/banners', data={
            'title': 'Test Upload Banner',
            'subtitle': 'Special promotional offer',
            'badge_text': 'PROMO',
            'coupon_code': 'PROMO10',
            'link_url': '/category/rice',
            'bg_gradient': 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
            'display_order': 5,
            'image_file': banner_file
        }, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res_banner.status_code, 302)

        banner = query_db("SELECT * FROM banners WHERE title = 'Test Upload Banner'", one=True)
        self.assertIsNotNone(banner)
        self.created_banner_id = banner['id']
        self.assertTrue(banner['image_url'].startswith('/static/uploads/banners/'))
        self.assertTrue(banner['image_url'].endswith('test_banner.png'))
        self.uploaded_files_to_clean.append(banner['image_url'])

if __name__ == '__main__':
    unittest.main()
