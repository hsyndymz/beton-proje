import PyPDF2

def search_road_concrete(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text().upper()
            if "TİP-1" in text or "TİP 1" in text:
                if "GRADASYON" in text or "ELEK" in text:
                    print(f"ELEK/GRADASYON Bulundu: Sayfa {i+1}")
                    print(text[:500].replace('\n', ' '))
            
            if "BETON YOL" in text and ("ŞARTNAME" in text or "KISIM" in text):
                print(f"BETON YOL Kısım Adayı: Sayfa {i+1}")
                print(text[:500].replace('\n', ' '))

if __name__ == "__main__":
    search_road_concrete(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
