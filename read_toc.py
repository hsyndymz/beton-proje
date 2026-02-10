import PyPDF2

def read_page(pdf_path, page_num):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = reader.pages[page_num-1].extract_text()
        print(f"--- SAYFA {page_num} ---\n")
        print(text)

if __name__ == "__main__":
    # Page 11 and 12 usually have the 400 section contents
    read_page(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 11)
    read_page(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 12)
    read_page(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 13)
