# 🛠️ Proje Bakım ve Güncelleme Kılavuzu

Bu belge, **Beton Tasarım Programı** üzerinde yapılacak veri ve parametre değişikliklerinin sistemin geneline nasıl doğru şekilde yansıtılacağını anlatır.

> **⚠️ ÖNEMLİ:** Yapılan herhangi bir isim değişikliği (örneğin malzeme adı), mevcut veritabanındaki kayıtlarla uyuşmazlığa yol açabilir. Bu tür değişikliklerde **Veri Taşıma (Migration)** işlemi gerekebilir.

---

## 1. Malzeme İsimlerini Değiştirmek

Malzeme isimleri (`Kaba Elek`, `Orta Kaba` vb.) projenin birçok yerinde **sabit metin (hardcoded)** olarak bulunmaktadır. Birini değiştirmek isterseniz aşağıdaki dosyaların hepsinde **birebir aynı** değişikliği yapmalısınız:

### 📍 Güncellenecek Dosyalar

1.  **`app.py`**
    *   **Konum:** `materials = [...]` satırı (Kodun başlarında, Global Veriler bölümünde).
    *   **Amaç:** Ana uygulama ve grafiklerin doğru çalışması için.

2.  **`logic/modular_tabs.py`**
    *   **Konum:** `render_tab_1` fonksiyonu içindeki `materials = [...]` listesi.
    *   **Amaç:** Veri giriş ekranındaki etiketlerin güncellenmesi için.

3.  **`logic/tabs/tab_reports.py`**
    *   **Konum:** `render_tab_3` fonksiyonu içinde, Malzeme Analiz Raporu bölümündeki `materials = [...]` listesi.
    *   **Amaç:** Rapor önizleme ekranında doğru görünmesi için.

4.  **`logic/report_generator.py`**
    *   **Konum:** `generate_pdf_raporu` fonksiyonu içinde `mats = [...]` listesi (2 yerde geçer).
    *   **Amaç:** PDF çıktısında doğru isimlerin yazması için.

5.  **`logic/tabs/tab_material_library.py`**
    *   **Konum:** `render_tab_1` fonksiyonu içindeki `materials = [...]` listesi.
    *   **Amaç:** Malzeme kütüphanesinin doğru çalışması için.

### 🔄 Veri Taşıma (Migration) Gerekliliği

Eğer malzeme ismini sadece "görünüm" olarak değiştiriyorsanız sorun yok. Ancak **yeni bir malzeme** gibi davranmasını istiyorsanız, eski kayıtlı verilerinizi kaybetmemek için bir Python betiği (script) ile veritabanındaki anahtarları (key) güncellemeniz gerekir.

**Örnek Senaryo:** `No:1` ismini `Orta Agrega` yapmak istiyorsunuz.
*   Kodlarda isimleri değiştirdiniz.
*   Programı açtığınızda eski projelerdeki `No:1` verileri görünmeyecektir.
*   Çözüm: `projects_merkez.json` dosyasındaki `"No:1"` anahtarlarını `"Orta Agrega"` olarak değiştiren bir script çalıştırılmalıdır.

---

## 2. Elek Serisini Değiştirmek

Elek boyutları `logic/engineering.py` dosyasında merkezi olarak tanımlanmıştır.

### 📍 Güncellenecek Dosya

*   **`logic/engineering.py`**
    *   **Değişken:** `SIEVE_SETS` sözlüğü.
    *   **Yapılacak:** İlgili Dmax (örneğin 31.5) için listeyi güncelleyin.
    *   **Dikkat:** Elekler **büyükten küçüğe** sıralı olmalıdır.

---

## 3. Standart Limitlerini (Eğrileri) Güncellemek

TS 802 standart eğrileri (A, B, C) `logic/engineering.py` dosyasında yer alır.

### 📍 Güncellenecek Dosya

*   **`logic/engineering.py`**
    *   **Değişken:** `STD_LIMITS` sözlüğü.
    *   **Yapı:** Her Dmax (31.5, 22.4 vb.) için `A`, `B`, `C` anahtarları altında limit değerleri bulunur.
    *   **Dikkat:** Buradaki değer sayısı, `SIEVE_SETS` içindeki elek sayısı ile **eşit** olmalıdır.

---

## 4. Beton Sınıfı Dayanım Hedeflerini Güncellemek

C30/37 vb. sınıfların hedef dayanımları ve renk kodları.

### 📍 Güncellenecek Dosya

*   **`logic/engineering.py`**
    *   **Değişken:** `CONCRETE_RULES` sözlüğü.
    *   **Yapılacak:** İlgili sınıfın `min_mpa`, `target_mpa` değerlerini güncelleyebilirsiniz.

---

## 5. Çevresel Etki Sınıflarını (XC, XF vb.) Düzenlemek

Etki sınıfları ve açıklamaları.

### 📍 Güncellenecek Dosya

*   **`logic/engineering.py`**
    *   **Değişken:** `EXPOSURE_CLASSES` sözlüğü.

---

## 💡 İpucu: Merkezi Yapılandırma (Öneri)

Gelecekte bu değişiklikleri tek bir yerden yapmak isterseniz, tüm bu sabit verileri `config.py` veya yeni bir `logic/constants.py` dosyasına taşıyıp, diğer tüm dosyalarda oradan import ederek kullanmak en iyi yazılım pratiğidir.

**Örnek `constants.py`:**
```python
MATERIALS_LIST = [
    "Kaba Elek (19-25)(15-25)", 
    "Orta Kaba (7-19)(5-15)", 
    "İnce No:1 (0-7)(0-5)", 
    "İnce No:2 (0-5)(0-7)"
]
```

**Kullanım:**
`from logic.constants import MATERIALS_LIST` (Tüm dosyalarda)
