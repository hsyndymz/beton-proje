import pandas as pd
import numpy as np

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    for sheet_name in xls.sheet_names:
        print(f"\n--- Searching in sheet: {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Iterate over all cells
        for r_idx, row in df.iterrows():
            for c_idx, val in enumerate(row):
                if pd.notna(val):
                    s_val = str(val).lower()
                    # Check for keywords
                    keywords = ["su", "çimento", "cimento", "rutubet", "muhteva", "agrega", "kantar", "batch", "net", "toplam", "wa"]
                    if any(k in s_val for k in keywords):
                        # Print the found cell and some surrounding values
                        context = []
                        # Look at the next few columns (often the value is to the right)
                        for offset in range(1, 5):
                            if c_idx + offset < len(row):
                                nv = row[c_idx+offset]
                                if pd.notna(nv):
                                    context.append(str(nv))
                        
                        print(f"R{r_idx} C{c_idx}: {val} -> Values found: {', '.join(context)}")

except Exception as e:
    print(f"Error: {e}")
