import PyPDF2
import re

def search_sections(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            # Look for "KISIM 5xx" at the top
            match = re.search(r"KISIM\s+(5\d{2})", text)
            if match:
                results.append(f"Sayfa {i+1} | {match.group(0)}")
                # Extract first two lines after KISIM
                lines = text.split('\n')
                for j, line in enumerate(lines):
                    if "KISIM" in line:
                        if j+1 < len(lines):
                            results.append(f"  Başlık: {lines[j+1].strip()}")
                        if j+2 < len(lines):
                            results.append(f"  Alt-Başlık: {lines[j+2].strip()}")
                        break
        
        with open('section_500_search.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(results))
        print("Sonuçlar 'section_500_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    search_sections(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
