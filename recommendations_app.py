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
    
    # HS Code Filter (always available)
    st.header("��️ Filter by HS Code")
    available_hs_codes = sorted(raiv_df['HS_Code'].unique())
    selected_hs_codes = st.multiselect("Select HS Codes", available_hs_codes, default=available_hs_codes)
    
    # Analysis Mode
    st.header("📊 Analysis Mode")
    analysis_mode = st.radio("Select Analysis Mode", 
                           ["By Year", "Aggregated (All Years)"])
    
    if analysis_mode == "By Year":
        # Year Filter
        st.header("📅 Filter by Year")
        available_years = sorted(raiv_df['Year'].unique())
        selected_year = st.selectbox("Select Year", available_years, index=len(available_years)-1)
    
    else:  # Aggregated mode
        st.header("📈 Aggregation Settings")
        st.info("This mode will aggregate all years by PartnerName")

# Normalize weights
total = raiv_weight + timeliness_weight + risk_weight
if total == 0:
    st.error("Total weight must be greater than 0")
    st.stop()
raiv_weight /= total
timeliness_weight /= total
risk_weight /= total

# First, filter by HS codes (applies to both modes)
filtered_df = raiv_df[raiv_df['HS_Code'].isin(selected_hs_codes)].copy()

# Process data based on analysis mode
if analysis_mode == "By Year":
    # Filter by year
    filtered_df = filtered_df[filtered_df['Year'] == selected_year].copy()
    
    # Aggregate by PartnerName for the selected year
    aggregated_df = filtered_df.groupby('PartnerName').agg({
        'RAIV': 'sum',
        'TimelinessScore': 'mean',
        'RiskScore': 'mean'
    }).reset_index()
    
    # Composite Score Calculation
    aggregated_df["CompositeScore"] = (
        raiv_weight * aggregated_df["RAIV"] +
        timeliness_weight * aggregated_df["TimelinessScore"] +
        risk_weight * (1 - aggregated_df["RiskScore"])
    )
    
    # Top N Recommendations
    st.subheader(f"📊 Top Country Recommendations for {selected_year}")
    top_n = st.slider("How many results to show?", 5, 25, 10)
    top_df = aggregated_df.sort_values(by="CompositeScore", ascending=False).head(top_n)
    
else:  # Aggregated mode
    # Aggregate by PartnerName across all years
    aggregated_df = filtered_df.groupby('PartnerName').agg({
        'RAIV': 'sum',
        'TimelinessScore': 'mean',
        'RiskScore': 'mean'
    }).reset_index()
    
    # Composite Score Calculation for aggregated data
    aggregated_df["CompositeScore"] = (
        raiv_weight * aggregated_df["RAIV"] +
        timeliness_weight * aggregated_df["TimelinessScore"] +
        risk_weight * (1 - aggregated_df["RiskScore"])
    )
    
    # Top N Recommendations
    st.subheader("📊 Top Country Recommendations (Aggregated)")
    top_n = st.slider("How many results to show?", 5, 25, 10)
    top_df = aggregated_df.sort_values(by="CompositeScore", ascending=False).head(top_n)

# Display results
st.dataframe(top_df.reset_index(drop=True), use_container_width=True)

# Show summary statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Countries Analyzed", len(top_df))
with col2:
    st.metric("Average RAIV", f"${top_df['RAIV'].mean():,.0f}")
with col3:
    st.metric("Average Composite Score", f"{top_df['CompositeScore'].mean():.3f}")

# Download Option
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(top_df)
if analysis_mode == "By Year":
    filename = f"top_recommendations_{selected_year}.csv"
else:
    filename = "top_recommendations_aggregated.csv"

st.download_button("Download Results as CSV", csv, filename, "text/csv")

# Footer
st.markdown("""

---
Made with ❤️ by Nathan | [GitHub](https://github.com/yourusername)
""")
