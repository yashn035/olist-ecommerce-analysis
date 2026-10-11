# Analytical Decisions & Architectural Trade-Offs Log

This document records the critical methodological choices, alternative approaches considered, and operational impacts across the Olist E-Commerce analytics pipeline.

---

## Decision 1: Bounding Analysis Window (2017-01-01 to 2018-08-31)
* **Chosen:** Bounded the analytical window strictly between January 1, 2017 and August 31, 2018 (20 complete, contiguous monthly periods).
* **Alternatives Considered:** Analyzing the entire raw range (Sept 2016 – Oct 2018), or imputing missing boundary days.
* **Rationale:** Raw timestamps show 2016 had sporadic pilot activity (~329 total orders across 4 months), while September and October 2018 contain truncated data after system logging was cut off. Including them skews MoM growth rates, creates false visual revenue collapses, and distorts seasonal baselines.
* **Impact:** Excluded ~329 pilot orders from 2016 and ~16 orders from late 2018. Preserved 96,211 delivered orders with clean, reliable MoM and YoY trends.

---

## Decision 2: Defining Revenue as Gross Merchandise Value (Price + Freight)
* **Chosen:** Defined top-line revenue as customer-paid Gross Merchandise Value (GMV): `SUM(price) + SUM(freight_value)`. In category comparisons, isolated `SUM(price)` to measure product merchandise demand without geographic freight distortions.
* **Alternatives Considered:** Product price only (`SUM(price)`), or attempting to estimate Olist's net take-rate commission.
* **Rationale:** Olist functions as an e-commerce platform facilitator. GMV represents the total economic throughput across the ecosystem. Because take-rate percentages vary and are not disclosed in the Kaggle schema, GMV is the standard industry metric.
* **Impact:** Gross platform GMV totaled R$ 13.18M across the period (R$ 11.42M pure merchandise + R$ 1.76M freight).

---

## Decision 3: Local SQLite Engine Fallback Over PostgreSQL
* **Chosen:** Utilized an indexed local SQLite database (`data/olist.db`) as the execution engine for the pipeline, while preserving PostgreSQL-compatible SQL queries in documentation.
* **Alternatives Considered:** Requiring the user to install and configure an external PostgreSQL server, Docker container, or cloud RDS instance before running.
* **Rationale:** `psql` was not present in the host system PATH. Demanding a manual Postgres install would block immediate pipeline execution. SQLite runs zero-configuration in standard Python environments.
* **Impact:** To maintain sub-second query performance on 100k+ row joins, secondary B-Tree indexes were created on primary join keys (`orders.order_id`, `orders.customer_id`, `customers.customer_unique_id`, `order_items.product_id`). Query syntax was adapted from Postgres (`DATE_TRUNC`, `AGE`, `EXTRACT`) to SQLite equivalents (`strftime`, `julianday`).

---

## Decision 4: Cohort Retention Grain at `customer_unique_id`
* **Chosen:** Anchored customer identification and monthly cohort groupings strictly on `customer_unique_id`.
* **Alternatives Considered:** Grouping by `customer_id`.
* **Rationale:** `customer_id` is generated anew for every single checkout, acting as a transaction-level key (99,441 rows). `customer_unique_id` tracks the real individual shopper across multiple transactions (96,096 distinct people).
* **Impact:** If `customer_id` were used, repeat purchase rate would calculate as 0.00%. Using `customer_unique_id` surfaced the true 3.00% repeat purchase rate and revealed the 0.48% Month 1 retention rate.

---

## Decision 5: Filtering Exclusively for `order_status = 'delivered'`
* **Chosen:** Filtered all financial and customer performance metrics strictly to completed orders: `order_status = 'delivered'`.
* **Alternatives Considered:** Including `shipped`, `invoiced`, or `canceled` orders.
* **Rationale:** Completed delivery is the only state where revenue is fully realized, delivery transit durations can be computed, and review scores are systematically collected (>99% of reviews correspond to delivered orders). Canceled (625) and unavailable (609) orders have missing delivery dates and represent unfulfilled transactions.
* **Impact:** Focuses the analysis on 96,478 delivered orders (>97% of total volume), preventing distorted delivery duration metrics.

---

## Decision 6: Seller Late-Rate Threshold at Minimum 50 Completed Orders
* **Chosen:** Filtered seller delivery lateness analysis in Q10 to merchants with at least 50 completed orders (`HAVING COUNT(*) >= 50`).
* **Alternatives Considered:** No volume threshold, or a 10-order threshold.
* **Rationale:** Without a sample size threshold, a seller who completed 1 order that happened to be late ranks as 100% late, dominating the worst-seller list despite negligible operational impact. Focusing on $\ge 50$ orders isolates systemic operational failures that harm large numbers of customers.
* **Impact:** Narrowed the seller pool from 3,095 sellers down to 460 high-volume merchants, accurately identifying chronic repeat offenders (such as sellers with 70–80 orders maintaining >30% late rates).

---

## Decision 7: Pareto Analysis Grain at Customer Level Rather Than Order Grain
* **Chosen:** Aggregated total historical spend per unique human customer (`customer_unique_id`) before computing cumulative revenue percentiles.
* **Alternatives Considered:** Computing the Pareto curve on individual transaction order values.
* **Rationale:** The Pareto principle in retail strategy evaluates customer lifetime concentration to determine whether VIP loyalty programs are economically viable. Measuring at the order level would confuse basket size variance with customer value concentration.
* **Impact:** Proved that the top 20% of customers account for only 56.61% of total platform revenue, and that reaching 80% requires 45.00% of all shoppers.

---

## Decision 8: Correlational Review Framing & Causal Matched-Pair Validation
* **Chosen:** Framed the macro review drop (4.29 ★ on-time vs. 2.57 ★ late) as strongly correlational, and engineered a matched-pair control query (Q11) comparing late vs. on-time orders within the exact same state, product ID, and order value range.
* **Alternatives Considered:** Claiming pure causality without addressing confounds, or omitting the review-score drop entirely due to lack of an experimental A/B test.
* **Rationale:** Claiming direct causality ignores obvious confounding variables: remote geography, carrier mishandling, and product defect rates. Matched-pair analysis controls for these observable confounds.
* **Impact:** In the matched-pair analysis ($n=3,309$ unique late orders matched to 32,710 on-time orders), the review penalty persisted at $-1.59$ stars (4.19 ★ on-time vs. 2.61 ★ late). This suggests the review penalty is not explained by geography, product category, or basket size alone, while acknowledging that seller quality and seasonal factors remain unmeasured confounds requiring randomization to establish true causation.
