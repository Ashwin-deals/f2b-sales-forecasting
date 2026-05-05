import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Demand Intelligence", layout="wide")

st.title("📊 Demand Intelligence Dashboard")
st.caption("Smart product demand insights for decision making")

tab1, tab2 = st.tabs(["🔮 Demand Intelligence", "📈 Historical Sales"])

with tab1:
    # --- DEMAND INTELLIGENCE TAB ---
    try:
        df = pd.read_csv("latest_demand_intelligence.csv")
        
        # Summary Cards (Top Section)
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("🔥 Top Products", (df["priority_score"] >= 5).sum())
        col2.metric("📦 Active Products", (df["activity"] == "ACTIVE").sum())
        col3.metric("🚫 No Demand", (df["demand_level"] == "NO DEMAND").sum())
        col4.metric("📊 Total Products", len(df))
        
        # Filters (Sidebar)
        st.sidebar.header("🔍 Filters")
        
        demand_filter = st.sidebar.multiselect(
            "Demand Level", df["demand_level"].unique()
        )
        
        activity_filter = st.sidebar.multiselect(
            "Activity", df["activity"].unique()
        )
        
        trend_filter = st.sidebar.multiselect(
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
        
        # Top Products Table
        st.subheader("🔥 Top Priority Products")
        
        top_df = filtered_df.sort_values(
            by="priority_score", ascending=False
        ).head(10)
        
        st.dataframe(
            top_df[[
                "productName",
                "priority_score",
                "demand_level",
                "activity",
                "trend"
            ]],
            use_container_width=True
        )
        
        # Charts Section
        col1, col2, col3 = st.columns(3)
        
        # Demand Level Chart
        demand_counts = filtered_df["demand_level"].value_counts().reset_index()
        demand_counts.columns = ["Demand Level", "Count"]
        
        fig1 = px.bar(demand_counts, x="Demand Level", y="Count", title="Demand Distribution")
        col1.plotly_chart(fig1, use_container_width=True)
        
        # Activity Chart
        activity_counts = filtered_df["activity"].value_counts().reset_index()
        activity_counts.columns = ["Activity", "Count"]
        
        fig2 = px.bar(activity_counts, x="Activity", y="Count", title="Activity Distribution")
        col2.plotly_chart(fig2, use_container_width=True)
        
        # Trend Chart
        trend_counts = filtered_df["trend"].value_counts().reset_index()
        trend_counts.columns = ["Trend", "Count"]
        
        fig3 = px.bar(trend_counts, x="Trend", y="Count", title="Trend Distribution")
        col3.plotly_chart(fig3, use_container_width=True)
        
        # Full Data Table
        st.subheader("📋 All Products")
        st.dataframe(filtered_df, use_container_width=True)
    except FileNotFoundError:
        st.warning("Please run the pipeline (app.py) first to generate latest_demand_intelligence.csv")

with tab2:
    # --- HISTORICAL SALES TAB ---
    try:
        df_sales = pd.read_csv("historical_sales.csv")
        df_sales["date"] = pd.to_datetime(df_sales["date"])
        
        st.sidebar.markdown("---")
        
        # Step 6: DATE FILTER (Daily View)
        st.sidebar.subheader("📅 Daily Sales")
        selected_date = st.sidebar.date_input("Select Date", df_sales["date"].max())
        
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
            .head(5)
            .reset_index(drop=True)
        )

        # Fix serial number
        top_daily.index = top_daily.index + 1

        # Display column
        top_daily["Packets Sold"] = (
            top_daily["quantity_sold"].astype(str) + " packets"
        )

        st.subheader(f"📅 Top 5 Products on {selected_date.strftime('%d-%m-%Y') if hasattr(selected_date, 'strftime') else selected_date}")
        st.dataframe(top_daily[["productName", "Packets Sold", "order_count"]], use_container_width=True)
        
        if not top_daily.empty:
            fig_daily = px.bar(
                top_daily,
                x="productName",
                y="quantity_sold",
                title=f"Top Daily Products ({selected_date})"
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No sales data available for this date.")
            
        st.markdown("---")
        
        # Step 7: MONTH FILTER (Monthly View)
        st.sidebar.subheader("📆 Monthly Sales")
        
        # Extract month properly
        df_sales["month"] = df_sales["date"].dt.to_period("M").astype(str)
        
        selected_month = st.sidebar.selectbox(
            "Select Month",
            sorted(df_sales["month"].unique(), reverse=True)
        )
        
        monthly_filtered = df_sales[
            df_sales["month"] == selected_month
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
            .head(5)
            .reset_index(drop=True)
        )

        top_monthly.index = top_monthly.index + 1

        top_monthly["Packets Sold"] = (
            top_monthly["quantity_sold"].astype(str) + " packets"
        )

        st.subheader(f"📆 Top 5 Products in {selected_month}")
        st.dataframe(top_monthly[["productName", "Packets Sold", "order_count"]], use_container_width=True)
        
        if not top_monthly.empty:
            fig_monthly = px.bar(
                top_monthly,
                x="productName",
                y="quantity_sold",
                title=f"Top Monthly Products ({selected_month})"
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No sales data available for this month.")

    except FileNotFoundError:
        st.warning("Please run the pipeline (app.py) first to generate historical sales datasets.")
