-- Loads the nine Olist CSV files from /data. Safe to run again: it empties the tables first.
-- Run: docker compose exec -T db psql -U postgres -d analyst -v ON_ERROR_STOP=1 -f /db/02_load.sql
BEGIN;
TRUNCATE raw.olist_order_reviews, raw.olist_order_payments, raw.olist_order_items, raw.olist_orders,
         raw.olist_products, raw.olist_sellers, raw.olist_customers, raw.olist_geolocation,
         raw.product_category_name_translation;
\copy raw.product_category_name_translation FROM '/data/product_category_name_translation.csv' CSV HEADER
\copy raw.olist_customers      FROM '/data/olist_customers_dataset.csv'      CSV HEADER
\copy raw.olist_sellers        FROM '/data/olist_sellers_dataset.csv'        CSV HEADER
\copy raw.olist_products       FROM '/data/olist_products_dataset.csv'       CSV HEADER
\copy raw.olist_orders         FROM '/data/olist_orders_dataset.csv'         CSV HEADER
\copy raw.olist_order_items    FROM '/data/olist_order_items_dataset.csv'    CSV HEADER
\copy raw.olist_order_payments FROM '/data/olist_order_payments_dataset.csv' CSV HEADER
\copy raw.olist_order_reviews  FROM '/data/olist_order_reviews_dataset.csv'  CSV HEADER
\copy raw.olist_geolocation    FROM '/data/olist_geolocation_dataset.csv'    CSV HEADER
COMMIT;
ANALYZE;
SELECT 'olist_orders' AS table_name, count(*) FROM raw.olist_orders
UNION ALL SELECT 'olist_order_items', count(*) FROM raw.olist_order_items
UNION ALL SELECT 'olist_customers', count(*) FROM raw.olist_customers
UNION ALL SELECT 'olist_sellers', count(*) FROM raw.olist_sellers
UNION ALL SELECT 'olist_products', count(*) FROM raw.olist_products
UNION ALL SELECT 'olist_order_payments', count(*) FROM raw.olist_order_payments
UNION ALL SELECT 'olist_order_reviews', count(*) FROM raw.olist_order_reviews
UNION ALL SELECT 'olist_geolocation', count(*) FROM raw.olist_geolocation;
