import streamlit as st

class SessionStateInitializer:
    """
    Uygulamanın Session State (Oturum Durumu) değişkenlerini
    merkezi olarak başlatır ve varsayılan değerleri atar.
    Bu, 'KeyError' hatalarını önler ve dağınık başlatma kodlarını temizler.
    """
    @staticmethod
    def initialize_defaults():
        # 1. Genel Karışım Ayarları
        defaults = {
            "p1": 22, "p2": 16, "p3": 28, "p4": 34,
            "cimento_val": 350, 
            "su_val": 185, 
            "katki_val": 1.2,
            "cem_type": "CEM I 42.5 R",
            "ucucu_kul": 0.0,
            "hava_yuzde": 1.0,
            "proj_name_input": "ŞANLIURFA YÜREKLİ BETON",
            # Diğer widget key'leri
            "dmax_val": 31.5,
            "curve_type_val": "B (İdeal)",
            "elek_input_key": "31.5, 22.4, 16.0, 11.2, 8.0, 4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.063",
            "mix_snapshot": None,
            "last_mix_data": None,
            "last_decision": None,
            "exposure_class": "XC3",
            "asr_status": "Düzeltme Gerekmiyor (İnert)"
        }
        
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
                
        # 2. Malzeme Listesi ve Özellikleri (Tab 1)
        # 4 Malzeme varsayıyoruz: No:2, No:1, K.Kum, D.Kum
        def_rhos = [2.576, 2.472, 2.439, 2.650]
        def_was = [3.06, 4.64, 5.75, 1.20]
        
        for i in range(4):
            # Aktiflik Durumu
            k_act = f"act_{i}"
            if k_act not in st.session_state: 
                st.session_state[k_act] = True
            
            # Yoğunluk (Rho)
            k_rho = f"rho_{i}"
            if k_rho not in st.session_state: 
                st.session_state[k_rho] = def_rhos[i]
            
            # Su Emme (WA)
            k_wa = f"wa_{i}"
            if k_wa not in st.session_state: 
                st.session_state[k_wa] = def_was[i]
            
            # Los Angeles (LA) - Sadece ilk malzeme için varsayılan değer var
            k_la = f"la_{i}"
            if k_la not in st.session_state: 
                st.session_state[k_la] = 36.7 if i == 0 else 0.0

            # Metilen Mavisi (MB)
            k_mb = f"mb_{i}"
            if k_mb not in st.session_state: 
                st.session_state[k_mb] = 0.0
                
        # 3. Yüklenmiş Veriler (Loaded Data)
        if 'loaded_ri' not in st.session_state:
            st.session_state['loaded_ri'] = {}

    @staticmethod
    def load_project_data(project_name, plant_id="merkez"):
        """
        Seçilen projenin verilerini santral bazlı dosyadan okur ve session_state'e yükler.
        """
        from logic.data_manager import veriyi_yukle
        all_data = veriyi_yukle(plant_id=plant_id)
        p_data = all_data.get(project_name)
        
        if not p_data or not isinstance(p_data, dict):
            return

        # 1. Malzeme Özelliklerini (Tab 1) Eşle
        rhos = p_data.get("rhos", [])
        was = p_data.get("was", [])
        las = p_data.get("las", [])
        mbs = p_data.get("mbs", [])
        m1s = p_data.get("m1s", [])
        ri_dict = p_data.get("ri", {})
        active = p_data.get("active", [True, True, True, True])

        for i in range(len(rhos)):
            st.session_state[f"rho_{i}"] = rhos[i]
            st.session_state[f"wa_{i}"] = was[i]
            st.session_state[f"act_{i}"] = active[i]
            if i < len(las): st.session_state[f"la_{i}"] = las[i]
            if i < len(mbs): st.session_state[f"mb_{i}"] = mbs[i]
            if i < len(m1s): st.session_state[f"m1_{i}"] = m1s[i]
            
            # Data Editor State'ini temizle (Eski verilerin kalmaması için kritik)
            ed_key = f"ri_ed_{i}"
            if ed_key in st.session_state:
                del st.session_state[ed_key]
        
        # Elek kalan verileri (RI) - İndeks bazlı değil mat ismi bazlı saklama desteği
        st.session_state['loaded_ri'] = ri_dict if ri_dict else {}

        # 2. Karışım Oranlarını (Tab 2) Eşle
        p_ratios = p_data.get("p", [25, 25, 25, 25])
        for i, val in enumerate(p_ratios):
            st.session_state[f"p{i+1}"] = int(val)

        # 3. Reçete Değerlerini Eşle
        st.session_state["cimento_val"] = p_data.get("cim", 350)
        st.session_state["su_val"] = p_data.get("su", 185)
        st.session_state["katki_val"] = p_data.get("kat", 1.2)
        st.session_state["ucucu_kul"] = p_data.get("ucucu", 0.0)
        st.session_state["hava_yuzde"] = p_data.get("hava", 1.0)
        st.session_state["exposure_class"] = p_data.get("exp_class", "XC3")
        st.session_state["asr_status"] = p_data.get("asr_stat", "Düzeltme Gerekmiyor (İnert)")
        
        # 4. Tesis Adı (Widget tetiklemek için manuel set gerekebilir ama genelde text_input value= ile çözülür)
        # Ancak burada set etmek daha garanti
        # Note: plant_name widget key'i yoksa skip

def init_session_state():
    """
    app.py tarafından çağrılan kolay erişim fonksiyonu.
    """
    SessionStateInitializer.initialize_defaults()

