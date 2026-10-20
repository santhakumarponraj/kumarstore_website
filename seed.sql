-- ========================================================
-- KUMAR STORE DATABASE SEED SCRIPT
-- Sample Data with 10 Mandatory Categories & Dual B2C/B2B Units
-- ========================================================

USE `kumarstore_db`;

-- 1. Store Settings
INSERT INTO `store_settings` (`setting_key`, `setting_value`, `description`) VALUES
('site_mode', 'HYBRID', 'Global storefront mode: HYBRID, B2C, or B2B'),
('store_name', 'Kumar Store', 'Store brand name'),
('store_tagline', 'Fresh Groceries & Wholesale Supplies Daily', 'Store slogan'),
('store_gstin', '00000000000000', 'GSTIN identification number for tax invoices'),
('store_phone', '8122687377', 'Primary customer care phone number'),
('store_email', 'santhakumarponraj@gmail.com', 'Official support email address'),
('store_address', '81/135, Kuppichipalayam road, Periyanaickenpalayam, Coimbatore - 641020', 'Physical store & warehouse address'),
('free_shipping_threshold', '1000.00', 'Minimum order amount for free delivery in retail'),
('standard_shipping_fee', '50.00', 'Standard flat delivery charge if below free threshold');

-- 2. Initial Users
INSERT INTO `users` (`name`, `email`, `password_hash`, `phone`, `role`, `company_name`, `gstin`, `is_b2b_verified`, `address`, `city`, `state`, `pincode`) VALUES
('Admin Kumar', 'admin@kumarstore.com', 'scrypt:32768:8:1$ei8XU3YRpaD7rLbo$31c564c69196741db188dcde6efd829d4c06e2b1bf7d614d26b3471036707991b1d15506bffa7eeb669aafd487adbc90acba13e1505a7baa48d8766f8949dc3b', '8122687377', 'admin', 'Kumar Store HQ', '00000000000000', TRUE, '81/135, Kuppichipalayam road, Periyanaickenpalayam', 'Coimbatore', 'Tamil Nadu', '641020'),
('Ramesh Kumar (Retail)', 'user@kumarstore.com', 'scrypt:32768:8:1$yeQ7Cw4qYoJuE5eI$bfec64848402344667d8ec50d9e33adcb4698cd96661bdef072990c04c8ded37ef4010a09b926155c3e33bc39cb48ba77ed1655121815df48b0f7350b778d6f8', '9840123456', 'b2c', NULL, NULL, FALSE, '15 Green Park Avenue, Anna Nagar', 'Chennai', 'Tamil Nadu', '600040'),
('Sri Krishna Traders (Wholesale)', 'wholesale@kumarstore.com', 'scrypt:32768:8:1$ZhYubTujghIZgJ8M$dc32ad62ae38e00811bddbe1f14c8577392a4d7af6eb6eee7a30e67a0382a9beabf14353f3d6f41d5ccc6729707d60968d11f356a0d05d940f9bf1beb25b863e', '9894098765', 'b2b', 'Sri Krishna Wholesale Traders Pvt Ltd', '33AAAAA0000A1Z5', TRUE, 'Plot 88, Wholesale Grain Mandi, Koyambedu', 'Chennai', 'Tamil Nadu', '600107');

-- 3. The 10 Mandatory Categories
INSERT INTO `categories` (`id`, `name`, `slug`, `description`, `image_url`, `display_order`) VALUES
(1, 'Dal and Pulse', 'dal-and-pulse', 'Premium quality lentils, unpolished pulses, and grams sourced directly from farms.', 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?w=500&auto=format&fit=crop&q=80', 1),
(2, 'Rice', 'rice', 'Aged Basmati, Sona Masoori, Ponni boiled rice, and organic raw rice selections.', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500&auto=format&fit=crop&q=80', 2),
(3, 'Flour and Sooji', 'flour-and-sooji', 'Freshly ground chakki atta, maida, semolina, roasted rava, and gram flour.', 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=80', 3),
(4, 'Masala and Spices', 'masala-and-spices', 'Whole aromatic spices, blended garam masalas, pure turmeric, and red chilli powders.', 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=500&auto=format&fit=crop&q=80', 4),
(5, 'Oil and Food Grains', 'oil-and-food-grains', 'Cold-pressed cooking oils, refined sunflower oils, pure cow ghee, and nutritious millets.', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&auto=format&fit=crop&q=80', 5),
(6, 'Snacks and Beverages', 'snacks-and-beverages', 'Crispy traditional namkeens, biscuits, roasted dry fruits, filter coffee, and premium tea blends.', 'https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=500&auto=format&fit=crop&q=80', 6),
(7, 'Beauty and Hygiene', 'beauty-and-hygiene', 'Herbal soaps, shampoos, oral hygiene care, body washes, and daily personal grooming.', 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop&q=80', 7),
(8, 'Detergent and Household Care', 'detergent-and-household-care', 'High-efficiency laundry powders, dishwashing liquids, floor cleaners, and disinfectants.', 'https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=500&auto=format&fit=crop&q=80', 8),
(9, 'Napkins', 'napkins', 'Soft facial tissues, kitchen paper rolls, table napkins, and wet wipes for daily hygiene.', 'https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=500&auto=format&fit=crop&q=80', 9),
(10, 'Other Products', 'other-products', 'Pooja essentials, matchboxes, aluminium foils, disposables, and general provisions.', 'https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=500&auto=format&fit=crop&q=80', 10);

-- 4. Products across the 10 categories
INSERT INTO `products` (`id`, `category_id`, `name`, `slug`, `description`, `image_url`, `is_featured`, `is_active`, `hsn_code`, `tax_rate`) VALUES
-- Category 1: Dal and Pulse
(1, 1, 'Premium Toor Dal (Pigeon Pea)', 'premium-toor-dal', 'High-protein, unpolished desi Toor Dal. Cooks smooth and delivers authentic aroma for sambar and dal fry.', 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0713', 0.00),
(2, 1, 'Organic Moong Dal Yellow', 'organic-moong-dal-yellow', 'Naturally polished yellow split moong dal, easy to digest and rich in vitamins and dietary fibre.', 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0713', 0.00),
(3, 1, 'Black Urad Dal Whole', 'black-urad-dal-whole', 'A-Grade whole black urad dal, ideal for making crispy dosas, fluffy idlis, and traditional dal makhani.', 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '0713', 0.00),

-- Category 2: Rice
(4, 2, 'Royal Classic Basmati Rice', 'royal-classic-basmati-rice', 'Extra long grain, aged 2 years for signature aroma and fluffy, non-sticky grains upon cooking.', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '1006', 0.00),
(5, 2, 'South Indian Sona Masoori Raw Rice', 'sona-masoori-raw-rice', 'Lightweight, aromatic medium grain rice harvested from the Cauvery delta, perfect for daily meals.', 'https://images.unsplash.com/photo-1536304929831-ee1ca9d44906?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '1006', 0.00),
(6, 2, 'Tanjore Ponni Boiled Rice', 'tanjore-ponni-boiled-rice', 'Nutrient-rich parboiled Ponni rice, firm grain texture, ideal for everyday South Indian dining.', 'https://images.unsplash.com/photo-1516684732162-798a0062be99?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '1006', 0.00),

-- Category 3: Flour and Sooji
(7, 3, '100% Whole Wheat Chakki Atta', 'whole-wheat-chakki-atta', 'Traditional stone-ground whole wheat flour retaining 100% bran and germ for soft, fluffy rotis.', 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '1101', 0.00),
(8, 3, 'Roasted Wheat Sooji (Rava)', 'roasted-wheat-sooji', 'Pre-roasted granulated wheat semolina for quick and lump-free upma, halwa, and rava dosa.', 'https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '1103', 5.00),

-- Category 4: Masala and Spices
(9, 4, 'Pure Malabar Black Pepper', 'pure-malabar-black-pepper', 'Handpicked bold black peppercorns from the hills of Wayanad, high piperine content and intense heat.', 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0904', 5.00),
(10, 4, 'Organic Salem Turmeric Powder', 'organic-salem-turmeric-powder', 'Golden turmeric ground from dry Salem fingers with over 3.5% natural curcumin content.', 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0910', 5.00),
(11, 4, 'Authentic Madras Sambar Powder', 'authentic-madras-sambar-powder', 'Artisanal secret blend of roasted coriander, red chillies, fenugreek, and asafoetida.', 'https://images.unsplash.com/photo-1505253758473-96b46c5f69ee?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '2103', 5.00),

-- Category 5: Oil and Food Grains
(12, 5, 'Cold Pressed Groundnut Oil', 'cold-pressed-groundnut-oil', 'Extracted using traditional wooden chekku / ghani without heat treatment to preserve natural antioxidants.', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '1508', 5.00),
(13, 5, 'Pure Desi Cow Ghee (Bilona)', 'pure-desi-cow-ghee', 'Traditional cultured butter churned ghee with rich golden granules and irresistible festive aroma.', 'https://images.unsplash.com/photo-1589927986089-35812388d1f4?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0405', 12.00),

-- Category 6: Snacks and Beverages
(14, 6, 'South Indian Filter Coffee Powder (80:20)', 'filter-coffee-powder', 'Freshly roasted plantation peaberry beans blended with 20% premium chicory for thick decoction.', 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '0901', 5.00),
(15, 6, 'Crunchy Roasted Cashews (W240)', 'crunchy-roasted-cashews', 'Jumbo grade W240 whole cashew nuts roasted with a pinch of Himalayan pink salt.', 'https://images.unsplash.com/photo-1509358271058-acd22cc93898?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '0801', 5.00),

-- Category 7: Beauty and Hygiene
(16, 7, 'Natural Ayurvedic Neem & Tulsi Bath Soap', 'neem-tulsi-bath-soap', 'Antibacterial herbal bath soap enriched with cold-pressed neem oil, basil extracts, and coconut base.', 'https://images.unsplash.com/photo-1607006314187-c729cb190578?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '3401', 18.00),
(17, 7, 'Complete Herbal Clove Toothpaste', 'herbal-clove-toothpaste', 'Ayurvedic toothpaste with pure clove oil and mint for long-lasting fresh breath and gum protection.', 'https://images.unsplash.com/photo-1559599101-f09722fb4948?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '3306', 18.00),

-- Category 8: Detergent and Household Care
(18, 8, 'Ultra Clean Active Laundry Powder', 'ultra-clean-laundry-powder', 'Advanced enzymatic stain-removal washing powder suitable for top load, front load, and hand wash.', 'https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '3402', 18.00),
(19, 8, 'Lemon Fresh Anti-Bacterial Dishwash Gel', 'lemon-dishwash-gel', 'Super concentrated grease-cutting liquid with real lime extract, leaves zero residue on utensils.', 'https://images.unsplash.com/photo-1585670210693-e7fdd16b142e?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '3402', 18.00),

-- Category 9: Napkins
(20, 9, '2-Ply Soft Touch Table Napkins (100 Pcs)', '2-ply-table-napkins', '100% virgin pulp, highly absorbent, chlorine-free and safe for food contact and dining.', 'https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=500&auto=format&fit=crop&q=80', TRUE, TRUE, '4818', 12.00),
(21, 9, 'Multi-Use Kitchen Paper Towel Roll', 'kitchen-paper-towel-roll', 'Extra thick embossed paper towels for absorbing excess oil, spill cleanup, and surface wiping.', 'https://images.unsplash.com/photo-1616401784845-180882ba9ba8?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '4818', 12.00),

-- Category 10: Other Products
(22, 10, 'Pure Camphor Tablets for Pooja', 'pure-camphor-tablets', '100% refined Bhimseni camphor tablets, burns completely without leaving ash or black soot.', 'https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '2914', 12.00),
(23, 10, 'Heavy Duty Food Grade Aluminium Foil (18m)', 'food-grade-aluminium-foil', '11-micron thick kitchen foil keeps food fresh, warm, and hygienic for travel and lunchboxes.', 'https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=500&auto=format&fit=crop&q=80', FALSE, TRUE, '7607', 18.00);

-- 5. Product Units with Dual B2C and B2B Variants
INSERT INTO `product_units` (`product_id`, `unit_name`, `unit_type`, `mrp`, `selling_price`, `b2b_price`, `moq`, `stock_qty`, `is_default`) VALUES
-- 1: Toor Dal
(1, '500 g', 'B2C', 110.00, 95.00, 85.00, 1, 150, FALSE),
(1, '1 kg', 'BOTH', 210.00, 175.00, 155.00, 1, 300, TRUE),
(1, '5 kg Bag', 'BOTH', 1050.00, 850.00, 750.00, 1, 80, FALSE),
(1, '25 kg Sack', 'B2B', 5250.00, 4250.00, 3600.00, 5, 40, FALSE),

-- 2: Moong Dal
(2, '500 g', 'B2C', 85.00, 72.00, 65.00, 1, 120, FALSE),
(2, '1 kg', 'BOTH', 160.00, 138.00, 120.00, 1, 200, TRUE),
(2, '25 kg Sack', 'B2B', 4000.00, 3450.00, 2850.00, 3, 35, FALSE),

-- 3: Urad Dal
(3, '500 g', 'B2C', 95.00, 82.00, 74.00, 1, 100, FALSE),
(3, '1 kg', 'BOTH', 180.00, 155.00, 135.00, 1, 180, TRUE),
(3, '30 kg Sack', 'B2B', 5400.00, 4650.00, 3900.00, 2, 25, FALSE),

-- 4: Basmati Rice
(4, '1 kg', 'B2C', 180.00, 145.00, 130.00, 1, 250, TRUE),
(4, '5 kg Bag', 'BOTH', 899.00, 699.00, 610.00, 1, 120, FALSE),
(4, '25 kg Master Pack', 'B2B', 4500.00, 3495.00, 2900.00, 5, 50, FALSE),

-- 5: Sona Masoori
(5, '1 kg', 'B2C', 70.00, 58.00, 50.00, 1, 300, FALSE),
(5, '5 kg Bag', 'BOTH', 340.00, 275.00, 240.00, 1, 150, TRUE),
(5, '25 kg Bag', 'BOTH', 1650.00, 1320.00, 1150.00, 1, 90, FALSE),
(5, '50 kg Jute Bag', 'B2B', 3300.00, 2640.00, 2200.00, 5, 45, FALSE),

-- 6: Tanjore Ponni Boiled
(6, '5 kg Bag', 'BOTH', 320.00, 265.00, 230.00, 1, 140, TRUE),
(6, '25 kg Bag', 'BOTH', 1550.00, 1250.00, 1080.00, 1, 80, FALSE),
(6, '50 kg Bag', 'B2B', 3100.00, 2500.00, 2050.00, 5, 30, FALSE),

-- 7: Whole Wheat Atta
(7, '1 kg', 'B2C', 60.00, 49.00, 42.00, 1, 200, FALSE),
(7, '5 kg Bag', 'BOTH', 280.00, 225.00, 195.00, 1, 180, TRUE),
(7, '10 kg Bag', 'BOTH', 550.00, 435.00, 375.00, 1, 110, FALSE),
(7, '50 kg Commercial Sack', 'B2B', 2750.00, 2175.00, 1750.00, 5, 40, FALSE),

-- 8: Roasted Sooji
(8, '500 g', 'B2C', 45.00, 38.00, 32.00, 1, 150, TRUE),
(8, '1 kg', 'BOTH', 85.00, 72.00, 60.00, 1, 100, FALSE),
(8, '25 kg Sack', 'B2B', 2125.00, 1800.00, 1420.00, 2, 20, FALSE),

-- 9: Black Pepper
(9, '100 g', 'B2C', 120.00, 99.00, 85.00, 1, 120, FALSE),
(9, '250 g', 'BOTH', 290.00, 235.00, 205.00, 1, 90, TRUE),
(9, '1 kg Pouch', 'BOTH', 1100.00, 890.00, 760.00, 1, 40, FALSE),
(9, '10 kg Wholesale Crate', 'B2B', 11000.00, 8900.00, 7200.00, 2, 15, FALSE),

-- 10: Turmeric Powder
(10, '200 g', 'B2C', 60.00, 48.00, 40.00, 1, 200, FALSE),
(10, '500 g', 'BOTH', 140.00, 115.00, 95.00, 1, 150, TRUE),
(10, '1 kg Pack', 'BOTH', 270.00, 215.00, 180.00, 1, 80, FALSE),
(10, '25 kg Bag', 'B2B', 6750.00, 5375.00, 4200.00, 2, 20, FALSE),

-- 11: Sambar Powder
(11, '100 g', 'B2C', 45.00, 38.00, 32.00, 1, 140, FALSE),
(11, '500 g', 'BOTH', 210.00, 175.00, 148.00, 1, 90, TRUE),
(11, '5 kg Catering Tub', 'B2B', 2100.00, 1750.00, 1350.00, 2, 25, FALSE),

-- 12: Groundnut Oil
(12, '1 Litre Pouch', 'B2C', 220.00, 185.00, 168.00, 1, 200, TRUE),
(12, '5 Litre Can', 'BOTH', 1080.00, 890.00, 795.00, 1, 90, FALSE),
(12, '15 Litre Commercial Tin', 'B2B', 3240.00, 2670.00, 2300.00, 3, 40, FALSE),

-- 13: Desi Cow Ghee
(13, '200 ml Jar', 'B2C', 190.00, 165.00, 145.00, 1, 100, FALSE),
(13, '500 ml Jar', 'BOTH', 450.00, 390.00, 345.00, 1, 120, TRUE),
(13, '1 Litre Jar', 'BOTH', 880.00, 760.00, 670.00, 1, 80, FALSE),
(13, '15 kg Commercial Tin', 'B2B', 13200.00, 11400.00, 9600.00, 2, 15, FALSE),

-- 14: Filter Coffee Powder
(14, '250 g', 'B2C', 140.00, 120.00, 105.00, 1, 180, TRUE),
(14, '500 g', 'BOTH', 270.00, 230.00, 198.00, 1, 120, FALSE),
(14, '5 kg Hotel Pack', 'B2B', 2700.00, 2300.00, 1850.00, 2, 30, FALSE),

-- 15: Roasted Cashews
(15, '250 g', 'B2C', 320.00, 265.00, 235.00, 1, 110, TRUE),
(15, '500 g', 'BOTH', 620.00, 510.00, 450.00, 1, 70, FALSE),
(15, '10 kg Vacuum Tin', 'B2B', 12400.00, 10200.00, 8600.00, 1, 15, FALSE),

-- 16: Neem Soap
(16, 'Pack of 3 (125g each)', 'B2C', 135.00, 115.00, 98.00, 1, 150, TRUE),
(16, 'Carton of 48 Bars', 'B2B', 2160.00, 1750.00, 1440.00, 2, 25, FALSE),

-- 17: Herbal Clove Toothpaste
(17, '150 g Tube', 'B2C', 95.00, 80.00, 68.00, 1, 180, TRUE),
(17, 'Wholesale Bundle of 24', 'B2B', 2280.00, 1850.00, 1500.00, 2, 30, FALSE),

-- 18: Laundry Powder
(18, '1 kg Pouch', 'B2C', 145.00, 125.00, 105.00, 1, 160, TRUE),
(18, '4 kg Bucket', 'BOTH', 560.00, 460.00, 395.00, 1, 80, FALSE),
(18, '25 kg Laundry Sack', 'B2B', 3500.00, 2875.00, 2350.00, 2, 20, FALSE),

-- 19: Lemon Dishwash Gel
(19, '500 ml Bottle', 'B2C', 115.00, 95.00, 80.00, 1, 200, TRUE),
(19, '2 Litre Refill Can', 'BOTH', 420.00, 345.00, 290.00, 1, 90, FALSE),
(19, '5 Litre Restaurant Can', 'B2B', 980.00, 790.00, 640.00, 3, 25, FALSE),

-- 20: Table Napkins
(20, 'Pack of 100 Pcs', 'B2C', 65.00, 52.00, 42.00, 1, 250, TRUE),
(20, 'Bundle of 10 Packs', 'BOTH', 650.00, 490.00, 390.00, 1, 80, FALSE),
(20, 'Master Carton (50 Packs)', 'B2B', 3250.00, 2450.00, 1850.00, 2, 35, FALSE),

-- 21: Kitchen Paper Towel
(21, 'Twin Roll Pack (2 x 60 pulls)', 'B2C', 130.00, 105.00, 88.00, 1, 150, TRUE),
(21, 'Box of 12 Rolls', 'B2B', 780.00, 600.00, 480.00, 3, 40, FALSE),

-- 22: Pure Camphor
(22, '50 g Box', 'B2C', 80.00, 68.00, 55.00, 1, 200, TRUE),
(22, '500 g Tub', 'BOTH', 750.00, 620.00, 510.00, 1, 60, FALSE),
(22, '5 kg Wholesale Carton', 'B2B', 7500.00, 6100.00, 4800.00, 2, 15, FALSE),

-- 23: Aluminium Foil
(23, '18 Metre Roll', 'B2C', 125.00, 105.00, 89.00, 1, 180, TRUE),
(23, '72 Metre Catering Roll', 'BOTH', 460.00, 380.00, 320.00, 1, 70, FALSE),
(23, 'Case of 24 Rolls (18m)', 'B2B', 3000.00, 2400.00, 1950.00, 2, 20, FALSE);

-- 6. Offer Banners for Carousel (Layer 2)
INSERT INTO `banners` (`title`, `subtitle`, `badge_text`, `coupon_code`, `image_url`, `link_url`, `bg_gradient`, `display_order`) VALUES
('Farm Fresh Pulses & Grains', 'Directly from certified agricultural cooperatives. Unpolished & nutritious.', 'Special Retail Offer', 'KUMAR10', 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?w=1200&auto=format&fit=crop&q=80', '/category/dal-and-pulse', 'linear-gradient(135deg, #059669 0%, #065f46 100%)', 1),
('B2B Bulk Grocery Supply', 'Special Wholesale rates, minimum order quantities, and 100% GST invoice support for hotels & shops.', 'Wholesale Mandi', 'B2BBULK5', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=1200&auto=format&fit=crop&q=80', '/category/rice', 'linear-gradient(135deg, #1e3a8a 0%, #172554 100%)', 2),
('Festive Cooking Oils & Pure Ghee', 'Traditional cold-pressed wood chekku oils and golden Vedic cow ghee.', 'Save up to 30%', 'FREESHIP', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=1200&auto=format&fit=crop&q=80', '/category/oil-and-food-grains', 'linear-gradient(135deg, #b45309 0%, #78350f 100%)', 3);

-- 7. Coupons
INSERT INTO `coupons` (`code`, `discount_type`, `discount_value`, `min_order_amount`, `applicable_mode`, `description`) VALUES
('KUMAR10', 'percentage', 10.00, 500.00, 'both', 'Get 10% off on all orders above ₹500 (Max ₹250 discount)'),
('B2BBULK5', 'percentage', 5.00, 5000.00, 'b2b', 'Extra 5% wholesale discount on bulk purchase above ₹5000'),
('FREESHIP', 'fixed', 50.00, 499.00, 'b2c', 'Enjoy free shipping on grocery retail cart above ₹499');

-- 8. Customer Reviews & Feedback
INSERT INTO `feedback` (`user_id`, `product_id`, `name`, `email`, `rating`, `subject`, `comment`, `status`) VALUES
(2, 1, 'Ramesh Kumar', 'user@kumarstore.com', 5, 'Exceptional Toor Dal Quality', 'Cooks uniformly and the aroma of authentic south Indian sambar came out wonderfully. Will definitely buy regularly.', 'approved'),
(3, 4, 'Sri Krishna Wholesale', 'wholesale@kumarstore.com', 5, 'Great B2B bulk pricing and packaging', 'We ordered 10 bags of Basmati rice for our catering business. Delivery was prompt with a clean GST invoice.', 'approved'),
(2, 12, 'Ananya Sundaram', 'ananya.s@example.com', 5, 'Authentic cold pressed aroma', 'The wood pressed groundnut oil has that natural fragrance our grandmothers used. Clean packaging!', 'approved'),
(NULL, NULL, 'Murugan Provisions', 'murugan@example.com', 5, 'Best wholesale vendor in city', 'Kumar Store is our reliable partner for dal, rice and spices. Very transparent B2B rates.', 'approved');
