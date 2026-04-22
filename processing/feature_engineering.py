import pandas as pd
import logging

logger = logging.getLogger(__name__)

def build_features(df):
    """
    Rebuilds continuous daily timelines for each product securely.
    Removes padded 'phantom zeroes' preceding a product's very first sale.
    Computes safe roll-forward features without data leakage.
    Outputs to local file `processed_data.csv`.
    """
    if df.empty:
        return df

    logger.info("Building timelines and discarding pre-launch inactive data...")
    
    # Ensure date is datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Track the very first exact sale date of each product globally
    first_sales = df[df["sales"] > 0].groupby("productId")["date"].min().reset_index()
    first_sales.rename(columns={"date": "first_sale_date"}, inplace=True)
    
    min_date = df["date"].min()
    max_date = df["date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # Full Cartesian product template
    products = df["productId"].unique()
    idx = pd.MultiIndex.from_product([products, all_dates], names=["productId", "date"])
    template = pd.DataFrame(index=idx).reset_index()
    
    # Merge template with target sales metrics
    df = pd.merge(template, df, on=["productId", "date"], how="left")
    
    # Merge back the first_sale_date metric
    df = pd.merge(df, first_sales, on="productId", how="left")
    
    # Fill any product that had absolutely NO sales in history with a max date to nullify them
    df["first_sale_date"] = df["first_sale_date"].fillna(max_date)
    
    # Filter phantom zeroes: ONLY keep records that occurred on or after their first ever sale
    df = df[df["date"] >= df["first_sale_date"]].copy()
    df.drop(columns=["first_sale_date"], inplace=True)
    
    # Fill remaining valid inner gaps with 0
    df["sales"] = df["sales"].fillna(0)
    
    logger.info("Computing features (month, is_weekend, weekday, lag_1, lag_7, avg_7)...")
    
    df = df.sort_values(["productId", "date"])
    
    # Date properties
    df["weekday"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["weekday"].apply(lambda x: 1 if x >= 5 else 0)
    
    # Lag properties
    df["lag_1"] = df.groupby("productId")["sales"].shift(1)
    df["lag_7"] = df.groupby("productId")["sales"].shift(7)
    
    # Safe Rolling average
    df["avg_7"] = df.groupby("productId")["sales"] \
                    .transform(lambda x: x.shift(1).rolling(window=7, min_periods=1).mean())
                    
    # Drop rows with NaN values created by lag shifts
    df = df.dropna().reset_index(drop=True)
    
    # Save the processed data locally 
    df.to_csv("processed_data.csv", index=False)
    logger.info("Saved strictly active features to 'processed_data.csv'.")
    
    return df
