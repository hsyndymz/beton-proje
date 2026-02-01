import pandas as pd
import openpyxl

try:
    wb = openpyxl.load_workbook('DİZAYN CIKTISI.xlsx', data_only=True)
    sheet = wb.active
    print(f"Active Sheet: {sheet.title}")
    
    # Print non-empty cells to find coordinates
    for row in sheet.iter_rows(max_row=50, max_col=20):
        for cell in row:
            if cell.value:
                val = str(cell.value).strip()
                if len(val) > 0:
                    print(f"{cell.coordinate}: {val}")
                    
except Exception as e:
    print(e)
