import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name='03.02.2026', header=None)
    
    # Rows around 27
    for r_idx in range(max(0, 20), min(len(df), 60)):
        row = df.iloc[r_idx]
        r_data = []
        for c_idx, val in enumerate(row):
            if pd.notna(val):
                r_data.append(f"C{c_idx}: {val}")
        if r_data:
            print(f"R{r_idx}: " + " | ".join(r_data))

except Exception as e:
    print(f"Error: {e}")
