# Project Setup, Data Ingestion, and Power BI Guide

This guide contains the exact commands and architecture required to set up the Olist database, ingest raw datasets, execute SQL analytical queries, and construct the Power BI dimensional model.

---

## 1. Environment Setup & Kaggle Download

### Step 1.1: Clone and Create Virtual Environment
```bash
# Navigate to project directory
cd "Olist E-Commerce Analysis"

# Create a Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
.\venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### Step 1.2: Download Kaggle Dataset into `data/raw/`
Make sure you have your Kaggle API key configured (`kaggle.json` in `~/.kaggle/`).
```bash
# Using Kaggle CLI:
kaggle datasets download -d olistbr/brazilian-ecommerce --unzip -p data/raw/
```
*Manual alternative:*
1. Visit https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Download the archive and extract the 9 CSV files directly into `data/raw/`:
   * `olist_orders_dataset.csv`
   * `olist_order_items_dataset.csv`
   * `olist_customers_dataset.csv`
   * `olist_products_dataset.csv`
   * `olist_sellers_dataset.csv`
   * `olist_order_payments_dataset.csv`
   * `olist_order_reviews_dataset.csv`
   * `olist_geolocation_dataset.csv`
   * `product_category_name_translation.csv`

---

## 2. PostgreSQL Database Setup

### Step 2.1: Create Database in PostgreSQL
Using `psql` (PostgreSQL CLI):
```sql
-- Connect to PostgreSQL server as superuser
psql -U postgres

-- Create the dedicated database
CREATE DATABASE olist;

-- Optional: Create a dedicated user with permissions
CREATE USER olist_user WITH ENCRYPTED PASSWORD 'olist_secure_password';
GRANT ALL PRIVILEGES ON DATABASE olist TO olist_user;
\q
```

### Step 2.2: Configure `.env` Credentials
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Edit `.env` with your actual credentials:
```ini
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=olist
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

*(SQLite Fallback: If PostgreSQL is not installed, set `DB_TYPE=sqlite` and `SQLITE_DB_PATH=data/olist.db` in `.env`)*.

---

## 3. Data Ingestion & SQL Query Execution

### Step 3.1: Run Python Loader
```bash
python scripts/load_olist.py
```
This script validates data presence, establishes connection to the database, coerces datetime fields, loads records (using chunking for geolocation), and prints an ingestion summary report.

### Step 3.2: Run Validation Checks
In your SQL client (`psql`, pgAdmin, or DBeaver), execute [sql/validation.sql](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/sql/validation.sql) to audit row counts and integrity:
```bash
psql -U postgres -d olist -f sql/validation.sql
```

### Step 3.3: Run Analytical Queries & Export to `data/processed/`
Execute the queries in [sql/analysis.sql](file:///c:/Users/yashn/Olist%20E-Commerce%20Analysis/sql/analysis.sql) and export each result to its designated CSV in `data/processed/`:

Using PostgreSQL `\copy` command in `psql`:
```bash
psql -U postgres -d olist -c "\copy (SELECT ... FROM ...) TO 'data/processed/monthly_revenue.csv' WITH CSV HEADER;"
```

Or run this automated export bash/powershell script:
```powershell
# PowerShell automated export example:
$queries = @(
  @{ File="monthly_revenue.csv"; Num=1 },
  @{ File="category_trend.csv"; Num=2 },
  @{ File="top_products_per_category.csv"; Num=3 },
  @{ File="cohort_retention.csv"; Num=4 },
  @{ File="delivery_vs_reviews.csv"; Num=5 },
  @{ File="late_by_state.csv"; Num=6 },
  @{ File="freight_burden.csv"; Num=7 },
  @{ File="repeat_rate.csv"; Num=8 },
  @{ File="pareto.csv"; Num=9 },
  @{ File="seller_late_rate.csv"; Num=10 }
)
```

The 10 resulting CSVs must reside in `data/processed/`:
1. `monthly_revenue.csv`
2. `category_trend.csv`
3. `top_products_per_category.csv`
4. `cohort_retention.csv`
5. `delivery_vs_reviews.csv`
6. `late_by_state.csv`
7. `freight_burden.csv`
8. `repeat_rate.csv`
9. `pareto.csv`
10. `seller_late_rate.csv`

---

## 4. Run Jupyter Exploratory Data Analysis (EDA)

Launch Jupyter Notebook or Jupyter Lab:
```bash
jupyter notebook notebooks/eda.ipynb
```
Run all 12 cells top-to-bottom.
* Cell 3 outputs the verified figures needed to populate `REPLACE_WITH_ACTUAL_...` in `README.md`.
* Cells 4–11 save figures directly to `dashboard/screenshots/` (e.g. `01_monthly_revenue.png`).

---

## 5. Power BI Dimensional Data Model (Star Schema)

### Architectural Architecture & Grain Rules
When modeling Olist data in Power BI:
* **Core Fact Table (`Fact_Sales`):** Model at the **order_item grain** (`order_id` + `order_item_id`).
  * Measures: `price`, `freight_value`.
  * Degenerate attributes: `shipping_limit_date`, `order_status`.
* **Dimension Tables:**
  * `Dim_Date`: Linked to `Fact_Sales[order_purchase_timestamp]`.
  * `Dim_Customers`: Linked via `Fact_Sales[customer_id]`. Contains `customer_unique_id`, `customer_city`, `customer_state`.
  * `Dim_Products`: Linked via `Fact_Sales[product_id]`. Contains translated `product_category_name_english`.
  * `Dim_Sellers`: Linked via `Fact_Sales[seller_id]`. Contains `seller_city`, `seller_state`.

> [!CAUTION]
> **CRITICAL GRAIN WARNING — DO NOT RELATE PAYMENTS OR REVIEWS DIRECTLY TO `Fact_Sales`:**
> `payments` is at the **order/payment installment grain**, and `reviews` is at the **order/review grain**. 
> An order can contain 3 items and be paid with 2 credit cards. If `payments` is joined directly to `Fact_Sales` at the item level, card payment amounts will duplicate for every item, corrupting all revenue calculations.
> 
> **Correct Modeling:**
> Keep `Fact_Payments` and `Fact_Reviews` as separate fact tables connected to a common `Dim_Orders` bridge, OR aggregate payments and reviews to the order level before relating.

---

## 6. Core Power BI DAX Measures

Implement these 10 DAX measures in a dedicated `_Measures` table:

### 1. Total Revenue
```dax
Total Revenue = 
SUM(Fact_Sales[price])
```

### 2. Total Freight Value
```dax
Total Freight = 
SUM(Fact_Sales[freight_value])
```

### 3. Total Orders
```dax
Total Orders = 
DISTINCTCOUNT(Fact_Sales[order_id])
```

### 4. Average Order Value (AOV)
```dax
Average Order Value = 
DIVIDE([Total Revenue], [Total Orders], 0)
```

### 5. Month-over-Month Revenue Growth %
```dax
MoM Revenue Growth % = 
VAR CurrentRevenue = [Total Revenue]
VAR PreviousMonthRevenue = 
    CALCULATE(
        [Total Revenue],
        DATEADD(Dim_Date[Date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentRevenue - PreviousMonthRevenue, PreviousMonthRevenue, 0) * 100
```

### 6. Late Delivery Orders Count
```dax
Late Delivery Orders = 
CALCULATE(
    [Total Orders],
    Fact_Sales[order_delivered_customer_date] > Fact_Sales[order_estimated_delivery_date]
)
```

### 7. Late Delivery Rate %
```dax
Late Delivery Rate % = 
DIVIDE([Late Delivery Orders], [Total Orders], 0) * 100
```

### 8. Average Delivery Duration (Days)
```dax
Avg Delivery Days = 
AVERAGEX(
    FILTER(
        Fact_Sales,
        NOT(ISBLANK(Fact_Sales[order_delivered_customer_date]))
    ),
    DATEDIFF(
        Fact_Sales[order_purchase_timestamp],
        Fact_Sales[order_delivered_customer_date],
        DAY
    )
)
```

### 9. Repeat Customer Count
```dax
Repeat Customers = 
COUNTROWS(
    FILTER(
        VALUES(Dim_Customers[customer_unique_id]),
        CALCULATE([Total Orders]) > 1
    )
)
```

### 10. Repeat Purchase Rate %
```dax
Repeat Purchase Rate % = 
VAR TotalUniqueCustomers = DISTINCTCOUNT(Dim_Customers[customer_unique_id])
RETURN
    DIVIDE([Repeat Customers], TotalUniqueCustomers, 0) * 100
```
