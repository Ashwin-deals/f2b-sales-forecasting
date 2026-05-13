"""
Demand Intelligence Dashboard — Premium SaaS Layout
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import datetime

st.set_page_config(page_title="Demand Intelligence", layout="wide", page_icon="📊")

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

/* Premium KPI Cards */
div[data-testid="metric-container"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border-left: 5px solid #2563EB;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
div[data-testid="stVerticalBlock"] > div > div:nth-child(2) div[data-testid="metric-container"] { border-left-color: #10B981; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(3) div[data-testid="metric-container"] { border-left-color: #F59E0B; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(4) div[data-testid="metric-container"] { border-left-color: #8B5CF6; }

/* Metric Text Styling */
div[data-testid="metric-container"] label {
    font-size: 14px;
    color: #6B7280;
    font-weight: 500;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 28px;
    color: #111827;
    font-weight: 700;
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
        default_index=1,
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
    elif selected_page == "Vendor Analysis":
        st.switch_page("pages/2_🏪_Vendor_Analysis.py")
    elif selected_page == "Historical Sales":
        st.switch_page("pages/3_📈_Historical_Sales.py")

# ── Dashboard Header ──────────────────────────────────────────────────────────
hc1, hc2 = st.columns([8, 2])
with hc1:
    st.markdown(f"""
        <div class="header-title">Demand Intelligence</div>
        <div class="header-subtitle">Smart product demand insights for decision making</div>
        <div class="header-time">Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
    """, unsafe_allow_html=True)

# ── Content ───────────────────────────────────────────────────────────────────
try:
    df = pd.read_csv("latest_demand_intelligence.csv")
    
    # Summary Cards (Top Section)
    col1, col2, col3, col4 = st.columns(4)
    
    threshold = df["priority_score"].quantile(0.75)
    priority_count = len(df[df["priority_score"] >= threshold])
    col1.metric("🔥 Top Products (Top 25%)", priority_count)
    col2.metric("📦 Active Products", (df["activity"] == "ACTIVE").sum())
    col3.metric("🚫 No Demand", (df["demand_level"] == "NO DEMAND").sum())
    col4.metric("📊 Total Products", len(df))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filters in a styled container
    with st.container():
        st.markdown("<h4 style='color:#111827; font-weight:600;'>🔍 Quick Filters</h4>", unsafe_allow_html=True)
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            demand_filter = st.multiselect(
                "Demand Level", df["demand_level"].unique()
            )
            
        with f_col2:
            activity_filter = st.multiselect(
                "Activity", df["activity"].unique()
            )
            
        with f_col3:
            trend_filter = st.multiselect(
                "Trend", df["trend"].unique()
            )
    
    # Apply filters
    filtered_df = df.copy()
    if demand_filter:
        filtered_df = filtered_df[filtered_df["demand_level"].isin(demand_filter)]
    if activity_filter:
        filtered_df = filtered_df[filtered_df["activity"].isin(activity_filter)]
    if trend_filter:
        filtered_df = filtered_df[filtered_df["trend"].isin(trend_filter)]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c_table, c_insights = st.columns([6, 4])
    
    with c_table:
        # Top Products Table
        st.markdown("<h4 style='color:#111827; font-weight:600;'>🔥 Top Priority Products</h4>", unsafe_allow_html=True)
        top_df = filtered_df.sort_values(by="priority_score", ascending=False)
        top_df.insert(0, "Rank", range(1, len(top_df) + 1))
        
        st.dataframe(
            top_df[[
                "Rank",
                "productName",
                "priority_score",
                "demand_level"
            ]].rename(columns={
                "productName": "Product Name",
                "priority_score": "Score",
                "demand_level": "Demand"
            }),
            use_container_width=True,
            hide_index=True
        )

    with c_insights:
        st.markdown("<h4 style='color:#111827; font-weight:600;'>📋 All Products</h4>", unsafe_allow_html=True)
        display_df = filtered_df[[
            "productId", "productName", "will_sell", "demand_level", "activity", "trend"
        ]].copy()
        
        display_df.rename(columns={
            "productId": "Product ID",
            "productName": "Product Name",
            "will_sell": "Will Sell",
            "demand_level": "Demand Level",
            "activity": "Activity",
            "trend": "Trend"
        }, inplace=True)
        
        display_df.insert(0, "S.No", range(1, len(display_df) + 1))
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- WEEKLY DEMAND DISTRIBUTION (FROM SALES DATA) ---
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#111827; font-weight:700;'>📅 Weekly Demand Distribution</h3>", unsafe_allow_html=True)
    
    try:
        sales_df = pd.read_csv("historical_sales.csv")
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        
        sales_df["year"] = sales_df["date"].dt.year.fillna(0).astype(int)
        sales_df["month"] = sales_df["date"].dt.month_name()
        sales_df["month_num"] = sales_df["date"].dt.month.fillna(0).astype(int)
        sales_df["week"] = ((sales_df["date"].dt.day - 1) // 7 + 1).fillna(0).astype(int)
        
        present_date = sales_df["date"].max()
        default_year = int(present_date.year)
        default_month = present_date.strftime('%B')
        default_week = (present_date.day - 1) // 7 + 1
        
        if not sales_df.empty:
            col_y, col_m, col_w = st.columns(3)
            
            with col_y:
                years = sorted(sales_df["year"].unique(), reverse=True)
                y_idx = years.index(default_year) if default_year in years else 0
                selected_year = st.selectbox("Select Year", years, index=y_idx)
            
            with col_m:
                months_df = sales_df[sales_df["year"] == selected_year][["month", "month_num"]].drop_duplicates().sort_values("month_num")
                months = months_df["month"].tolist()
                m_idx = months.index(default_month) if default_month in months else (len(months)-1 if months else 0)
                selected_month = st.selectbox("Select Month", months, index=m_idx)
            
            with col_w:
                weeks = sorted(sales_df[(sales_df["year"] == selected_year) & (sales_df["month"] == selected_month)]["week"].unique())
                w_idx = weeks.index(default_week) if default_week in weeks else (len(weeks)-1 if weeks else 0)
                selected_week = st.selectbox("Select Week", weeks, index=w_idx) if weeks else None
            
            monthly_sales = sales_df[(sales_df["year"] == selected_year) & (sales_df["month"] == selected_month)].copy()
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                compare_prev = st.checkbox("Compare with previous month")
            with col_opt2:
                metric_type = st.radio("Metric", ["Sales Volume", "Unique Products Sold"], horizontal=True)
            
            if metric_type == "Sales Volume":
                weekly_trend = monthly_sales.groupby("week")["final_quantity"].sum().reset_index()
                y_col = "final_quantity"
            else:
                weekly_trend = monthly_sales.groupby("week")["productId"].nunique().reset_index(name="unique_products")
                y_col = "unique_products"
            
            weekly_trend["Week Label"] = weekly_trend["week"].apply(lambda x: f"Week {x}")
            weekly_trend = weekly_trend.sort_values("week")
            
            curr_m_num = monthly_sales["month_num"].iloc[0] if not monthly_sales.empty else 1
            prev_m_num = curr_m_num - 1
            p_year = selected_year
            if prev_m_num == 0:
                prev_m_num = 12
                p_year -= 1
            
            prev_sales = sales_df[(sales_df["year"] == p_year) & (sales_df["month_num"] == prev_m_num)]
            
            if not weekly_trend.empty:
                peak_week = weekly_trend.loc[weekly_trend[y_col].idxmax()]
                lowest_week = weekly_trend.loc[weekly_trend[y_col].idxmin()]
                
                if metric_type == "Sales Volume":
                    curr_total = monthly_sales["final_quantity"].sum()
                    prev_total = prev_sales["final_quantity"].sum()
                else:
                    curr_total = monthly_sales["productId"].nunique()
                    prev_total = prev_sales["productId"].nunique()
                    
                growth = ((curr_total - prev_total) / prev_total) * 100 if prev_total > 0 else (100 if curr_total > 0 else 0)
                growth = max(-100, min(100, growth))
                
                st.markdown(f"**Insights for {selected_month} {selected_year}**")
                ic1, ic2, ic3 = st.columns(3)
                ic1.metric("📈 Peak Week", f"{peak_week['Week Label']}", f"{int(peak_week[y_col])}")
                ic2.metric("📉 Lowest Week", f"{lowest_week['Week Label']}", f"{int(lowest_week[y_col])}")
                ic3.metric("🚀 MoM Growth", f"{growth:.1f}%", "vs Previous Month")
            
            plot_data = weekly_trend[["Week Label", y_col]].copy()
            plot_data.rename(columns={y_col: f"Current Month ({selected_month})"}, inplace=True)
            
            if compare_prev and not prev_sales.empty:
                if metric_type == "Sales Volume":
                    prev_weekly = prev_sales.groupby("week")["final_quantity"].sum().reset_index()
                    prev_y = "final_quantity"
                else:
                    prev_weekly = prev_sales.groupby("week")["productId"].nunique().reset_index(name="unique_products")
                    prev_y = "unique_products"
                    
                prev_weekly["Week Label"] = prev_weekly["week"].apply(lambda x: f"Week {x}")
                prev_month_name = prev_sales["month"].iloc[0]
                prev_weekly.rename(columns={prev_y: f"Previous ({prev_month_name})"}, inplace=True)
                plot_data = plot_data.merge(prev_weekly[["Week Label", f"Previous ({prev_month_name})"]], on="Week Label", how="outer").fillna(0)
                    
            plot_data["week_num"] = plot_data["Week Label"].str.replace("Week ", "").astype(float).astype(int)
            plot_data = plot_data.sort_values("week_num").drop(columns=["week_num"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("<h4 style='color:#111827; font-weight:600;'>Monthly Weekly Trends</h4>", unsafe_allow_html=True)
                st.line_chart(plot_data.set_index("Week Label"))
            
            with col_chart2:
                if selected_week is not None:
                    weekly_sales = sales_df[
                        (sales_df["year"] == selected_year) & 
                        (sales_df["month"] == selected_month) & 
                        (sales_df["week"] == selected_week)
                    ].copy()
                    selected_week_label = f"{selected_month} {selected_year}, Week {selected_week}"
                    
                    weekly_sales["day_type"] = weekly_sales["date"].dt.dayofweek.apply(lambda x: "Weekend" if x >= 5 else "Weekday")
                    
                    total_weekday = weekly_sales[weekly_sales["day_type"] == "Weekday"]["final_quantity"].sum()
                    total_weekend = weekly_sales[weekly_sales["day_type"] == "Weekend"]["final_quantity"].sum()
                    
                    avg_weekday = total_weekday / 5
                    avg_weekend = total_weekend / 2
                    
                    day_type_df = pd.DataFrame({
                        "Day Type": ["Weekday (Avg/Day)", "Weekend (Avg/Day)"],
                        "Normalized Sales": [avg_weekday, avg_weekend]
                    })
                    
                    fig_day = px.bar(
                        day_type_df,
                        x="Day Type", y="Normalized Sales", text="Normalized Sales",
                        color="Day Type", color_discrete_map={"Weekday (Avg/Day)": "#2563EB", "Weekend (Avg/Day)": "#10B981"}
                    )
                    fig_day.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig_day.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        yaxis_title="Average Units Sold", showlegend=False,
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    st.plotly_chart(fig_day, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No weekly sales data available.")

    except Exception as e:
        st.error(f"Error loading weekly distribution: {e}")

except FileNotFoundError:
    st.warning("Please run the pipeline (app.py) first to generate latest_demand_intelligence.csv")
