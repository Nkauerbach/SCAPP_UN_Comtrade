-- RAIV Analysis SQL Queries
-- Working with the RAIV_Results table created by the Python calculation model

-- Create a comprehensive view for RAIV analysis
CREATE VIEW IF NOT EXISTS RAIV_Analysis_View AS
SELECT 
    Country,
    Year,
    ImportValue as Import_Value,
    TimelinessScore as LPI_Timeliness_Score,
    RiskPremium as Risk_Premium,
    t_value as t_power,
    RAIV,
    -- Calculate rank within each year
    ROW_NUMBER() OVER (PARTITION BY Year ORDER BY RAIV DESC) as Rank_by_Year,
    -- Calculate percentile within each year
    PERCENT_RANK() OVER (PARTITION BY Year ORDER BY RAIV) as Percentile_by_Year
FROM RAIV_Results
ORDER BY Year, RAIV DESC;

-- Top 10 RAIV values by year
SELECT 
    'Top 10 RAIV Values' as Analysis_Type,
    Year,
    Country,
    ROUND(RAIV, 2) as RAIV_Rounded,
    ROUND(Import_Value, 2) as Import_Value_Rounded,
    LPI_Timeliness_Score,
    Risk_Premium,
    t_power,
    Rank_by_Year
FROM RAIV_Analysis_View
WHERE Rank_by_Year <= 10
ORDER BY Year, Rank_by_Year;

-- Summary statistics by year
SELECT 
    'Summary Statistics by Year' as Analysis_Type,
    Year,
    COUNT(*) as Country_Count,
    ROUND(AVG(RAIV), 2) as Avg_RAIV,
    ROUND(MIN(RAIV), 2) as Min_RAIV,
    ROUND(MAX(RAIV), 2) as Max_RAIV,
    ROUND(AVG(Import_Value), 2) as Avg_Import_Value,
    ROUND(AVG(LPI_Timeliness_Score), 2) as Avg_Timeliness,
    ROUND(AVG(Risk_Premium), 4) as Avg_Risk_Premium,
    -- Calculate standard deviation
    ROUND(
        SQRT(AVG((RAIV - (SELECT AVG(RAIV) FROM RAIV_Results r2 WHERE r2.Year = RAIV_Results.Year)) * 
                 (RAIV - (SELECT AVG(RAIV) FROM RAIV_Results r2 WHERE r2.Year = RAIV_Results.Year)))), 2
    ) as Std_Dev_RAIV
FROM RAIV_Results
GROUP BY Year
ORDER BY Year;

-- Countries with highest RAIV growth/decline from 2022 to 2024
WITH raiv_comparison AS (
    SELECT 
        r2022.Country,
        r2022.RAIV as RAIV_2022,
        r2024.RAIV as RAIV_2024,
        (r2024.RAIV - r2022.RAIV) as RAIV_Change,
        CASE 
            WHEN r2022.RAIV > 0 THEN 
                ROUND(((r2024.RAIV - r2022.RAIV) / r2022.RAIV) * 100, 2)
            ELSE NULL 
        END as RAIV_Change_Percent
    FROM (SELECT Country, RAIV FROM RAIV_Results WHERE Year = 2022) r2022
    INNER JOIN (SELECT Country, RAIV FROM RAIV_Results WHERE Year = 2024) r2024
        ON r2022.Country = r2024.Country
)
SELECT 
    'RAIV Change Analysis 2022-2024' as Analysis_Type,
    Country,
    ROUND(RAIV_2022, 2) as RAIV_2022,
    ROUND(RAIV_2024, 2) as RAIV_2024,
    ROUND(RAIV_Change, 2) as RAIV_Change,
    RAIV_Change_Percent as RAIV_Change_Percent
FROM raiv_comparison
WHERE RAIV_2022 IS NOT NULL AND RAIV_2024 IS NOT NULL
ORDER BY RAIV_Change DESC
LIMIT 20;

-- Risk Premium Analysis - Countries grouped by risk level
SELECT 
    'Risk Premium Analysis' as Analysis_Type,
    CASE 
        WHEN Risk_Premium <= 0.05 THEN 'Low Risk (≤5%)'
        WHEN Risk_Premium <= 0.07 THEN 'Medium Risk (5-7%)'
        ELSE 'High Risk (>7%)'
    END as Risk_Category,
    Year,
    COUNT(*) as Country_Count,
    ROUND(AVG(RAIV), 2) as Avg_RAIV,
    ROUND(AVG(Import_Value), 2) as Avg_Import_Value,
    ROUND(AVG(LPI_Timeliness_Score), 2) as Avg_Timeliness
FROM RAIV_Results
GROUP BY 
    CASE 
        WHEN Risk_Premium <= 0.05 THEN 'Low Risk (≤5%)'
        WHEN Risk_Premium <= 0.07 THEN 'Medium Risk (5-7%)'
        ELSE 'High Risk (>7%)'
    END,
    Year
ORDER BY Year, Risk_Category;

-- Timeliness Score Impact Analysis
SELECT 
    'Timeliness Score Impact' as Analysis_Type,
    CASE 
        WHEN TimelinessScore <= 2.5 THEN 'Low Timeliness (≤2.5)'
        WHEN TimelinessScore <= 3.5 THEN 'Medium Timeliness (2.5-3.5)'
        ELSE 'High Timeliness (>3.5)'
    END as Timeliness_Category,
    Year,
    COUNT(*) as Country_Count,
    ROUND(AVG(RAIV), 2) as Avg_RAIV,
    ROUND(AVG(Import_Value), 2) as Avg_Import_Value,
    ROUND(AVG(TimelinessScore), 2) as Avg_Timeliness_Score
FROM RAIV_Results
GROUP BY 
    CASE 
        WHEN TimelinessScore <= 2.5 THEN 'Low Timeliness (≤2.5)'
        WHEN TimelinessScore <= 3.5 THEN 'Medium Timeliness (2.5-3.5)'
        ELSE 'High Timeliness (>3.5)'
    END,
    Year
ORDER BY Year, Timeliness_Category;

-- Countries present in all three years (complete data)
SELECT 
    'Countries with Complete Data (2022-2024)' as Analysis_Type,
    Country,
    COUNT(*) as Years_Present,
    ROUND(AVG(RAIV), 2) as Avg_RAIV_All_Years,
    ROUND(MIN(RAIV), 2) as Min_RAIV,
    ROUND(MAX(RAIV), 2) as Max_RAIV,
    ROUND(MAX(RAIV) - MIN(RAIV), 2) as RAIV_Range
FROM RAIV_Results
GROUP BY Country
HAVING COUNT(*) = 3
ORDER BY Avg_RAIV_All_Years DESC
LIMIT 20;