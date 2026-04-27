import pandas as pd
import logging

logger = logging.getLogger(__name__)

def aggregate_daily_sales(df):
    """
    Groups data by productId and date, computing total sales per product per day.
    Filters for recent data (>= 2025-01-01) and selects top 50 active products.
    """
    if df.empty:
        return df
        
    # Aggregate data: total sales per product per day
    df_agg = df.groupby(["productId", "date"], as_index=False)["sales"].sum()
    
    # Restrict to recent data
    df_agg["date"] = pd.to_datetime(df_agg["date"])
    df_agg = df_agg[df_agg["date"] >= "2025-01-01"]
    
    # Select top 50 active products
    top_products = df_agg.groupby("productId")["sales"].sum().nlargest(50).index
    df_agg = df_agg[df_agg["productId"].isin(top_products)]
    
    logger.info(f"Filtered to {len(top_products)} active products since 2025.")
    
    # Sort to ensure chronological order per product
    df_agg = df_agg.sort_values(["productId", "date"]).reset_index(drop=True)
    
    return df_agg
