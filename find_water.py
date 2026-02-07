import pandas as pd

file_path = 'OCB-8.xls'

try:
    xls = pd.ExcelFile(file_path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Look for "Net Su" or "Kantar" or "Dizayn Su"
        for r_idx, row in df.iterrows():
            row_str = " ".join([str(v) for v in row if pd.notna(v)])
            if any(k in row_str.lower() for k in ["net su", "su miktari", "kantar", "batch", "rutubet", "su emme"]):
                print(f"Sheet: {sheet_name}, Row: {r_idx}, Content: {row_str}")

except Exception as e:
    print(f"Error: {e}")
