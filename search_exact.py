import PyPDF2
import re

def search_exact_phrase(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        phrase = "Beton Yol Kaplamaları"
        
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if phrase.lower() in text.lower():
                results.append(f"Sayfa {i+1}:\n")
                lines = text.split('\n')
                for line in lines:
                    if phrase.lower() in line.lower():
                        results.append(f"  {line.strip()}\n")
        
        with open('exact_phrase_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print(f"Sonuçlar 'exact_phrase_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_exact_phrase(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
