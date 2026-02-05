import streamlit as st
import pandas as pd
import numpy as np
from logic.engineering import calculate_passing

def render_tab_1(elek_serisi):
    st.subheader("1. Fraksiyonel Deney Verileri (Tartım Esaslı)")
    materials = ["No:2 (15-25)", "No:1 (5-15)", "K.Kum (0-5)", "D.Kum (0-7)"]
    current_rhos, current_was, current_las, current_mbs, computed_passing, active_mats, all_ri_values = [], [], [], [], {"Elek (mm)": elek_serisi}, [], {}
    
    col_f = st.columns(4)
    for i, (col, mat) in enumerate(zip(col_f, materials)):
        with col:
            act_k = f"act_{i}"
            is_active = st.checkbox(f"Dahil Et: {mat}", key=act_k)
            active_mats.append(is_active)
            m1_val = st.number_input(f"M1 (g)", value=4000.0 if i < 2 else 2000.0, key=f"m1_{i}", disabled=not is_active)
            rho_val = st.number_input("SSD Yoğunluk", format="%.3f", key=f"rho_{i}", disabled=not is_active)
            wa_val = st.number_input("Su Emme (%)", key=f"wa_{i}", disabled=not is_active)
            la_val = st.number_input("LA Aşınma (%)", key=f"la_{i}", disabled=not is_active)
            mb_val = st.number_input("MB Değeri", key=f"mb_{i}", disabled=not is_active)
            
            current_rhos.append(rho_val if is_active else 0)
            current_was.append(wa_val if is_active else 0)
            current_las.append(la_val if is_active else 0)
            current_mbs.append(mb_val if is_active else 0)
            
            # Elek verileri
            ri_data = {"Elek": elek_serisi, "Kalan (g)": [0.0]*len(elek_serisi)}
            if 'loaded_ri' in st.session_state:
                 saved_ri = st.session_state['loaded_ri'].get(mat) or st.session_state['loaded_ri'].get(i)
                 if saved_ri and len(saved_ri) == len(elek_serisi): 
                     ri_data["Kalan (g)"] = saved_ri
            
            ri_df = st.data_editor(pd.DataFrame(ri_data), hide_index=True, key=f"ri_ed_{i}", disabled=not is_active)
            ri_values = ri_df["Kalan (g)"].tolist()
            all_ri_values[mat] = ri_values
            
            # Geçen yüzde hesapla
            if is_active and m1_val > 0:
                passing = calculate_passing(ri_values, m1_val)
                computed_passing[mat] = passing
    
    # Sonuçları göster
    if any(active_mats):
        st.subheader("📊 Birleşik Granülometri Eğrisi")
        passing_df = pd.DataFrame(computed_passing)
        passing_df["Elek (mm)"] = elek_serisi
        passing_df = passing_df.set_index("Elek (mm)")
        
        fig_passing = go.Figure()
        for mat in passing_df.columns:
            if mat != "Elek (mm)":
                fig_passing.add_trace(go.Scatter(
                    x=passing_df.index, y=passing_df[mat],
                    mode='lines+markers', name=mat, line=dict(width=2)
                ))
        
        fig_passing.update_layout(
            title="Fraksiyonel Geçme Yüzdeleri",
            xaxis=dict(
                title="Elek Açıklığı (mm) - Log Ölçek",
                type="log",
                tickvals=elek_serisi,
                ticktext=[str(s) for s in elek_serisi],
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis_title="Geçme Yüzdesi (%)",
            height=500,
            template="plotly_white"
        )
        st.plotly_chart(fig_passing, use_container_width=True)
        
        # Standart limitlerle karşılaştırma
        st.subheader("📏 Standart Granülometri Karşılaştırması")
        from logic.engineering import get_std_limits
        std_limits = get_std_limits()
        
        if std_limits:
            comparison_df = passing_df.copy()
            for limit_name, limit_data in std_limits.items():
                comparison_df[f"Std_{limit_name}"] = limit_data
            
            st.dataframe(comparison_df.round(1), use_container_width=True)
    
    return current_rhos, current_was, current_las, current_mbs, computed_passing, active_mats, all_ri_values
