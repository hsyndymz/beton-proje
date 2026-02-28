import streamlit as st
import pandas as pd
import numpy as np
from logic.engineering import (
    calculate_theoretical_mpa, evaluate_mix_compliance, 
    classify_plant, optimize_mix, generate_expert_suggestions
)
from logic.ai_model import predict_strength_ai, generate_suggestions, derive_local_engineering_constants
from logic.data_manager import havuz_yukle

def render_tab_2(proje, tesis_adi, hedef_sinif, litoloji, elek_serisi, materials, 
                  active_mats, current_rhos, current_was, current_las, current_mbs, 
                  current_site_factor, get_global_qc_history):
    st.subheader("2. Karışım Dizaynı ve Optimizasyon")
    
    # Yerel Otonom Zeka: Katsayı Türetme
    pool_data = havuz_yukle()
    local_const = derive_local_engineering_constants(pool_data)
    
    # Karışım parametreleri
    col_mix1, col_mix2 = st.columns(2)
    
    with col_mix1:
        st.markdown("#### 🎯 Temel Karışım Parametreleri")
        cimento_val = st.number_input("Çimento (kg/m³)", min_value=200, max_value=600, value=350, key="cimento_val")
        su_val = st.number_input("Su (lt/m³)", min_value=100, max_value=300, value=180, key="su_val")
        katki_val = st.number_input("Kimyasal Katkı (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1, key="katki_val")
        wc_ratio = su_val / cimento_val if cimento_val > 0 else 0
        
        st.metric("Su/Çimento Oranı", f"{wc_ratio:.3f}")
        
        # Hedef sınıfa göre uyarı (KGM 2016 Uyumlu)
        from logic.engineering import CONCRETE_RULES
        
        # Yol betonu limitleri (KGM 2016)
        is_yol = "Yol" in hedef_sinif
        max_wc = 0.45 if is_yol else CONCRETE_RULES.get(hedef_sinif, {}).get("max_wc", 0.55)
        min_cem = 350 if is_yol else CONCRETE_RULES.get(hedef_sinif, {}).get("min_cem", 260)
        
        if wc_ratio > max_wc:
            st.error(f"⚠️ W/C oranı {max_wc} üzerinde! {'(KGM 2016 Limit)' if is_yol else ''}")
        else:
            st.success(f"✅ W/C oranı uygun (≤ {max_wc})")
            
        if cimento_val < min_cem:
            st.error(f"⚠️ Çimento miktarı {min_cem} kg altında! {'(KGM 2016 Limit)' if is_yol else ''}")
        else:
            st.success(f"✅ Çimento miktarı yeterli (≥ {min_cem})")
    
    with col_mix2:
        st.markdown("#### 📊 Agrega Dağılımı")
        p_values = []
        total_p = 0
        
        for i, mat in enumerate(materials):
            if active_mats[i]:
                p_val = st.number_input(f"{mat} (%)", min_value=0, max_value=100, value=25, key=f"p{i+1}")
                p_values.append(p_val)
                total_p += p_val
        
        if total_p != 100 and total_p > 0:
            st.warning(f"⚠️ Toplam agrega yüzdesi: {total_p}% (100% olmalı)")
        elif total_p == 0:
            st.warning("⚠️ Hiç agrega seçilmedi")
    
    # Hava ve uçucu madde
    st.markdown("#### 🌬️ Hava ve Uçucu Maddeler")
    col_air1, col_air2 = st.columns(2)
    
    with col_air1:
        hava_yuzde = st.number_input("Hava İçeriği (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1, key="hava_yuzde")
    
    with col_air2:
        ucucu_kul = st.number_input("Uçucu Kül (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1, key="ucucu_kul")
    
    # Teorik dayanım hesabı
    st.markdown("#### 🔬 Teorik Dayanım Analizi")
    
    if all(active_mats) and cimento_val > 0:
        # AI model tahmini
        qc_history = get_global_qc_history(include_pool=True)
        
        if qc_history and len(qc_history) >= 5:
            from logic.ai_model import train_prediction_model
            coeffs, intercept, r2 = train_prediction_model(qc_history)
            
            if coeffs is not None:
                # Model inputları
                model_inputs = np.array([
                    cimento_val, su_val, ucucu_kul, hava_yuzde, katki_val
                ])
                
                pred_mpa = predict_strength_ai(coeffs, intercept, model_inputs)
                st.metric("🤖 AI Tahmini", f"{pred_mpa:.1f} MPa", delta=f"R²={r2:.3f}")
                
                # Hedefe göre optimizasyon önerileri
                target_mpa = CONCRETE_RULES[hedef_sinif]["min_mpa"]
                if pred_mpa < target_mpa:
                    suggestions = generate_suggestions(target_mpa, pred_mpa, model_inputs, coeffs)
                    if suggestions:
                        st.warning("💡 Optimizasyon Önerileri:")
                        for suggestion in suggestions:
                            st.info(f"• {suggestion}")
        
        # Teorik hesap
        theoretical_mpa = calculate_theoretical_mpa(wc_ratio, hava_yuzde, local_constants=local_const)
        
        st.metric("📈 Teorik Hesap", f"{theoretical_mpa:.1f} MPa")
        
        # Uygunluk değerlendirmesi için veri paketi hazırla
        mix_data = {
            "class": hedef_sinif,
            "wc": wc_ratio,
            "cement": cimento_val,
            "pred_mpa": theoretical_mpa,
            "avg_la": np.mean(current_las) if current_las else 0,
            "avg_mb": np.mean(current_mbs) if current_mbs else 0,
            "grading_violation": False, # Sieve analizi bu sekmede tam değil
            "asr_status": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor')
        }
        
        compliance = evaluate_mix_compliance(mix_data)
        
        # Durum göstergesi
        status_map = {"GREEN": ("🟢", "success"), "YELLOW": ("🟡", "warning"), "RED": ("🔴", "error")}
        icon, method = status_map.get(compliance["status"], ("❓", "info"))
        
        st.markdown(f"### {icon} Karışım Durumu: {compliance['title']}")
        st.write(compliance["main_msg"])
        
        if compliance["violations"]:
            for v in compliance["violations"]:
                st.error(v)
        
        if compliance["warnings"]:
            for w in compliance["warnings"]:
                st.warning(w)
                
                for r in compliance["rationales"]:
                    st.info(r)

        # AI Mühendislik Önerileri (Dinamik)
        expert_insights = generate_expert_suggestions(mix_data)
        if expert_insights:
            st.markdown("##### 🧬 AI Mühendislik Önerileri")
            for ins in expert_insights:
                with st.expander(f"🎯 {ins['topic']}", expanded=False):
                    st.error(f"**Sorun:** {ins['problem']}")
                    st.info(f"**Analiz:** {ins['rationale']}")
                    st.success(f"**Öneri:** {ins['solution']}")
    

    # Optimizasyon butonu
    st.markdown("---")
    col_opt1, col_opt2, col_opt3 = st.columns([1, 2, 1])
    
    with col_opt2:
        if st.button("🚀 Akıllı Optimizasyon", use_container_width=True, help="AI destekli karışım optimizasyonu"):
            if all(active_mats):
                with st.spinner("🧠 Optimizasyon hesaplanıyor..."):
                    optimized_mix = optimize_mix(
                        hedef_sinif, cimento_val, su_val, p_values, 
                        current_rhos, current_was, litoloji, current_site_factor
                    )
                    
                    if optimized_mix:
                        st.success("✅ Optimizasyon tamamlandı!")
                        st.json(optimized_mix)
                    else:
                        st.error("❌ Optimizasyon yapılamadı. Lütfen parametreleri kontrol edin.")
            else:
                st.error("❌ Lütfen önce malzeme verilerini girin.")
