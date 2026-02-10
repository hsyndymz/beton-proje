import PyPDF2

def find_414_in_all(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        print(f"Toplam Sayfa: {len(reader.pages)}")
        for i in range(len(reader.pages)):
            # Sadece ilk 200 karakteri oku, hız için
            text = reader.pages[i].extract_text()
            if "414" in text and ("BÖLÜM" in text or "KISIM" in text or "BETON YOL" in text):
                print(f"Potansiyel Sayfa: {i+1}")
                print(text[:200].replace('\n', ' '))
                # Eğer "BETON YOL" geçiyorsa ve 414 varsa büyük ihtimalle budur
                if "BETON YOL" in text:
                    print(f"--- KESİN BULUNDU: Sayfa {i+1} ---")

if __name__ == "__main__":
    find_414_in_all(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
