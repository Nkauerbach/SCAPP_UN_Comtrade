#!/usr/bin/env python3
"""
RAIV Calculation Model - Simplified Version
==========================================

This script calculates the Risk-Adjusted Import Value (RAIV) for each country using the formula:
RAIV = Import Value (2022, 2023, or 2024) × LPI Timeliness Score (2023) / (1 + Risk Premium)^t

Where:
- t = 0 for 2022 data
- t = 1 for 2023 data  
- t = 2 for 2024 data

This version uses only built-in Python libraries.
"""

import sqlite3
import csv
import math
from collections import defaultdict

class SimpleRAIVCalculator:
    """Simplified RAIV calculator using only built-in libraries."""
    
    def __init__(self, db_path='trade_analysis.db'):
        """Initialize the calculator."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        
        # Country name mappings for normalization
        self.name_mappings = {
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
        
    def normalize_country_name(self, country):
        """Normalize a country name."""
        return self.name_mappings.get(country, country)
        
    def get_import_data(self, year):
        """Get import data for a specific year."""
        table_name = f"Cleaned_Imports_{year}"
        query = f"""
        SELECT 
            PartnerName as Country,
            SUM(TradeValuein1000USD) as ImportValue
        FROM {table_name}
        WHERE PartnerName != 'World'
        GROUP BY PartnerName
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        import_data = {}
        for row in cursor.fetchall():
            country = self.normalize_country_name(row['Country'])
            import_data[country] = row['ImportValue']
            
        print(f"Retrieved import data for {len(import_data)} countries in {year}")
        return import_data
        
    def get_lpi_data(self):
        """Get LPI timeliness data."""
        query = """
        SELECT 
            Economy as Country,
            TimelinessScore
        FROM LPI_2023_only
        WHERE TimelinessScore IS NOT NULL
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        lpi_data = {}
        for row in cursor.fetchall():
            country = self.normalize_country_name(row['Country'])
            lpi_data[country] = row['TimelinessScore']
            
        print(f"Retrieved LPI data for {len(lpi_data)} countries")
        return lpi_data
        
    def get_risk_premium_data(self):
        """Get risk premium data."""
        query = """
        SELECT 
            Economy as Country,
            RiskPremium
        FROM Risk_Premium_Lookup
        WHERE RiskPremium IS NOT NULL
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        risk_data = {}
        for row in cursor.fetchall():
            country = self.normalize_country_name(row['Country'])
            risk_data[country] = row['RiskPremium']
            
        print(f"Retrieved risk premium data for {len(risk_data)} countries")
        return risk_data
        
    def calculate_raiv_for_year(self, year):
        """Calculate RAIV for a specific year."""
        # Determine t value
        t_values = {2022: 0, 2023: 1, 2024: 2}
        t = t_values[year]
        
        # Get all data
        import_data = self.get_import_data(year)
        lpi_data = self.get_lpi_data()
        risk_data = self.get_risk_premium_data()
        
        # Calculate RAIV for countries with complete data
        results = []
        
        for country in import_data:
            if country in lpi_data and country in risk_data:
                import_value = import_data[country]
                timeliness_score = lpi_data[country]
                risk_premium = risk_data[country]
                
                # RAIV = Import Value × LPI Timeliness Score / (1 + Risk Premium)^t
                raiv = (import_value * timeliness_score) / math.pow(1 + risk_premium, t)
                
                results.append({
                    'Country': country,
                    'Year': year,
                    'ImportValue': import_value,
                    'TimelinessScore': timeliness_score,
                    'RiskPremium': risk_premium,
                    't_value': t,
                    'RAIV': raiv
                })
                
        print(f"Calculated RAIV for {len(results)} countries in {year}")
        return results
        
    def calculate_raiv_all_years(self):
        """Calculate RAIV for all years."""
        all_results = []
        
        for year in [2022, 2023, 2024]:
            try:
                year_results = self.calculate_raiv_for_year(year)
                all_results.extend(year_results)
            except Exception as e:
                print(f"Error calculating RAIV for {year}: {e}")
                
        # Sort by country and year
        all_results.sort(key=lambda x: (x['Country'], x['Year']))
        
        print(f"Total RAIV calculations: {len(all_results)}")
        return all_results
        
    def save_to_csv(self, results, filename='raiv_results.csv'):
        """Save results to CSV."""
        if not results:
            print("No results to save")
            return
            
        fieldnames = ['Country', 'Year', 'ImportValue', 'TimelinessScore', 'RiskPremium', 't_value', 'RAIV']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"Results saved to {filename}")
        
    def save_to_database(self, results, table_name='RAIV_Results'):
        """Save results to database."""
        if not results:
            print("No results to save")
            return
            
        # Create table
        cursor = self.conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        cursor.execute(f'''
        CREATE TABLE {table_name} (
            Country TEXT,
            Year INTEGER,
            ImportValue REAL,
            TimelinessScore REAL,
            RiskPremium REAL,
            t_value INTEGER,
            RAIV REAL
        )
        ''')
        
        # Insert data
        for result in results:
            cursor.execute(f'''
            INSERT INTO {table_name} 
            (Country, Year, ImportValue, TimelinessScore, RiskPremium, t_value, RAIV)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['Country'],
                result['Year'],
                result['ImportValue'],
                result['TimelinessScore'],
                result['RiskPremium'],
                result['t_value'],
                result['RAIV']
            ))
            
        self.conn.commit()
        print(f"Results saved to database table: {table_name}")
        
    def generate_summary_statistics(self, results):
        """Generate summary statistics."""
        if not results:
            return []
            
        # Group by year
        year_groups = defaultdict(list)
        for result in results:
            year_groups[result['Year']].append(result)
            
        summary_stats = []
        for year in sorted(year_groups.keys()):
            year_results = year_groups[year]
            raiv_values = [r['RAIV'] for r in year_results]
            import_values = [r['ImportValue'] for r in year_results]
            timeliness_values = [r['TimelinessScore'] for r in year_results]
            risk_values = [r['RiskPremium'] for r in year_results]
            
            # Calculate statistics
            raiv_mean = sum(raiv_values) / len(raiv_values)
            raiv_min = min(raiv_values)
            raiv_max = max(raiv_values)
            
            # Calculate median
            sorted_raiv = sorted(raiv_values)
            n = len(sorted_raiv)
            raiv_median = sorted_raiv[n//2] if n % 2 == 1 else (sorted_raiv[n//2-1] + sorted_raiv[n//2]) / 2
            
            # Calculate standard deviation
            raiv_var = sum((x - raiv_mean) ** 2 for x in raiv_values) / len(raiv_values)
            raiv_std = math.sqrt(raiv_var)
            
            summary_stats.append({
                'Year': year,
                'Count': len(year_results),
                'RAIV_Mean': round(raiv_mean, 4),
                'RAIV_Median': round(raiv_median, 4),
                'RAIV_Std': round(raiv_std, 4),
                'RAIV_Min': round(raiv_min, 4),
                'RAIV_Max': round(raiv_max, 4),
                'ImportValue_Mean': round(sum(import_values) / len(import_values), 4),
                'TimelinessScore_Mean': round(sum(timeliness_values) / len(timeliness_values), 4),
                'RiskPremium_Mean': round(sum(risk_values) / len(risk_values), 4)
            })
            
        return summary_stats
        
    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Main function."""
    print("="*80)
    print("RAIV CALCULATION MODEL")
    print("="*80)
    print("Formula: RAIV = Import Value × LPI Timeliness Score / (1 + Risk Premium)^t")
    print("Where t = 0 for 2022, t = 1 for 2023, t = 2 for 2024")
    print("="*80)
    
    # Initialize calculator
    calculator = SimpleRAIVCalculator()
    
    try:
        # Calculate RAIV for all years
        results = calculator.calculate_raiv_all_years()
        
        if not results:
            print("No RAIV results calculated")
            return
            
        # Display basic statistics
        countries = set(r['Country'] for r in results)
        years = set(r['Year'] for r in results)
        
        print(f"\nTotal calculations: {len(results)}")
        print(f"Countries covered: {len(countries)}")
        print(f"Years covered: {sorted(years)}")
        
        # Show top 10 RAIV values for each year
        for year in sorted(years):
            year_results = [r for r in results if r['Year'] == year]
            year_results.sort(key=lambda x: x['RAIV'], reverse=True)
            top_10 = year_results[:10]
            
            print(f"\n--- Top 10 RAIV Values for {year} ---")
            print(f"{'Country':<25} {'RAIV':<15} {'Import Value':<15} {'Timeliness':<12} {'Risk Premium':<12}")
            print("-" * 80)
            for result in top_10:
                print(f"{result['Country']:<25} {result['RAIV']:<15.2f} {result['ImportValue']:<15.2f} {result['TimelinessScore']:<12.2f} {result['RiskPremium']:<12.3f}")
        
        # Generate summary statistics
        summary_stats = calculator.generate_summary_statistics(results)
        
        print(f"\n--- Summary Statistics ---")
        for stat in summary_stats:
            print(f"\nYear {stat['Year']}:")
            print(f"  Count: {stat['Count']}")
            print(f"  RAIV - Mean: {stat['RAIV_Mean']}, Median: {stat['RAIV_Median']}, Std: {stat['RAIV_Std']}")
            print(f"  RAIV - Min: {stat['RAIV_Min']}, Max: {stat['RAIV_Max']}")
            print(f"  Avg Import Value: {stat['ImportValue_Mean']}")
            print(f"  Avg Timeliness Score: {stat['TimelinessScore_Mean']}")
            print(f"  Avg Risk Premium: {stat['RiskPremium_Mean']}")
        
        # Save results
        calculator.save_to_csv(results)
        calculator.save_to_database(results)
        
        # Save summary statistics
        summary_fieldnames = ['Year', 'Count', 'RAIV_Mean', 'RAIV_Median', 'RAIV_Std', 'RAIV_Min', 'RAIV_Max',
                             'ImportValue_Mean', 'TimelinessScore_Mean', 'RiskPremium_Mean']
        with open('raiv_summary_statistics.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=summary_fieldnames)
            writer.writeheader()
            writer.writerows(summary_stats)
        print("Summary statistics saved to raiv_summary_statistics.csv")
        
        print("\n" + "="*80)
        print("RAIV calculation completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"Error in calculation: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        calculator.close()


if __name__ == "__main__":
    main()