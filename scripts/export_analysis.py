"""
Run Analysis Queries and Export 10 CSVs
---------------------------------------
Executes all 10 queries from sql/analysis.sql on data/olist.db
and exports results to data/processed/.
"""

import sqlite3
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "olist.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

QUERIES = {
    "monthly_revenue.csv": """
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
""",
    "category_trend.csv": """
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
""",
    "top_products_per_category.csv": """
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
""",
    "cohort_retention.csv": """
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
""",
    "delivery_vs_reviews.csv": """
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
""",
    "late_by_state.csv": """
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
""",
    "freight_burden.csv": """
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
""",
    "repeat_rate.csv": """
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
""",
    "pareto.csv": """
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
""",
    "seller_late_rate.csv": """
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
"""
}

def main():
    print("=" * 80)
    print("EXECUTING 10 ANALYSIS QUERIES AND EXPORTING CSVs")
    print("=" * 80)

    for filename, sql in QUERIES.items():
        out_path = OUTPUT_DIR / filename
        df = pd.read_sql(sql, conn)
        df.to_csv(out_path, index=False)

        print(f"\n[SAVED] {filename}")
        print(f"Row count: {len(df):,}")
        print(f"Columns:   {list(df.columns)}")
        print("First 3 rows:")
        print(df.head(3).to_string(index=False))

    # Sanity checks
    print("\n" + "=" * 80)
    print("SANITY CHECKS")
    print("=" * 80)
    
    df_rev = pd.read_csv(OUTPUT_DIR / "monthly_revenue.csv")
    first_month = df_rev['order_month'].iloc[0]
    last_month = df_rev['order_month'].iloc[-1]
    assert first_month == "2017-01-01", f"First month is {first_month}, expected 2017-01-01"
    assert last_month == "2018-08-01", f"Last month is {last_month}, expected 2018-08-01"
    print(f"[PASS] monthly_revenue.csv: window {first_month} to {last_month} (20 months)")

    df_cohort = pd.read_csv(OUTPUT_DIR / "cohort_retention.csv")
    max_cohort_m = df_cohort['months_since_first'].max()
    assert max_cohort_m > 12, f"Cohort max month is {max_cohort_m}, expected > 12"
    print(f"[PASS] cohort_retention.csv: max months_since_first = {max_cohort_m} (> 12)")

    df_rep = pd.read_csv(OUTPUT_DIR / "repeat_rate.csv")
    assert len(df_rep) == 1, f"repeat_rate.csv has {len(df_rep)} rows, expected 1"
    print(f"[PASS] repeat_rate.csv: exactly 1 row (repeat rate = {df_rep['repeat_purchase_rate_pct'].iloc[0]:.2f}%)")

    df_deliv = pd.read_csv(OUTPUT_DIR / "delivery_vs_reviews.csv")
    on_time_score = df_deliv[df_deliv['delivery_performance'] == 'On-Time']['avg_review_score'].iloc[0]
    late_score = df_deliv[df_deliv['delivery_performance'] == 'Late']['avg_review_score'].iloc[0]
    assert on_time_score > late_score + 1.0, "On-time score is not substantially higher than late score"
    print(f"[PASS] delivery_vs_reviews.csv: On-time score ({on_time_score}) >> Late score ({late_score})")

    df_pareto = pd.read_csv(OUTPUT_DIR / "pareto.csv")
    first_rank_pct = df_pareto['cumulative_revenue_share_pct'].iloc[0]
    assert first_rank_pct < 1.0, f"Largest rank cumulative rev share is {first_rank_pct}%, expected < 1%"
    print(f"[PASS] pareto.csv: Rank 1 cumulative revenue share = {first_rank_pct}% (< 50%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
