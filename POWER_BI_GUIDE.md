# Power BI Implementation Guide: Olist E-Commerce Analytics

A comprehensive, step-by-step tutorial designed to build a portfolio-grade 3-page interactive Power BI dashboard in 4–6 hours using the processed Olist dataset.

---

## 1. Data Ingestion (Get Data)

Open Power BI Desktop. Click **Get Data → Text/CSV** and import these 6 source CSV files from `data/raw/`:
1. `olist_orders_dataset.csv`
2. `olist_order_items_dataset.csv`
3. `olist_customers_dataset.csv`
4. `olist_products_dataset.csv`
5. `olist_sellers_dataset.csv`
6. `product_category_name_translation.csv`

Click **Transform Data** to open the **Power Query Editor**.

---

## 2. Power Query Transformations (ETL & Modeling)

### Step 2.1: Clean Date Columns & Data Types
In `olist_orders_dataset`:
* Select `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`.
* Change data type to **Date/Time**.
* Add a conditional column or transform: Replace errors with `null`.

In `olist_order_items_dataset`:
* `price` → **Decimal Number / Fixed Decimal (Currency)**
* `freight_value` → **Decimal Number / Fixed Decimal (Currency)**
* `shipping_limit_date` → **Date/Time**

### Step 2.2: Construct `Fact_Sales` (Order-Item Grain)
To avoid multi-fact Cartesian products, merge orders attributes directly into order items:
1. Select `olist_order_items_dataset`.
2. Click **Merge Queries as New** (or rename to `Fact_Sales`).
3. Join with `olist_orders_dataset` on `order_id` (Inner Join).
4. Expand the joined table to include:
   * `customer_id`
   * `order_status`
   * `order_purchase_timestamp`
   * `order_delivered_customer_date`
   * `order_estimated_delivery_date`
5. **Filter Status**: Add a filter step on `order_status` where `order_status = "delivered"`.
6. Select Columns to keep:
   * `order_id` (Text)
   * `order_item_id` (Integer)
   * `product_id` (Text)
   * `seller_id` (Text)
   * `customer_id` (Text)
   * `price` (Decimal)
   * `freight_value` (Decimal)
   * `order_purchase_timestamp` (Date/Time)
   * `order_delivered_customer_date` (Date/Time)
   * `order_estimated_delivery_date` (Date/Time)
   * `order_status` (Text)
7. Uncheck **Enable Load** on the raw `olist_orders_dataset` and `olist_order_items_dataset` staging queries.

### Step 2.3: Dimension Table Setup
* **`Dim_Customers`**:
  * Select `olist_customers_dataset`. Rename query to `Dim_Customers`.
  * Keep only: `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state`.
  * Remove duplicate rows on `customer_id` if any exist.
* **`Dim_Products`**:
  * Select `olist_products_dataset`. Rename query to `Dim_Products`.
  * Click **Merge Queries** with `product_category_name_translation` on `product_category_name` (Left Outer).
  * Expand `product_category_name_english`. Rename to `category_english`.
  * Replace nulls in `category_english` with `"Unknown"`.
  * Keep `product_id`, `category_english`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`.
* **`Dim_Sellers`**:
  * Select `olist_sellers_dataset`. Rename query to `Dim_Sellers`.
  * Keep `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state`.
* Click **Close & Apply**.

### Step 2.4: Create `Dim_Date` (DAX Calculated Table)
In Power BI Model view, click **New Table** and enter:

```dax
Dim_Date = 
VAR StartDate = DATE(2016, 1, 1)
VAR EndDate = DATE(2018, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(StartDate, EndDate),
    "Year", YEAR([Date]),
    "MonthNumber", MONTH([Date]),
    "MonthYear", FORMAT([Date], "yyyy-MM"),
    "MonthName", FORMAT([Date], "mmm"),
    "Quarter", "Q" & FORMAT([Date], "q"),
    "YearMonthOrder", YEAR([Date]) * 100 + MONTH([Date])
)
```
* Select `MonthName` column → click **Sort by column** → select `MonthNumber`.
* Select `MonthYear` column → click **Sort by column** → select `YearMonthOrder`.
* Right-click `Dim_Date` table → select **Mark as date table** → choose `Date`.

---

## 3. Relationships & Star Schema Architecture

Navigate to the **Model View** and arrange your tables in a classic Star Schema:

```
        ┌────────────────┐       ┌─────────────────┐
        │  Dim_Customers │       │    Dim_Date     │
        └───────┬────────┘       └────────┬────────┘
        1       │                         │ 1
                │ customer_id             │ Date (to order_purchase_timestamp)
                ▼                         ▼
            ┌───────────────────────────────────┐
            │            Fact_Sales             │
            └───────▲───────────────────▲───────┘
          product_id│                  seller_id
                    │ 1                         │ 1
        ┌───────────┴────┐       ┌──────────────┴──┐
        │  Dim_Products  │       │   Dim_Sellers   │
        └────────────────┘       └─────────────────┘
```

### Relationship Properties:
1. `Dim_Customers[customer_id]` (1) ───< `Fact_Sales[customer_id]` (*)
2. `Dim_Date[Date]` (1) ───< `Fact_Sales[order_purchase_timestamp]` (*)
3. `Dim_Products[product_id]` (1) ───< `Fact_Sales[product_id]` (*)
4. `Dim_Sellers[seller_id]` (1) ───< `Fact_Sales[seller_id]` (*)

* **Cardinality**: One to Many (1:*).
* **Cross filter direction**: **Single** (Never use Both).

---

## 4. DAX Measures Library

Create a dedicated empty table named `_Measures` (Home → Enter Data → Load). Create the following 12 production DAX measures:

### 1. Total Revenue (GMV)
```dax
Total Revenue = SUM(Fact_Sales[price]) + SUM(Fact_Sales[freight_value])
```

### 2. Product Revenue
```dax
Product Revenue = SUM(Fact_Sales[price])
```

### 3. Freight Revenue
```dax
Freight Revenue = SUM(Fact_Sales[freight_value])
```

### 4. Total Orders
```dax
Total Orders = DISTINCTCOUNT(Fact_Sales[order_id])
```

### 5. Average Order Value (AOV)
```dax
Average Order Value = DIVIDE([Total Revenue], [Total Orders], 0)
```

### 6. Total Unique Customers
```dax
Total Customers = DISTINCTCOUNT(Dim_Customers[customer_unique_id])
```

### 7. Month-over-Month Revenue Growth %
```dax
MoM Revenue Growth % = 
VAR CurrentRev = [Total Revenue]
VAR PrevRev = 
    CALCULATE(
        [Total Revenue],
        DATEADD(Dim_Date[Date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentRev - PrevRev, PrevRev, 0) * 100
```

### 8. Late Orders Count
```dax
Late Orders = 
CALCULATE(
    [Total Orders],
    Fact_Sales[order_delivered_customer_date] > Fact_Sales[order_estimated_delivery_date]
)
```

### 9. Late Delivery Rate %
```dax
Late Delivery Rate % = 
DIVIDE([Late Orders], [Total Orders], 0) * 100
```

### 10. Average Delivery Days
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

### 11. Repeat Customer Count
```dax
Repeat Customers = 
COUNTROWS(
    FILTER(
        VALUES(Dim_Customers[customer_unique_id]),
        CALCULATE([Total Orders]) > 1
    )
)
```

### 12. Repeat Purchase Rate %
```dax
Repeat Rate % = 
VAR TotalUnique = [Total Customers]
RETURN
    DIVIDE([Repeat Customers], TotalUnique, 0) * 100
```

---

## 5. Visual Dashboard Construction (3 Pages)

### Page 1 — Executive Sales & Customer Retention
* **Canvas Title**: *Executive Sales Overview & Customer Lifecycle*
* **KPI Cards (Top Banner)**:
  1. `Total Revenue`: R$ 13.18M
  2. `Total Orders`: 96.2K
  3. `AOV`: R$ 137.00
  4. `Repeat Purchase Rate %`: 3.00%
* **Visual 1 (Line & Clustered Column Chart)**:
  * X-Axis: `Dim_Date[MonthYear]`
  * Column Values: `Total Revenue`
  * Line Values: `MoM Revenue Growth %`
* **Visual 2 (Filled Map / Shape Map)**:
  * Location: `Dim_Customers[customer_state]`
  * Tooltip: Country = `"Brazil"`
  * Color Saturation: `Total Revenue` (Highlights SP dominance at 38.36%)
* **Slicers**:
  * Year (`Dim_Date[Year]`)
  * State (`Dim_Customers[customer_state]`)

### Page 2 — Product & Category Commercial Performance
* **Canvas Title**: *Category Revenue & Product Performance*
* **KPI Cards**:
  1. Top Category Revenue (`health_beauty`: R$ 532.8k)
  2. Average Product Revenue
* **Visual 1 (Horizontal Bar Chart)**:
  * Y-Axis: `Dim_Products[category_english]` (Top 10 by `Product Revenue`)
  * X-Axis: `Product Revenue`
* **Visual 2 (Ranked Product Table)**:
  * Columns: `product_id`, `category_english`, `Product Revenue`, `Total Orders`
  * Sort: `Product Revenue` Descending
* **Slicers**:
  * Category Dropdown (`Dim_Products[category_english]`)

### Page 3 — Logistics, Fulfillment & Delivery Bottlenecks
* **Canvas Title**: *Logistics Operations & SLA Enforcement*
* **KPI Cards**:
  1. `Late Delivery Rate %`: 8.01% (Marketplace average)
  2. `Average Delivery Days`: 12.5 days
* **Visual 1 (Clustered Bar Chart)**:
  * Y-Axis: `Dim_Customers[customer_state]`
  * X-Axis: `Late Delivery Rate %` (Sorted descending, AL leads at 23.99%)
* **Visual 2 (Scatter / Line Chart)**:
  * X-Axis: `Avg Delivery Days` by State
  * Y-Axis: `Late Delivery Rate %`
* **Visual 3 (Chronic Late Seller Watchlist Table)**:
  * Columns: `Dim_Sellers[seller_id]`, `Dim_Sellers[seller_state]`, `Total Orders`, `Late Delivery Rate %`, `Avg Delivery Days`
  * Filter: Visual-level filter `Total Orders >= 50`
  * Sort: `Late Delivery Rate %` Descending (Highlights chronic offenders >30%)
* **Slicer**:
  * Seller State (`Dim_Sellers[seller_state]`)

---

## 6. Export Screenshots Checklist
Export high-resolution PNGs of each completed page (File → Export → Export to PDF or capture screenshot) and save to `dashboard/screenshots/`:
* `09_powerbi_executive.png`
* `10_powerbi_products.png`
* `11_powerbi_operations.png`

---

## 7. Power BI Troubleshooting Guide

### Issue 1: Relationship Refuses to Create Between `Dim_Date` and `Fact_Sales`
* **Root Cause**: `order_purchase_timestamp` contains timestamps with seconds (`2017-10-02 10:56:33`), while `Dim_Date[Date]` is integer day grain (`2017-10-02`).
* **Fix**: In Power Query, transform `order_purchase_timestamp` into a dedicated date column `order_purchase_date` (Data Type: **Date**), and relate `Dim_Date[Date]` to `Fact_Sales[order_purchase_date]`.

### Issue 2: `Repeat Rate %` Returns Blank or 100%
* **Root Cause**: Measure evaluated across `customer_id` instead of `customer_unique_id`.
* **Fix**: Verify `Repeat Customers` iterates across `VALUES(Dim_Customers[customer_unique_id])`. Ensure single-direction filter propagation from `Dim_Customers` to `Fact_Sales`.

### Issue 3: Filled Map Does Not Render Brazilian States
* **Root Cause**: Two-letter Brazilian state codes (SP, RJ, MG, RO) conflict with international state abbreviations.
* **Fix**: In Power Query, add a custom column to `Dim_Customers`:
  ```powerquery
  [customer_state] & ", Brazil"
  ```
  Set Data Category for this column to **State or Province**. Map renders immediately.
