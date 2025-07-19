-- RAIV Calculation SQL Query
-- Formula: RAIV = Import Value × LPI Timeliness Score / (1 + Risk Premium)^t
-- Where t = 0 for 2022, t = 1 for 2023, t = 2 for 2024

-- Create a comprehensive view with RAIV calculations for all years
CREATE VIEW IF NOT EXISTS RAIV_Analysis AS
WITH raiv_2022 AS (
    SELECT 
        i.Country,
        i.Country_Code,
        2022 as Year,
        i.Import_Value_USD as Import_Value,
        l.Timeliness as LPI_Timeliness_Score,
        r.Risk_Premium,
        0 as t_power,
        (i.Import_Value_USD * l.Timeliness) / POWER((1 + r.Risk_Premium), 0) as RAIV
    FROM Cleaned_Imports_2022 i
    INNER JOIN LPI_2023_only l ON i.Country = l.Country
    INNER JOIN Risk_Premium_Lookup r ON i.Country = r.Country
    WHERE i.Import_Value_USD IS NOT NULL 
      AND l.Timeliness IS NOT NULL 
      AND r.Risk_Premium IS NOT NULL
),
raiv_2023 AS (
    SELECT 
        i.Country,
        i.Country_Code,
        2023 as Year,
        i.Import_Value_USD as Import_Value,
        l.Timeliness as LPI_Timeliness_Score,
        r.Risk_Premium,
        1 as t_power,
        (i.Import_Value_USD * l.Timeliness) / POWER((1 + r.Risk_Premium), 1) as RAIV
    FROM Cleaned_Imports_2023 i
    INNER JOIN LPI_2023_only l ON i.Country = l.Country
    INNER JOIN Risk_Premium_Lookup r ON i.Country = r.Country
    WHERE i.Import_Value_USD IS NOT NULL 
      AND l.Timeliness IS NOT NULL 
      AND r.Risk_Premium IS NOT NULL
),
raiv_2024 AS (
    SELECT 
        i.Country,
        i.Country_Code,
        2024 as Year,
        i.Import_Value_USD as Import_Value,
        l.Timeliness as LPI_Timeliness_Score,
        r.Risk_Premium,
        2 as t_power,
        (i.Import_Value_USD * l.Timeliness) / POWER((1 + r.Risk_Premium), 2) as RAIV
    FROM Cleaned_Imports_2024 i
    INNER JOIN LPI_2023_only l ON i.Country = l.Country
    INNER JOIN Risk_Premium_Lookup r ON i.Country = r.Country
    WHERE i.Import_Value_USD IS NOT NULL 
      AND l.Timeliness IS NOT NULL 
      AND r.Risk_Premium IS NOT NULL
)
SELECT * FROM raiv_2022
UNION ALL
SELECT * FROM raiv_2023
UNION ALL
SELECT * FROM raiv_2024
ORDER BY Year, RAIV DESC;

-- Query to get top 10 RAIV values by year
SELECT 
    'Top 10 RAIV Values by Year' as Analysis_Type,
    Year,
    Country,
    Country_Code,
    ROUND(RAIV, 2) as RAIV_Rounded,
    ROUND(Import_Value, 2) as Import_Value_Rounded,
    LPI_Timeliness_Score,
    Risk_Premium,
    t_power
FROM RAIV_Analysis
WHERE RAIV IN (
    SELECT RAIV FROM RAIV_Analysis ra2 
    WHERE ra2.Year = RAIV_Analysis.Year 
    ORDER BY RAIV DESC 
    LIMIT 10
)
ORDER BY Year, RAIV DESC;

-- Summary statistics by year
SELECT 
    'Summary Statistics' as Analysis_Type,
    Year,
    COUNT(*) as Country_Count,
    ROUND(AVG(RAIV), 2) as Avg_RAIV,
    ROUND(MIN(RAIV), 2) as Min_RAIV,
    ROUND(MAX(RAIV), 2) as Max_RAIV,
    ROUND(AVG(Import_Value), 2) as Avg_Import_Value,
    ROUND(AVG(LPI_Timeliness_Score), 2) as Avg_Timeliness,
    ROUND(AVG(Risk_Premium), 4) as Avg_Risk_Premium
FROM RAIV_Analysis
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
    FROM (SELECT Country, RAIV FROM RAIV_Analysis WHERE Year = 2022) r2022
    INNER JOIN (SELECT Country, RAIV FROM RAIV_Analysis WHERE Year = 2024) r2024
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