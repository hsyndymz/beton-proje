import PyPDF2

def search_sections(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "BÖLÜM 500" in text or "BÖLÜM 600" in text or "BÖLÜM 700" in text:
                print(f"Bölüm Başlığı Bulundu: Sayfa {i+1}")
                print(text[:200].replace('\n', ' '))
            
            if "TİP 1" in text.upper() and ("GRADASYON" in text.upper() or "ELEK" in text.upper()):
                print(f"Gradasyon Tablosu Adayı: Sayfa {i+1}")
                print(text[:300].replace('\n', ' '))

if __name__ == "__main__":
    search_sections(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
