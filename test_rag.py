from logic.rag_service import RAGService
import os

def test_rag():
    print("--- RAG Service Testi Başlatılıyor ---")
    
    # Bilgi bankası yolunu kontrol et
    kb_path = "data/knowledge_base.json"
    if not os.path.exists(kb_path):
        print(f"Hata: {kb_path} bulunamadı!")
        return

    rag = RAGService(kb_path)
    print(f"Bilgi bankası yüklendi. Parça sayısı: {len(rag.knowledge_base)}")

    # Test sorgusu
    query = "dayanım sınıfları ve su emme"
    print(f"\nSorgu: '{query}'")
    context = rag.search_context(query, top_k=2)
    
    if context:
        print("Sonuç Bulundu:")
        print(context)
    else:
        print("Sonuç bulunamadı.")

if __name__ == "__main__":
    test_rag()
