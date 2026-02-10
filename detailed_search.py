import PyPDF2
import re

def search_with_results(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            upper_text = text.upper()
            
            hits = []
            if re.search(r"C\s?35/45|C\s?30/37", upper_text):
                hits.append("Beton Sınıfı")
            if "İNCELİK MODÜLÜ" in upper_text:
                hits.append("İncelik Modülü")
            if "S/Ç" in upper_text or "SU/ÇİMENTO" in upper_text:
                hits.append("S/Ç Oranı")
            if "TİP-1" in upper_text or "TİP 1" in upper_text:
                hits.append("Tip-1")
            
            if hits:
                results.append(f"SAyfa {i+1} | Hits: {', '.join(hits)}\n")
                results.append(text[:1000] + "\n" + "-"*50 + "\n")
        
        with open('search_results.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'search_results.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_with_results(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
