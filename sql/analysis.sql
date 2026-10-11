-- =============================================================================
-- Olist E-Commerce Core Analytical Queries (SQLite Engine)
-- =============================================================================
-- Business Context: "Which factors drive revenue growth and repeat purchases, 
-- and where should retention and logistics investment go?"
--
-- Filtering Standards:
-- All revenue-related queries filter strictly for:
--   order_status = 'delivered'
--   order_purchase_timestamp >= '2017-01-01' AND order_purchase_timestamp < '2018-09-01'
-- (Excluding incomplete 2016 launch data and truncated September/October 2018).
--
-- Note on Dialect: Adapted from PostgreSQL to SQLite:
--   - DATE_TRUNC('month', x) -> strftime('%Y-%m-01', x)
--   - AGE(a, b) -> (CAST(strftime('%Y', a) AS INT) - CAST(strftime('%Y', b) AS INT)) * 12 + ...
--   - EXTRACT(EPOCH FROM ...) / 86400.0 -> julianday(end) - julianday(start)
--   - Removed ::numeric and ::date Postgres casting operators
--
-- Deliverables: Results from Q1 through Q10 exported to data/processed/.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- QUERY 1: Monthly Revenue, Orders, AOV, and Month-over-Month Growth
-- Business Question: How has revenue, order volume, and average order value 
-- evolved over time, and what is the month-over-month growth rate?
-- Target CSV: data/processed/monthly_revenue.csv
-- -----------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        strftime('%Y-%m-01', o.order_purchase_timestamp) AS order_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.price) AS total_revenue,
        ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS average_order_value
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY 1
)
SELECT 
    order_month,
    total_orders,
    ROUND(total_revenue, 2) AS total_revenue,
    average_order_value,
    ROUND(
        ((total_revenue - LAG(total_revenue) OVER (ORDER BY order_month)) * 100.0
        / NULLIF(LAG(total_revenue) OVER (ORDER BY order_month), 0)), 
        2
    ) AS mom_growth_pct
FROM monthly_metrics
ORDER BY order_month;


-- -----------------------------------------------------------------------------
-- QUERY 2: Category Revenue Performance (H1 2017 vs H1 2018 YoY Growth)
-- Business Question: Which merchandise categories generated the most revenue 
-- and demonstrated the highest Year-over-Year growth between H1 2017 and H1 2018?
-- Target CSV: data/processed/category_trend.csv
-- -----------------------------------------------------------------------------
WITH category_h1 AS (
    SELECT 
        COALESCE(ct.product_category_name_english, p.product_category_name, 'Unknown') AS category_name,
        SUM(CASE 
            WHEN o.order_purchase_timestamp >= '2017-01-01' AND o.order_purchase_timestamp < '2017-07-01' 
            THEN oi.price ELSE 0 END
        ) AS revenue_h1_2017,
        SUM(CASE 
            WHEN o.order_purchase_timestamp >= '2018-01-01' AND o.order_purchase_timestamp < '2018-07-01' 
            THEN oi.price ELSE 0 END
        ) AS revenue_h1_2018
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND (
          (o.order_purchase_timestamp >= '2017-01-01' AND o.order_purchase_timestamp < '2017-07-01')
          OR
          (o.order_purchase_timestamp >= '2018-01-01' AND o.order_purchase_timestamp < '2018-07-01')
      )
    GROUP BY 1
)
SELECT 
    category_name,
    ROUND(revenue_h1_2017, 2) AS revenue_h1_2017,
    ROUND(revenue_h1_2018, 2) AS revenue_h1_2018,
    ROUND(
        ((revenue_h1_2018 - revenue_h1_2017) * 100.0 / NULLIF(revenue_h1_2017, 0)), 
        2
    ) AS yoy_growth_pct
FROM category_h1
ORDER BY revenue_h1_2018 DESC;


-- -----------------------------------------------------------------------------
-- QUERY 3: Top 3 Products Per Category by Revenue
-- Business Question: What are the top 3 highest-revenue individual products 
-- within each category across the marketplace?
-- Target CSV: data/processed/top_products_per_category.csv
-- -----------------------------------------------------------------------------
WITH product_revenue AS (
    SELECT 
        COALESCE(ct.product_category_name_english, p.product_category_name, 'Unknown') AS category_name,
        oi.product_id,
        SUM(oi.price) AS total_revenue,
        COUNT(oi.order_item_id) AS total_units_sold,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY 1, 2
),
ranked_products AS (
    SELECT 
        category_name,
        product_id,
        ROUND(total_revenue, 2) AS total_revenue,
        total_units_sold,
        total_orders,
        DENSE_RANK() OVER (
            PARTITION BY category_name 
            ORDER BY total_revenue DESC
        ) AS product_rank_in_category
    FROM product_revenue
)
SELECT 
    category_name,
    product_rank_in_category,
    product_id,
    total_revenue,
    total_units_sold,
    total_orders
FROM ranked_products
WHERE product_rank_in_category <= 3
ORDER BY category_name, product_rank_in_category;


-- -----------------------------------------------------------------------------
-- QUERY 4: Customer Cohort Retention Analysis
-- Business Question: What proportion of customers from each monthly cohort 
-- return to place repeat orders in subsequent months?
-- Target CSV: data/processed/cohort_retention.csv
-- -----------------------------------------------------------------------------
WITH first_order AS (
    SELECT c.customer_unique_id,
           MIN(strftime('%Y-%m-01', o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
order_months AS (
    SELECT c.customer_unique_id,
           strftime('%Y-%m-01', o.order_purchase_timestamp) AS order_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
)
SELECT f.cohort_month, om.order_month,
       (CAST(strftime('%Y', om.order_month) AS INTEGER) - CAST(strftime('%Y', f.cohort_month) AS INTEGER)) * 12
        + (CAST(strftime('%m', om.order_month) AS INTEGER) - CAST(strftime('%m', f.cohort_month) AS INTEGER)) AS months_since_first,
       COUNT(DISTINCT om.customer_unique_id) AS customers
FROM order_months om
JOIN first_order f ON om.customer_unique_id = f.customer_unique_id
GROUP BY 1,2,3
ORDER BY 1,2;


-- -----------------------------------------------------------------------------
-- QUERY 5: Review Score by Delivery Performance (Late vs On-Time)
-- Business Question: What is the impact of late delivery on customer review 
-- satisfaction scores compared to on-time deliveries?
-- Target CSV: data/processed/delivery_vs_reviews.csv
-- -----------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Late'
        ELSE 'On-Time'
    END AS delivery_performance,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(r.review_id) AS total_reviews,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(COUNT(CASE WHEN r.review_score = 5 THEN 1 END) * 100.0 / COUNT(r.review_id), 2) AS pct_5_star,
    ROUND(COUNT(CASE WHEN r.review_score = 1 THEN 1 END) * 100.0 / COUNT(r.review_id), 2) AS pct_1_star
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY 1
ORDER BY delivery_performance DESC;


-- -----------------------------------------------------------------------------
-- QUERY 6: Delivery Lateness Rate and Duration by Customer State
-- Business Question: Which Brazilian states experience the highest late delivery 
-- rates and longest transit times?
-- Target CSV: data/processed/late_by_state.csv
-- -----------------------------------------------------------------------------
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN o.order_id END) AS late_orders,
    ROUND(
        COUNT(DISTINCT CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN o.order_id END) * 100.0 
        / NULLIF(COUNT(DISTINCT o.order_id), 0), 
        2
    ) AS late_rate_pct,
    ROUND(
        AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 
        2
    ) AS avg_delivery_days,
    ROUND(
        AVG(julianday(o.order_estimated_delivery_date) - julianday(o.order_purchase_timestamp)), 
        2
    ) AS avg_estimated_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY c.customer_state
ORDER BY late_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- QUERY 7: Freight Burden as % of Product Price by State
-- Business Question: How does shipping friction (freight cost relative to product 
-- price) vary by geographic region for states with significant volume?
-- Target CSV: data/processed/freight_burden.csv
-- -----------------------------------------------------------------------------
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(AVG(oi.price), 2) AS avg_item_price,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_value,
    ROUND(
        AVG(oi.freight_value * 100.0 / NULLIF(oi.price, 0)), 
        2
    ) AS avg_freight_pct_of_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY c.customer_state
HAVING COUNT(DISTINCT o.order_id) > 100
ORDER BY avg_freight_pct_of_price DESC;


-- -----------------------------------------------------------------------------
-- QUERY 8: Repeat Purchase Rate and Customer Value
-- Business Question: What percentage of unique shoppers complete more than one 
-- purchase, and how does spend compare between one-time and repeat buyers?
-- Target CSV: data/processed/repeat_rate.csv
-- -----------------------------------------------------------------------------
WITH customer_order_counts AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(oi.price) AS total_customer_spend
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY c.customer_unique_id
)
SELECT 
    COUNT(customer_unique_id) AS total_unique_customers,
    COUNT(CASE WHEN order_count = 1 THEN 1 END) AS one_time_buyers,
    COUNT(CASE WHEN order_count > 1 THEN 1 END) AS repeat_buyers,
    ROUND(
        COUNT(CASE WHEN order_count > 1 THEN 1 END) * 100.0 / NULLIF(COUNT(customer_unique_id), 0), 
        2
    ) AS repeat_purchase_rate_pct,
    ROUND(AVG(CASE WHEN order_count = 1 THEN total_customer_spend END), 2) AS avg_spend_one_time_buyer,
    ROUND(AVG(CASE WHEN order_count > 1 THEN total_customer_spend END), 2) AS avg_spend_repeat_buyer
FROM customer_order_counts;


-- -----------------------------------------------------------------------------
-- QUERY 9: Pareto Analysis - Cumulative Revenue Share by Customer Rank
-- Business Question: Does the customer base exhibit an 80/20 Pareto distribution, 
-- or is revenue distributed broadly across single-purchase transactions?
-- Target CSV: data/processed/pareto.csv
-- -----------------------------------------------------------------------------
WITH customer_revenue AS (
    SELECT 
        c.customer_unique_id,
        SUM(oi.price) AS customer_revenue
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY c.customer_unique_id
),
ranked_customers AS (
    SELECT 
        customer_unique_id,
        customer_revenue,
        ROW_NUMBER() OVER (ORDER BY customer_revenue DESC) AS customer_rank,
        COUNT(*) OVER () AS total_customers,
        SUM(customer_revenue) OVER () AS total_system_revenue,
        SUM(customer_revenue) OVER (ORDER BY customer_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cumulative_revenue
    FROM customer_revenue
)
SELECT 
    customer_rank,
    customer_unique_id,
    ROUND(customer_revenue, 2) AS customer_revenue,
    ROUND(running_cumulative_revenue, 2) AS running_cumulative_revenue,
    ROUND(customer_rank * 100.0 / total_customers, 4) AS customer_percentile,
    ROUND(running_cumulative_revenue * 100.0 / total_system_revenue, 4) AS cumulative_revenue_share_pct
FROM ranked_customers
ORDER BY customer_rank;


-- -----------------------------------------------------------------------------
-- QUERY 10: Seller Delivery Lateness Rate (Filtered to >= 50 Orders)
-- Business Question: Which high-volume sellers exhibit chronic delivery lateness, 
-- requiring SLA enforcement or logistics intervention?
-- Target CSV: data/processed/seller_late_rate.csv
-- -----------------------------------------------------------------------------
SELECT 
    s.seller_id,
    s.seller_state,
    s.seller_city,
    COUNT(*) AS total_items_sold,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 END) AS late_deliveries,
    ROUND(
        COUNT(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 END) * 100.0 
        / NULLIF(COUNT(*), 0), 
        2
    ) AS seller_late_rate_pct,
    ROUND(
        AVG(CASE 
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date 
            THEN julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) 
        END), 
        2
    ) AS avg_days_late
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY s.seller_id, s.seller_state, s.seller_city
HAVING COUNT(*) >= 50
ORDER BY seller_late_rate_pct DESC, total_orders DESC;


-- -----------------------------------------------------------------------------
-- QUERY 11: Causal Matched-Pair Analysis - Late vs On-Time Deliveries
-- Business Question: When controlling for geographic state, exact product ID,
-- and order price (+/- 10%), what is the true review score penalty of late delivery?
-- Target CSV: data/processed/late_delivery_matched.csv
-- -----------------------------------------------------------------------------
WITH late_orders AS (
    SELECT o.order_id, c.customer_state, oi.product_id,
           (oi.price + oi.freight_value) AS order_value,
           r.review_score
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date > o.order_estimated_delivery_date
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
),
ontime_orders AS (
    SELECT o.order_id, c.customer_state, oi.product_id,
           (oi.price + oi.freight_value) AS order_value,
           r.review_score
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date <= o.order_estimated_delivery_date
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
)
SELECT
    l.order_id AS late_order_id,
    o.order_id AS matched_ontime_order_id,
    l.customer_state,
    l.order_value AS late_value,
    o.order_value AS ontime_value,
    l.review_score AS late_score,
    o.review_score AS ontime_score
FROM late_orders l
JOIN ontime_orders o
    ON l.customer_state = o.customer_state
    AND l.product_id = o.product_id
    AND ABS(l.order_value - o.order_value) < 0.1 * l.order_value;
