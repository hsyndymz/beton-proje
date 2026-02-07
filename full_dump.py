import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name='03.02.2026', header=None)
    
    print("--- 03.02.2026 Data ---")
    for r_idx in range(len(df)):
        row = df.iloc[r_idx]
        has_val = False
        vals = []
        for c_idx, val in enumerate(row):
            if pd.notna(val):
                vals.append(f"C{c_idx}:{val}")
                has_val = True
        if has_val:
            print(f"R{r_idx}: " + " | ".join(vals))

except Exception as e:
    print(f"Error: {e}")
