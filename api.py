from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import pandas as pd
import os

app = FastAPI(title="Demand Intelligence API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/predictions")
def get_predictions(
    demand_level: str = Query(None, description="Filter by demand level: NO DEMAND, NORMAL, HIGH, SURGE"),
    top: int = Query(None, description="Return top N products by demand_score")
):
    if not os.path.exists("latest_predictions.csv"):
        return JSONResponse(status_code=503, content={"error": "Predictions not ready. Run the pipeline first."})

    df = pd.read_csv("latest_predictions.csv")

    if demand_level:
        df = df[df["demand_level"] == demand_level.upper()]

    if top:
        df = df.sort_values("demand_score", ascending=False).head(top)

    return df.to_dict(orient="records")

@app.get("/summary")
def get_summary():
    if not os.path.exists("latest_predictions.csv"):
        return JSONResponse(status_code=503, content={"error": "Predictions not ready."})

    df = pd.read_csv("latest_predictions.csv")
    return {
        "active_products": len(df),
        "total_7day_demand": round(df["forecast_7_days"].sum(), 2),
        "surge_products": int((df["demand_level"] == "SURGE").sum()),
        "high_products": int((df["demand_level"] == "HIGH").sum()),
        "normal_products": int((df["demand_level"] == "NORMAL").sum()),
        "no_demand_products": int((df["demand_level"] == "NO DEMAND").sum()),
    }
