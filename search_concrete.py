import PyPDF2

def search_concrete_classes(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for i in range(len(reader.pages)):
            text = reader.pages[i].extract_text().upper()
            if "C 35/45" in text or "C35/45" in text or "C 30/37" in text or "C30/37" in text:
                print(f"BETON SINIFI Bulundu: Sayfa {i+1}")
                print(text[:500].replace('\n', ' '))
                if "YOL" in text:
                    print("--- POTANSİYEL YOL SAYFASI ---")
            
            if "İNCELİK MODÜLÜ" in text or "S/Ç ORANI" in text:
                print(f"TEKNİK PARAMETRE Bulundu: Sayfa {i+1}")
                print(text[:500].replace('\n', ' '))

if __name__ == "__main__":
    search_concrete_classes(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
