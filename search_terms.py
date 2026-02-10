import PyPDF2
import re

def search_pavement_terms(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        terms = ["Derzli Donatısız", "Derzli Donatılı", "Sürekli Donatılı", "Sıkıştırılmış Beton"]
        
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            found = False
            for term in terms:
                if term in text:
                    found = True
                    break
            
            if found:
                results.append(f"Sayfa {i+1}:\n")
                lines = text.split('\n')
                for line in lines:
                    if any(term in line for term in terms):
                        results.append(f"  {line.strip()}\n")
        
        with open('pavement_terms_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'pavement_terms_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_pavement_terms(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
