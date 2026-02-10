import PyPDF2
import re

def proximity_search(pdf_path, word1, word2, distance=5):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        pattern = re.compile(rf"{word1}\W+(?:\w+\W+){{0,{distance}}}{word2}|{word2}\W+(?:\w+\W+){{0,{distance}}}{word1}", re.IGNORECASE)
        
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            if pattern.search(text):
                results.append(f"Sayfa {i+1}:\n")
                matches = pattern.finditer(text)
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].replace('\n', ' ')
                    results.append(f"  ...{context}...\n")
        
        with open('proximity_search.txt', 'w', encoding='utf-8') as f:
            f.write("".join(results))
        print(f"Sonuçlar 'proximity_search.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    proximity_search(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', "Beton", "Yol")
