import streamlit as st
import pandas as pd
from logic.engineering import calculate_passing, calculate_fm, get_std_limits

def render_tab_grading(elek_serisi):
    """
    1. Fraksiyonel Deney Verileri (Tartım Esaslı)
    Returns:
        current_rhos, current_was, current_las, current_mbs, current_moists, computed_passing, active_mats, all_ri_values
    """
    st.subheader("1. Fraksiyonel Deney Verileri (Tartım Esaslı)")
    materials = ["Kaba Elek (19-25)(15-25)", "Orta Kaba (7-19)(5-15)", "İnce No:1 (0-7)(0-5)", "İnce No:2 (0-5)(0-7)"]
    current_rhos, current_was, current_las, current_mbs, current_moists = [], [], [], [], []
    computed_passing = {"Elek (mm)": elek_serisi}
    active_mats = []
    all_ri_values = {}
    
    col_f = st.columns(4)
    for i, (col, mat) in enumerate(zip(col_f, materials)):
        with col:
            act_k = f"act_{i}"
            is_active = st.checkbox(f"Dahil Et: {mat}", key=act_k)
            active_mats.append(is_active)
            m1_val = st.number_input(f"M1 (g)", value=4000.0 if i < 2 else 2000.0, key=f"m1_{i}", disabled=not is_active)
            rho_val = st.number_input("SSD Yoğunluk", format="%.3f", key=f"rho_{i}", disabled=not is_active)
            wa_val = st.number_input("Su Emme (%)", key=f"wa_{i}", disabled=not is_active)
            moist_val = st.number_input("Muhteva (%)", key=f"moist_{i}", disabled=not is_active, min_value=0.0, max_value=15.0, step=0.1)
            la_val = st.number_input("LA Aşınma (%)", key=f"la_{i}", disabled=not is_active)
            mb_val = st.number_input("MB Değeri", key=f"mb_{i}", disabled=not is_active)
            
            current_rhos.append(rho_val if is_active else 0)
            current_was.append(wa_val if is_active else 0)
            current_moists.append(moist_val if is_active else 0)
            current_las.append(la_val if is_active else 0)
            current_mbs.append(mb_val if is_active else 0)
            
            # Elek verileri
            ri_data = {"Elek": elek_serisi, "Kalan (g)": [0.0]*len(elek_serisi)}
            if 'loaded_ri' in st.session_state:
                 # Hem isim hem de index bazlı kontrol (Geriye dönük uyumluluk için)
                 saved_ri = st.session_state['loaded_ri'].get(mat) or st.session_state['loaded_ri'].get(i)
                 if saved_ri and len(saved_ri) == len(elek_serisi): 
                     ri_data["Kalan (g)"] = saved_ri
            
            ri_df = st.data_editor(pd.DataFrame(ri_data), hide_index=True, key=f"ri_ed_{i}", disabled=not is_active)
            mat_weights = ri_df.iloc[:, 1].tolist()
            all_ri_values[mat] = mat_weights
            computed_passing[mat] = calculate_passing(m1_val, mat_weights) if is_active else [0.0]*len(elek_serisi)
            
            # --- ÖZET ÖLÇÜM BİLGİSİ ---
            if is_active:
                sum_ret = sum(mat_weights)
                filler_g = m1_val - sum_ret
                filler_p = (filler_g / m1_val * 100) if m1_val > 0 else 0
                mat_fm = calculate_fm(elek_serisi, computed_passing[mat])
                
                st.caption(f"🔢 Toplam: {sum_ret:.1f}g | 🌪️ Pan/Filler: {filler_g:.1f}g (%{filler_p:.2f})")
                st.markdown(f"📐 **İncelik Modülü (İM): {mat_fm:.2f}**")

    st.session_state['computed_passing'] = computed_passing
    st.session_state['active_mats'] = active_mats
    
    # Sadece aktif olan malzemeleri tabloda göster
    disp_cols = ["Elek (mm)"] + [m for i, m in enumerate(materials) if active_mats[i]]
    df_disp = pd.DataFrame(computed_passing)[disp_cols]
    
    # --- ŞARTNAME (REFERANS) EKLE ---
    dmax_ref = st.session_state.get('dmax_select', 31.5)
    alt_b, _ = get_std_limits(dmax_ref, "B (İdeal)", elek_serisi)
    df_disp["Şartname"] = alt_b
    
    # --- DÜZENLENEBİLİRLİK HAKKI ---
    st.markdown("##### ✏️ Geometrik Düzeltme (Geçen Yüzdeleri Manuel Düzelt)")
    edited_df = st.data_editor(
        df_disp, 
        use_container_width=True, 
        hide_index=True, 
        key="material_passing_editor",
        disabled=["Elek (mm)", "Şartname"]
    )
    
    # Düzenlenen değerleri session state ve return değerine aktar
    for mat in disp_cols:
        if mat != "Elek (mm)" and mat != "Şartname":
            computed_passing[mat] = edited_df[mat].tolist()

    st.session_state['computed_passing'] = computed_passing
    st.session_state['active_mats'] = active_mats
    st.session_state['current_moists'] = current_moists
    
    return current_rhos, current_was, current_las, current_mbs, current_moists, computed_passing, active_mats, all_ri_values
