-- Initialize VISOR database

CREATE DATABASE visor;

\c visor

CREATE EXTENSION IF NOT EXISTS vector;

-- Sample products for testing
INSERT INTO products (product_id, title, brand, price, currency, image_url, buy_url, category) VALUES
('prod_001', 'Blue Yeti USB Microphone', 'Blue', 129.99, 'USD', 'https://example.com/images/blue-yeti.jpg', 'https://example.com/buy/blue-yeti', 'Audio'),
('prod_002', 'Sony WH-1000XM5 Headphones', 'Sony', 399.99, 'USD', 'https://example.com/images/sony-headphones.jpg', 'https://example.com/buy/sony-headphones', 'Audio'),
('prod_003', 'Herman Miller Aeron Chair', 'Herman Miller', 1395.00, 'USD', 'https://example.com/images/aeron-chair.jpg', 'https://example.com/buy/aeron-chair', 'Furniture'),
('prod_004', 'Philips Hue Smart Bulb', 'Philips', 49.99, 'USD', 'https://example.com/images/hue-bulb.jpg', 'https://example.com/buy/hue-bulb', 'Lighting'),
('prod_005', 'Apple MacBook Pro 16"', 'Apple', 2499.00, 'USD', 'https://example.com/images/macbook-pro.jpg', 'https://example.com/buy/macbook-pro', 'Electronics');
