import streamlit as st
import pandas as pd

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
    raiv_weight = st.slider("RAIV Weight", 0.0, 1.0, 0.1)
    timeliness_weight = st.slider("Timeliness Weight", 0.0, 1.0, 0.45)
    risk_weight = st.slider("Risk Premium Weight", 0.0, 1.0, 0.45)
    
    # HS Code Filter
    st.header("️ Filter by HS Code")
    available_hs_codes = sorted(raiv_df['HS Code'].unique())
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
    (raiv_df['HS Code'].isin(selected_hs_codes)) & 
    (raiv_df['Year'].isin(selected_years))
].copy()

# Aggregate by PartnerName/Economy
aggregated_df = filtered_df.groupby('PartnerName').agg({
    'RAIV': 'sum',                    # Sum RAIV across years
    'TimelinessScore': 'mean',        # Average Timeliness across years
    'RiskScore': 'mean'               # Average Risk across years
}).reset_index()

# Normalization for composite score
max_raiv = aggregated_df['RAIV'].max() if not aggregated_df['RAIV'].isnull().all() else 1
max_risk = aggregated_df['RiskScore'].max() if not aggregated_df['RiskScore'].isnull().all() else 1

aggregated_df["CompositeScore"] = (
    (aggregated_df["RAIV"] / max_raiv) * raiv_weight +
    (aggregated_df["TimelinessScore"] / 5) * timeliness_weight +
    (1 - (aggregated_df["RiskScore"] / max_risk)) * risk_weight
)

# Top N Recommendations
st.subheader("Top Country Recommendations")
top_n = st.slider("How many results to show?", 5, 50, 10)
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

**Explaining the Methodology:**  
- RAIV (Raw Adjusted Import Value) is computed using the following formula: Import Value (2022-2023-2024) * LPI 2023 Score / (1 + Supply Chain Risk Premium)^"t"
WHERE 
- "t" = time component (t years since 2022)
- "p" = risk premium (basic conditonal logic based on countries LPI 2023 timeliness scores gave an explicit value of either 0.05, 0.06, 0.075- lower indicates less risk)
- "Import Value" is derived from each specific HS Code, and Year

- TimelinessScore is divided by 5 (the max possible score)
- RAIV and Risk Score are divided by the "max value" in the data set to adjust weighting disparities
- The composite score is a weighted sum of these normalized values

---
**Additional Intellegence and Future Plans**

HS CODE TOC
- 230910: Pet Food 
- 392690: Miscelaneous plastic articles for pets such as bowls, litter boxes, etc.
- 420100: Saddlery and harnesses such as collars, leashes, chokers 

---
Only 3 Pet Related Pet Codes have been utilized thus far, soon I will be implementing more to give users the oppurtunity for a more comprehensive analysis
Connecting Maritime Trade Data from UNCTAD as an additional layer (factor) of the reccomendation tool
Integration of Trade Data (RAIV modeling) into Energy System Optimization using NC State's open source software "TEMOA"
---
Made with ❤️ by Nathan | [GitHub](https://github.com/yourusername)
""")