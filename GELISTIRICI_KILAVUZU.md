# 🏗️ Beton Tasarım Programı - Geliştirici ve Bakım Kılavuzu

Bu doküman, Beton Tasarım Programı'nın (AR-GE ve Kalite Kontrol Sistemi) teknik altyapısını, dosya hiyerarşisini ve sistem üzerinde değişiklik yapma yöntemlerini detaylı bir şekilde anlatır. 

**Hedef Kitle:** Sistemi geliştirmek, modifiye etmek veya bakımını yapmak isteyen teknik personel.

---

## 1. 📂 Proje ve Dosya Yapısı

Proje, modüler bir yapıda tasarlanmıştır. Her modül (logic) belirli bir sorumluluğa sahiptir.

### Temel Dosyalar
| Dosya | Açıklama |
| :--- | :--- |
| **`app.py`** | **Ana Giriş Noktası.** Uygulamanın beyni. Menüleri çizer, sayfaları yönetir ve diğer tüm modülleri birleştirir. Streamlit konfigürasyonu buradadır. |
| **`config.py`** | **Konfigürasyon.** API anahtarları, güvenlik secret'ları ve veritabanı yolları burada tanımlanır. |
| **`requirements.txt`** | **Bağımlılıklar.** Projenin çalışması için gereken kütüphanelerin listesi (pandas, streamlit, numpy vb.). |

### Mantıksal Modüller (`logic/` Klasörü)
| Dosya | Sorumluluk | Önem Derecesi |
| :--- | :--- | :--- |
| **`engineering.py`** | **Kural Motoru & Hesaplamalar.** Beton sınıfları, standart limitleri, elek analizleri, su/çimento oranları hesapları. Burası sistemin "Mühendislik Beyni"dir. | ⭐⭐⭐⭐⭐ |
| **`modular_tabs.py`** | **Arayüz (UI) Modülleri.** Sekmelerin (Tab 1, Tab 2...) içeriğini ve görünümünü çizen kodlar. Input widget'ları (kutucuklar) buradadır. | ⭐⭐⭐⭐ |
| **`data_manager.py`** | **Veri Yönetimi.** JSON dosyalarına yazma ve okuma işlemlerini yapar. Veritabanı katmanıdır. | ⭐⭐⭐ |
| **`report_generator.py`** | **Raporlama.** PDF çıktılarını tasarlar ve oluşturur. | ⭐⭐⭐ |
| **`ai_model.py`** | **Yapay Zeka.** Gemini/GPT entegrasyonu, veri analizi ve tahminleme motoru. | ⭐⭐ |
| **`state_manager.py`** | **Oturum Yönetimi.** Session State (oturum verileri) başlatma ve temizleme işlemleri. | ⭐⭐ |

### Veri Klasörü (`data/` Klasörü)
Veriler JSON formatında saklanır.
*   **`projects_merkez.json`:** Merkez santralin tüm proje ve reçete verileri.
*   **`plants.json`:** Tanımlı santrallerin listesi.
*   **`users.json`:** Kullanıcı adları ve şifreleri.

---

## 2. 🔄 Veri Akışı ve Mimari

Sistem **Streamlit** üzerine kuruludur ve **Durum Tabanlı (State-Based)** çalışır.

1.  **Giriş (Input):** Kullanıcı `modular_tabs.py` üzerinden veri girer.
2.  **Oturum (Session State):** Girilen veriler `st.session_state` sözlüğünde geçici olarak tutulur.
3.  **Hesaplama:** `engineering.py` fonksiyonları, session state'teki verileri alıp işler (örn: `calculate_passing`).
4.  **Kayıt:** Kullanıcı "Kaydet" dediğinde `data_manager.py`, session state verilerini `projects_merkez.json` dosyasına yazar.
5.  **Çıktı:** `report_generator.py`, JSON'dan veya session state'ten veriyi okuyup PDF üretir.

---

## 3. 🛠️ Nasıl Değiştirilir? (Adım Adım Senaryolar)

### Senaryo A: Yeni Bir Malzeme Eklemek veya İsmini Değiştirmek
**Risk:** ⚠️ Yüksek (Eski veriler kaybolabilir)

1.  **Değişiklik:** Aşağıdaki 5 dosyada malzeme listesini güncelleyin:
    *   `app.py` -> `materials = [...]` satırı.
    *   `logic/modular_tabs.py` -> `render_tab_1` içindeki liste.
    *   `logic/tabs/tab_reports.py` -> `render_tab_3` içindeki liste.
    *   `logic/report_generator.py` -> `generate_pdf_raporu` içinde **iki yerde** bulunan liste.
    *   `logic/tabs/tab_material_library.py` -> `render_tab_1` içindeki liste.
2.  **Veri Kurtarma:** Eğer isim değiştirdiyseniz, eski verileri (eski isimle kayıtlı olanları) yeni isme taşıyan bir "Migration Script" yazmalısınız. (Bunu AI asistanınızdan isteyebilirsiniz).

### Senaryo B: Beton Dayanım Standartlarını (C30/37 vb.) Değiştirmek
**Risk:** 🟢 Düşük

1.  **Dosya:** `logic/engineering.py`
2.  **Değişken:** `CONCRETE_RULES` sözlüğü.
3.  **İşlem:** İlgili beton sınıfını bulun (örn: "C30/37") ve `min_mpa`, `min_cem` gibi değerleri değiştirin.
4.  **Etki:** Anında tüm uygunluk kontrollerine yansır.

### Senaryo C: Yeni Bir Elek Boyutu Eklemek
**Risk:** 🟠 Orta

1.  **Dosya:** `logic/engineering.py`
2.  **Değişken:** `SIEVE_SETS` sözlüğü.
3.  **İşlem:** 31.5 mm veya 22.4 mm serisine yeni eleği ekleyin (Büyükten küçüğe sıralı olmalı!).
4.  **Ek İşlem:** `STD_GRADING_DB` değişkeninde de aynı elek boyutu için limit (A, B, C eğrileri) değerlerini girmelisiniz. Aksi takdirde grafik hata verir.

### Senaryo D: PDF Rapor Tasarımını Değiştirmek
**Risk:** 🟢 Düşük

1.  **Dosya:** `logic/report_generator.py`
2.  **Fonksiyon:** `generate_pdf_raporu`
3.  **İşlem:**
    *   `pdf.cell(...)`: Hücre/Metin ekler.
    *   `pdf.ln(...)`: Alt satıra geçer.
    *   `pdf.set_font(...)`: Yazı tipini ayarlar.
    *   `pdf.image(...)`: Resim/Logo ekler.

### Senaryo E: Yeni Bir Sekme (Tab) Eklemek
**Risk:** 🟠 Orta

1.  **Dosya:** `logic/modular_tabs.py`
2.  **İşlem:** `def render_tab_yeni(...):` şeklinde yeni bir fonksiyon oluşturun. İçine `st.text_input` gibi araçlar ekleyin.
3.  **Dosya:** `app.py`
4.  **İşlem:** `tabs = st.tabs(["Mevcutlar", ..., "YENİ SEKME"])` listesine ekleyin.
5.  **Bağlama:** `with tabs[5]: render_tab_yeni(...)` şeklinde fonksiyonu çağırın.

---

## 4. 🚨 Sorun Giderme (Troubleshooting)

| Sorun | Olası Neden | Çözüm |
| :--- | :--- | :--- |
| **"KeyError: 'No:1'" Hatası** | Malzeme ismi kodda değişti ama JSON veritabanında eski hali duruyor. | Veri taşıma (migration) işlemi yapılmalı veya veritabanı sıfırlanmalı. |
| **Grafik Çizilmiyor / Boş** | `app.py` içindeki malzeme listesi ile `modular_tabs.py` içindeki liste uyuşmuyor. | `app.py` içindeki `materials` listesini kontrol edin, boşluk hatası olabilir. |
| **PDF Türkçe Karakter Sorunu** | Yazı tipi "Arial" değil "Helvetica" olarak kalmış. | `logic/report_generator.py` içinde `C:\Windows\Fonts\arial.ttf` yolunu kontrol edin. |
| **Veriler Kaydolmuyor** | `logic/data_manager.py` dosyasına erişim izni yok veya dosya açık. | Klasör izinlerini kontrol edin, JSON dosyasının başka programda açık olmadığından emin olun. |

---

## 💡 Geliştirici İpuçları

1.  **Yedekleme:** Büyük bir değişiklik yapmadan önce daima `data/` klasörünü yedekleyin (Kopyala-Yapıştır yapın).
2.  **Git Kullanımı:** Versiyon kontrol sistemi kullanıyorsanız her değişiklikten önce `git commit` yapın.
3.  **Loglar:** Hata aldığınızda terminal ekranındaki (cmd) hata mesajını okuyun. Genellikle hangi dosyada ve kaçıncı satırda hata olduğu yazar.
4.  **AI Desteği:** Takıldığınızda hata mesajını kopyalayıp bana (AI Asistanı) sorun, çözümü saniyeler içinde verebilirim.
