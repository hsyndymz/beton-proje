import PyPDF2

def read_toc_pages(pdf_path, pages):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for p in pages:
            text = reader.pages[p-1].extract_text()
            print(f"--- SAYFA {p} ---\n")
            print(text)

if __name__ == "__main__":
    read_toc_pages(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', [13, 14])
