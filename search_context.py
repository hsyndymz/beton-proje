import PyPDF2
import re

def search_beton_yol_context(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        current_section = "Unknown"
        
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            
            # Update current section
            section_match = re.findall(r"KISIM\s+(\d{3})", text)
            if section_match:
                current_section = section_match[-1]
            
            if "Beton Yol" in text or "BETON YOL" in text:
                results.append(f"Sayfa {i+1} | Kısım: {current_section}\n")
                lines = text.split('\n')
                for line in lines:
                    if "Beton Yol" in line or "BETON YOL" in line:
                        results.append(f"  {line.strip()}\n")
        
        with open('beton_yol_context_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print("Sonuçlar 'beton_yol_context_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_beton_yol_context(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
