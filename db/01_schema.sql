-- Olist raw tables. Safe to run more than once.
-- Run: docker compose exec -T db psql -U postgres -d analyst -v ON_ERROR_STOP=1 -f /db/01_schema.sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS api;

CREATE TABLE IF NOT EXISTS raw.product_category_name_translation (
  product_category_name          text PRIMARY KEY,
  product_category_name_english  text NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.olist_customers (
  customer_id               text PRIMARY KEY,   -- one per order
  customer_unique_id        text NOT NULL,      -- the same person across orders
  customer_zip_code_prefix  text,
  customer_city             text,
  customer_state            text
);

CREATE TABLE IF NOT EXISTS raw.olist_sellers (
  seller_id               text PRIMARY KEY,
  seller_zip_code_prefix  text,
  seller_city             text,
  seller_state            text
);

-- product_category_name has no foreign key: two categories in the data
-- are missing from the translation file, and some products have no category.
CREATE TABLE IF NOT EXISTS raw.olist_products (
  product_id                  text PRIMARY KEY,
  product_category_name       text,
  product_name_lenght         numeric,   -- spelling is from the source file
  product_description_lenght  numeric,   -- numeric, not int: the file may write 40.0
  product_photos_qty          numeric,
  product_weight_g            numeric,
  product_length_cm           numeric,
  product_height_cm           numeric,
  product_width_cm            numeric
);

CREATE TABLE IF NOT EXISTS raw.olist_orders (
  order_id                       text PRIMARY KEY,
  customer_id                    text NOT NULL REFERENCES raw.olist_customers (customer_id),
  order_status                   text NOT NULL,
  order_purchase_timestamp       timestamp,
  order_approved_at              timestamp,
  order_delivered_carrier_date   timestamp,
  order_delivered_customer_date  timestamp,
  order_estimated_delivery_date  timestamp
);

CREATE TABLE IF NOT EXISTS raw.olist_order_items (
  order_id             text NOT NULL REFERENCES raw.olist_orders (order_id),
  order_item_id        int  NOT NULL,
  product_id           text NOT NULL REFERENCES raw.olist_products (product_id),
  seller_id            text NOT NULL REFERENCES raw.olist_sellers (seller_id),
  shipping_limit_date  timestamp,
  price                numeric(10,2),
  freight_value        numeric(10,2),
  PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS raw.olist_order_payments (
  order_id              text NOT NULL REFERENCES raw.olist_orders (order_id),
  payment_sequential    int  NOT NULL,
  payment_type          text,
  payment_installments  int,
  payment_value         numeric(10,2),
  PRIMARY KEY (order_id, payment_sequential)
);

-- review_id repeats in the source data, so the key is (review_id, order_id).
CREATE TABLE IF NOT EXISTS raw.olist_order_reviews (
  review_id                text NOT NULL,
  order_id                 text NOT NULL REFERENCES raw.olist_orders (order_id),
  review_score             int,
  review_comment_title     text,
  review_comment_message   text,
  review_creation_date     timestamp,
  review_answer_timestamp  timestamp,
  PRIMARY KEY (review_id, order_id)
);

-- Many rows per zip prefix, so no primary key and no foreign keys point here.
CREATE TABLE IF NOT EXISTS raw.olist_geolocation (
  geolocation_zip_code_prefix  text,
  geolocation_lat              double precision,
  geolocation_lng              double precision,
  geolocation_city             text,
  geolocation_state            text
);

CREATE INDEX IF NOT EXISTS ix_orders_customer      ON raw.olist_orders (customer_id);
CREATE INDEX IF NOT EXISTS ix_orders_purchase      ON raw.olist_orders (order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS ix_items_seller         ON raw.olist_order_items (seller_id);
CREATE INDEX IF NOT EXISTS ix_items_product        ON raw.olist_order_items (product_id);
CREATE INDEX IF NOT EXISTS ix_reviews_order        ON raw.olist_order_reviews (order_id);
CREATE INDEX IF NOT EXISTS ix_customers_unique     ON raw.olist_customers (customer_unique_id);
CREATE INDEX IF NOT EXISTS ix_geo_zip              ON raw.olist_geolocation (geolocation_zip_code_prefix);
