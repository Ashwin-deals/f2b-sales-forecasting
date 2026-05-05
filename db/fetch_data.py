from db.mongo_connection import get_database
import logging

logger = logging.getLogger(__name__)

def fetch_order_data():
    """
    Fetches raw order data from the 'orderdetails' and 'retailorders' collections.
    Strictly performs read-only operations.
    Extracts only specific required fields to minimize memory usage.
    """
    db = get_database()
    
    projection = {
        "_id": 0,
        "productId": 1,
        "quantity": 1,
        "subUnits": 1,
        "unit": "$unitValue",
        "createdAt": 1
    }
    
    pipeline = [
        {
            "$lookup": {
                "from": "orders",
                "localField": "orderId",
                "foreignField": "_id",
                "as": "order_info"
            }
        },
        {"$unwind": "$order_info"},
        {
            "$project": {
                "_id": 0,
                "productId": "$farmProductId",
                "quantity": 1,
                "subUnits": 1,
                "unit": "$unitValue",
                "date": "$order_info.createdOn"
            }
        }
    ]
    
    logger.info("Fetching data from 'orderdetails' collection (with orders join)...")
    orderdetails_cursor = db.orderdetails.aggregate(pipeline)
    orderdetails_data = list(orderdetails_cursor)
    logger.info(f"Fetched {len(orderdetails_data)} records from online orders.")
    
    logger.info("Fetching data from 'retailorders' collection...")
    retailorders_cursor = db.retailorders.find({}, projection)
    retailorders_data = list(retailorders_cursor)
    logger.info(f"Fetched {len(retailorders_data)} records from offline orders.")
    
    return orderdetails_data, retailorders_data

def fetch_products():
    """
    Fetches product details from the 'farmproducts' collection.
    """
    db = get_database()
    logger.info("Fetching data from 'farmproducts' collection...")
    products_cursor = db["farmproducts"].find(
        {"isDeleted": False},
        {"_id": 1, "productName": 1}
    )
    return list(products_cursor)
