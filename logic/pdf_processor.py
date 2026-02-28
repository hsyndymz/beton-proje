from pypdf import PdfReader
import streamlit as st
import os
import re
import requests

def extract_text_from_pdf(pdf_file):
    """PDF dosyasından metin ayıklar."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"PDF Okuma Hatası: {str(e)}"

def parse_concrete_design_with_ai(text, google_key=None, groq_key=None, deepseek_key=None):
    """
    Ayıklanan metni AI kullanarak teknik şemaya dönüştürür.
    Retry ve Hardened JSON parsing içerir.
    """
    if not text or len(text.strip()) < 50:
        return {"error": "PDF metni okunamadı veya çok kısa. PDF taranmış bir resim olabilir."}

    prompt_template = """
    Aşağıdaki metin bir beton karışım dizaynı (KGM Onaylı Reçete) belgesinden alınmıştır. 
    Lütfen bu metindeki teknik verileri bul ve SADECE aşağıdaki JSON formatında geri dön.
    Eğer bir veri bulunamazsa 0 veya null bırak. Sayıları sadece sayı olarak yaz (örn: 340, 0.45).
    ÖNEMLİ: Yanıt sadece JSON bloğu içermelidir, açıklama yapma.
    
    Beklenen JSON formatı:
    {
        "target_class": "Beton Sınıfı (Örn: C30/37)",
        "cement": 350.0,
        "water": 175.0,
        "ash": 0.0,
        "slag": 0.0,
        "air": 1.5,
        "admixture": 4.2,
        "d28": 38.5,
        "wc_ratio": 0.50,
        "aggregates": {
            "kum": 850.0,
            "ag1": 450.0,
            "ag2": 520.0,
            "ag3": 0.0
        }
    }

    Metin:
    \"\"\"{metin_parca}\"\"\"
    """
    
    metin_parca = text[:4000]
    prompt = prompt_template.replace("{metin_parca}", metin_parca)
    errors = []

    # --- 1. ADIM: GEMINI (With Multi-Retry) ---
    if google_key and str(google_key).strip():
        import time
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                if not response.text:
                    errors.append(f"Gemini (Deneme {attempt+1}): Boş yanıt.")
                    continue
                
                data = _parse_json_from_response(response.text)
                if data:
                    return _clean_concrete_data(data)
                errors.append(f"Gemini (Deneme {attempt+1}): Geçerli JSON ayıklanamadı.")
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg and attempt < max_retries:
                    st.warning(f"⚠️ Gemini kotası (429) doldu. {attempt+1}. deneme sonrası bekleniyor...")
                    time.sleep(6) # 429 için bekleme
                    continue
                errors.append(f"Gemini Hatası: {err_msg}")
                break
    else:
        errors.append("Gemini: API Anahtarı eksik.")

    # --- 2. ADIM: GROQ ---
    if groq_key and str(groq_key).strip():
        try:
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": "You are a specialized JSON extraction bot. Output only valid JSON."}, 
                             {"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                data = _parse_json_from_response(content)
                if data: 
                    st.info("✅ Groq üzerinden veri ayıklandı.")
                    return _clean_concrete_data(data)
                errors.append("Groq: JSON ayıklanamadı.")
            else:
                errors.append(f"Groq Hatası (Kod {resp.status_code})")
        except Exception as e:
            errors.append(f"Groq Hatası: {str(e)}")

    # --- 3. ADIM: DEEPSEEK ---
    if deepseek_key and str(deepseek_key).strip():
        try:
            actual_ds_key = str(deepseek_key).strip()
            if actual_ds_key.startswith("k-"): actual_ds_key = "s" + actual_ds_key
            headers = {"Authorization": f"Bearer {actual_ds_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                data = _parse_json_from_response(content)
                if data: return _clean_concrete_data(data)
                errors.append("DeepSeek: JSON ayıklanamadı.")
            else:
                errors.append(f"DeepSeek Hatası (Kod {resp.status_code})")
        except Exception as e:
            errors.append(f"DeepSeek Hatası: {str(e)}")

    # --- 4. ADIM: YEREL AI (OLLAMA) ---
    local_api = st.session_state.get('local_api_base', 'http://localhost:11434')
    local_model = st.session_state.get('local_model_name', 'llama3')
    
    # Yerel mod aktifse veya diğerleri başarısızsa ve kullanıcı yerel seçmişse dene
    # (Buradaki mantık: Eğer kullanıcı yerel seçmişse PDF taramada da onu denemeli)
    try:
        url = f"{local_api}/api/chat"
        payload = {
            "model": local_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.0}
        }
        resp = requests.post(url, json=payload, timeout=180)
        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            data = _parse_json_from_response(content)
            if data:
                st.info(f"✅ Yerel Model ({local_model}) ile veri ayıklandı.")
                return _clean_concrete_data(data)
            errors.append("Yerel AI: JSON ayıklanamadı.")
        elif resp.status_code == 404:
            errors.append(f"Yerel AI: '{local_model}' modeli bulunamadı. Lütfen 'ollama pull {local_model}' komutu ile indirin.")
        else:
            errors.append(f"Yerel AI Hatası (Kod {resp.status_code})")
    except Exception as e:
        errors.append(f"Yerel AI Bağlantı Hatası: {str(e)}")

    all_err_summary = " | ".join(errors)
    return {"error": f"Tüm servisler başarısız: {all_err_summary}"}

def _clean_concrete_data(data):
    """Beton tasarım verilerini temizler ve sayısal alanları doğrular."""
    if not isinstance(data, dict): return data
    
    numeric_keys = ["cement", "water", "ash", "slag", "air", "admixture", "d28", "wc_ratio"]
    
    # Ana sayısal alanları temizle
    for key in numeric_keys:
        if key in data:
            data[key] = _to_float(data[key])
        else:
            data[key] = 0.0
            
    # Agrega alanlarını temizle
    if "aggregates" in data and isinstance(data["aggregates"], dict):
        for ak in data["aggregates"]:
            data["aggregates"][ak] = _to_float(data["aggregates"][ak])
            
    return data

def _to_float(val):
    """Herhangi bir değeri float'a çevirmeye çalışır."""
    if val is None: return 0.0
    try:
        if isinstance(val, (int, float)): return float(val)
        s_val = str(val).replace(',', '.')
        nums = re.findall(r'\d+\.?\d*', s_val)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

def analyze_asr_risk_with_geological_ai(lithology, lat, lon, name, google_key=None, groq_key=None, deepseek_key=None):
    """
    Ocağın konumu ve litolojisine göre jeolojik ASR risk analizi yapar.
    """
    prompt = f"""
    Sen uzman bir Jeoloji ve Beton yapı malzemesi mühendisisin. 
    Aşağıdaki verilere göre bir agrega ocağının Alkali-Silika Reaksiyonu (ASR) riskini analiz et:

    OCAK ADI: {name}
    LİTOLOJİ: {lithology}
    KONUM (Lat/Lon): {lat}, {lon}

    Lütfen şu formatta (JSON) yanıt ver:
    {{
        "risk_level": "İnert" / "Potansiyel Reaktif" / "Yüksek Reaktif",
        "geological_insight": "Bölgenin jeolojik yapısına göre (örneğin Güneydoğu Anadolu formasyonları) kısa bir analiz.",
        "mitigation_suggestion": "Eğer risk varsa ne gibi önlemler alınmalı (Uçucu kül %?, Düşük alkalili çimento vb.)",
        "confidence_score": 0-100 arası bir güven puanı
    }}
    Yanıtı sadece JSON olarak ver.
    """
    
    errors = []

    # --- 1. GEMINI ---
    if google_key and str(google_key).strip():
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            data = _parse_json_from_response(response.text)
            if data: return data
            errors.append("Gemini: Geçerli JSON dönmedi.")
        except Exception as e:
            errors.append(f"Gemini Hatası: {str(e)}")
    else:
        errors.append("Gemini: API Anahtarı eksik.")

    # --- 2. GROQ ---
    if groq_key and str(groq_key).strip():
        try:
            import requests
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                text = resp.json()['choices'][0]['message']['content']
                data = _parse_json_from_response(text)
                if data: return data
                errors.append("Groq: JSON ayıklanamadı.")
            else:
                errors.append(f"Groq Hatası ({resp.status_code}): {resp.text[:50]}")
        except Exception as e:
            errors.append(f"Groq Hatası: {str(e)}")
    else:
        errors.append("Groq: API Anahtarı eksik.")

    # --- 3. DEEPSEEK ---
    if deepseek_key and str(deepseek_key).strip():
        try:
            import requests
            actual_ds_key = str(deepseek_key).strip()
            if actual_ds_key.startswith("k-"):
                actual_ds_key = "s" + actual_ds_key
            
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {actual_ds_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                text = resp.json()['choices'][0]['message']['content']
                data = _parse_json_from_response(text)
                if data: return data
                errors.append("DeepSeek: JSON ayıklanamadı.")
            else:
                errors.append(f"DeepSeek Hatası ({resp.status_code}): {resp.text[:50]}")
        except Exception as e:
            errors.append(f"DeepSeek Hatası: {str(e)}")
    else:
        errors.append("DeepSeek: API Anahtarı eksik.")

    # --- 4. YEREL AI (OLLAMA) ---
    local_api = st.session_state.get('local_api_base', 'http://localhost:11434')
    local_model = st.session_state.get('local_model_name', 'llama3')
    try:
        url = f"{local_api}/api/chat"
        payload = {
            "model": local_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            data = _parse_json_from_response(content)
            if data: return data
            errors.append("Yerel AI: JSON ayıklanamadı.")
        elif resp.status_code == 404:
            errors.append(f"Yerel AI: '{local_model}' modeli bulunamadı. Lütfen 'ollama pull {local_model}' komutu ile indirin.")
        else:
            errors.append(f"Yerel AI Hatası ({resp.status_code})")
    except Exception as e:
        errors.append(f"Yerel AI Bağlantı Hatası: {str(e)}")

    all_err_summary = " | ".join(errors)
    return {"error": f"ASR analizi yapılamadı: {all_err_summary}"}

def _parse_json_from_response(text):
    """Metin içindeki JSON bloğunu bulur ve temizler."""
    if not text: return None
    import json
    
    # Debug: Ham metni session state'e atalım (Son hata/başarıyı görebilmek için)
    st.session_state['last_ai_response'] = text
    
    # 0. Yorumları temizle (AI bazen JSON içine // veya # ile yorum ekler)
    # Satır sonu yorumlarını temizle
    clean_text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    clean_text = re.sub(r'#.*$', '', clean_text, flags=re.MULTILINE)
    
    # 1. Yol: Direkt Yükleme
    try:
        return json.loads(clean_text.strip())
    except:
        pass
        
    # 2. Yol: Markdown ve Regex Ayıklama
    try:
        clean_text = re.sub(r'```json\s*', '', clean_text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        
        json_match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            
            # JSON tamir denemeleri
            # Trailing commas: ,} -> }
            json_str = re.sub(r',\s*\}', '}', json_str)
            json_str = re.sub(r',\s*\]', ']', json_str)
            
            try:
                return json.loads(json_str)
            except:
                import ast
                try:
                    return ast.literal_eval(json_str)
                except:
                    pass
    except:
        pass
    return None
