import PyPDF2

def find_section_414(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        print(f"Toplam Sayfa Sayısı: {len(reader.pages)}")
        
        # İlk 100 sayfaya bak (İçindekiler genellikle burada)
        for i in range(min(100, len(reader.pages))):
            text = reader.pages[i].extract_text()
            if "BÖLÜM 414" in text or "KISIM 414" in text or "BETON YOL KAPLAMALARI" in text:
                print(f"Bulundu! Sayfa: {i+1}")
                # Sayfanın içeriğine bir göz atalım (belki sayfa numarası yazıyordur)
                print(text[:500])

if __name__ == "__main__":
    find_section_414(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
