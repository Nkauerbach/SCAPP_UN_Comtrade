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
st.title("Top Import Recommendations Tool")
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
    
    # Year Filter
    st.header("📅 Filter by Year")
    available_years = sorted(raiv_df['Year'].unique())
    selected_year = st.selectbox("Select Year", available_years, index=len(available_years)-1)

# Normalize weights
total = raiv_weight + timeliness_weight + risk_weight
if total == 0:
    st.error("Total weight must be greater than 0")
    st.stop()
raiv_weight /= total
timeliness_weight /= total
risk_weight /= total

# Filter data by selected year
filtered_df = raiv_df[raiv_df['Year'] == selected_year].copy()

# Composite Score Calculation (only for filtered data)
filtered_df["CompositeScore"] = (
    raiv_weight * filtered_df["RAIV"] +
    timeliness_weight * filtered_df["TimelinessScore"] +
    risk_weight * (1 - filtered_df["RiskScore"])
)

# Top N Recommendations
st.subheader(f" Top Country Recommendations for {selected_year}")
top_n = st.slider("How many results to show?", 5, 25, 10)
top_df = filtered_df.sort_values(by="CompositeScore", ascending=False).head(top_n)
st.dataframe(top_df.reset_index(drop=True), use_container_width=True)

# Show summary statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Countries Analyzed", len(filtered_df))
with col2:
    st.metric("Average RAIV", f"${filtered_df['RAIV'].mean():,.0f}")
with col3:
    st.metric("Average Composite Score", f"{filtered_df['CompositeScore'].mean():.3f}")

# Download Option
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(top_df)
st.download_button("Download Results as CSV", csv, f"top_recommendations_{selected_year}.csv", "text/csv")

# Footer
st.markdown("""

---
Made with ❤️ by Nathan | [GitHub](https://github.com/yourusername)
""")
