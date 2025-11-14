import pandas as pd
import json

# Check the Excel file structure
try:
    # Try to read the Excel file with different approaches
    print("Checking Excel file structure...")
    
    # Method 1: Read all sheets
    try:
        excel_data = pd.read_excel("Portfolio Data_Hypothetical.xlsx", sheet_name=None)
        print(f"Found {len(excel_data)} sheets:")
        for sheet_name, df in excel_data.items():
            print(f"  Sheet '{sheet_name}': {df.shape}")
            print(f"  Columns: {df.columns.tolist()}")
            print(f"  First few rows:")
            print(df.head())
            print("-" * 50)
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Read default sheet
    try:
        df = pd.read_excel("Portfolio Data_Hypothetical.xlsx")
        print(f"\nDefault sheet shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Sample data:")
        print(df.head())
    except Exception as e:
        print(f"Method 2 failed: {e}")
        
except Exception as e:
    print(f"Could not read Excel file: {e}")