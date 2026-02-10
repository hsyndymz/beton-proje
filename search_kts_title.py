import PyPDF2

def search_title(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "BETON YOL KAPLAMALARI" in text.upper():
                print(f"BULDUM: Sayfa {i+1}")
                print(text[:300].replace('\n', ' '))
                # Eğer "KISIM" veya "BÖLÜM" + sayı geçiyorsa tam budur
                if "KISIM" in text.upper() or "BÖLÜM" in text.upper():
                    print(f"--- KESİN KONUM ---")

if __name__ == "__main__":
    search_title(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
