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
This lightweight app helps you explore optimal exporting countries into the US, make analytical procurement decisions with data from the UN and WorldBank, and functionally change the weights of factors based on:
- **RAIV** (Risk-Adjusted Import Value) - Summed across years
- **Timeliness Score** - Averaged across years
- **Risk Score** - Averaged across years

Use the sliders below to customize your preferences.
""")

# Sidebar Inputs
with st.sidebar:
    st.header("Adjust Weights")
    raiv_weight = st.slider("RAIV Weight", 0.0, 1.0, 0.4)
    timeliness_weight = st.slider("Timeliness Weight", 0.0, 1.0, 0.3)
    risk_weight = st.slider("Risk Premium Weight", 0.0, 1.0, 0.3)
    
    # HS Code Filter
    st.header("️ Filter by HS Code")
    available_hs_codes = sorted(raiv_df['HS_Code'].unique())
    selected_hs_codes = st.multiselect("Select HS Codes", available_hs_codes, default=available_hs_codes)
    
    # Year Filter
    st.header("Filter by Year")
    available_years = sorted(raiv_df['Year'].unique())
    selected_years = st.multiselect("Select Years", available_years, default=available_years)

# Normalize weights
total = raiv_weight + timeliness_weight + risk_weight
if total == 0:
    st.error("Total weight must be greater than 0")
    st.stop()
raiv_weight /= total
timeliness_weight /= total
risk_weight /= total

# Filter data by selected HS codes and years
filtered_df = raiv_df[
    (raiv_df['HS_Code'].isin(selected_hs_codes)) & 
    (raiv_df['Year'].isin(selected_years))
].copy()

# Aggregate by PartnerName/Economy
# RAIV: Sum across years
# TimelinessScore: Average across years  
# RiskScore: Average across years
aggregated_df = filtered_df.groupby('PartnerName').agg({
    'RAIV': 'sum',                    # Sum RAIV across years
    'TimelinessScore': 'mean',        # Average Timeliness across years
    'RiskScore': 'mean'               # Average Risk across years
}).reset_index()

# Composite Score Calculation
aggregated_df["CompositeScore"] = (
    raiv_weight * aggregated_df["RAIV"] +
    timeliness_weight * aggregated_df["TimelinessScore"] +
    risk_weight * (1 - aggregated_df["RiskScore"])
)

# Top N Recommendations
st.subheader("Top Country Recommendations")
top_n = st.slider("How many results to show?", 5, 25, 10)
top_df = aggregated_df.sort_values(by="CompositeScore", ascending=False).head(top_n)

# Display results
st.dataframe(top_df.reset_index(drop=True), use_container_width=True)

# Show summary statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Countries Analyzed", len(top_df))
with col2:
    st.metric("Total RAIV (Sum)", f"${top_df['RAIV'].sum():,.0f}")
with col3:
    st.metric("Average Composite Score", f"{top_df['CompositeScore'].mean():.3f}")

# Additional metrics
st.subheader("Summary Statistics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Timeliness Score", f"{top_df['TimelinessScore'].mean():.2f}")
with col2:
    st.metric("Average Risk Score", f"{top_df['RiskScore'].mean():.2f}")
with col3:
    st.metric("Data Points Used", len(filtered_df))

# Download Option
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(top_df)
filename = f"top_recommendations_{len(selected_years)}years.csv"
st.download_button("Download Results as CSV", csv, filename, "text/csv")

# Footer
st.markdown("""

Explainging the Methodology: 

---
Made with ❤️ by Nathan | [GitHub](https://github.com/yourusername)
""")
