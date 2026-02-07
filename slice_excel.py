import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name='03.02.2026', header=None)
    
    # Let's print rows 25 to 65 with column indices to match headers
    print("--- 03.02.2026 Detailed Slice (25-65) ---")
    for r_idx in range(25, 65):
        row = df.iloc[r_idx]
        vals = [f"C{c_idx}:{val}" for c_idx, val in enumerate(row) if pd.notna(val)]
        if vals:
            print(f"R{r_idx}: " + " | ".join(vals))

except Exception as e:
    print(f"Error: {e}")
