# RAIV Calculation Model - Summary Report

## Overview

This document summarizes the Risk-Adjusted Import Value (RAIV) calculation model developed for analyzing trade data across countries from 2022-2024.

## Formula

**RAIV = Import Value × LPI Timeliness Score / (1 + Risk Premium)^t**

Where:
- **Import Value**: Trade value in thousands USD for each country and year
- **LPI Timeliness Score**: Logistics Performance Index Timeliness score from 2023 data
- **Risk Premium**: Country-specific risk premium
- **t**: Time adjustment factor
  - t = 0 for 2022 data
  - t = 1 for 2023 data  
  - t = 2 for 2024 data

## Data Sources

1. **Import Data**: Cleaned import values from UN Comtrade data (2022, 2023, 2024)
2. **LPI Timeliness**: World Bank Logistics Performance Index 2023 timeliness scores
3. **Risk Premium**: Country-specific risk premium lookup table

## Key Findings

### Coverage
- **Total RAIV calculations**: 323 country-year observations
- **Countries covered**: 118 unique countries
- **Years covered**: 2022, 2023, 2024
- **Countries per year**: 
  - 2022: 106 countries
  - 2023: 109 countries
  - 2024: 108 countries

### Top Performing Countries (by RAIV)

#### 2022 Rankings
1. **China**: 21,347,196.42 (Import: 5,769,512.54, Timeliness: 3.7, Risk: 6.0%)
2. **Mexico**: 6,090,779.29 (Import: 1,740,222.65, Timeliness: 3.5, Risk: 6.0%)
3. **Canada**: 5,085,650.14 (Import: 1,240,402.47, Timeliness: 4.1, Risk: 5.0%)
4. **Thailand**: 4,239,794.33 (Import: 1,211,369.81, Timeliness: 3.5, Risk: 6.0%)
5. **Germany**: 2,386,133.86 (Import: 581,983.87, Timeliness: 4.1, Risk: 5.0%)

#### 2024 Rankings
1. **China**: 15,772,468.84 (Import: 4,789,715.13, Timeliness: 3.7, Risk: 6.0%)
2. **Mexico**: 5,986,439.44 (Import: 1,921,818.10, Timeliness: 3.5, Risk: 6.0%)
3. **Canada**: 4,693,162.86 (Import: 1,262,002.94, Timeliness: 4.1, Risk: 5.0%)
4. **Thailand**: 3,164,747.00 (Import: 1,015,974.21, Timeliness: 3.5, Risk: 6.0%)
5. **Germany**: 2,203,974.53 (Import: 592,654.13, Timeliness: 4.1, Risk: 5.0%)

### Summary Statistics by Year

| Year | Countries | Average RAIV | Min RAIV | Max RAIV | Average Import Value |
|------|-----------|--------------|----------|----------|---------------------|
| 2022 | 106 | 490,750.05 | 0.79 | 21,347,196.42 | 132,094.85 |
| 2023 | 109 | 383,991.59 | 1.16 | 15,838,691.56 | 109,142.03 |
| 2024 | 108 | 402,134.53 | 0.90 | 15,772,468.84 | 121,347.62 |

### Countries with Highest RAIV Growth (2022-2024)

1. **Dominican Republic**: +41.0% (258,859.77 → 365,038.01)
2. **Colombia**: +219.5% (41,953.44 → 134,049.76)
3. **Cambodia**: +21.3% (359,351.18 → 436,010.98)
4. **Poland**: +29.6% (248,430.67 → 321,835.73)
5. **Spain**: +20.4% (321,038.75 → 386,618.11)

## Model Implementation

### Files Created

1. **`raiv_calculation_simple.py`**: Main calculation engine using built-in Python libraries
2. **`raiv_sql_analysis.sql`**: SQL queries for database-based analysis
3. **`raiv_results.csv`**: Complete results in CSV format
4. **`raiv_summary_statistics.csv`**: Summary statistics by year
5. **Database table**: `RAIV_Results` in SQLite database

### Database Structure

The `RAIV_Results` table contains:
- `Country`: Country name
- `Year`: Year (2022, 2023, 2024)
- `ImportValue`: Import value in thousands USD
- `TimelinessScore`: LPI Timeliness score
- `RiskPremium`: Risk premium rate
- `t_value`: Time adjustment factor (0, 1, 2)
- `RAIV`: Calculated Risk-Adjusted Import Value

## Key Insights

### 1. Market Concentration
- **China dominates** with the highest RAIV values across all years
- Top 5 countries consistently include China, Mexico, Canada, Thailand, and Germany

### 2. Temporal Trends
- **Overall decline** in average RAIV from 2022 to 2023 (-21.7%)
- **Slight recovery** in 2024 (+4.7% from 2023)
- China's RAIV declined significantly from 2022 to 2023-2024

### 3. Growth Patterns
- **Colombia** shows exceptional growth (+219.5%)
- Several countries show consistent positive growth despite global challenges
- **Dominican Republic, Poland, Spain** demonstrate strong resilience

### 4. Risk-Timeliness Balance
- Countries with **low risk premiums** (≤5%) and **high timeliness scores** (>3.5) achieve higher RAIV values
- **Germany, Canada, Japan** benefit from low risk premiums (5%)
- **Thailand, Mexico** perform well despite higher risk premiums (6%) due to substantial import volumes

## Usage Instructions

### Running the Python Model
```bash
python3 raiv_calculation_simple.py
```

### Running SQL Analysis
```sql
-- Load the SQL file into your SQLite database
.read raiv_sql_analysis.sql

-- Query the results
SELECT * FROM RAIV_Analysis_View WHERE Year = 2024 ORDER BY RAIV DESC LIMIT 10;
```

### Accessing Results
- **CSV files**: `raiv_results.csv` and `raiv_summary_statistics.csv`
- **Database**: Query the `RAIV_Results` table
- **SQL Views**: Use `RAIV_Analysis_View` for enhanced analysis

## Methodology Notes

1. **Data Matching**: Countries were matched across import data, LPI scores, and risk premiums
2. **Missing Data**: Countries without complete data across all three sources were excluded
3. **Time Adjustment**: The exponential time factor accounts for increasing uncertainty over time
4. **Currency**: All values in thousands USD
5. **Aggregation**: Import values were aggregated by country and year from detailed trade records

## Recommendations for Further Analysis

1. **Sector-specific RAIV**: Calculate RAIV by product categories
2. **Quarterly Analysis**: Break down by quarters if data available
3. **Correlation Analysis**: Examine relationships between RAIV components
4. **Forecasting**: Use historical RAIV trends to project future values
5. **Benchmarking**: Compare countries within similar risk/timeliness categories

---

*Model developed using SQL database analysis with Python implementation for comprehensive RAIV calculations across 118 countries and 3 years of trade data.*