import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    for sheet_name in xls.sheet_names:
        print(f"\n--- Detailed View: {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Check rows 40 to 65 specifically
        for r_idx in range(max(0, 40), min(len(df), 100)):
            row = df.iloc[r_idx]
            r_data = []
            for c_idx, val in enumerate(row):
                if pd.notna(val):
                    r_data.append(f"C{c_idx}: {val}")
            if r_data:
                print(f"R{r_idx}: " + " | ".join(r_data))

except Exception as e:
    print(f"Error: {e}")
