import PyPDF2

def search_en206(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "EN 206" in text.upper():
                print(f"BULDUM: Sayfa {i+1}")
                print(text[:300].replace('\n', ' '))
                if "YOL" in text.upper():
                    print("--- POTANSİYEL BETON YOL SAYFASI ---")

if __name__ == "__main__":
    search_en206(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
