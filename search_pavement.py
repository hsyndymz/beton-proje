import PyPDF2
import re

def search_abbreviations(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "JPCP" in text or "JRCP" in text or "CRCP" in text:
                results.append(f"Sayfa {i+1}:\n")
                lines = text.split('\n')
                for line in lines:
                    if any(x in line for x in ["JPCP", "JRCP", "CRCP"]):
                        results.append(f"  {line.strip()}\n")
        
        with open('pavement_type_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'pavement_type_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_abbreviations(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
