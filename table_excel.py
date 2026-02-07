import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, sheet_name='03.02.2026', header=None)
    
    # Target specific rows and columns for clarity
    rows = range(20, 70)
    cols = range(0, 15)
    
    print(f"{'Row':<5} | " + " | ".join([f"C{c:<8}" for c in cols]))
    print("-" * 150)
    
    for r in rows:
        row_vals = []
        for c in cols:
            val = df.iloc[r, c] if r < len(df) and c < len(df.columns) else None
            if pd.isna(val):
                row_vals.append(f"{'':<10}")
            else:
                sval = str(val)[:10]
                row_vals.append(f"{sval:<10}")
        print(f"{r:<5} | " + " | ".join(row_vals))

except Exception as e:
    print(f"Error: {e}")
