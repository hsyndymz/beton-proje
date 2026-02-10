import PyPDF2
import re

def list_sections(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        sections = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            # Match "KISIM [Number] [Title]" or similar
            # Often it's at the top of the page
            lines = text.split('\n')
            for line in lines[:10]: # Check first 10 lines
                if "KISIM" in line.upper() and re.search(r"\d+", line):
                    sections.append(f"Sayfa {i+1}: {line.strip()}")
                    break
        
        with open('kts_sections_list.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(sections))
        print("Bölüm listesi 'kts_sections_list.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    list_sections(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
