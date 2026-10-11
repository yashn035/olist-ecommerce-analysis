# Olist E-Commerce Data Dictionary & Schema Reference

A centralized reference guide documenting table grains, cardinalities, primary/foreign keys, and data anomalies across the 9 relational tables in the Olist Brazilian E-Commerce dataset.

---

## 1. Relational Tables Overview

| Table | Grain | Row Count | Key Columns | Notes & Analytical Watchouts |
|---|---|---|---|---|
| **`orders`** | 1 row per order | **99,441** | `order_id` (PK), `customer_id` (FK), `order_status`, `order_purchase_timestamp`, `order_delivered_customer_date`, `order_estimated_delivery_date` | 97.02% completed (`delivered`). Exactly 8 delivered orders are missing `order_delivered_customer_date`. Filter for `order_status = 'delivered'` on revenue queries. |
| **`order_items`** | 1 row per order line item | **112,650** | `order_id` (FK), `order_item_id`, `product_id` (FK), `seller_id` (FK), `price`, `freight_value` | An order can contain multiple items. Always use `COUNT(DISTINCT o.order_id)` when counting orders from item joins. |
| **`customers`** | 1 row per order transaction | **99,441** | `customer_id` (PK, order-scoped), `customer_unique_id` (person-scoped), `customer_zip_code_prefix`, `customer_city`, `customer_state` | `customer_id` is unique per transaction (1:1 with orders). `customer_unique_id` identifies real human shoppers across multiple purchases (96,096 distinct). |
| **`products`** | 1 row per catalog product | **32,951** | `product_id` (PK), `product_category_name`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | Approximately 610 products have a `NULL` category name. Requires `LEFT JOIN` to category translation. |
| **`sellers`** | 1 row per marketplace seller | **3,095** | `seller_id` (PK), `seller_zip_code_prefix`, `seller_city`, `seller_state` | Concentrated heavily in São Paulo (SP). Exactly 460 sellers have completed $\ge 50$ orders. |
| **`payments`** | 1 row per payment installment | **103,886** | `order_id` (FK), `payment_sequential`, `payment_type`, `payment_installments`, `payment_value` | An order can have multiple payment methods (e.g. credit card + voucher). **Do NOT join directly to `order_items`** (causes Cartesian explosion). |
| **`reviews`** | 1 row per review response | **99,224** | `review_id`, `order_id` (FK), `review_score`, `review_creation_date`, `review_answer_timestamp` | Contains 789 duplicate `review_id` values resulting from review edits or multi-order customer notifications. |
| **`geolocation`** | 1 row per geographic coordinate | **1,000,163** | `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state` | ~52.6 coordinates per zip prefix (up to 1,146 rows for single zips). Must deduplicate or average coordinates before spatial joining. |
| **`category_translation`** | 1 row per category name | **71** | `product_category_name`, `product_category_name_english` | Maps Portuguese category names to standard English equivalents. |

---

## 2. Core Relational Gotchas (Common Analytical Traps)

### 1. `customer_id` vs. `customer_unique_id` (The #1 Mistake)
* **The Trap:** Analysts assume `customer_id` represents unique individual humans. If you calculate repeat purchase rate using `COUNT(DISTINCT customer_id)`, the repeat rate calculates as **exactly 0%**.
* **The Reality:** Olist assigns a fresh `customer_id` to each transaction. `customer_unique_id` is the real persistent human identifier. There are 99,441 `customer_id` records, but only 96,096 `customer_unique_id` values, revealing 3,345 repeat purchase transactions (3.00% repeat rate).

### 2. Double-Counting Revenue via Item-Level Fact Joins
* **The Trap:** Joining `payments` or `reviews` directly to `order_items` at the line-item grain.
* **The Reality:** An order with 3 items and 2 credit card payments produces a Cartesian join of $3 \times 2 = 6$ rows. Summing `payment_value` or `price` across this joined table inflates revenue by multiples. Always maintain `Fact_Sales` at the `(order_id, order_item_id)` grain, and keep payments at the order grain.

### 3. Many-to-Many Geolocation Joins
* **The Trap:** Joining `customers` or `sellers` directly to `geolocation` on `zip_code_prefix`.
* **The Reality:** `geolocation` contains over 1,000,000 rows across only 19,015 prefixes. Joining without grouping causes massive row multiplication. Geolocation coordinates must be grouped by zip prefix (`AVG(lat), AVG(lng)`) before joining.

### 4. Truncated Boundary Months
* **The Trap:** Analyzing all raw order timestamps from September 2016 to October 2018.
* **The Reality:** 2016 data contains only ~329 pilot launch orders. September and October 2018 contain truncated data after database logging ceased. Including these boundary periods creates false 90% revenue drop-offs. The clean operating window is strictly **2017-01-01 to 2018-08-31** (20 contiguous months).

### 5. Delivered Status Filtering
* **The Trap:** Computing sales volume across all order statuses.
* **The Reality:** Over 97% of orders are `delivered`. Canceled (`625`) and unavailable (`609`) orders never generated realized merchandise value and lack valid delivery timestamps. All revenue and performance queries must explicitly filter for `order_status = 'delivered'`.
