import streamlit as st
import pandas as pd
import base64

# Load your RAIV data
@st.cache_data
def load_data():
return pd.read_csv("adjusted_RM_raiv_no_china.csv")


raiv_df = load_data()

# Page Config
st.set_page_config(page_title="Top Import Recommendations", layout="centered")

# Header
st.title("🌍 Top Import Recommendations Tool")
st.markdown("""
This lightweight app helps you explore optimal import sourcing countries based on:
- **RAIV** (Risk-Adjusted Import Value)
- **Timeliness Score**
- **Risk Premium**

Use the sliders below to customize your preferences.
""")

# Sidebar Inputs
with st.sidebar:
    st.header("🔧 Adjust Weights")
    raiv_weight = st.slider("RAIV Weight", 0.0, 1.0, 0.4)
    timeliness_weight = st.slider("Timeliness Weight", 0.0, 1.0, 0.3)
    risk_weight = st.slider("Risk Premium Weight", 0.0, 1.0, 0.3)

# Normalize weights
total = raiv_weight + timeliness_weight + risk_weight
if total == 0:
    st.error("Total weight must be greater than 0")
    st.stop()
raiv_weight /= total
timeliness_weight /= total
risk_weight /= total

# Composite Score Calculation
raiv_df["CompositeScore"] = (
    raiv_weight * raiv_df["RAIV"] +
    timeliness_weight * raiv_df["TimelinessScore"] +
    risk_weight * (1 - raiv_df["RiskScore"])
)

# Top N Recommendations
st.subheader("📊 Top Country Recommendations")
top_n = st.slider("How many results to show?", 5, 25, 10)
top_df = raiv_df.sort_values(by="CompositeScore", ascending=False).head(top_n)
st.dataframe(top_df.reset_index(drop=True), use_container_width=True)

# Download Option
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(top_df)
st.download_button("📥 Download Results as CSV", csv, "top_recommendations.csv", "text/csv")

# Footer
st.markdown("""
---
Made with ❤️ by Nathan | [GitHub](https://github.com/yourusername)
""")
