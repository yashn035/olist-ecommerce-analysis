-- =============================================================================
-- Olist E-Commerce Data Validation & Data Quality Checks
-- =============================================================================
-- Purpose: Validate data completeness, integrity, and structural anomalies 
-- before executing core business queries. Run this script in PostgreSQL.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- (A) TABLE ROW COUNTS
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- All 9 tables must be populated. Approximate expected row counts from Kaggle:
-- - orders: ~99,441
-- - order_items: ~112,650
-- - customers: ~99,441
-- - products: ~32,951
-- - sellers: ~3,095
-- - payments: ~103,886
-- - reviews: ~99,224
-- - geolocation: ~1,000,163
-- - category_translation: ~71
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL
SELECT 'category_translation', COUNT(*) FROM category_translation
ORDER BY table_name;


-- -----------------------------------------------------------------------------
-- (B.1) CUSTOMER ID VS CUSTOMER UNIQUE ID DISTINCT COUNTS
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- total_customer_ids = distinct_customer_ids (~99,441)
-- distinct_unique_customers will be LOWER (~96,096).
-- This validates that `customer_id` is an order-level proxy, whereas
-- `customer_unique_id` tracks real human individuals across multiple orders.
SELECT 
    COUNT(customer_id) AS total_customer_ids,
    COUNT(DISTINCT customer_id) AS distinct_customer_ids,
    COUNT(DISTINCT customer_unique_id) AS distinct_unique_customers,
    COUNT(customer_id) - COUNT(DISTINCT customer_unique_id) AS repeat_buyer_id_gap
FROM customers;


-- -----------------------------------------------------------------------------
-- (B.2) ORDER STATUS DISTRIBUTION
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- 'delivered' must represent >97% of all orders (~96,478).
-- Small counts for 'shipped' (~1,107), 'canceled' (~625), 'unavailable' (~609),
-- 'invoiced' (~314), 'processing' (~301), 'created' (~5), 'approved' (~2).
-- Revenue analyses MUST filter strictly for order_status = 'delivered'.
SELECT 
    order_status,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;


-- -----------------------------------------------------------------------------
-- (B.3) ORDERS WITH ZERO ITEMS
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- ~775 orders exist in the orders table with 0 associated items in order_items.
-- Crucially, NONE of these zero-item orders should have status = 'delivered'
-- (they are predominantly 'unavailable' or 'canceled').
SELECT 
    o.order_status,
    COUNT(o.order_id) AS orders_without_items
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.order_id IS NULL
GROUP BY o.order_status
ORDER BY orders_without_items DESC;


-- -----------------------------------------------------------------------------
-- (B.4) DELIVERED ORDERS WITH NULL DELIVERY DATE
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- Exactly ~8 orders have status = 'delivered' but NULL in 
-- order_delivered_customer_date. Any delivery speed/lateness calculations
-- must filter out orders where order_delivered_customer_date IS NULL.
SELECT 
    COUNT(*) AS delivered_orders_with_null_delivered_date
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NULL;


-- -----------------------------------------------------------------------------
-- (B.5) MIN / MAX ORDER PURCHASE TIMESTAMP (EXPOSING TRUNCATED MONTHS)
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- min_purchase_timestamp is ~2016-09-04 and max_purchase_timestamp is ~2018-10-17.
-- However, monthly aggregation reveals 2016 is sporadic pilot data (under 350 orders),
-- and September/October 2018 contains only a few orders.
-- Analysis window must be bounded to 2017-01-01 through 2018-08-31.
SELECT 
    MIN(order_purchase_timestamp) AS min_purchase_timestamp,
    MAX(order_purchase_timestamp) AS max_purchase_timestamp,
    DATE_TRUNC('month', MIN(order_purchase_timestamp)) AS earliest_month,
    DATE_TRUNC('month', MAX(order_purchase_timestamp)) AS latest_month
FROM orders;


-- -----------------------------------------------------------------------------
-- (B.6) DUPLICATE GEOLOCATION ROWS PER ZIP PREFIX
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- There are ~19,015 distinct zip code prefixes, but over 1,000,000 rows.
-- Multiple entries per zip code represent street-level coordinates and slight
-- city spelling variations. Geolocation cannot be joined directly on 
-- zip_code_prefix without first taking the average coordinate or mode state/city.
SELECT 
    COUNT(geolocation_zip_code_prefix) AS total_geo_rows,
    COUNT(DISTINCT geolocation_zip_code_prefix) AS distinct_zip_prefixes,
    ROUND(COUNT(*)::numeric / COUNT(DISTINCT geolocation_zip_code_prefix), 2) AS avg_rows_per_zip_prefix,
    MAX(zip_count) AS max_rows_for_single_zip
FROM (
    SELECT geolocation_zip_code_prefix, COUNT(*) AS zip_count
    FROM geolocation
    GROUP BY geolocation_zip_code_prefix
) sub;


-- -----------------------------------------------------------------------------
-- (B.7) DUPLICATE REVIEW_ID CHECK
-- -----------------------------------------------------------------------------
-- What a correct result looks like:
-- ~800+ review_ids appear more than once (approx. 98,410 unique review_ids 
-- across 99,224 rows). This occurs when customers review multi-item orders
-- or update review text/answers. Joins to reviews must account for 1:N relations.
SELECT 
    review_id,
    COUNT(*) AS occurrence_count
FROM reviews
GROUP BY review_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC
LIMIT 10;
