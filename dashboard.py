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
        
        threshold = df["priority_score"].quantile(0.75)
        priority_count = len(df[df["priority_score"] >= threshold])
        col1.metric("🔥 Top Products (Top 25%)", priority_count)
        col2.metric("📦 Active Products", (df["activity"] == "ACTIVE").sum())
        col3.metric("🚫 No Demand", (df["demand_level"] == "NO DEMAND").sum())
        col4.metric("📊 Total Products", len(df))
        
        # Filters (In Tab)
        st.markdown("### 🔍 Filters")
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
        
        # Top Products Table
        st.subheader("🔥 Top Priority Products")
        
        top_df = filtered_df.sort_values(
            by="priority_score", ascending=False
        )
        
        # Add Rank column
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
        
        # --- WEEKLY DEMAND DISTRIBUTION (FROM SALES DATA) ---
        st.markdown("---")
        st.subheader("📅 Weekly Demand Distribution")
        
        try:
            # 1. Load sales data to calculate weekly demand dynamically
            sales_df = pd.read_csv("historical_sales.csv")
            sales_df["date"] = pd.to_datetime(sales_df["date"])
            
            # Prepare Time Columns
            sales_df["year"] = sales_df["date"].dt.year.fillna(0).astype(int)
            sales_df["month"] = sales_df["date"].dt.month_name()
            sales_df["month_num"] = sales_df["date"].dt.month.fillna(0).astype(int)
            # Calculate relative week of the month (1 to 5)
            sales_df["week"] = ((sales_df["date"].dt.day - 1) // 7 + 1).fillna(0).astype(int)
            
            # Determine Present Defaults (Latest Date in Data)
            present_date = sales_df["date"].max()
            default_year = int(present_date.year)
            default_month = present_date.strftime('%B')
            default_week = (present_date.day - 1) // 7 + 1
            
            if not sales_df.empty:
                # Time Control: 3 Dropdowns
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
                    if weeks:
                        selected_week = st.selectbox("Select Week", weeks, index=w_idx)
                    else:
                        selected_week = None
                
                monthly_sales = sales_df[(sales_df["year"] == selected_year) & (sales_df["month"] == selected_month)].copy()
                
                # Pro improvements options
                st.markdown("---")
                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    compare_prev = st.checkbox("Compare with previous month")
                with col_opt2:
                    metric_type = st.radio("Metric", ["Sales Volume", "Unique Products Sold"], horizontal=True)
                
                # 3. Aggregate weekly for the line chart
                if metric_type == "Sales Volume":
                    weekly_trend = monthly_sales.groupby("week")["final_quantity"].sum().reset_index()
                    y_col = "final_quantity"
                else:
                    weekly_trend = monthly_sales.groupby("week")["productId"].nunique().reset_index(name="unique_products")
                    y_col = "unique_products"
                
                weekly_trend["Week Label"] = weekly_trend["week"].apply(lambda x: f"Week {x}")
                weekly_trend = weekly_trend.sort_values("week")
                
                # Pre-calculate previous month for MoM Growth
                curr_m_num = monthly_sales["month_num"].iloc[0] if not monthly_sales.empty else 1
                prev_m_num = curr_m_num - 1
                p_year = selected_year
                if prev_m_num == 0:
                    prev_m_num = 12
                    p_year -= 1
                
                prev_sales = sales_df[(sales_df["year"] == p_year) & (sales_df["month_num"] == prev_m_num)]
                
                # Insights
                if not weekly_trend.empty:
                    peak_week = weekly_trend.loc[weekly_trend[y_col].idxmax()]
                    lowest_week = weekly_trend.loc[weekly_trend[y_col].idxmin()]
                    
                    # Calculate MoM Growth
                    if metric_type == "Sales Volume":
                        curr_total = monthly_sales["final_quantity"].sum()
                        prev_total = prev_sales["final_quantity"].sum()
                    else:
                        curr_total = monthly_sales["productId"].nunique()
                        prev_total = prev_sales["productId"].nunique()
                        
                    if prev_total > 0:
                        growth = ((curr_total - prev_total) / prev_total) * 100
                    else:
                        growth = 100 if curr_total > 0 else 0
                    
                    # Cap growth to a 0-100 scale (allowing negative for decline)
                    growth = max(-100, min(100, growth))
                    
                    st.markdown(f"**Insights for {selected_month} {selected_year}**")
                    ic1, ic2, ic3 = st.columns(3)
                    ic1.metric("📈 Peak Week", f"{peak_week['Week Label']}", f"{int(peak_week[y_col])}")
                    ic2.metric("📉 Lowest Week", f"{lowest_week['Week Label']}", f"{int(lowest_week[y_col])}")
                    ic3.metric("🚀 MoM Growth", f"{growth:.1f}%", "vs Previous Month")
                
                # Line Chart Data Prep
                plot_data = weekly_trend[["Week Label", y_col]].copy()
                plot_data.rename(columns={y_col: f"Current Month ({selected_month})"}, inplace=True)
                
                if compare_prev:
                    if not prev_sales.empty:
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
                        
                # Ensure sort for Edge Case: 5 weeks
                plot_data["week_num"] = plot_data["Week Label"].str.replace("Week ", "").astype(float).astype(int)
                plot_data = plot_data.sort_values("week_num").drop(columns=["week_num"])
                
                st.markdown("---")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown("**Monthly Weekly Trends**")
                    st.line_chart(plot_data.set_index("Week Label"))
                
                with col_chart2:
                    if selected_week is not None:
                        # Weekday vs Weekend logic for selected week
                        weekly_sales = sales_df[
                            (sales_df["year"] == selected_year) & 
                            (sales_df["month"] == selected_month) & 
                            (sales_df["week"] == selected_week)
                        ].copy()
                        selected_week_label = f"{selected_month} {selected_year}, Week {selected_week}"
                        
                        weekly_sales["day_type"] = weekly_sales["date"].dt.dayofweek.apply(lambda x: "Weekend" if x >= 5 else "Weekday")
                        
                        total_weekday = weekly_sales[weekly_sales["day_type"] == "Weekday"]["final_quantity"].sum()
                        total_weekend = weekly_sales[weekly_sales["day_type"] == "Weekend"]["final_quantity"].sum()
                        
                        # Normalize averages
                        avg_weekday = total_weekday / 5
                        avg_weekend = total_weekend / 2
                        
                        day_type_df = pd.DataFrame({
                            "Day Type": ["Weekday (Avg/Day)", "Weekend (Avg/Day)"],
                            "Normalized Sales": [avg_weekday, avg_weekend]
                        })
                        
                        fig_day = px.bar(
                            day_type_df,
                            x="Day Type",
                            y="Normalized Sales",
                            text="Normalized Sales",
                            title=f"Weekday vs Weekend Avg ({selected_week_label})",
                            color="Day Type",
                            color_discrete_map={"Weekday (Avg/Day)": "#636EFA", "Weekend (Avg/Day)": "#EF553B"}
                        )
                        fig_day.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                        fig_day.update_layout(
                            transition_duration=500,
                            yaxis_title="Average Units Sold",
                            showlegend=False
                        )
                        st.plotly_chart(fig_day, use_container_width=True)
                    else:
                        st.info("No weekly sales data available.")
                
        except Exception as e:
            st.error(f"Error loading weekly distribution: {e}")
        
        # Full Data Table (Custom Columns)
        st.subheader("📋 All Products")
        
        # Prepare display DataFrame
        display_df = filtered_df[[
            "productId", "productName", "will_sell", "demand_level", "activity", "trend"
        ]].copy()
        
        # Rename columns for display
        display_df.rename(columns={
            "productId": "Product ID",
            "productName": "Product Name",
            "will_sell": "Will Sell",
            "demand_level": "Demand Level",
            "activity": "Activity",
            "trend": "Trend"
        }, inplace=True)
        
        # Add S.No
        display_df.insert(0, "S.No", range(1, len(display_df) + 1))
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    except FileNotFoundError:
        st.warning("Please run the pipeline (app.py) first to generate latest_demand_intelligence.csv")

with tab2:
    # --- HISTORICAL SALES TAB ---
    try:
        df_sales = pd.read_csv("historical_sales.csv")
        df_sales["date"] = pd.to_datetime(df_sales["date"])
        
        # Step 6: DATE FILTER (Daily View)
        st.subheader("📅 Daily Sales")
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
        
        if top_daily.empty:
            st.info("No sales data available for this date.")
            
        st.markdown("---")
        
        # Step 7: MONTH FILTER (Monthly View)
        st.subheader("📆 Monthly Sales")
        
        # Extract month properly
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
            .head(5)
            .reset_index(drop=True)
        )

        top_monthly.index = top_monthly.index + 1

        top_monthly["Packets Sold"] = (
            top_monthly["quantity_sold"].astype(str) + " packets"
        )

        st.subheader(f"📆 Top 5 Products in {selected_month_hist}")
        st.dataframe(top_monthly[["productName", "Packets Sold", "order_count"]], use_container_width=True)
        
        if top_monthly.empty:
            st.info("No sales data available for this month.")

    except FileNotFoundError:
        st.warning("Please run the pipeline (app.py) first to generate historical sales datasets.")
