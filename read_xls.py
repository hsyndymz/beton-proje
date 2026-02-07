import xlrd

file_path = r'F:\OCB-8.xls'

try:
    # Open the workbook with xlrd to see raw content
    book = xlrd.open_workbook(file_path)
    print(f"Sheet names: {book.sheet_names()}")
    
    for sheet_index in range(book.nsheets):
        sheet = book.sheet_by_index(sheet_index)
        print(f"\n--- Sheet: {sheet.name} ---")
        for row_index in range(min(sheet.nrows, 100)):
            row_data = []
            for col_index in range(min(sheet.ncols, 20)):
                cell = sheet.cell(row_index, col_index)
                if cell.value:
                    row_data.append(f"C{col_index}: {cell.value}")
            if row_data:
                print(f"R{row_index}: " + " | ".join(row_data))

except Exception as e:
    print(f"Error: {e}")
