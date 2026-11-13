-- Small test data set for pytest and CI (no Olist download needed).

-- Run after 01_schema.sql INSTEAD OF 02_load.sql. Safe to run again.

-- Two sellers (seller_a, seller_b) so tests can prove one seller never sees the other's rows.

BEGIN;
TRUNCATE raw.olist_order_reviews, raw.olist_order_payments, raw.olist_order_items, raw.olist_orders,
         raw.olist_products, raw.olist_sellers, raw.olist_customers, raw.olist_geolocation,
         raw.product_category_name_translation;

INSERT INTO raw.product_category_name_translation VALUES
  ('beleza_saude', 'health_beauty'),
  ('moveis_decoracao', 'furniture_decor'),
  ('informatica_acessorios', 'computers_accessories');

INSERT INTO raw.olist_customers VALUES
  ('cust_01', 'person_1', '01001', 'sao paulo', 'SP'),
  ('cust_02', 'person_2', '01002', 'campinas', 'SP'),
  ('cust_03', 'person_3', '01003', 'rio de janeiro', 'RJ'),
  ('cust_04', 'person_4', '01004', 'curitiba', 'PR'),
  ('cust_05', 'person_5', '01005', 'salvador', 'BA'),
  ('cust_06', 'person_6', '01006', 'salvador', 'BA'),
  ('cust_07', 'person_1', '01001', 'sao paulo', 'SP'),
  ('cust_08', 'person_2', '01002', 'campinas', 'SP'),
  ('cust_09', 'person_3', '01003', 'rio de janeiro', 'RJ'),
  ('cust_10', 'person_4', '01004', 'curitiba', 'PR'),
  ('cust_11', 'person_5', '01005', 'salvador', 'BA'),
  ('cust_12', 'person_6', '01006', 'salvador', 'BA');

INSERT INTO raw.olist_sellers VALUES
  ('seller_a', '13023', 'campinas', 'SP'),
  ('seller_b', '80010', 'curitiba', 'PR');

INSERT INTO raw.olist_products VALUES
  ('prod_1', 'beleza_saude', 40, 300, 2, 250, 16, 10, 12),
  ('prod_2', 'moveis_decoracao', 55, 800, 4, 9000, 80, 40, 60),
  ('prod_3', 'informatica_acessorios', 48, 500, 3, 400, 20, 5, 15),
  ('prod_4', NULL, 30, 100, 1, 150, 10, 10, 10);

INSERT INTO raw.olist_orders VALUES
  ('order_01', 'cust_01', 'delivered', '2018-05-10 11:00:00', '2018-05-10 13:00:00', '2018-05-11 11:00:00', '2018-05-15 11:00:00', '2018-05-20 11:00:00'),
  ('order_02', 'cust_02', 'delivered', '2018-05-13 12:00:00', '2018-05-13 14:00:00', '2018-05-15 12:00:00', '2018-05-31 12:00:00', '2018-05-25 12:00:00'),
  ('order_03', 'cust_03', 'delivered', '2018-05-16 13:00:00', '2018-05-16 15:00:00', '2018-05-17 13:00:00', '2018-05-22 13:00:00', '2018-05-27 13:00:00'),
  ('order_04', 'cust_04', 'shipped', '2018-05-19 14:00:00', '2018-05-19 16:00:00', '2018-05-21 14:00:00', NULL, '2018-05-28 14:00:00'),
  ('order_05', 'cust_05', 'canceled', '2018-05-22 15:00:00', '2018-05-22 17:00:00', NULL, NULL, '2018-06-05 15:00:00'),
  ('order_06', 'cust_06', 'delivered', '2018-05-25 16:00:00', '2018-05-25 18:00:00', '2018-05-26 16:00:00', '2018-05-29 16:00:00', '2018-06-02 16:00:00'),
  ('order_07', 'cust_07', 'delivered', '2018-05-28 17:00:00', '2018-05-28 19:00:00', '2018-05-29 17:00:00', '2018-06-04 17:00:00', '2018-06-07 17:00:00'),
  ('order_08', 'cust_08', 'delivered', '2018-05-31 18:00:00', '2018-05-31 20:00:00', '2018-06-05 18:00:00', '2018-06-25 18:00:00', '2018-06-15 18:00:00'),
  ('order_09', 'cust_09', 'delivered', '2018-06-03 19:00:00', '2018-06-03 21:00:00', '2018-06-04 19:00:00', '2018-06-06 19:00:00', '2018-06-12 19:00:00'),
  ('order_10', 'cust_10', 'processing', '2018-06-06 20:00:00', '2018-06-06 22:00:00', NULL, NULL, '2018-06-18 20:00:00'),
  ('order_11', 'cust_11', 'unavailable', '2018-06-09 21:00:00', '2018-06-09 23:00:00', NULL, NULL, '2018-06-19 21:00:00'),
  ('order_12', 'cust_12', 'delivered', '2018-06-12 22:00:00', '2018-06-13 00:00:00', '2018-06-14 22:00:00', '2018-06-23 22:00:00', '2018-06-25 22:00:00');

INSERT INTO raw.olist_order_items VALUES
  ('order_01', 1, 'prod_1', 'seller_a', '2018-05-13 11:00:00', 59.9, 15.59),
  ('order_02', 1, 'prod_2', 'seller_a', '2018-05-16 12:00:00', 349.0, 32.94),
  ('order_03', 1, 'prod_1', 'seller_a', '2018-05-19 13:00:00', 59.9, 15.59),
  ('order_03', 2, 'prod_3', 'seller_a', '2018-05-19 13:00:00', 129.9, 19.79),
  ('order_04', 1, 'prod_3', 'seller_a', '2018-05-22 14:00:00', 129.9, 19.79),
  ('order_05', 1, 'prod_2', 'seller_a', '2018-05-25 15:00:00', 349.0, 32.94),
  ('order_06', 1, 'prod_4', 'seller_a', '2018-05-28 16:00:00', 19.9, 13.19),
  ('order_07', 1, 'prod_3', 'seller_b', '2018-05-31 17:00:00', 129.9, 19.79),
  ('order_08', 1, 'prod_2', 'seller_b', '2018-06-03 18:00:00', 349.0, 32.94),
  ('order_09', 1, 'prod_1', 'seller_b', '2018-06-06 19:00:00', 59.9, 15.59),
  ('order_10', 1, 'prod_3', 'seller_b', '2018-06-09 20:00:00', 129.9, 19.79),
  ('order_10', 2, 'prod_4', 'seller_b', '2018-06-09 20:00:00', 19.9, 13.19),
  ('order_11', 1, 'prod_1', 'seller_b', '2018-06-12 21:00:00', 59.9, 15.59),
  ('order_12', 1, 'prod_2', 'seller_b', '2018-06-15 22:00:00', 349.0, 32.94);

INSERT INTO raw.olist_order_payments VALUES
  ('order_01', 1, 'credit_card', 1, 75.49),
  ('order_02', 1, 'credit_card', 6, 381.94),
  ('order_03', 1, 'boleto', 1, 225.18),
  ('order_04', 1, 'credit_card', 3, 149.69),
  ('order_05', 1, 'boleto', 1, 381.94),
  ('order_06', 1, 'voucher', 1, 33.09),
  ('order_07', 1, 'credit_card', 2, 149.69),
  ('order_08', 1, 'credit_card', 10, 381.94),
  ('order_09', 1, 'debit_card', 1, 75.49),
  ('order_10', 1, 'boleto', 1, 182.78),
  ('order_11', 1, 'credit_card', 1, 75.49),
  ('order_12', 1, 'credit_card', 12, 381.94);

INSERT INTO raw.olist_order_reviews VALUES
  ('review_01', 'order_01', 5, NULL, NULL, '2018-05-16 11:00:00', '2018-05-17 11:00:00'),
  ('review_02', 'order_02', 2, NULL, 'Chegou atrasado', '2018-06-01 12:00:00', '2018-06-02 12:00:00'),
  ('review_03', 'order_03', 4, NULL, NULL, '2018-05-23 13:00:00', '2018-05-24 13:00:00'),
  ('review_05', 'order_05', 1, NULL, 'Chegou atrasado', '2018-06-06 15:00:00', '2018-06-07 15:00:00'),
  ('review_06', 'order_06', 5, NULL, NULL, '2018-05-30 16:00:00', '2018-05-31 16:00:00'),
  ('review_07', 'order_07', 5, NULL, NULL, '2018-06-05 17:00:00', '2018-06-06 17:00:00'),
  ('review_08', 'order_08', 1, NULL, 'Chegou atrasado', '2018-06-26 18:00:00', '2018-06-27 18:00:00'),
  ('review_09', 'order_09', 4, NULL, NULL, '2018-06-07 19:00:00', '2018-06-08 19:00:00'),
  ('review_12', 'order_12', 3, NULL, NULL, '2018-06-24 22:00:00', '2018-06-25 22:00:00');

INSERT INTO raw.olist_geolocation VALUES
  ('13023', -22.9, -47.06, 'campinas', 'SP'),
  ('80010', -25.43, -49.27, 'curitiba', 'PR');

COMMIT;

ANALYZE;
