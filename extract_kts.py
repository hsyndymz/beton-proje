import PyPDF2
import re

def extract_kts_info(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        found_section = False
        section_text = []

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if "KISIM 414" in page_text or "BÖLÜM 414" in page_text or "BETON YOL KAPLAMALARI" in page_text:
                found_section = True
            
            if found_section:
                section_text.append(page_text)
                # Kısım 414 genellikle birkaç sayfa sürer, 5 sayfa okuyalım
                if len(section_text) > 20: 
                    break
        
        full_text = "\n".join(section_text)
        
        # Limitleri ara
        print("--- KTŞ 2023 BÖLÜM 414 ÖZET ---")
        
        # Su Çimento
        sc_matches = re.findall(r"su/çimento\s*oranı\s*(?:en\s*fazla|azami|maksimum)?\s*([\d,\.]+)", full_text, re.IGNORECASE)
        print(f"Su/Çimento Oranı Adayları: {sc_matches}")
        
        # Çimento Dozajı
        cem_matches = re.findall(r"en\s*az\s*(\d{3})\s*kg/m³", full_text, re.IGNORECASE)
        print(f"Minimum Çimento Adayları: {cem_matches}")
        
        # Filler
        filler_matches = re.findall(r"0,063\s*mm.*?([\d,\.]+)", full_text, re.IGNORECASE)
        print(f"0.063mm (Filler) Adayları: {filler_matches}")
        
        # Tüm metni kaydet (İncelemek için)
        with open('kts_414_extract.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)
        print("\nTam metni 'kts_414_extract.txt' dosyasına kaydettim.")

if __name__ == "__main__":
    extract_kts_info(r'c:\MASAÜSTÜ\yeni proje\yayınlar\KTŞ_2023.pdf')
