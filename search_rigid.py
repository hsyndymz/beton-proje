import PyPDF2
import re

def search_rigid_composite(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if "Rijit" in text or "Kompozit" in text:
                results.append(f"Sayfa {i+1}:\n")
                lines = text.split('\n')
                for line in lines:
                    if "Rijit" in line or "Kompozit" in line:
                        results.append(f"  {line.strip()}\n")
        
        with open('rigid_composite_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'rigid_composite_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_rigid_composite(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
