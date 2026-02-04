import pandas as pd
import os

files = [
    r"F:\DENEYLER 2025\AL BETON\0-7 KALKER.xls",
    r"F:\DENEYLER 2025\BLOK TAŞLAR VE OCAKLAR\URFA\AŞAĞI OYLUM TAŞ OCAĞI BAZALT.xls"
]

for f_path in files:
    print(f"\n--- FILE: {os.path.basename(f_path)} ---")
    try:
        df = pd.read_excel(f_path, sheet_name=0)
        print("HEAD (Top 15 rows):")
        print(df.head(15))
    except Exception as e:
        print(f"Error reading {f_path}: {e}")
