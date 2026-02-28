import os
import json
import sys
import re

# Ana proje dizinini path'e ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# STREAMLIT MOCKING - Bu script terminalden çalıştığı için st.* çağrılarını engellemeliyiz
class MockStreamlit:
    def __getattr__(self, name):
        # Decorator desteği: @st.cache_data(ttl=600) gibi kullanımlarda
        # st.cache_data(...) bir fonksiyon dönmeli, o fonksiyon da hedefi dönmeli.
        def mock_wrapper(*args, **kwargs):
            return lambda f: f if callable(f) else None
        return mock_wrapper
    @property
    def secrets(self): return {}

sys.modules['streamlit'] = MockStreamlit()
import streamlit as st # Artık mocklu

try:
    from logic.pdf_processor import extract_text_from_pdf, parse_concrete_design_with_ai
    from logic.data_manager import havuz_yukle, havuz_kaydet
except ImportError as e:
    print(f"Hata: Modüller yüklenemedi. {e}")
    sys.exit(1)

# API anahtarlarını environment'tan al
google_key = os.environ.get("GOOGLE_API_KEY")
groq_key = os.environ.get("GROQ_API_KEY")
deepseek_key = os.environ.get("DEEPSEEK_API_KEY")

def batch_process_pdfs(drive_path="G:\\"):
    print(f"\n🚀 {drive_path} üzerinde tarama başlatılıyor...")
    
    pdf_files = []
    # Sadece belirli klasörleri tara (G:\ Yeni Klasör (2) ve kök dizin gibi)
    # Veya heryeri tara
    for root, dirs, files in os.walk(drive_path):
        # Gizli klasörleri atla
        if any(d.startswith('.') for d in root.split(os.sep)): continue
        
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    
    print(f"📂 Toplam {len(pdf_files)} PDF dosyası bulundu.\n")
    
    new_data = []
    processed_count = 0
    errors = 0

    for pdf_path in pdf_files:
        processed_count += 1
        fname = os.path.basename(pdf_path)
        print(f"[{processed_count}/{len(pdf_files)}] 📄 {fname:40.40}", end=" ", flush=True)
        
        try:
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text or len(raw_text.strip()) < 100:
                print("❌ (Metin yok/Taramış)")
                continue
                
            parsed = parse_concrete_design_with_ai(raw_text, google_key, groq_key, deepseek_key)
            
            if "error" not in parsed:
                parsed["source"] = f"Bulk Local Path: {pdf_path}"
                parsed["filename"] = fname
                parsed["is_approved"] = True
                new_data.append(parsed)
                print("✅")
            else:
                # Sadece teknik hata varsa yazdır
                err = parsed['error']
                if "JSON" in err or "429" in err:
                    print(f"⚠️ {err[:30]}...")
                else:
                    print("❌")
                errors += 1
        except Exception as e:
            print(f"🔥 Hata: {str(e)[:20]}")
            errors += 1

        # Her 10 dosyada bir kaydet (güvenlik için)
        if len(new_data) % 10 == 0 and len(new_data) > 0:
            current_pool = havuz_yukle()
            # Mükerrer kaydı engellemek için filename kontrolü yapabiliriz ama havuzda filename yok henüz
            current_pool.extend(new_data)
            havuz_kaydet(current_pool)
            new_data = [] # Belleği boşalt ve havuza yazıldı

    # Kalanları kaydet
    if new_data:
        current_pool = havuz_yukle()
        current_pool.extend(new_data)
        havuz_kaydet(current_pool)

    print(f"\n✨ İŞLEM TAMAMLANDI!")
    print(f"✅ Başarıyla eklenen: {processed_count - errors - (processed_count-len(pdf_files))}")
    print(f"❌ Hatalı/Atlanan: {errors}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "G:\\"
    batch_process_pdfs(target)
