import pandas as pd
import logging

logger = logging.getLogger(__name__)

def parse_and_clean_data(orderdetails_data, retailorders_data):
    """
    Converts raw dict lists to DataFrames, homogenizes columns.
    Converts createdAt -> date, quantity -> sales.
    """
    df_online = pd.DataFrame(orderdetails_data)
    df_offline = pd.DataFrame(retailorders_data)
    
    # Normalize offline createdAt to date before concat
    if not df_offline.empty and "createdAt" in df_offline.columns:
        df_offline["date"] = df_offline["createdAt"]
        df_offline = df_offline.drop(columns=["createdAt"])

    if not df_online.empty and "createdAt" in df_online.columns:
        df_online["date"] = df_online["createdAt"]
        df_online = df_online.drop(columns=["createdAt"])

    # Combine datasets
    df = pd.concat([df_online, df_offline], ignore_index=True)
    
    if df.empty:
        logger.warning("No data found in both collections.")
        return df

    # Normalize columns
    if "date" in df.columns:
        # Convert to datetime and strip time to just keep date
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    
    if "quantity" in df.columns:
        df = df.rename(columns={"quantity": "sales"})
        # Ensure numeric type
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)
        
    return df
