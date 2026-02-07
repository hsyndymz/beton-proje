import pandas as pd
import openpyxl
import xlrd
import os

file_path = 'OCB-8.xls'

def try_all():
    print(f"Checking file: {file_path}")
    if not os.path.exists(file_path):
        print("File not found locally!")
        return

    # Try pandas default
    try:
        print("\n--- Trying pandas default ---")
        df = pd.read_excel(file_path)
        print("Success! Head:")
        print(df.head())
        return
    except Exception as e:
        print(f"Failed: {e}")

    # Try openpyxl directly
    try:
        print("\n--- Trying openpyxl ---")
        wb = openpyxl.load_workbook(file_path, data_only=True)
        print(f"Success! Sheets: {wb.sheetnames}")
        return
    except Exception as e:
        print(f"Failed: {e}")

    # Try xlrd directly with ignore_workbook_corruption
    try:
        print("\n--- Trying xlrd ---")
        book = xlrd.open_workbook(file_path)
        print(f"Success! Sheets: {book.sheet_names()}")
        return
    except Exception as e:
        print(f"Failed: {e}")

    # Check first few bytes to see magic number
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            print(f"\nMagic number: {header.hex().upper()}")
    except Exception as e:
        print(f"Header check failed: {e}")

try_all()
