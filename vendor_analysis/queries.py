"""
MongoDB Aggregation Pipelines for Vendor-Based Sales Analysis.

Schema confirmed from live database inspection:
  - Collection: warehousepurchases  (NOTE: plural)
  - productDetails is an ARRAY of sub-documents (must $unwind before grouping)
  - GST is stored as gstValue (percentage) per productDetails item
  - castingscreens linked via productId (no direct vendorId)
"""

import logging
from pymongo.database import Database
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Confirmed Collection Names ────────────────────────────────────────────────
COL_WAREHOUSE_PURCHASES = "warehousepurchases"
COL_VENDORS             = "vendors"
COL_CASTINGSCREENS      = "castingscreens"

# ── warehousepurchases top-level fields ───────────────────────────────────────
WP_VENDOR_ID      = "vendorId"
WP_PURCHASE_AMT   = "totalPurchaseCost"    # total for the whole purchase doc
WP_PURCHASE_DATE  = "purchaseDate"         # stored as string "YYYY-MM-DD"
WP_STATUS         = "status"               # e.g. "Completed"
WP_PAYMENT_STATUS = "paymentStatus"

# ── productDetails array sub-document fields ──────────────────────────────────
PD_PRODUCT_ID     = "productDetails.productId"
PD_PRODUCT_NAME   = "productDetails.productName"
PD_QUANTITY       = "productDetails.totalquantity"      # qty received
PD_PRICE_PER_UNIT = "productDetails.pricePerUnitWithTax"
PD_PURCHASE_COST  = "productDetails.purchaseCost"       # line-level cost
PD_GST_VALUE      = "productDetails.gstValue"           # GST % (e.g. 5)
PD_UNIT           = "productDetails.unitValue"

# ── vendors fields ────────────────────────────────────────────────────────────
V_NAME            = "vendorName"
V_CONTACT         = "mobile"
V_LOCATION        = "address"
V_COMPANY         = "vendorName"           # no separate company field

# ── castingscreens fields ─────────────────────────────────────────────────────
CS_PRODUCT_ID     = "productId"
CS_SELLING_PRICE  = "sellingPricePerUnit"
CS_NUM_PACKS      = "numberOfPacks"
CS_PROFIT_PCT     = "profitPercentage"
CS_PROFIT_VAL     = "profitValue"
CS_SELLING_COST   = "sellingCost"          # total selling value
CS_COST_PER_UNIT  = "costPerUnit"
CS_PACK_SIZE      = "packSize"
CS_CREATED_ON     = "createdOn"


# ── Pipeline Helpers ──────────────────────────────────────────────────────────

def _get_fy_start_date():
    """Returns April 1st of the current financial year as YYYY-MM-DD string."""
    now = datetime.now()
    year = now.year if now.month >= 4 else now.year - 1
    return f"{year}-04-01"

def _vendor_lookup_on_id():
    """$lookup vendors after a $group where _id = vendorId."""
    return {
        "$lookup": {
            "from": COL_VENDORS,
            "localField": "_id",
            "foreignField": "_id",
            "as": "vendorInfo"
        }
    }

def _vendor_name_project():
    """Project fields to extract vendor name/contact/location safely."""
    return {
        "vendorName":    {"$ifNull": [f"$vendorInfo.{V_NAME}",    "Unknown Vendor"]},
        "contactNumber": {"$ifNull": [f"$vendorInfo.{V_CONTACT}", "N/A"]},
        "location":      {"$ifNull": [f"$vendorInfo.{V_LOCATION}","N/A"]},
    }


# ── Pipeline 1: Vendor Purchase Summary ──────────────────────────────────────

def get_vendor_purchase_summary(db: Database):
    """
    Vendor-wise totals: quantity, purchase cost, estimated GST, product count.
    productDetails is an array → $unwind before grouping.

    GST is computed as: purchaseCost * (gstValue/100) per line item.
    """
    pipeline = [
        # Only completed purchases with a valid cost
        {"$match": {
            WP_PURCHASE_AMT: {"$gt": 0},
            "isDeleted": {"$ne": True},
            WP_PURCHASE_DATE: {"$gte": _get_fy_start_date()}
        }},

        # Flatten productDetails array
        {"$unwind": {"path": "$productDetails", "preserveNullAndEmptyArrays": False}},

        # Remove deleted product lines
        {"$match": {"productDetails.isDeleted": {"$ne": True}}},

        # Compute GST amount per line: purchaseCost × (gstValue% / 100)
        {"$addFields": {
            "lineGST": {
                "$multiply": [
                    {"$ifNull": ["$productDetails.purchaseCost", 0]},
                    {"$divide": [{"$ifNull": ["$productDetails.gstValue", 0]}, 100]}
                ]
            },
            "lineCostWithoutGST": {
                "$divide": [
                    {"$ifNull": ["$productDetails.purchaseCost", 0]},
                    {"$add": [1, {"$divide": [{"$ifNull": ["$productDetails.gstValue", 0]}, 100]}]}
                ]
            }
        }},

        # Group by vendor
        {"$group": {
            "_id":              f"${WP_VENDOR_ID}",
            "totalQuantity":    {"$sum": {"$ifNull": ["$productDetails.totalquantity", 0]}},
            "totalPurchaseAmt": {"$sum": {"$ifNull": ["$productDetails.purchaseCost", 0]}},
            "totalGST":         {"$sum": "$lineGST"},
            "transactionCount": {"$sum": 1},
            "uniqueProducts":   {"$addToSet": "$productDetails.productId"},
            "firstDate":        {"$min": f"${WP_PURCHASE_DATE}"},
            "lastDate":         {"$max": f"${WP_PURCHASE_DATE}"},
        }},

        {"$addFields": {
            "uniqueProductCount": {"$size": "$uniqueProducts"}
        }},

        # Join vendor info
        _vendor_lookup_on_id(),
        {"$unwind": {"path": "$vendorInfo", "preserveNullAndEmptyArrays": True}},

        {"$project": {
            "_id": 0,
            "vendorId":          {"$toString": "$_id"},
            "vendorName":        {"$ifNull": [f"$vendorInfo.{V_NAME}",    "Unknown Vendor"]},
            "contactNumber":     {"$ifNull": [f"$vendorInfo.{V_CONTACT}", "N/A"]},
            "location":          {"$ifNull": [f"$vendorInfo.{V_LOCATION}","N/A"]},
            "totalQuantity":     1,
            "totalPurchaseAmt":  1,
            "totalGST":          1,
            "uniqueProductCount":1,
            "transactionCount":  1,
            "firstDate":         1,
            "lastDate":          1,
        }},
        {"$sort": {"totalPurchaseAmt": -1}}
    ]

    try:
        logger.info("Running vendor purchase summary pipeline...")
        result = list(db[COL_WAREHOUSE_PURCHASES].aggregate(pipeline, allowDiskUse=True))
        logger.info(f"Vendor purchase summary: {len(result)} vendors found.")
        return result
    except Exception as e:
        logger.error(f"Error in get_vendor_purchase_summary: {e}")
        return []


# ── Pipeline 2: Profit Analysis ───────────────────────────────────────────────

def get_profit_analysis(db: Database):
    """
    Joins warehousepurchases (unwound productDetails) → castingscreens
    via productId to compute revenue, cost, and profit per vendor.

    Revenue = sellingPricePerUnit × numberOfPacks (from castingscreens)
    Cost    = purchaseCost per product line (includes GST)
    Profit  = Revenue − Cost
    """
    pipeline = [
        {"$match": {
            WP_PURCHASE_AMT: {"$gt": 0},
            "isDeleted": {"$ne": True},
            WP_PURCHASE_DATE: {"$gte": _get_fy_start_date()}
        }},

        # Flatten productDetails array
        {"$unwind": {"path": "$productDetails", "preserveNullAndEmptyArrays": False}},
        {"$match": {"productDetails.isDeleted": {"$ne": True}}},

        # Join castingscreens on productId
        {"$lookup": {
            "from": COL_CASTINGSCREENS,
            "localField": "productDetails.productId",
            "foreignField": CS_PRODUCT_ID,
            "as": "casting"
        }},
        # Take the most recent castingscreen entry for this product
        {"$unwind": {"path": "$casting", "preserveNullAndEmptyArrays": True}},

        # Compute line-level financials
        {"$addFields": {
            "lineSellingPrice": {"$ifNull": [f"$casting.{CS_SELLING_PRICE}", 0]},
            "lineNumPacks":     {"$ifNull": [f"$casting.{CS_NUM_PACKS}",     0]},
            "linePurchaseCost": {"$ifNull": ["$productDetails.purchaseCost", 0]},
            "lineGST": {
                "$multiply": [
                    {"$ifNull": ["$productDetails.purchaseCost", 0]},
                    {"$divide": [{"$ifNull": ["$productDetails.gstValue", 0]}, 100]}
                ]
            }
        }},
        {"$addFields": {
            "lineRevenue": {"$multiply": ["$lineSellingPrice", "$lineNumPacks"]},
            "lineProfit":  {
                "$subtract": [
                    {"$multiply": ["$lineSellingPrice", "$lineNumPacks"]},
                    "$linePurchaseCost"
                ]
            }
        }},

        # Group by vendor
        {"$group": {
            "_id":              f"${WP_VENDOR_ID}",
            "totalRevenue":     {"$sum": "$lineRevenue"},
            "totalPurchaseAmt": {"$sum": "$linePurchaseCost"},
            "totalGST":         {"$sum": "$lineGST"},
            "estimatedProfit":  {"$sum": "$lineProfit"},
            "totalQuantity":    {"$sum": {"$ifNull": ["$productDetails.totalquantity", 0]}},
            "transactionCount": {"$sum": 1},
        }},

        # Profit margin %
        {"$addFields": {
            "totalCost": {"$add": ["$totalPurchaseAmt", "$totalGST"]},
            "profitMarginPct": {
                "$cond": [
                    {"$eq": ["$totalRevenue", 0]},
                    0,
                    {"$multiply": [
                        {"$divide": ["$estimatedProfit", "$totalRevenue"]},
                        100
                    ]}
                ]
            }
        }},

        # Join vendor name
        _vendor_lookup_on_id(),
        {"$unwind": {"path": "$vendorInfo", "preserveNullAndEmptyArrays": True}},

        {"$project": {
            "_id": 0,
            "vendorId":         {"$toString": "$_id"},
            "vendorName":       {"$ifNull": [f"$vendorInfo.{V_NAME}",    "Unknown Vendor"]},
            "contactNumber":    {"$ifNull": [f"$vendorInfo.{V_CONTACT}", "N/A"]},
            "location":         {"$ifNull": [f"$vendorInfo.{V_LOCATION}","N/A"]},
            "totalRevenue":     1,
            "totalPurchaseAmt": 1,
            "totalGST":         1,
            "totalCost":        1,
            "estimatedProfit":  1,
            "profitMarginPct":  1,
            "totalQuantity":    1,
            "transactionCount": 1,
        }},
        {"$sort": {"estimatedProfit": -1}}
    ]

    try:
        logger.info("Running profit analysis pipeline...")
        result = list(db[COL_WAREHOUSE_PURCHASES].aggregate(pipeline, allowDiskUse=True))
        logger.info(f"Profit analysis: {len(result)} vendors.")
        return result
    except Exception as e:
        logger.error(f"Error in get_profit_analysis: {e}")
        return []


# ── Pipeline 3: Monthly Vendor Trends ────────────────────────────────────────

def get_monthly_vendor_trends(db: Database):
    """
    Monthly time-series of purchase cost and quantity per vendor.
    purchaseDate is stored as string 'YYYY-MM-DD' → extract year/month.
    """
    pipeline = [
        {"$match": {
            WP_PURCHASE_AMT: {"$gt": 0},
            WP_PURCHASE_DATE: {"$exists": True, "$ne": None, "$gte": _get_fy_start_date()},
            "isDeleted": {"$ne": True}
        }},

        # Unwind products to get per-product monthly data
        {"$unwind": {"path": "$productDetails", "preserveNullAndEmptyArrays": False}},
        {"$match": {"productDetails.isDeleted": {"$ne": True}}},

        # Parse date string to extract year/month
        # purchaseDate is "YYYY-MM-DD" string
        {"$addFields": {
            "parsedDate": {
                "$dateFromString": {
                    "dateString": f"${WP_PURCHASE_DATE}",
                    "onError": None,
                    "onNull": None
                }
            }
        }},
        {"$match": {"parsedDate": {"$ne": None}}},
        {"$addFields": {
            "year":     {"$year":  "$parsedDate"},
            "month":    {"$month": "$parsedDate"},
            "monthStr": {"$dateToString": {"format": "%Y-%m", "date": "$parsedDate"}}
        }},

        # Group by vendor + month
        {"$group": {
            "_id": {
                "vendorId": f"${WP_VENDOR_ID}",
                "year":     "$year",
                "month":    "$month",
                "monthStr": "$monthStr"
            },
            "totalQuantity":    {"$sum": {"$ifNull": ["$productDetails.totalquantity", 0]}},
            "totalPurchaseAmt": {"$sum": {"$ifNull": ["$productDetails.purchaseCost", 0]}},
            "totalGST": {
                "$sum": {
                    "$multiply": [
                        {"$ifNull": ["$productDetails.purchaseCost", 0]},
                        {"$divide": [{"$ifNull": ["$productDetails.gstValue", 0]}, 100]}
                    ]
                }
            },
            "transactionCount": {"$sum": 1},
        }},

        # Join vendor name
        {"$lookup": {
            "from": COL_VENDORS,
            "localField": "_id.vendorId",
            "foreignField": "_id",
            "as": "vendorInfo"
        }},
        {"$unwind": {"path": "$vendorInfo", "preserveNullAndEmptyArrays": True}},

        {"$project": {
            "_id": 0,
            "vendorId":         {"$toString": "$_id.vendorId"},
            "vendorName":       {"$ifNull": [f"$vendorInfo.{V_NAME}", "Unknown Vendor"]},
            "year":             "$_id.year",
            "month":            "$_id.month",
            "monthStr":         "$_id.monthStr",
            "totalQuantity":    1,
            "totalPurchaseAmt": 1,
            "totalGST":         1,
            "transactionCount": 1,
        }},
        {"$sort": {"year": 1, "month": 1}}
    ]

    try:
        logger.info("Running monthly vendor trends pipeline...")
        result = list(db[COL_WAREHOUSE_PURCHASES].aggregate(pipeline, allowDiskUse=True))
        logger.info(f"Monthly trends: {len(result)} records.")
        return result
    except Exception as e:
        logger.error(f"Error in get_monthly_vendor_trends: {e}")
        return []


# ── Pipeline 4: Top Vendors ───────────────────────────────────────────────────

def get_top_vendors_by_revenue(db: Database, limit: int = 10):
    results = get_profit_analysis(db)
    return sorted(results, key=lambda x: x.get("totalRevenue", 0), reverse=True)[:limit]


def get_top_vendors_by_profit(db: Database, limit: int = 10):
    results = get_profit_analysis(db)
    return sorted(results, key=lambda x: x.get("estimatedProfit", 0), reverse=True)[:limit]


# ── Pipeline 5: Product Breakdown per Vendor ─────────────────────────────────

def get_vendor_product_breakdown(db: Database, vendor_id: str):
    """
    For a specific vendor: product-level detail with purchase cost,
    GST, and selling price from castingscreens.
    """
    from bson import ObjectId
    try:
        vid = ObjectId(vendor_id)
    except Exception:
        vid = vendor_id

    pipeline = [
        {"$match": {
            WP_VENDOR_ID: {"$in": [vendor_id, vid]},
            WP_PURCHASE_AMT: {"$gt": 0},
            "isDeleted": {"$ne": True},
            WP_PURCHASE_DATE: {"$gte": _get_fy_start_date()}
        }},

        # Flatten productDetails
        {"$unwind": {"path": "$productDetails", "preserveNullAndEmptyArrays": False}},
        {"$match": {"productDetails.isDeleted": {"$ne": True}}},

        # Add GST amount per line
        {"$addFields": {
            "lineGST": {
                "$multiply": [
                    {"$ifNull": ["$productDetails.purchaseCost", 0]},
                    {"$divide": [{"$ifNull": ["$productDetails.gstValue", 0]}, 100]}
                ]
            }
        }},

        # Group by product
        {"$group": {
            "_id":              "$productDetails.productId",
            "productName":      {"$first": "$productDetails.productName"},
            "unitValue":        {"$first": "$productDetails.unitValue"},
            "totalQuantity":    {"$sum": {"$ifNull": ["$productDetails.totalquantity", 0]}},
            "totalPurchaseCost":{"$sum": {"$ifNull": ["$productDetails.purchaseCost", 0]}},
            "totalGST":         {"$sum": "$lineGST"},
            "avgPricePerUnit":  {"$avg": {"$ifNull": ["$productDetails.pricePerUnitWithTax", 0]}},
            "transactionCount": {"$sum": 1},
        }},

        # Join castingscreens for selling price
        {"$lookup": {
            "from": COL_CASTINGSCREENS,
            "localField": "_id",
            "foreignField": CS_PRODUCT_ID,
            "as": "casting"
        }},
        {"$unwind": {"path": "$casting", "preserveNullAndEmptyArrays": True}},

        {"$addFields": {
            "sellingPricePerUnit": {"$ifNull": [f"$casting.{CS_SELLING_PRICE}", 0]},
            "numberOfPacks":       {"$ifNull": [f"$casting.{CS_NUM_PACKS}",     0]},
            "profitPercentage":    {"$ifNull": [f"$casting.{CS_PROFIT_PCT}",    0]},
        }},
        {"$addFields": {
            "totalRevenue":    {"$multiply": ["$sellingPricePerUnit", "$numberOfPacks"]},
            "estimatedProfit": {
                "$subtract": [
                    {"$multiply": ["$sellingPricePerUnit", "$numberOfPacks"]},
                    "$totalPurchaseCost"
                ]
            }
        }},

        {"$project": {
            "_id": 0,
            "productId":          {"$toString": "$_id"},
            "productName":        1,
            "unitValue":          1,
            "totalQuantity":      1,
            "totalPurchaseCost":  1,
            "totalGST":           1,
            "avgPricePerUnit":    1,
            "sellingPricePerUnit":1,
            "numberOfPacks":      1,
            "profitPercentage":   1,
            "totalRevenue":       1,
            "estimatedProfit":    1,
            "transactionCount":   1,
        }},
        {"$sort": {"totalPurchaseCost": -1}}
    ]

    try:
        logger.info(f"Running product breakdown for vendor: {vendor_id}")
        return list(db[COL_WAREHOUSE_PURCHASES].aggregate(pipeline, allowDiskUse=True))
    except Exception as e:
        logger.error(f"Error in get_vendor_product_breakdown: {e}")
        return []


# ── Indexing Recommendations ─────────────────────────────────────────────────

INDEX_RECOMMENDATIONS = """
Run these in MongoDB shell for best performance:

db.warehousepurchases.createIndex({ vendorId: 1 })
db.warehousepurchases.createIndex({ purchaseDate: 1 })
db.warehousepurchases.createIndex({ "productDetails.productId": 1 })
db.warehousepurchases.createIndex({ vendorId: 1, purchaseDate: 1 })
db.warehousepurchases.createIndex({ totalPurchaseCost: 1 })
db.castingscreens.createIndex({ productId: 1 })
"""
