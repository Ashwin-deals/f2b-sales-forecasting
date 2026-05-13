"""
Data Loader for Vendor Analysis.

Calls the MongoDB aggregation pipelines from queries.py and returns
clean pandas DataFrames ready for Streamlit visualizations.
"""

import logging
import pandas as pd
from bson import ObjectId
from db.mongo_connection import get_database
from vendor_analysis.queries import (
    get_vendor_purchase_summary,
    get_profit_analysis,
    get_monthly_vendor_trends,
    get_vendor_product_breakdown,
    get_top_vendors_by_revenue,
    get_top_vendors_by_profit,
)

logger = logging.getLogger(__name__)


def _oid_to_str(val):
    """Convert ObjectId to string safely."""
    if isinstance(val, ObjectId):
        return str(val)
    return val


def _clean_df(records: list, default_numeric_cols: list = None) -> pd.DataFrame:
    """
    Convert a list of dicts to a DataFrame.
    - Converts ObjectId fields to strings.
    - Fills NaN numeric columns with 0.
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Convert any ObjectId columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: _oid_to_str(x) if isinstance(x, ObjectId) else x)

    # Fill numeric NaN with 0
    if default_numeric_cols:
        for col in default_numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# ── Public Loader Functions ───────────────────────────────────────────────────

def load_vendor_purchase_summary() -> pd.DataFrame:
    """
    Returns vendor-wise purchase totals.
    Columns: vendorId, vendorName, companyName, location, contactNumber,
             totalQuantity, totalPurchaseAmt, totalGST,
             uniqueProductCount, transactionCount
    """
    db = get_database()
    records = get_vendor_purchase_summary(db)
    numeric_cols = ["totalQuantity", "totalPurchaseAmt", "totalGST",
                    "uniqueProductCount", "transactionCount"]
    df = _clean_df(records, numeric_cols)
    logger.info(f"load_vendor_purchase_summary: {len(df)} rows")
    return df


def load_profit_analysis() -> pd.DataFrame:
    """
    Returns vendor-wise profit data.
    Columns: vendorId, vendorName, companyName, location,
             totalRevenue, totalCost, totalPurchaseAmt, totalGST,
             estimatedProfit, profitMarginPct, totalQuantity, transactionCount
    """
    db = get_database()
    records = get_profit_analysis(db)
    numeric_cols = ["totalRevenue", "totalCost", "totalPurchaseAmt", "totalGST",
                    "estimatedProfit", "profitMarginPct", "totalQuantity", "transactionCount"]
    df = _clean_df(records, numeric_cols)
    logger.info(f"load_profit_analysis: {len(df)} rows")
    return df


def load_monthly_trends() -> pd.DataFrame:
    """
    Returns month-level vendor purchase data for time-series charts.
    Columns: vendorId, vendorName, year, month, monthStr,
             totalQuantity, totalPurchaseAmt, totalGST, transactionCount
    """
    db = get_database()
    records = get_monthly_vendor_trends(db)
    numeric_cols = ["year", "month", "totalQuantity", "totalPurchaseAmt",
                    "totalGST", "transactionCount"]
    df = _clean_df(records, numeric_cols)
    if not df.empty and "monthStr" in df.columns:
        df["monthStr"] = df["monthStr"].astype(str)
    logger.info(f"load_monthly_trends: {len(df)} rows")
    return df


def load_vendor_product_breakdown(vendor_id: str) -> pd.DataFrame:
    """
    Returns product-level breakdown for a single vendor.
    Columns: productId, productName, totalQuantity, totalPurchaseAmt,
             totalGST, totalRevenue, estimatedProfit,
             avgSellingPrice, transactionCount
    """
    db = get_database()
    records = get_vendor_product_breakdown(db, vendor_id)
    numeric_cols = ["totalQuantity", "totalPurchaseAmt", "totalGST",
                    "totalRevenue", "estimatedProfit", "avgSellingPrice", "transactionCount"]
    df = _clean_df(records, numeric_cols)
    logger.info(f"load_vendor_product_breakdown({vendor_id}): {len(df)} rows")
    return df


def load_top_vendors_by_revenue(limit: int = 10) -> pd.DataFrame:
    db = get_database()
    records = get_top_vendors_by_revenue(db, limit)
    return _clean_df(records, ["totalRevenue", "estimatedProfit", "profitMarginPct"])


def load_top_vendors_by_profit(limit: int = 10) -> pd.DataFrame:
    db = get_database()
    records = get_top_vendors_by_profit(db, limit)
    return _clean_df(records, ["totalRevenue", "estimatedProfit", "profitMarginPct"])
