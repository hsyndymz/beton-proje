import PyPDF2
import re

def search_sc(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "S/Ç" in text or "SU/ÇİMENTO" in text.upper():
                print(f"BULDUM: Sayfa {i+1}")
                # Kısım numarasını bulmaya çalış
                kisim = re.search(r"KISIM\s*\d+", text, re.IGNORECASE)
                if kisim:
                    print(f"Kısım: {kisim.group(0)}")
                print(text[:300].replace('\n', ' '))
                if "YOL" in text.upper():
                    print("--- POTANSİYEL BETON YOL SAYFASI ---")

if __name__ == "__main__":
    search_sc(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
