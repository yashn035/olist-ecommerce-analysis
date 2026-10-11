"""
Olist E-Commerce Analytics Dashboard
------------------------------------
Interactive self-service application built with Streamlit.
Visualizes key sales metrics, cohort retention, and logistics operations.

Run locally:
    streamlit run app.py
"""

from pathlib import Path
import pandas as pd
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
IMG_DIR = BASE_DIR / "dashboard" / "screenshots"

@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

# Load processed datasets
df_rev = load_csv("monthly_revenue.csv")
df_cat = load_csv("category_trend.csv")
df_prod = load_csv("top_products_per_category.csv")
df_cohort = load_csv("cohort_retention.csv")
df_deliv = load_csv("delivery_vs_reviews.csv")
df_state = load_csv("late_by_state.csv")
df_fb = load_csv("freight_burden.csv")
df_rep = load_csv("repeat_rate.csv")
df_pareto = load_csv("pareto.csv")
df_sellers = load_csv("seller_late_rate.csv")
df_matched = load_csv("late_delivery_matched.csv")

# Sidebar
st.sidebar.title("Olist Analytics Hub")
st.sidebar.markdown(
    """
    **Dataset:** Brazilian E-Commerce (2017–2018)  
    **Delivered Orders:** 96,211  
    **GMV Analyzed:** R$ 13.18 Million  
    """
)
st.sidebar.info("Use the tabs below to explore commercial growth, customer retention, and logistics SLAs.")

# Header
st.title("📊 Olist E-Commerce Commercial & Operations Dashboard")
st.markdown(
    "Empirical analysis of growth drivers, cohort retention decay, and logistics bottlenecks across 96,211 delivered orders."
)

tab1, tab2, tab3 = st.tabs(["📈 Executive Overview", "🛍️ Products & Categories", "🚚 Logistics & SLAs"])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Marketplace Executive Summary")
    
    # Top KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    total_rev = df_rev["total_revenue"].sum() if not df_rev.empty else 0
    total_orders = df_rev["total_orders"].sum() if not df_rev.empty else 0
    aov = total_rev / total_orders if total_orders else 0
    rep_rate = df_rep["repeat_purchase_rate_pct"].iloc[0] if not df_rep.empty else 0
    
    c1.metric("Total GMV", f"R$ {total_rev:,.2f}")
    c2.metric("Delivered Orders", f"{total_orders:,}")
    c3.metric("Average Order Value (AOV)", f"R$ {aov:.2f}")
    c4.metric("Repeat Purchase Rate", f"{rep_rate:.2f}%")
    
    st.markdown("---")
    
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        st.markdown("#### Monthly GMV & Order Growth")
        img1 = IMG_DIR / "01_monthly_revenue.png"
        if img1.exists():
            st.image(str(img1), caption="Figure 1: Revenue surged 5x to peak in Nov 2017 (Black Friday).", use_container_width=True)
    
    with col_img2:
        st.markdown("#### The 30-Day Retention Window (Cohort Matrix)")
        img4 = IMG_DIR / "04_cohort_retention.png"
        if img4.exists():
            st.image(str(img4), caption="Figure 2: Month 1 retention averages 0.48% (a ceiling, not a slow-burn).", use_container_width=True)
            
    st.markdown("#### Pareto Revenue Distribution")
    img5 = IMG_DIR / "05_pareto.png"
    if img5.exists():
        st.image(str(img5), caption="Figure 3: Top 20% generate only 56.6% of revenue; 80% requires 45.0% of shoppers.", use_container_width=True)

    with st.expander("View Monthly Revenue Table"):
        st.dataframe(df_rev, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: PRODUCTS & CATEGORIES
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Category Performance & Product Concentration")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### Top Categories by H1 2018 Revenue")
        img2 = IMG_DIR / "02_top_categories.png"
        if img2.exists():
            st.image(str(img2), caption="Figure 4: Health & Beauty (R$ 532.8k) outpaced Watches & Gifts and Bed/Bath.", use_container_width=True)
            
    with col_p2:
        st.markdown("#### Geographic Demand Concentration")
        img6 = IMG_DIR / "06_revenue_by_state.png"
        if img6.exists():
            st.image(str(img6), caption="Figure 5: São Paulo (SP) represents 38.36% of total delivered volume.", use_container_width=True)

    st.markdown("#### Top 3 Individual Products per Category")
    if not df_prod.empty:
        categories = ["All"] + sorted(df_prod["category_name"].dropna().unique().tolist())
        selected_cat = st.selectbox("Filter by Category", categories)
        if selected_cat == "All":
            st.dataframe(df_prod, use_container_width=True)
        else:
            st.dataframe(df_prod[df_prod["category_name"] == selected_cat], use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: LOGISTICS & SLAs
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Delivery Timeliness, Review Ratings, and Merchant SLAs")
    
    kpi_l1, kpi_l2, kpi_l3 = st.columns(3)
    kpi_l1.metric("On-Time Avg Review", "4.29 ★")
    kpi_l2.metric("Late Avg Review", "2.57 ★")
    kpi_l3.metric("Rating Cliff (Penalty)", "-1.72 ★")
    
    st.markdown("---")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown("#### Review Score Impact (On-Time vs Late)")
        img3 = IMG_DIR / "03_delivery_vs_reviews.png"
        if img3.exists():
            st.image(str(img3), caption="Figure 6: Late deliveries suffer a 40% collapse in customer reviews.", use_container_width=True)
            
    with col_l2:
        st.markdown("#### Causal Matched-Pair Validation")
        img9 = IMG_DIR / "09_matched_pairs.png"
        if img9.exists():
            st.image(str(img9), caption="Figure 7: Controlling for state, product, and price (n=3,309 pairs), delay penalty persists at -1.59 ★.", use_container_width=True)

    st.markdown("#### Actual vs Estimated Delivery Duration by State")
    img8 = IMG_DIR / "08_delivery_days_by_state.png"
    if img8.exists():
        st.image(str(img8), caption="Figure 8: Northern states endure average delivery times of 24 to 30 days.", use_container_width=True)

    with st.expander("View Chronic Late Seller Watchlist (>= 50 Orders)"):
        st.dataframe(df_sellers, use_container_width=True)

st.markdown("---")
st.caption("Olist Analytics Portfolio Project | Built with SQL, Python, Matplotlib, and Streamlit.")
