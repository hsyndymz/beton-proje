import PyPDF2

def read_full_toc(pdf_path, start, end):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(start-1, min(end, len(reader.pages))):
            text = reader.pages[i].extract_text()
            print(f"--- SAYFA {i+1} ---\n")
            print(text)

if __name__ == "__main__":
    read_full_toc(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 10, 25)
