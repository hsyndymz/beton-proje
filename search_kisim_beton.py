import PyPDF2
import re

def search_concrete_sections(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        pattern = re.compile(r"Kısım\s*\d+.*Beton", re.IGNORECASE)
        
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            lines = text.split('\n')
            for line in lines:
                if "Kısım" in line and "Beton" in line:
                    results.append(f"Sayfa {i+1}: {line.strip()}\n")
        
        with open('concrete_sections_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print(f"Sonuçlar 'concrete_sections_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_concrete_sections(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
