import pandas as pd

def aggregate_daily_sales(df):
    """
    Groups data by productId and date, computing total sales per product per day.
    """
    if df.empty:
        return df
        
    # Aggregate data: total sales per product per day
    df_agg = df.groupby(["productId", "date"], as_index=False)["sales"].sum()
    
    # Sort to ensure chronological order per product
    df_agg = df_agg.sort_values(["productId", "date"]).reset_index(drop=True)
    
    return df_agg
