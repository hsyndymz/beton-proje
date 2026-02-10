import PyPDF2

def search_keywords(pdf_path, keywords):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        results = []
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text()
            for kw in keywords:
                if kw.upper() in text.upper():
                    results.append(f"KW: {kw} | Sayfa {i+1} | {text[:150].replace('\n', ' ')}")
                    # İlk 5 sonucu bulursak durabiliriz her kw için
                    break
            if len(results) > 20: 
                break
        
        for r in results:
            print(r)

if __name__ == "__main__":
    search_keywords(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf', ["ÇİMENTO", "AGREGA", "BETON", "DAYANIM"])
