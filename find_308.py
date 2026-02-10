import PyPDF2
import re

def find_section_308(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "KISIM 308" in text:
                print(f"KISIM 308 Sayfa {i+1}'de başlıyor.")
                # Also search for "Beton Yol" within the first 100 pages of 308
                for j in range(i, min(i+100, len(reader.pages))):
                    page_text = reader.pages[j].extract_text()
                    if "Beton Yol" in page_text or "BETON YOL" in page_text:
                        print(f"BULDUM: 'Beton Yol' Sayfa {j+1}'de.")
                return

if __name__ == "__main__":
    find_section_308(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
