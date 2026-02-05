import streamlit as st

class SessionStateInitializer:
    """
    Uygulamanın Session State (Oturum Durumu) değişkenlerini
    merkezi olarak başlatır ve varsayılan değerleri atar.
    """
    @staticmethod
    def initialize_defaults(force=False):
        # 1. Genel Karışım Ayarları
        defaults = {
            "p1": 22, "p2": 16, "p3": 28, "p4": 34,
            "cimento_val": 350, 
            "su_val": 185, 
            "katki_val": 1.2,
            "cem_type": "CEM I 42.5 R",
            "ucucu_kul": 0.0,
            "hava_yuzde": 1.0,
            "proj_name_input": "Yeni Proje",
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
            if force or k not in st.session_state:
                st.session_state[k] = v
                
        def_rhos = [2.576, 2.472, 2.439, 2.650]
        def_was = [3.06, 4.64, 5.75, 1.20]
        
        for i in range(4):
            for k, v in {f"act_{i}": True, f"rho_{i}": def_rhos[i], f"wa_{i}": def_was[i], f"la_{i}": (36.7 if i == 0 else 0.0), f"mb_{i}": 0.0}.items():
                if force or k not in st.session_state:
                    st.session_state[k] = v
        
        if force or 'loaded_ri' not in st.session_state:
            st.session_state['loaded_ri'] = {}

    @staticmethod
    def clear_all_project_state(exclude_selection=False):
        """
        Tüm proje verilerini ve hesaplama sonuçlarını session_state'den siler.
        """
        all_keys = list(st.session_state.keys())
        fixed_keys = [
            'loaded_project_name', 'mix_snapshot', 'last_decision', 
            'computed_passing', 'last_mix_data', 'loaded_ri',
            'cimento_val', 'su_val', 'katki_val', 'cem_type', 'ucucu_kul', 
            'hava_yuzde', 'exposure_class', 'asr_status'
        ]
        
        for k in fixed_keys:
            if k in st.session_state: del st.session_state[k]
        
        for k in all_keys:
            if any(k.startswith(p) for p in ["rho_", "wa_", "la_", "mb_", "act_", "m1_", "ri_ed_", "p"]):
                if k in st.session_state: del st.session_state[k]
            
            if not exclude_selection and (k.startswith("proj_selector_") or k.startswith("trial_selector_")):
                if k in st.session_state: del st.session_state[k]
        
        if not exclude_selection:
            if 'loaded_project_id' in st.session_state: del st.session_state['loaded_project_id']
            if 'loaded_trial_id' in st.session_state: del st.session_state['loaded_trial_id']
            if 'proj_selector' in st.session_state: del st.session_state['proj_selector']

    @staticmethod
    def load_project_data(project_name, trial_name=None, plant_id="merkez"):
        """
        Seçilen projenin (ve denemenin) verilerini okur ve session_state'e yükler.
        """
        from logic.data_manager import veriyi_yukle
        
        # 0. Verileri temizle ama seçimi bırak ki döngüye girmesin
        SessionStateInitializer.clear_all_project_state(exclude_selection=True)
        SessionStateInitializer.initialize_defaults(force=True)

        all_data = veriyi_yukle(plant_id=plant_id)
        raw_p_data = all_data.get(project_name)
        
        if not raw_p_data or not isinstance(raw_p_data, dict):
            for i in range(4):
                ed_key = f"ri_ed_{i}"
                if ed_key in st.session_state: del st.session_state[ed_key]
            return

        # 1. Yapı Analizi (Nested mu yoksa Flat mı?)
        # Eğer 'trials' yoksa bu eski formatta bir projedir
        if "trials" not in raw_p_data:
            # Migration: Eski veriyi bir trial içine saralım
            p_data = raw_p_data
            active_trial = "Ana Reçete"
        else:
            # Yeni format: Trial seçimi varsa onu yükle, yoksa aktif olanı
            trials = raw_p_data.get("trials", {})
            active_trial = trial_name if trial_name and trial_name in trials else raw_p_data.get("active_trial", list(trials.keys())[0] if trials else "Ana Reçete")
            p_data = trials.get(active_trial, {})

        # 2. Veriyi Map Et
        SessionStateInitializer._map_data_to_state(p_data)
        
        # 3. Ek Bilgiler
        st.session_state['loaded_project_name'] = project_name
        st.session_state['active_trial_name'] = active_trial

    @staticmethod
    def _map_data_to_state(p_data):
        """Yardımcı fonksiyon: Saf veriyi session_state'e eşler."""
        rhos = p_data.get("rhos", [])
        was = p_data.get("was", [])
        las = p_data.get("las", [])
        mbs = p_data.get("mbs", [])
        m1s = p_data.get("m1s", [])
        ri_dict = p_data.get("ri", {})
        active = p_data.get("active", [True, True, True, True])

        for i in range(4):
            if i < len(rhos): st.session_state[f"rho_{i}"] = rhos[i]
            if i < len(was): st.session_state[f"wa_{i}"] = was[i]
            if i < len(active): st.session_state[f"act_{i}"] = active[i]
            if i < len(las): st.session_state[f"la_{i}"] = las[i]
            if i < len(mbs): st.session_state[f"mb_{i}"] = mbs[i]
            if i < len(m1s): st.session_state[f"m1_{i}"] = m1s[i]
            
            # Data Editor Reset
            ed_key = f"ri_ed_{i}"
            if ed_key in st.session_state: del st.session_state[ed_key]
        
        st.session_state['loaded_ri'] = ri_dict if ri_dict else {}

        # Karışım Oranları
        p_ratios = p_data.get("p", [25, 25, 25, 25])
        for i, val in enumerate(p_ratios):
            st.session_state[f"p{i+1}"] = int(val)

        # Reçete
        st.session_state["cimento_val"] = p_data.get("cim", 350)
        st.session_state["su_val"] = p_data.get("su", 185)
        st.session_state["katki_val"] = p_data.get("kat", 1.2)
        st.session_state["ucucu_kul"] = p_data.get("ucucu", 0.0)
        st.session_state["hava_yuzde"] = p_data.get("hava", 1.0)
        st.session_state["exposure_class"] = p_data.get("exp_class", "XC3")
        st.session_state["asr_status"] = p_data.get("asr_stat", "Düzeltme Gerekmiyor (İnert)")
        st.session_state["computed_passing"] = p_data.get("passing", {})

def init_session_state(force=False):
    """Session state baslaticisi. app.py tarafindan ana kontrol noktasidir."""
    SessionStateInitializer.initialize_defaults(force=force)
