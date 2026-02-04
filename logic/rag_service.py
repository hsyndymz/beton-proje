import json
import os
import re

class RAGService:
    """
    Beton Uzmanı bilgi bankası üzerinden bağlam (context) arama servisi.
    """
    def __init__(self, kb_path="data/knowledge_base.json"):
        self.kb_path = kb_path
        self.knowledge_base = []
        self._load_kb()

    def _load_kb(self):
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        
        # Ocak verilerini de bilgi bankasına sanal olarak ekle
        quarries_file = "data/quarries.json"
        if os.path.exists(quarries_file):
            with open(quarries_file, 'r', encoding='utf-8') as f:
                ocaklar = json.load(f)
                for oid, info in ocaklar.items():
                    content = (f"Ocak Adı: {info['name']}, Litoloji: {info['lithology']}, "
                               f"LA Aşınma: %{info['la_wear']}, MB: {info['mb_value']}, "
                               f"ASR Riski: {info['asr_risk']}, Çimentolaşma: {info['cementation_index']}. "
                               f"Konum: {info['lat']}, {info['lon']}. Not: {info['description']}")
                    self.knowledge_base.append({
                        "source": f"Ocak Verisi: {info['name']}",
                        "tags": ["ocak", "agrega", info['lithology'].lower(), info['asr_risk'].lower(), "aşınma"],
                        "content": content
                    })

    def search_context(self, query, top_k=3):
        """
        Sorgu kelimelerine göre en alakalı bilgi parçalarını döner.
        """
        if not self.knowledge_base:
            return ""

        # Basit anahtar kelime skoru (Keyword matching)
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_items = []

        for item in self.knowledge_base:
            content = item.get("content", "").lower()
            tags = [t.lower() for t in item.get("tags", [])]
            
            score = 0
            for word in query_words:
                if word in content:
                    score += 1
                if word in tags:
                    score += 2 # Tag eşleşmesine daha fazla puan
            
            if score > 0:
                scored_items.append((score, item))

        # Skora göre sırala ve top_k seç
        scored_items.sort(key=lambda x: x[0], reverse=True)
        results = scored_items[:top_k]

        if not results:
            return ""

        context_str = "\n--- BİLGİ BANKASI KESİTLERİ ---\n"
        for _, res in results:
            src = res.get("source", "Bilinmeyen Kaynak")
            cont = res.get("content", "").strip()
            context_str += f"🔗 Kaynak: {src}\n📝 İçerik: {cont}\n\n"
        
        return context_str
