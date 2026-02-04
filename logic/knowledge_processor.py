import os
import json
import re
from pypdf import PdfReader

class KnowledgeProcessor:
    """
    Belirtilen klasördeki PDF dosyalarını tarar, metinlerini çıkartır
    ve anahtar kelimelere göre indeksleyerek AI için bir bilgi tabanı oluşturur.
    """
    def __init__(self, docs_dir, output_file):
        self.docs_dir = docs_dir
        self.output_file = output_file
        self.knowledge_index = []

    def process_all(self):
        if not os.path.exists(self.docs_dir):
            return "Klasör bulunamadı."

        files = [f for f in os.listdir(self.docs_dir) if f.endswith('.pdf')]
        
        for filename in files:
            path = os.path.join(self.docs_dir, filename)
            print(f"İşleniyor: {filename}...")
            content = self._extract_text(path)
            if content:
                # Metni parçalara (chunks) böl ve indeksle
                self._index_content(filename, content)
        
        self._save_index()
        return f"{len(files)} dosya işlendi ve {len(self.knowledge_index)} bilgi parçası oluşturuldu."

    def _extract_text(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            full_text = []
            # Çok büyük dosyalar için (örn. KTŞ) ilk ve son kısımlara veya 
            # belli sayfa limitlerine odaklanılabilir ama şimdilik tamamını deneyelim.
            # Performans için ilk 200 sayfa ile sınırlayalım (genelde ana kurallar buradadır)
            page_limit = 200
            for i, page in enumerate(reader.pages):
                if i > page_limit: break
                text = page.extract_text()
                if text:
                    full_text.append(text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Hata ({pdf_path}): {e}")
            return None

    def _index_content(self, source, text):
        # Basit bir yöntem: Paragraflara veya sayfalara göre böl
        # Şimdilik anahtar kelimeler üzerinden cümle bazlı veya paragraf bazlı gidelim
        paragraphs = text.split('\n\n')
        
        # Kritik beton anahtar kelimeleri
        keywords = {
            "dayanım": ["dayanım", "mukavemet", "mpa", "kırım"],
            "su/çimento": ["su/çimento", "w/c", "su oranı"],
            "agrega": ["agrega", "elek", "gradasyon", "granülometri"],
            "çimento": ["çimento", "dozaj", "cem", "tip"],
            "kür": ["kür", "bakım", "sulama", "nemli"],
            "katkı": ["katkı", "kimyasal", "akışkanlaştırıcı"],
            "asr": ["asr", "reaktif", "alkali"],
            "şartname": ["limit", "sınır", "şart", "karşılamalı"]
        }

        for p in paragraphs:
            if len(p.strip()) < 50: continue # Çok kısa satırları geç
            
            p_clean = p.strip()
            found_tags = []
            for tag, syns in keywords.items():
                if any(s.lower() in p_clean.lower() for s in syns):
                    found_tags.append(tag)
            
            if found_tags:
                self.knowledge_index.append({
                    "source": source,
                    "tags": found_tags,
                    "content": p_clean[:1000] # Çok uzun paragrafları kırp
                })

    def _save_index(self):
        data_dir = os.path.dirname(self.output_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_index, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Test amaçlı manuel çalıştırma
    processor = KnowledgeProcessor("../../yayınlar", "../../data/knowledge_base.json")
    print(processor.process_all())
