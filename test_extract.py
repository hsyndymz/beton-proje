import PyPDF2

def test_extract(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(10):
            text = reader.pages[i].extract_text()
            print(f"Sayfa {i+1} metin uzunluğu: {len(text)}")
            if len(text) > 50:
                print(f"İçerik: {text[:200]}")

if __name__ == "__main__":
    test_extract(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
