import PyPDF2

def read_pages(pdf_path, start, end):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(start-1, min(end, len(reader.pages))):
            text = reader.pages[i].extract_text()
            print(f"--- SAYFA {i+1} ---\n")
            print(text[:1000])

if __name__ == "__main__":
    read_pages(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 15, 25)
