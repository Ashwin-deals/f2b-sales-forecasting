import streamlit as st
import pandas as pd
import os

st.title("Demand Forecast Dashboard")

if not os.path.exists("latest_predictions.csv"):
    st.warning("No predictions available yet.")
else:
    df = pd.read_csv("latest_predictions.csv")
    
    st.dataframe(df.sort_values(by="predicted_sales", ascending=False))
    
    st.bar_chart(df.set_index("productId")["predicted_sales"])
