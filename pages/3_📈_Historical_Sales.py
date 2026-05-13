"""
Historical Sales Dashboard
"""

import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime

st.set_page_config(page_title="Historical Sales", layout="wide", page_icon="📈")

# ── Custom CSS Injection ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif;
    background-color: #F5F7FB; 
}

/* Hide default streamlit header/footer and sidebar nav */
[data-testid="stSidebarNav"] {display: none !important;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Header */
.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0 30px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid #E5E7EB;
}
.header-title {
    font-size: 32px;
    font-weight: 700;
    color: #111827;
    margin: 0;
    padding: 0;
}
.header-subtitle {
    font-size: 15px;
    color: #6B7280;
    margin-top: 4px;
}
.header-time {
    font-size: 13px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* Dataframe container */
div[data-testid="stDataFrame"] > div {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0; text-align: center;">
            <h2 style="color: #2563EB; font-weight: 700; font-family: 'Inter', sans-serif;">F2B Analytics</h2>
        </div>
    """, unsafe_allow_html=True)
    
    selected_page = option_menu(
        menu_title=None,
        options=["Home", "Demand Intelligence", "Vendor Analysis", "Historical Sales"],
        icons=["house", "graph-up", "shop", "clock-history"],
        menu_icon="cast",
        default_index=3,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6B7280", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px", 
                "text-align": "left", 
                "margin": "5px 0", 
                "color": "#4B5563",
                "font-family": "'Inter', sans-serif",
                "border-radius": "8px"
            },
            "nav-link-selected": {"background-color": "#EFF6FF", "color": "#2563EB", "font-weight": "600"},
        }
    )
    
    if selected_page == "Home":
        st.switch_page("Home.py")
    elif selected_page == "Demand Intelligence":
        st.switch_page("pages/1_📊_Demand_Intelligence.py")
    elif selected_page == "Vendor Analysis":
        st.switch_page("pages/2_🏪_Vendor_Analysis.py")

# ── Dashboard Header ──────────────────────────────────────────────────────────
hc1, hc2 = st.columns([8, 2])
with hc1:
    st.markdown(f"""
        <div class="header-title">Historical Sales</div>
        <div class="header-subtitle">View and filter historical performance trends by day or month</div>
        <div class="header-time">Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
    """, unsafe_allow_html=True)

# ── Content ───────────────────────────────────────────────────────────────────
try:
    df_sales = pd.read_csv("historical_sales.csv")
    df_sales["date"] = pd.to_datetime(df_sales["date"])
    
    col_daily, col_monthly = st.columns(2)
    
    with col_daily:
        # Step 6: DATE FILTER (Daily View)
        st.markdown("<h4 style='color:#111827; font-weight:600;'>📅 Daily Sales View</h4>", unsafe_allow_html=True)
        selected_date = st.date_input("Select Date", df_sales["date"].max())
        
        daily_filtered = df_sales[
            df_sales["date"] == pd.to_datetime(selected_date)
        ]

        daily_grouped = (
            daily_filtered
            .groupby(["productName"])
            .agg(
                quantity_sold=("final_quantity", "sum"),
                order_count=("final_quantity", "count")
            )
            .reset_index()
        )

        top_daily = (
            daily_grouped
            .sort_values(by="quantity_sold", ascending=False)
            .head(10) # Expanded to 10 for better page utilization
            .reset_index(drop=True)
        )

        top_daily.index = top_daily.index + 1
        top_daily["Packets Sold"] = top_daily["quantity_sold"].astype(str) + " packets"

        st.markdown(f"**Top Products on {selected_date.strftime('%d-%m-%Y') if hasattr(selected_date, 'strftime') else selected_date}**")
        if top_daily.empty:
            st.info("No sales data available for this date.")
        else:
            st.dataframe(top_daily[["productName", "Packets Sold", "order_count"]].rename(columns={"productName": "Product", "order_count": "Orders"}), use_container_width=True)
            
    with col_monthly:
        # Step 7: MONTH FILTER (Monthly View)
        st.markdown("<h4 style='color:#111827; font-weight:600;'>📆 Monthly Sales View</h4>", unsafe_allow_html=True)
        
        df_sales["month"] = df_sales["date"].dt.to_period("M").astype(str)
        
        selected_month_hist = st.selectbox(
            "Select Month",
            sorted(df_sales["month"].unique(), reverse=True)
        )
        
        monthly_filtered = df_sales[
            df_sales["month"] == selected_month_hist
        ]
        
        monthly_grouped = (
            monthly_filtered
            .groupby(["productName"])
            .agg(
                quantity_sold=("final_quantity", "sum"),
                order_count=("final_quantity", "count")
            )
            .reset_index()
        )

        top_monthly = (
            monthly_grouped
            .sort_values(by="quantity_sold", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )

        top_monthly.index = top_monthly.index + 1
        top_monthly["Packets Sold"] = top_monthly["quantity_sold"].astype(str) + " packets"

        st.markdown(f"**Top Products in {selected_month_hist}**")
        if top_monthly.empty:
            st.info("No sales data available for this month.")
        else:
            st.dataframe(top_monthly[["productName", "Packets Sold", "order_count"]].rename(columns={"productName": "Product", "order_count": "Orders"}), use_container_width=True)

except FileNotFoundError:
    st.warning("Please run the pipeline (app.py) first to generate historical sales datasets.")
