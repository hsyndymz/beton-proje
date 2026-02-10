import PyPDF2

def read_page_12(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = reader.pages[11].extract_text()
        print("--- SAYFA 12 ---")
        print(text)

if __name__ == "__main__":
    read_page_12(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
