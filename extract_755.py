import PyPDF2

def extract_pages(pdf_path, start, end):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = []
        for i in range(start-1, min(end, len(reader.pages))):
            text.append(f"--- SAYFA {i+1} ---\n")
            text.append(reader.pages[i].extract_text())
        
        with open('kts_755_760.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(text))
        print(f"Sayfa {start}-{end} arası 'kts_755_760.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    extract_pages(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', 755, 760)
