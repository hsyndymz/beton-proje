import PyPDF2

def read_toc_start(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(5, 15): # Pages 6 to 15
            text = reader.pages[i].extract_text()
            print(f"--- SAYFA {i+1} ---\n")
            print(text)

if __name__ == "__main__":
    read_toc_start(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
