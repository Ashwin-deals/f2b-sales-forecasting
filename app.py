import logging
from db.fetch_data import fetch_order_data, fetch_products
from processing.clean_data import parse_and_clean_data
from processing.aggregate import aggregate_daily_sales
from processing.feature_engineering import build_features
# ML models completely removed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Demand Forecasting Pipeline...")

    # 1. Fetch
    logger.info("--- Step 1: Fetching Data ---")
    orderdetails, retailorders = fetch_order_data()

    # 2. Process
    logger.info("--- Step 2: Processing Data ---")
    dfRaw = parse_and_clean_data(orderdetails, retailorders)
    logger.info(f"Combined Raw DataFrame shape: {dfRaw.shape}")
    
    dfAgg = aggregate_daily_sales(dfRaw)
    logger.info(f"Aggregated DataFrame shape: {dfAgg.shape}")

    # --- HISTORICAL SALES DATASET ---
    import pandas as pd
    df_sales = dfRaw.copy()
    if "sales" in df_sales.columns:
        df_sales.rename(columns={"sales": "final_quantity"}, inplace=True)
    df_sales["date"] = pd.to_datetime(df_sales["date"])
    df_sales["date_str"] = df_sales["date"].dt.strftime("%d-%m-%Y")
    
    if "unit" not in df_sales.columns:
        df_sales["unit"] = ""
    else:
        df_sales["unit"] = df_sales["unit"].fillna("").astype(str)

    df_sales = df_sales[["productId", "date", "date_str", "final_quantity", "unit"]]
    
    products_data = fetch_products()
    if products_data:
        products_df = pd.DataFrame(products_data)
        products_df["_id"] = products_df["_id"].astype(str)
        df_sales["productId"] = df_sales["productId"].astype(str)
        
        df_sales = df_sales.merge(
            products_df[["_id", "productName"]],
            left_on="productId",
            right_on="_id",
            how="left"
        )
        if "_id" in df_sales.columns:
            df_sales.drop(columns=["_id"], inplace=True)
        if "productName" not in df_sales.columns:
            df_sales["productName"] = "UNKNOWN PRODUCT"
        else:
            df_sales["productName"] = df_sales["productName"].fillna("UNKNOWN PRODUCT")
    else:
        df_sales["productName"] = "UNKNOWN PRODUCT"

    df_sales["month"] = df_sales["date"].dt.to_period("M").astype(str)
    df_sales.to_csv("historical_sales.csv", index=False)
    logger.info("Generated historical_sales.csv")

    # --- STEP 3: FIX ACTIVE PRODUCT FILTER ---
    today = df_sales["date"].max()
    sales_60d = (
        df_sales[df_sales["date"] >= today - pd.Timedelta(days=60)]
        .groupby("productId")["final_quantity"]
        .sum()
    )
    active_products = sales_60d[sales_60d > 5].index
    
    df_active = df_sales[df_sales["productId"].isin(active_products)].copy()
    
    # --- STEP 5: RECOMPUTE FEATURES ON UNPADDED DATA ---
    df_active = df_active.sort_values(["productId", "date"])
    
    df_active["avg_7"] = df_active.groupby("productId")["final_quantity"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    
    df_active["recent_sales"] = df_active.groupby("productId")["final_quantity"].transform(
        lambda x: x.rolling(7, min_periods=1).sum()
    )
    
    # Get the latest row for each product
    df_today = df_active.groupby("productId").tail(1).copy()
    
    # --- STEP 6: DEMAND CLASSIFICATION ---
    def classify_demand(row):
        if row["recent_sales"] == 0:
            return "NO DEMAND"
        elif row["recent_sales"] < 5:
            return "LOW"
        elif row["recent_sales"] < 20:
            return "NORMAL"
        else:
            return "HIGH"

    df_today["demand_level"] = df_today.apply(classify_demand, axis=1)

    # --- STEP 7: WILL_SELL LOGIC ---
    df_today["will_sell"] = (df_today["recent_sales"] > 0).astype(int)

    # Activity and Trend Logic (Adapted for new structure)
    def activity(row):
        days_since = (today - row["date"]).days
        if days_since > 30:
            return "INACTIVE"
        elif row["avg_7"] > 2:
            return "ACTIVE"
        else:
            return "LOW ACTIVITY"

    df_today["activity"] = df_today.apply(activity, axis=1)

    def trend(row):
        if row["final_quantity"] > row["avg_7"] * 1.5:
            return "INCREASING"
        elif row["final_quantity"] < row["avg_7"] * 0.5:
            return "DECREASING"
        else:
            return "STABLE"

    df_today["trend"] = df_today.apply(trend, axis=1)

    # --- 8. ADD PRODUCT NAME AND CLEAN OUTPUT ---
    df_final = df_today[
        ["productId", "productName", "will_sell", "demand_level", "activity", "trend", "recent_sales"]
    ].copy()

    # PRIORITY SCORING
    def priority_score(row):
        score = 0
        if row["will_sell"] == 1:
            score += 2
        if row["activity"] == "ACTIVE":
            score += 2
        if row["trend"] == "INCREASING":
            score += 2
        if row["demand_level"] == "NORMAL":
            score += 1
        if row["demand_level"] == "HIGH":
            score += 2
        return score

    df_final["priority_score"] = df_final.apply(priority_score, axis=1)
    
    # SORTING AND TOP PRODUCTS
    df_final = df_final.sort_values(by="priority_score", ascending=False)
    top_products = df_final.head(10)

    # SAVE OUTPUTS
    df_final.to_csv("demand_intelligence_ranked.csv", index=False)
    top_products.to_csv("top_products.csv", index=False)

    # FINAL CLEAN OUTPUT (Single Source of Truth)
    df_final.to_csv("latest_demand_intelligence.csv", index=False)

    # MAINTAIN HISTORY
    import os
    from datetime import datetime
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    df_final["run_date"] = today_str
    
    history_file = "demand_history.csv"
    if os.path.exists(history_file):
        existing = pd.read_csv(history_file)
        combined = pd.concat([existing, df_final], ignore_index=True)
    else:
        combined = df_final.copy()
        
    combined.to_csv(history_file, index=False)

    # CONSOLE OUTPUT
    print("\n--- TOP DEMAND PRODUCTS ---")
    print(top_products[[
        "productName",
        "priority_score",
        "demand_level",
        "activity",
        "trend"
    ]])

    print("\n--- BUSINESS SUMMARY ---")
    print(f"Top Products: {(df_final['priority_score'] >= 5).sum()}")
    print(f"Active Products: {(df_final['activity'] == 'ACTIVE').sum()}")
    print(f"No Demand Products: {(df_final['demand_level'] == 'NO DEMAND').sum()}")
    print("----------------------")

    print("\n--- COCONUT VALIDATION ---")
    target_product = "Coconut (thengai)"
    validation_df = df_sales[df_sales["productName"] == target_product]
    if not validation_df.empty:
        total_qty = validation_df["final_quantity"].sum()
        print(f"Total packets sold for {target_product}: {total_qty}")
    else:
        print("Product not found.")
    print("------------------------------")
    
    logger.info("Pipeline Execution Completed Successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Pipeline failed: {e}")
