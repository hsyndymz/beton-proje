import PyPDF2
import re

def search_concrete_road(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            # Search for "Tip-1" and "Beton" or "Yol"
            if "Tip-1" in text and ("Beton" in text or "Yol" in text):
                results.append(f"Sayfa {i+1}:\n")
                # Find the context
                lines = text.split('\n')
                for line in lines:
                    if "Tip-1" in line or "Beton Yol" in line:
                        results.append(f"  {line.strip()}\n")
        
        with open('concrete_road_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'concrete_road_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_concrete_road(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
