#!/usr/bin/env python3
"""
RAIV Calculation Model
======================

This script calculates the Risk-Adjusted Import Value (RAIV) for each country using the formula:
RAIV = Import Value (2022, 2023, or 2024) × LPI Timeliness Score (2023) / (1 + Risk Premium)^t

Where:
- t = 0 for 2022 data
- t = 1 for 2023 data  
- t = 2 for 2024 data
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAIVCalculator:
    """Class to handle RAIV calculations for trade data."""
    
    def __init__(self, db_path: str = 'trade_analysis.db'):
        """Initialize the calculator with database connection."""
        self.db_path = db_path
        self.conn = None
        self.connect_db()
        
    def connect_db(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def get_import_data(self, year: int) -> pd.DataFrame:
        """
        Retrieve import data for a specific year.
        
        Args:
            year: Year to retrieve data for (2022, 2023, or 2024)
            
        Returns:
            DataFrame with import data
        """
        table_name = f"Cleaned_Imports_{year}"
        query = f"""
        SELECT 
            PartnerName as Country,
            SUM(TradeValuein1000USD) as ImportValue
        FROM {table_name}
        WHERE PartnerName != 'World'
        GROUP BY PartnerName
        """
        
        try:
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"Retrieved {len(df)} countries from {table_name}")
            return df
        except Exception as e:
            logger.error(f"Error retrieving import data for {year}: {e}")
            return pd.DataFrame()
            
    def get_lpi_data(self) -> pd.DataFrame:
        """
        Retrieve LPI 2023 data with Timeliness scores.
        
        Returns:
            DataFrame with LPI data
        """
        query = """
        SELECT 
            Economy as Country,
            TimelinessScore
        FROM LPI_2023_only
        WHERE TimelinessScore IS NOT NULL
        """
        
        try:
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"Retrieved LPI data for {len(df)} countries")
            return df
        except Exception as e:
            logger.error(f"Error retrieving LPI data: {e}")
            return pd.DataFrame()
            
    def get_risk_premium_data(self) -> pd.DataFrame:
        """
        Retrieve Risk Premium data.
        
        Returns:
            DataFrame with risk premium data
        """
        query = """
        SELECT 
            Economy as Country,
            RiskPremium
        FROM Risk_Premium_Lookup
        WHERE RiskPremium IS NOT NULL
        """
        
        try:
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"Retrieved risk premium data for {len(df)} countries")
            return df
        except Exception as e:
            logger.error(f"Error retrieving risk premium data: {e}")
            return pd.DataFrame()
            
    def normalize_country_names(self, df: pd.DataFrame, country_col: str = 'Country') -> pd.DataFrame:
        """
        Normalize country names for better matching across datasets.
        
        Args:
            df: DataFrame with country names
            country_col: Name of the country column
            
        Returns:
            DataFrame with normalized country names
        """
        # Create a copy to avoid modifying original
        df_norm = df.copy()
        
        # Common country name mappings based on the SQL script
        name_mappings = {
            'France+Monac': 'France',
            'Switz.Leicht': 'Switzerland', 
            'Korea Rep.': 'South Korea',
            'Norway,Sb,JM': 'Norway',
            'Ireland': 'Republic of Ireland',
            'Luxemberg': 'Luxembourg',
            'Czech Rep': 'Czech Republic',
            'Viet Nam': 'Vietnam',
            'TFYR Macedna': 'North Macedonia',
            'Bosnia Herzg': 'Bosnia and Herzegovina',
            'Antigua,Barb': 'Antigua and Barbuda',
            'Solomon Is': 'Solomon Islands',
            'Bahamas': 'Bahamas, The',
            'Papua N.Guin': 'Papua New Guinea',
            'Dem.Rp.Congo': 'Democratic Republic of the Congo',
            'Dominican Rp': 'Dominican Republic',
            'GuineaBissau': 'Guinea-Bissau',
            'Russian Fed': 'Russia',
            'Rep.Moldova': 'Moldova',
            'Trinidad Tbg': 'Trinidad and Tobago',
            'Lao P.Dem.R': 'Laos',
            'Gambia': 'The Gambia',
            'Iran-Islam.R': 'Iran',
            'Kyrgyzstan': 'Kyrgyz Republic',
            'Venezuela': 'Venezuela, RB',
            'Yemen': 'Yemen, Rep.'
        }
        
        # Apply mappings
        df_norm[country_col] = df_norm[country_col].replace(name_mappings)
        
        return df_norm
        
    def calculate_raiv_for_year(self, year: int) -> pd.DataFrame:
        """
        Calculate RAIV for a specific year.
        
        Args:
            year: Year to calculate RAIV for (2022, 2023, or 2024)
            
        Returns:
            DataFrame with RAIV calculations
        """
        # Determine t value based on year
        t_values = {2022: 0, 2023: 1, 2024: 2}
        t = t_values.get(year)
        if t is None:
            raise ValueError(f"Invalid year: {year}. Must be 2022, 2023, or 2024")
            
        # Get data from all sources
        import_df = self.get_import_data(year)
        lpi_df = self.get_lpi_data()
        risk_df = self.get_risk_premium_data()
        
        if import_df.empty or lpi_df.empty or risk_df.empty:
            logger.warning(f"Missing data for year {year}")
            return pd.DataFrame()
            
        # Normalize country names
        import_df = self.normalize_country_names(import_df)
        lpi_df = self.normalize_country_names(lpi_df)
        risk_df = self.normalize_country_names(risk_df)
        
        # Merge all datasets
        merged_df = import_df.merge(lpi_df, on='Country', how='inner')
        merged_df = merged_df.merge(risk_df, on='Country', how='inner')
        
        # Calculate RAIV using the formula:
        # RAIV = Import Value × LPI Timeliness Score / (1 + Risk Premium)^t
        merged_df['RAIV'] = (
            merged_df['ImportValue'] * 
            merged_df['TimelinessScore'] / 
            np.power(1 + merged_df['RiskPremium'], t)
        )
        
        # Add metadata
        merged_df['Year'] = year
        merged_df['t_value'] = t
        
        # Reorder columns
        columns = ['Country', 'Year', 'ImportValue', 'TimelinessScore', 'RiskPremium', 't_value', 'RAIV']
        merged_df = merged_df[columns]
        
        logger.info(f"Calculated RAIV for {len(merged_df)} countries in {year}")
        
        return merged_df
        
    def calculate_raiv_all_years(self) -> pd.DataFrame:
        """
        Calculate RAIV for all available years (2022, 2023, 2024).
        
        Returns:
            DataFrame with RAIV calculations for all years
        """
        all_results = []
        
        for year in [2022, 2023, 2024]:
            try:
                year_results = self.calculate_raiv_for_year(year)
                if not year_results.empty:
                    all_results.append(year_results)
            except Exception as e:
                logger.error(f"Error calculating RAIV for {year}: {e}")
                continue
                
        if not all_results:
            logger.warning("No RAIV results calculated for any year")
            return pd.DataFrame()
            
        # Combine all years
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Sort by country and year
        combined_df = combined_df.sort_values(['Country', 'Year'])
        
        logger.info(f"Total RAIV calculations: {len(combined_df)}")
        
        return combined_df
        
    def save_results_to_csv(self, df: pd.DataFrame, filename: str = 'raiv_results.csv'):
        """
        Save RAIV results to CSV file.
        
        Args:
            df: DataFrame with RAIV results
            filename: Output filename
        """
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            
    def save_results_to_database(self, df: pd.DataFrame, table_name: str = 'RAIV_Results'):
        """
        Save RAIV results back to the database.
        
        Args:
            df: DataFrame with RAIV results
            table_name: Name of the table to create
        """
        try:
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            logger.info(f"Results saved to database table: {table_name}")
        except Exception as e:
            logger.error(f"Error saving results to database: {e}")
            
    def generate_summary_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary statistics for RAIV results.
        
        Args:
            df: DataFrame with RAIV results
            
        Returns:
            DataFrame with summary statistics
        """
        if df.empty:
            return pd.DataFrame()
            
        summary_stats = df.groupby('Year').agg({
            'RAIV': ['count', 'mean', 'median', 'std', 'min', 'max'],
            'ImportValue': ['mean', 'median'],
            'TimelinessScore': ['mean', 'median'],
            'RiskPremium': ['mean', 'median']
        }).round(4)
        
        # Flatten column names
        summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns.values]
        summary_stats = summary_stats.reset_index()
        
        return summary_stats


def main():
    """Main function to run the RAIV calculation."""
    logger.info("Starting RAIV calculation model")
    
    # Initialize calculator
    calculator = RAIVCalculator()
    
    try:
        # Calculate RAIV for all years
        raiv_results = calculator.calculate_raiv_all_years()
        
        if raiv_results.empty:
            logger.error("No RAIV results calculated")
            return
            
        # Display sample results
        print("\n" + "="*80)
        print("RAIV CALCULATION RESULTS")
        print("="*80)
        print(f"\nTotal calculations: {len(raiv_results)}")
        print(f"Countries covered: {raiv_results['Country'].nunique()}")
        print(f"Years covered: {sorted(raiv_results['Year'].unique())}")
        
        # Show top 10 RAIV values for each year
        for year in sorted(raiv_results['Year'].unique()):
            year_data = raiv_results[raiv_results['Year'] == year]
            top_10 = year_data.nlargest(10, 'RAIV')
            
            print(f"\n--- Top 10 RAIV Values for {year} ---")
            print(top_10[['Country', 'RAIV', 'ImportValue', 'TimelinessScore', 'RiskPremium']].to_string(index=False))
        
        # Generate and display summary statistics
        summary_stats = calculator.generate_summary_statistics(raiv_results)
        print(f"\n--- Summary Statistics ---")
        print(summary_stats.to_string(index=False))
        
        # Save results
        calculator.save_results_to_csv(raiv_results)
        calculator.save_results_to_database(raiv_results)
        
        # Save summary statistics
        calculator.save_results_to_csv(summary_stats, 'raiv_summary_statistics.csv')
        
        logger.info("RAIV calculation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise
        
    finally:
        # Clean up
        calculator.close_db()


if __name__ == "__main__":
    main()