import pandas as pd
import os

file_path = 'OCB-8.xls'

try:
    # Read all sheets
    xls = pd.ExcelFile(file_path)
    print(f"Sheets: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        print(f"\n--- {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Drop completely empty columns and rows for readability
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        print(df.to_string())

except Exception as e:
    print(f"Error: {e}")
