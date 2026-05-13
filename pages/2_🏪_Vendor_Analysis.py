"""
Vendor-Based Sales Analysis Dashboard — Executive SaaS Layout.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
from streamlit_option_menu import option_menu
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vendor_analysis.data_loader import (
    load_vendor_purchase_summary,
    load_profit_analysis,
    load_monthly_trends,
    load_vendor_product_breakdown,
)

st.set_page_config(page_title="Vendor Analysis", layout="wide", page_icon="🏪")

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif;
    background-color: #F5F7FB; 
}
[data-testid="stSidebarNav"] {display: none !important;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Header */
.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0 20px 0;
    margin-bottom: 20px;
}
.header-title {
    font-size: 32px;
    font-weight: 700;
    color: #0F172A;
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
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border-left: 5px solid #2563EB;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

div[data-testid="stVerticalBlock"] > div > div:nth-child(2) div[data-testid="metric-container"] { border-left-color: #7C3AED; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(3) div[data-testid="metric-container"] { border-left-color: #F59E0B; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(4) div[data-testid="metric-container"] { border-left-color: #10B981; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(5) div[data-testid="metric-container"] { border-left-color: #3B82F6; }
div[data-testid="stVerticalBlock"] > div > div:nth-child(6) div[data-testid="metric-container"] { border-left-color: #8B5CF6; }

div[data-testid="metric-container"] label {
    font-size: 14px;
    color: #6B7280;
    font-weight: 500;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 28px;
    color: #0F172A;
    font-weight: 700;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding-top: 15px;
    padding-bottom: 15px;
    border-radius: 0;
    border-bottom: 3px solid transparent;
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    border-bottom: 3px solid #2563EB !important;
    color: #2563EB !important;
    font-weight: 600;
}

/* Plotly Graph Container Card */
.stPlotlyChart {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.stPlotlyChart:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

/* Dataframe container */
div[data-testid="stDataFrame"] > div {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.chart-title { font-size: 18px; font-weight: 700; color: #0F172A; margin: 0; }
.chart-subtitle { font-size: 13px; color: #6B7280; margin: 2px 0 15px 0; }

/* Empty State Card */
.empty-state-card {
    background-color: #FFFFFF;
    border: 1px dashed #D1D5DB;
    border-radius: 18px;
    padding: 40px;
    text-align: center;
    color: #6B7280;
    margin-top: 10px;
}
.empty-state-icon { font-size: 32px; margin-bottom: 10px; }
.empty-state-text { font-size: 15px; font-weight: 500; }

/* Multiselect Styling */
.stMultiSelect div[data-baseweb="select"] { border-radius: 12px; }
.stMultiSelect div[data-baseweb="select"] span[data-baseweb="tag"] {
    background-color: #EFF6FF;
    color: #1D4ED8;
    border-radius: 6px;
    font-weight: 500;
}

/* Single Month Analytics Card */
.single-month-card {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 40px 20px;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border-top: 5px solid #2563EB;
}
.smc-title { font-size: 16px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.smc-value { font-size: 48px; color: #0F172A; font-weight: 800; margin: 15px 0; }
.smc-subtitle { font-size: 15px; color: #4B5563; }
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
        default_index=2,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6B7280", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px", "text-align": "left", "margin": "5px 0", 
                "color": "#4B5563", "font-family": "'Inter', sans-serif", "border-radius": "8px"
            },
            "nav-link-selected": {"background-color": "#EFF6FF", "color": "#2563EB", "font-weight": "600"},
        }
    )
    
    if selected_page == "Home":
        st.switch_page("Home.py")
    elif selected_page == "Demand Intelligence":
        st.switch_page("pages/1_📊_Demand_Intelligence.py")
    elif selected_page == "Historical Sales":
        st.switch_page("pages/3_📈_Historical_Sales.py")

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_all():
    return load_vendor_purchase_summary(), load_profit_analysis(), load_monthly_trends()

with st.spinner("Fetching vendor data from MongoDB..."):
    try:
        purchase_df, profit_df, trends_df = fetch_all()
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        st.stop()

if purchase_df.empty and profit_df.empty:
    st.warning("⚠️ No vendor data found. Check `warehousepurchases` collection.")
    st.stop()

def fmt_inr(val):
    try: val = float(val)
    except: return "₹0"
    if val >= 1_00_00_000: return f"₹{val/1_00_00_000:.2f} Cr"
    elif val >= 1_00_000: return f"₹{val/1_00_000:.2f} L"
    return f"₹{val:,.0f}"

# ── Dashboard Header ──────────────────────────────────────────────────────────
hc1, hc2 = st.columns([8, 2])
with hc1:
    st.markdown(f"""
        <div class="header-title">Vendor Sales & Profit Analysis</div>
        <div class="header-subtitle">Executive analytics on vendor performance, purchase volumes, and profitability</div>
        <div class="header-time">Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
    """, unsafe_allow_html=True)
with hc2:
    st.write("")
    if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

st.write("")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_vendors  = purchase_df["vendorId"].nunique() if not purchase_df.empty else 0
total_purchase = purchase_df["totalPurchaseAmt"].sum() if not purchase_df.empty else 0
total_revenue  = profit_df["totalRevenue"].sum() if not profit_df.empty else 0
total_profit   = profit_df["estimatedProfit"].sum() if not profit_df.empty else 0
avg_margin     = profit_df["profitMarginPct"].mean() if not profit_df.empty else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Vendors", total_vendors)
k2.metric("Total Purchase Volume", fmt_inr(total_purchase))
k3.metric("Total Revenue Generated", fmt_inr(total_revenue))
k4.metric("Estimated Profit", fmt_inr(total_profit))
k5.metric("Avg Profit Margin", f"{avg_margin:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Plotly Globals ────────────────────────────────────────────────────────────
plotly_config = {'displayModeBar': False}
plotly_defaults = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter", size=13, color="#4B5563"),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Inter", bordercolor="#E5E7EB"),
)
primary_palette = ["#1D4ED8", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Executive Overview",
    "💰 Profit Analysis",
    "🔍 Vendor Drill-Down"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── [ Large Trend Chart ] ──
    st.markdown("<div class='chart-title'>Monthly Purchase Trend</div>", unsafe_allow_html=True)
    st.markdown("<div class='chart-subtitle'>Purchase growth performance over time</div>", unsafe_allow_html=True)
    
    if not trends_df.empty:
        available_months = sorted(trends_df["monthStr"].unique())
        f_col1, f_col2 = st.columns([3, 7])
        with f_col1:
            selected_months = st.multiselect("📅 Filter Months", available_months, default=available_months, key="trend_month_filter")
        
        filtered_trends = trends_df[trends_df["monthStr"].isin(selected_months)] if selected_months else pd.DataFrame()
        
        if filtered_trends.empty:
            st.markdown("""
            <div class='empty-state-card'>
                <div class='empty-state-icon'>📉</div>
                <div class='empty-state-text'>No purchase data available for selected months</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            monthly_total = filtered_trends.groupby("monthStr")["totalPurchaseAmt"].sum().reset_index()
            monthly_total = monthly_total.sort_values("monthStr")
            month_count = len(monthly_total)
            
            if month_count == 1:
                # CASE 1: Single month selected -> Centered Analytics Card
                single_month = monthly_total.iloc[0]["monthStr"]
                month_purchases = monthly_total.iloc[0]["totalPurchaseAmt"]
                vendor_count = filtered_trends["vendorName"].nunique()
                
                mom_text = "No previous month data"
                mom_color = "#6B7280"
                try:
                    curr_idx = available_months.index(single_month)
                    if curr_idx > 0:
                        prev_month = available_months[curr_idx - 1]
                        prev_purchases = trends_df[trends_df["monthStr"] == prev_month]["totalPurchaseAmt"].sum()
                        if prev_purchases > 0:
                            growth = ((month_purchases - prev_purchases) / prev_purchases) * 100
                            if growth > 0:
                                mom_text = f"↑ {growth:.1f}% vs {prev_month}"
                                mom_color = "#10B981"
                            else:
                                mom_text = f"↓ {abs(growth):.1f}% vs {prev_month}"
                                mom_color = "#EF4444"
                except Exception:
                    pass
                
                st.markdown(f"""
                <div class='single-month-card'>
                    <div class='smc-title'>Performance for {single_month}</div>
                    <div class='smc-value'>{fmt_inr(month_purchases)}</div>
                    <div class='smc-subtitle'>Across <b>{vendor_count}</b> active vendors &nbsp;|&nbsp; <span style='color: {mom_color}; font-weight: 600;'>{mom_text}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                # CASE 2 & 3: Multiple months -> Smooth Area Chart
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=monthly_total["monthStr"], y=monthly_total["totalPurchaseAmt"],
                    mode='lines+markers',
                    line=dict(color='#2563EB', width=3, shape='spline', smoothing=1.3),
                    marker=dict(size=8, color='#1D4ED8'),
                    fill='tozeroy',
                    fillcolor='rgba(37, 99, 235, 0.15)',
                    name='Total Purchases',
                    hovertemplate="<b>%{x}</b><br>Purchases: ₹%{y:,.0f}<extra></extra>"
                ))
                
                fig_trend.update_layout(
                    **plotly_defaults,
                    height=400,
                    margin=dict(l=10, r=20, t=10, b=40),
                    xaxis=dict(showgrid=False, zeroline=False, title="", type='category'),
                    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False, title="", tickfont=dict(color="#9CA3AF")),
                    hovermode="x unified"
                )
                
                if month_count >= 6:
                    fig_trend.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.08)
                    
                st.plotly_chart(fig_trend, use_container_width=True, config=plotly_config)
    else:
        st.info("No trend data available.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── [ Vendor Ranking ] [ Purchase Share ] ──
    c_rank, c_share = st.columns([6, 4])
    
    if not purchase_df.empty:
        # Process Top N
        top_n = 10
        top_vendors = purchase_df.sort_values("totalPurchaseAmt", ascending=False).head(top_n)
        
        with c_rank:
            st.markdown("<div class='chart-title'>Top Vendors by Purchase Volume</div>", unsafe_allow_html=True)
            st.markdown("<div class='chart-subtitle'>Highest performing vendors based on purchase amount</div>", unsafe_allow_html=True)
            
            # Executive ranking bar chart
            fig_bar = px.bar(
                top_vendors.sort_values("totalPurchaseAmt", ascending=True),
                x="totalPurchaseAmt", y="vendorName", orientation="h",
                color="totalPurchaseAmt", color_continuous_scale="Blues",
                text="totalPurchaseAmt",
            )
            fig_bar.update_traces(
                texttemplate="₹%{x:,.0f}", textposition="outside", 
                textfont=dict(size=13, color="#111827", family="Inter"),
                hovertemplate="<b>%{y}</b><br>Amount: ₹%{x:,.0f}<extra></extra>",
                marker=dict(line=dict(width=0)),
                width=0.7 # Thick bars
            )
            fig_bar.update_layout(
                **plotly_defaults,
                height=500,
                margin=dict(l=10, r=100, t=10, b=20),
                yaxis=dict(automargin=True, title="", tickfont=dict(color="#0F172A", weight="bold")),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False, title="", showticklabels=False),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config=plotly_config)
            
        with c_share:
            st.markdown("<div class='chart-title'>Purchase Share</div>", unsafe_allow_html=True)
            st.markdown("<div class='chart-subtitle'>Market share of top 5 vendors vs others</div>", unsafe_allow_html=True)
            
            # Donut chart: Top 5 + Others
            df_pie = purchase_df.sort_values("totalPurchaseAmt", ascending=False).copy()
            top_5 = df_pie.head(5).copy()
            others_amt = df_pie.iloc[5:]["totalPurchaseAmt"].sum()
            if others_amt > 0:
                others_row = pd.DataFrame([{"vendorName": "Others", "totalPurchaseAmt": others_amt}])
                df_pie = pd.concat([top_5, others_row], ignore_index=True)
            else:
                df_pie = top_5
                
            fig_pie = px.pie(
                df_pie, names="vendorName", values="totalPurchaseAmt", hole=0.65,
                color_discrete_sequence=primary_palette
            )
            fig_pie.update_traces(
                textinfo="percent", textposition="outside",
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
                marker=dict(line=dict(color='#FFFFFF', width=3))
            )
            # Add Total Center Text
            total_val = purchase_df["totalPurchaseAmt"].sum()
            fig_pie.add_annotation(
                text=f"<span style='font-size:14px;color:#6B7280'>Total Purchase</span><br><br><span style='font-size:24px;font-weight:700;color:#0F172A'>{fmt_inr(total_val)}</span>",
                x=0.5, y=0.5, showarrow=False
            )
            fig_pie.update_layout(
                **plotly_defaults,
                height=500,
                margin=dict(l=20, r=150, t=20, b=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0, title="")
            )
            st.plotly_chart(fig_pie, use_container_width=True, config=plotly_config)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── [ Heatmap ] [ Monthly Comparison ] ──
    c_heat, c_stack = st.columns([5, 5])
    
    if not trends_df.empty:
        # Prepare Top 5 vendors for Heatmap & Stacked to avoid clutter
        top5_vendor_names = purchase_df.sort_values("totalPurchaseAmt", ascending=False).head(5)["vendorName"].tolist()
        t_top5 = filtered_trends[filtered_trends["vendorName"].isin(top5_vendor_names)].copy() if 'filtered_trends' in locals() else trends_df[trends_df["vendorName"].isin(top5_vendor_names)].copy()
        
        with c_heat:
            st.markdown("<div class='chart-title'>Monthly Purchase Heatmap</div>", unsafe_allow_html=True)
            st.markdown("<div class='chart-subtitle'>Purchase intensity across top 5 vendors</div>", unsafe_allow_html=True)
            
            if filtered_trends.empty:
                st.markdown("""
                <div class='empty-state-card' style='padding: 20px;'>
                    <div class='empty-state-text'>No data</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                pivot = t_top5.pivot_table(index="vendorName", columns="monthStr", values="totalPurchaseAmt", aggfunc="sum")
                pivot = pivot.dropna(axis=1, how='all').fillna(0)
                
                if pivot.empty:
                    st.info("No data available for top vendors.")
                else:
                    month_order = sorted(pivot.columns, key=lambda x: datetime.strptime(x, "%Y-%m") if len(x.split('-'))==2 else x)
                    pivot = pivot[month_order]
                    
                    # Dynamically adjust aspect ratio for sparse data
                    num_cols = len(pivot.columns)
                    aspect_ratio = "auto" if num_cols > 2 else num_cols * 0.8
                    
                    fig_heat = px.imshow(
                        pivot.values,
                        x=pivot.columns,
                        y=pivot.index,
                        color_continuous_scale="Blues",
                        aspect=aspect_ratio,
                        text_auto=".2s"
                    )
                    fig_heat.update_traces(
                        hovertemplate="<b>Vendor:</b> %{y}<br><b>Month:</b> %{x}<br><b>Amount:</b> ₹%{z:,.0f}<extra></extra>",
                        textfont=dict(color="#0F172A", family="Inter")
                    )
                    fig_heat.update_layout(
                        **plotly_defaults,
                        height=400,
                        margin=dict(l=10, r=10, t=20, b=40),
                        coloraxis_showscale=False,
                        xaxis=dict(title="", showgrid=False, type='category', tickangle=0),
                        yaxis=dict(title="", showgrid=False, tickfont=dict(weight="bold", color="#0F172A"))
                    )
                    st.plotly_chart(fig_heat, use_container_width=True, config=plotly_config)
            
        with c_stack:
            st.markdown("<div class='chart-title'>Monthly Comparison (Top 5)</div>", unsafe_allow_html=True)
            st.markdown("<div class='chart-subtitle'>Stacked volume by top performing vendors</div>", unsafe_allow_html=True)
            
            if filtered_trends.empty or t_top5.empty:
                st.markdown("""
                <div class='empty-state-card' style='padding: 20px;'>
                    <div class='empty-state-text'>No data</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                t_top5 = t_top5.sort_values("monthStr")
                fig_stack = px.bar(
                    t_top5, x="monthStr", y="totalPurchaseAmt", color="vendorName",
                    barmode="stack", color_discrete_sequence=primary_palette
                )
                fig_stack.update_traces(
                    hovertemplate="<b>%{x}</b><br>%{fullData.name}: ₹%{y:,.0f}<extra></extra>",
                    marker=dict(line=dict(color='#FFFFFF', width=1))
                )
                
                bar_width = min(0.3 * t_top5["monthStr"].nunique(), 0.8)
                
                fig_stack.update_layout(
                    **plotly_defaults,
                    height=400,
                    margin=dict(l=10, r=10, t=20, b=40),
                    xaxis=dict(title="", showgrid=False, type='category'),
                    yaxis=dict(title="", showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False),
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=""),
                    bargap=1-bar_width
                )
                st.plotly_chart(fig_stack, use_container_width=True, config=plotly_config)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PROFIT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if profit_df.empty:
        st.info("No profit data available.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        rank_by = st.radio(
            "🏆 Rank vendors by",
            ["Estimated Profit", "Total Revenue", "Profit Margin %"],
            horizontal=True, key="rank_by"
        )
        rank_col = {"Estimated Profit": "estimatedProfit", "Total Revenue": "totalRevenue", "Profit Margin %": "profitMarginPct"}[rank_by]
        top_profit_df = profit_df.sort_values(rank_col, ascending=True).tail(15)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='chart-title'>Top Vendors — {rank_by}</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-subtitle'>Profitability and revenue performance ranking</div>", unsafe_allow_html=True)

        is_pct = "Margin" in rank_by
        fig_profit = px.bar(
            top_profit_df,
            x=rank_col, y="vendorName", orientation="h",
            color="profitMarginPct",
            color_continuous_scale="Blues", 
            text=rank_col,
        )
        fig_profit.update_traces(
            texttemplate="%{x:.1f}%" if is_pct else "₹%{x:,.0f}",
            textposition="outside", 
            textfont=dict(size=13, color="#0F172A", family="Inter"),
            hovertemplate="<b>%{y}</b><br>Value: %{text}<br>Margin: %{marker.color:.1f}%<extra></extra>",
            marker=dict(line=dict(width=0)), width=0.7
        )
        fig_profit.update_layout(
            **plotly_defaults,
            height=600,
            margin=dict(l=10, r=100, t=10, b=20),
            yaxis=dict(automargin=True, title="", tickfont=dict(color="#0F172A", weight="bold")),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False, title="", showticklabels=False),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_profit, use_container_width=True, config=plotly_config)

        st.markdown("<br><div class='chart-title'>Profit Summary Table</div><br>", unsafe_allow_html=True)
        ptbl = profit_df.sort_values("estimatedProfit", ascending=False).copy()
        for col in ["totalRevenue","totalCost","totalPurchaseAmt","totalGST","estimatedProfit"]:
            if col in ptbl.columns: ptbl[col] = ptbl[col].apply(fmt_inr)
        if "profitMarginPct" in ptbl.columns:
            ptbl["profitMarginPct"] = ptbl["profitMarginPct"].apply(lambda x: f"{x:.1f}%")
        ptbl = ptbl.rename(columns={
            "vendorName": "Vendor", "totalPurchaseAmt": "Purchase Cost", "totalGST": "GST",
            "totalRevenue": "Revenue", "estimatedProfit": "Est. Profit",
            "profitMarginPct": "Margin %", "totalQuantity": "Qty", "transactionCount": "Txns"
        })
        cols_p = [c for c in ["Vendor","Qty","Purchase Cost","GST","Revenue","Est. Profit","Margin %","Txns"] if c in ptbl.columns]
        ptbl.insert(0, "Rank", range(1, len(ptbl)+1))
        st.dataframe(ptbl[["Rank"]+cols_p], use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VENDOR DRILL-DOWN
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    if purchase_df.empty:
        st.info("No vendor data available.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        vendor_name_map = dict(zip(purchase_df["vendorName"], purchase_df["vendorId"]))
        selected_name = st.selectbox("🏢 Select Vendor for Deep-Dive", sorted(vendor_name_map.keys()))
        selected_id   = vendor_name_map[selected_name]

        st.markdown("<br>", unsafe_allow_html=True)
        vp = purchase_df[purchase_df["vendorId"] == selected_id]
        vf = profit_df[profit_df["vendorId"] == selected_id] if not profit_df.empty else pd.DataFrame()

        if not vp.empty:
            r = vp.iloc[0]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("📞 Contact", str(r.get("contactNumber","N/A")))
            d2.metric("📍 Location", str(r.get("location","N/A")))
            d3.metric("💰 Total Spent", fmt_inr(r.get("totalPurchaseAmt",0)))
            d4.metric("📦 Unique SKUs", int(r.get("uniqueProductCount",0)))
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if not vf.empty:
                rf = vf.iloc[0]
                e1, e2, e3, e4 = st.columns(4)
                e1.metric("🧾 GST Paid", fmt_inr(r.get("totalGST",0)))
                e2.metric("📈 Revenue", fmt_inr(rf.get("totalRevenue",0)))
                e3.metric("💹 Est. Profit", fmt_inr(rf.get("estimatedProfit",0)), f"{rf.get('profitMarginPct',0):.1f}% margin")
                e4.metric("📊 Transactions", int(r.get("transactionCount",0)))

        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:#0F172A; font-weight:700;'>Product Catalog for {selected_name}</h3>", unsafe_allow_html=True)
        
        with st.spinner("Loading product details..."):
            breakdown_df = load_vendor_product_breakdown(selected_id)

        if not breakdown_df.empty:
            pc1, pc2 = st.columns([6, 4])
            with pc1:
                st.markdown("<div class='chart-title'>Profit per Product</div>", unsafe_allow_html=True)
                st.markdown("<div class='chart-subtitle'>Highest margin items for this vendor</div>", unsafe_allow_html=True)
                fig_prod = px.bar(
                    breakdown_df.head(15).sort_values("estimatedProfit", ascending=True),
                    x="estimatedProfit", y="productName", orientation="h",
                    color="estimatedProfit", color_continuous_scale="Blues",
                    text="estimatedProfit"
                )
                fig_prod.update_traces(
                    texttemplate="₹%{x:,.0f}", textposition="outside", 
                    textfont=dict(size=12, family="Inter", color="#0F172A"),
                    hovertemplate="<b>%{y}</b><br>Profit: ₹%{x:,.0f}<extra></extra>", width=0.7
                )
                fig_prod.update_layout(
                    **plotly_defaults,
                    height=500, margin=dict(l=10, r=100, t=10, b=10),
                    yaxis=dict(automargin=True, title="", tickfont=dict(weight="bold")),
                    xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", title="", showticklabels=False),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_prod, use_container_width=True, config=plotly_config)

            with pc2:
                st.markdown("<div class='chart-title'>Revenue Share</div>", unsafe_allow_html=True)
                st.markdown("<div class='chart-subtitle'>Top 10 products proportion</div>", unsafe_allow_html=True)
                fig_rev = px.pie(
                    breakdown_df.head(10), names="productName", values="totalRevenue", hole=0.6,
                    color_discrete_sequence=primary_palette
                )
                fig_rev.update_traces(
                    textinfo="percent", textposition="outside",
                    hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
                    marker=dict(line=dict(color='#FFFFFF', width=2))
                )
                fig_rev.update_layout(
                    **plotly_defaults,
                    showlegend=False, height=500, margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(fig_rev, use_container_width=True, config=plotly_config)

            st.markdown("<br><div class='chart-title'>Product Details</div><br>", unsafe_allow_html=True)
            bd = breakdown_df.copy()
            for col in ["totalPurchaseCost","totalGST","totalRevenue","estimatedProfit","avgPricePerUnit","sellingPricePerUnit"]:
                if col in bd.columns: bd[col] = bd[col].apply(fmt_inr)
            if "profitPercentage" in bd.columns:
                bd["profitPercentage"] = bd["profitPercentage"].apply(lambda x: f"{x:.1f}%")
            bd = bd.rename(columns={
                "productName": "Product", "unitValue": "Unit", "totalQuantity": "Qty",
                "totalPurchaseCost": "Purchase Cost", "totalGST": "GST",
                "avgPricePerUnit": "Avg Buy Price", "sellingPricePerUnit": "Sell Price",
                "profitPercentage": "Margin %", "totalRevenue": "Revenue", "estimatedProfit": "Est. Profit"
            })
            bd.insert(0, "S.No", range(1, len(bd)+1))
            show = [c for c in ["S.No","Product","Unit","Qty","Purchase Cost","GST","Avg Buy Price","Sell Price","Margin %","Revenue","Est. Profit"] if c in bd.columns]
            st.dataframe(bd[show], use_container_width=True, hide_index=True)
