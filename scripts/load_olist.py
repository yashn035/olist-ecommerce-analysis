"""
Olist E-Commerce Data Loader
----------------------------
Loads raw Kaggle CSV files into PostgreSQL (or SQLite fallback) database.

Expected CSV files in data/raw/:
  - olist_orders_dataset.csv
  - olist_order_items_dataset.csv
  - olist_customers_dataset.csv
  - olist_products_dataset.csv
  - olist_sellers_dataset.csv
  - olist_order_payments_dataset.csv
  - olist_order_reviews_dataset.csv
  - olist_geolocation_dataset.csv
  - product_category_name_translation.csv
"""

import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Define project root and directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
ENV_FILE = PROJECT_ROOT / ".env"

# Mapping of raw CSV filenames to table names, date columns, and optional chunksize
DATASET_CONFIG = {
    "olist_orders_dataset.csv": {
        "table": "orders",
        "date_cols": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "olist_order_items_dataset.csv": {
        "table": "order_items",
        "date_cols": ["shipping_limit_date"],
    },
    "olist_customers_dataset.csv": {
        "table": "customers",
        "date_cols": [],
    },
    "olist_products_dataset.csv": {
        "table": "products",
        "date_cols": [],
    },
    "olist_sellers_dataset.csv": {
        "table": "sellers",
        "date_cols": [],
    },
    "olist_order_payments_dataset.csv": {
        "table": "payments",
        "date_cols": [],
    },
    "olist_order_reviews_dataset.csv": {
        "table": "reviews",
        "date_cols": [
            "review_creation_date",
            "review_answer_timestamp",
        ],
    },
    "olist_geolocation_dataset.csv": {
        "table": "geolocation",
        "date_cols": [],
        "chunksize": 10000,
    },
    "product_category_name_translation.csv": {
        "table": "category_translation",
        "date_cols": [],
    },
}


def get_db_engine():
    """Build and verify database engine connection based on .env config."""
    if not ENV_FILE.exists():
        print(f"[ERROR] Configuration file '{ENV_FILE}' not found.")
        print("Please copy '.env.example' to '.env' and configure your database settings.")
        print("See SETUP.md for database setup instructions.")
        sys.exit(1)

    load_dotenv(ENV_FILE)

    db_type = os.getenv("DB_TYPE", "postgresql").lower()

    if db_type == "sqlite":
        sqlite_path = os.getenv("SQLITE_DB_PATH", "data/olist.db")
        db_path = PROJECT_ROOT / sqlite_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn_str = f"sqlite:///{db_path}"
        print(f"[INFO] Using SQLite database at: {db_path}")
    else:
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "olist")
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        print(f"[INFO] Connecting to PostgreSQL at {host}:{port}/{dbname} (user: {user})...")

    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("[SUCCESS] Database connection verified successfully.\n")
        return engine
    except Exception as exc:
        print("\n" + "=" * 80)
        print("DATABASE CONNECTION FAILED")
        print("=" * 80)
        print(f"Error: {exc}\n")
        print("Ensure PostgreSQL is running and database exists, or verify credentials in .env.")
        print("Refer to SETUP.md for step-by-step instructions on database creation.")
        print("Fallback: Set DB_TYPE=sqlite in .env to load into a local SQLite database.")
        print("=" * 80 + "\n")
        sys.exit(1)


def check_raw_files():
    """Verify presence of raw data files in data/raw/."""
    missing_files = []
    present_files = []

    for filename in DATASET_CONFIG:
        filepath = DATA_RAW_DIR / filename
        if filepath.is_file():
            present_files.append(filename)
        else:
            missing_files.append(filename)

    return present_files, missing_files


def print_waiting_for_data():
    """Display clear waiting banner if raw CSV files are missing."""
    print("=" * 80)
    print("                              WAITING FOR DATA")
    print("=" * 80)
    print(f"The raw Kaggle Olist CSV datasets were not found in: {DATA_RAW_DIR}\n")
    print("Please download the Brazilian E-Commerce dataset and place the following")
    print("9 CSV files into 'data/raw/':\n")
    for idx, filename in enumerate(DATASET_CONFIG.keys(), start=1):
        print(f"  {idx}. {filename}")
    print("\nHow to obtain the data:")
    print("  Kaggle URL: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
    print("  CLI: kaggle datasets download -d olistbr/brazilian-ecommerce --unzip -p data/raw/")
    print("\nSee SETUP.md for full step-by-step setup instructions.")
    print("=" * 80)


def load_datasets(engine):
    """Load present CSV datasets into the database."""
    summary_report = []

    for filename, config in DATASET_CONFIG.items():
        filepath = DATA_RAW_DIR / filename
        table_name = config["table"]
        date_cols = config.get("date_cols", [])
        chunksize = config.get("chunksize", None)

        if not filepath.is_file():
            print(f"[SKIP] Missing file: {filename} -> table '{table_name}' skipped.")
            summary_report.append((table_name, "SKIPPED (File Not Found)"))
            continue

        print(f"[LOAD] Processing '{filename}' -> table '{table_name}'...")
        try:
            df = pd.read_csv(filepath, low_memory=False)

            # Parse specified date columns with errors='coerce'
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Write to database using replace strategy
            if chunksize:
                df.to_sql(table_name, con=engine, if_exists="replace", index=False, chunksize=chunksize)
            else:
                df.to_sql(table_name, con=engine, if_exists="replace", index=False)

            row_count = len(df)
            print(f"       -> Loaded {row_count:,} rows into '{table_name}'.")
            summary_report.append((table_name, f"{row_count:,} rows"))
        except Exception as err:
            print(f"[ERROR] Failed to load '{filename}': {err}")
            summary_report.append((table_name, f"FAILED ({err})"))

    # Print summary table
    print("\n" + "=" * 50)
    print("          INGESTION SUMMARY REPORT")
    print("=" * 50)
    for table_name, status in summary_report:
        print(f"  {table_name.ljust(25)} : {status}")
    print("=" * 50)


def main():
    present_files, missing_files = check_raw_files()

    if len(present_files) == 0:
        print_waiting_for_data()
        sys.exit(0)

    print(f"[INFO] Found {len(present_files)}/9 raw CSV files in data/raw/.")
    if missing_files:
        print(f"[WARN] {len(missing_files)} file(s) missing: {', '.join(missing_files)}")

    engine = get_db_engine()
    load_datasets(engine)


if __name__ == "__main__":
    main()
