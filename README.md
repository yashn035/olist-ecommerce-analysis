# Olist Brazilian E-Commerce Analysis: Growth Drivers, Customer Retention, and Logistics Optimization

## 1. Executive Summary & Headline Findings
* Gross marketplace revenue expanded rapidly throughout 2017 to peak at **R$ 987,765.37** BRL during Black Friday (November 2017) across 7,289 orders, before stabilizing into mature run-rates averaging **R$ 902,265.64** BRL per month in 2018.
* Customer retention is exceptionally low across all cohorts, with an overall repeat purchase rate of only **3.00%** (2,789 repeat buyers out of 93,104 unique customers) and an average Month 1 cohort retention rate of just **0.48%**.
* Logistics performance is the primary driver of customer satisfaction: orders delivered past the estimated date suffer a catastrophic rating collapse from **4.29** to **2.57** stars (-1.72 drop), with remote frontier states (RO, MA, PB) facing crushing freight costs reaching **51.53% to 59.58%** of product value.

---

## 2. Business Problem & Objective
This portfolio project addresses the central strategic question:
> **"Which commercial factors drive revenue growth and repeat purchases on Olist, and where should retention and logistics capital investments be directed?"**

Specifically, the analysis unpacks:
1. **Sales Momentum & Seasonality:** What propelled gross merchandise value (GMV), and which categories drove sustainable expansion?
2. **Customer Lifecycle & Retention:** Does Olist benefit from organic repeat purchasing, or is the platform dependent on continuous, single-transaction customer acquisition?
3. **Logistics Bottlenecks & Brand Equity:** How severely does late delivery penalize customer reviews, and which geographic regions suffer the highest delivery friction and freight burden?
4. **Seller Operational Reliability:** Are delivery failures systemic across carrier networks or driven by a subset of chronic late-dispatch sellers?

---

## 3. Dataset & Data Architecture
The project utilizes the public Brazilian E-Commerce dataset provided by Olist on Kaggle, encompassing real commercial records from 2016 through 2018.

* **Dataset Size:** 9 relational tables comprising approximately 100,000 orders, 112,000 items, and 96,000 unique human customers.
* **Grain & Entity Disambiguation:** 
  * `customer_id`: Unique identifier assigned per order (1:1 with transactions).
  * `customer_unique_id`: Persistent identifier tracking real individual human customers across multiple purchases.
* **Temporal Filtering & Data Cleaning Window:**
  * Raw orders span from September 2016 to October 2018.
  * **2016 Exclusion:** 2016 contains only ~329 orders representing pilot launch activity and is excluded from time-series and YoY comparisons.
  * **September–October 2018 Exclusion:** Records after August 31, 2018 represent truncated, incomplete reporting periods.
  * **Core Analytical Window:** Bounded strictly between **2017-01-01** and **2018-08-31** (`order_purchase_timestamp >= '2017-01-01' AND order_purchase_timestamp < '2018-09-01'`). Total delivered orders analyzed: **96,211** representing **R$ 13,181,027.13** in merchandise value.
  * **Status Filtering:** All financial and operational performance metrics strictly filter for completed orders: `order_status = 'delivered'`.

---

## 4. Methodology & Tech Stack
The analysis is structured as an end-to-end, production-grade analytics pipeline:

```
[Kaggle CSVs] ──> [Python ETL Loader] ──> [SQLite / Postgres DB] ──> [10 Analytical SQL Queries] ──> [Jupyter EDA] ──> [Power BI Star Schema]
```

1. **Database & SQL Engine (SQLite / PostgreSQL):**
   * Relational modeling and validation checks in [validation.sql](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/sql/validation.sql).
   * 10 production SQL queries in [analysis.sql](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/sql/analysis.sql) utilizing Common Table Expressions (CTEs), window functions (`LAG`, `DENSE_RANK`, running totals), and date arithmetic (`strftime`, `julianday`).
2. **Python Pipeline & EDA:**
   * Automated database ingestion via SQLAlchemy/Pandas in [load_olist.py](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/scripts/load_olist.py).
   * Headless data extraction in [export_analysis.py](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/scripts/export_analysis.py) and statistical visualization in [eda.ipynb](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/notebooks/eda.ipynb) (Matplotlib & Seaborn).
3. **Power BI Dashboard:**
   * Dimensional star schema model separating transaction grains from entity dimensions.
   * Executive reporting across 3 pages: *Executive Sales Overview*, *Logistics & Delivery Operations*, and *Customer Retention & Lifetime Behavior*.

---

## 5. Key Analytical Findings

### Finding 1: Seasonal Spike Driven by Black Friday with Category Concentration
Revenue surged from early 2017, reaching an all-time peak in November 2017 at **R$ 987,765.37** BRL across **7,289** orders (+**52.37%** MoM), before stabilizing around an average of **R$ 902,265.64** BRL per month in 2018. In H1 2018, the top revenue-generating categories were *Health & Beauty* (R$ 532.8k), *Watches & Gifts* (R$ 522.9k), *Bed, Bath & Table* (R$ 417.1k), and *Sports & Leisure* (R$ 397.6k), which together accounted for **34.25%** of gross marketplace sales.

### Finding 2: Retention Failure (The Single-Purchase Reality)
The repeat purchase rate across the marketplace is only **3.00%** (**2,789** repeat buyers out of **93,104** unique human customers). Cohort retention analysis reveals that after Month 0, an average of only **0.48%** of customers return to place another order in Month 1, and retention drops to under 0.2% by Month 6. Olist operates primarily as a top-of-funnel customer acquisition channel rather than an integrated recurring commerce ecosystem.

### Finding 3: Catastrophic Review Impact from Late Deliveries
Delivery punctuality is the single greatest determinant of customer sentiment. On-time deliveries achieve an average review score of **4.29** out of 5 stars (**62.45%** 5-star ratings, 6.58% 1-star). When an order is delivered past the estimated delivery date, the average review score plummets to **2.57** stars (-1.72 drop), with 1-star ratings surging to **46.15%**.

### Finding 4: Sharp Geographic Disparities in Shipping Performance
Logistics bottlenecks are concentrated outside the industrialized Southeast. While São Paulo (SP) boasts a low late rate of **5.90%** and an average transit time of **8.74** days, remote Northern and Northeastern states suffer severe friction: Alagoas (AL) suffers a late delivery rate of **23.99%** with an average delivery duration of **24.52** days, while Roraima (RR) endures an average transit duration of **29.91** days.

### Finding 5: Crippling Freight Friction in Frontier Regions
Freight cost relative to product price reveals immense regional inequality. In São Paulo (SP), freight represents **26.51%** of item price. In contrast, remote states face average freight burdens ranging from **51.53%** (Paraíba - PB) to **55.06%** (Maranhão - MA) and **59.58%** (Rondônia - RO) of product price. This steep freight friction suppresses conversion rates and punishes consumers in underserved states.

### Finding 6: The Pareto Misconception (Debunking the 80/20 VIP Rule)
Contrary to traditional retail assumptions, Olist does **not** exhibit an 80/20 Pareto distribution. Cumulative revenue curve analysis indicates that the top 20% of customers account for only **56.61%** of total marketplace revenue (far below the 80% rule). Reaching 80% of cumulative revenue requires **45.00%** of all customers. High customer churn and single-purchase behavior mean revenue is distributed broadly across a long tail of individual transactions.

---

## 6. Strategic Recommendations

### Recommendation 1: Argue AGAINST a "Top 20% VIP Loyalty Program"
* **Data-Driven Insight:** Standard e-commerce playbooks advocate investing heavily in a "Top 20% VIP Loyalty Tier". The data directly refutes this strategy for Olist. Because the top 20% of shoppers generate only **56.61%** of revenue (and reaching 80% requires **45.00%** of shoppers), there is no entrenched cohort of high-frequency VIP buyers.
* **Alternative Action:** Redirect proposed loyalty budget away from VIP perks and into **automated post-purchase replenishment triggers** at 30, 60, and 90 days for consumable categories (*Health & Beauty*, *Pet Shop*, *Baby*), directly attacking the **3.00%** repeat purchase ceiling.

### Recommendation 2: Implement Regional Fulfillment Hubs (Fulfillment by Olist)
* **Action:** Establish regional consolidation and micro-fulfillment centers in the Northeast (e.g. Bahia or Pernambuco) to cut transit durations for remote consumers from **21–29 days** down to under 10 days.
* **Impact:** Halving delivery times in the Northeast directly curbs late delivery spikes (currently **23.99%** in AL), preventing marketplace review scores from tumbling off the **2.57-star** late delivery cliff.

### Recommendation 3: Enforce Seller Dispatch SLAs and Late Penalties
* **Action:** Institutionalize strict seller dispatch Service Level Agreements (SLAs). SQL query Q10 identifies sellers with >= 50 completed orders who maintain chronic late dispatch rates reaching up to **32.10%** with average delays exceeding **28 to 40 days** (e.g. seller `54965bbe3e4f07ae045b90b0b8541f52` in PR).
* **Impact:** Penalize or temporarily delist chronic repeat offenders. Marketplace algorithms should prioritize Buy Box exposure for sellers maintaining <5% late delivery rates.

---

## 7. Project Limitations
1. **Lack of Marketing & Customer Acquisition Cost (CAC) Data:** The Kaggle dataset does not contain paid media spend, conversion funnels, or channel attribution, precluding direct calculation of Customer Lifetime Value to CAC ratios (LTV:CAC).
2. **Conditionality of Reviews:** Over 99% of customer reviews correspond to delivered orders. Feedback from canceled or unavailable orders before shipment is underrepresented.
3. **Correlation vs. Causation:** The strong correlation between late delivery and 1-star reviews may also be influenced by underlying product defect rates or seller packaging quality.
4. **Truncated Data Boundaries:** Analysis is restricted to Jan 2017 – Aug 2018 due to incomplete telemetry in late 2018.

---

## 8. Repository Structure & How to Run

```
olist-ecommerce-analysis/
├── README.md                      # Executive findings, methodology, and recommendations
├── SETUP.md                       # Comprehensive setup commands, Kaggle ingestion, and Power BI guide
├── requirements.txt               # Python package dependencies
├── .gitignore                     # Git ignore rules for data, pbix, and secrets
├── .env                           # Environment configuration (DB_TYPE=sqlite or postgresql)
├── scripts/
│   ├── load_olist.py              # Automated data ingestion into PostgreSQL / SQLite
│   ├── export_analysis.py         # Executes 10 SQL queries and exports CSVs to data/processed/
│   └── execute_notebook.py        # Headless executor for Jupyter EDA notebook
├── sql/
│   ├── validation.sql             # Row-count checks and data quality audit queries
│   └── analysis.sql               # 10 core analytical queries (CTEs, Window functions)
├── notebooks/
│   └── eda.ipynb                  # 12-cell reproducible EDA and visualization notebook
├── data/
│   ├── raw/                       # 9 raw Kaggle CSVs (git-ignored)
│   └── processed/                 # 10 exported query outputs (monthly_revenue.csv, etc.)
└── dashboard/
    └── screenshots/               # 8 exported figures (01_monthly_revenue.png, etc.)
```

### Quickstart Instructions
1. Clone repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ingest raw CSV datasets:
   ```bash
   python scripts/load_olist.py
   ```
3. Run the analytical queries and export CSVs:
   ```bash
   python scripts/export_analysis.py
   ```
4. Execute the visualization notebook:
   ```bash
   python scripts/execute_notebook.py
   ```
