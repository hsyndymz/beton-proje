import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name='03.02.2026', header=None)
    
    # Take a slice
    df_slice = df.iloc[20:75, 0:20]
    # Save to CSV
    df_slice.to_csv('excel_slice.csv', index=True, header=False, encoding='utf-8')
    print("Slice saved to excel_slice.csv")

except Exception as e:
    print(f"Error: {e}")
