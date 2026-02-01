import streamlit as st
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from logic.report_generator import generate_kgm_raporu
from logic.data_manager import (
    veriyi_yukle, veriyi_kaydet, havuz_yukle, havuz_kaydet, 
    tesis_faktor_yukle, tesis_faktor_kaydet, santralleri_yukle, santral_kaydet, santral_sil
)
from logic.engineering import (
    calculate_passing, calculate_theoretical_mpa, evaluate_mix_compliance, 
    classify_plant, get_std_limits, optimize_mix, update_site_factor,
    evolve_site_factor
)
from logic.intelligence import generate_smart_alerts, explain_ai_logic
from logic.corporate_logic import get_corp_performance_stats, calculate_cement_efficiency_stats, generate_risk_heatmap_data
from logic.ai_model import train_prediction_model, predict_strength_ai, generate_suggestions

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
                 # Hem isim hem de index bazlı kontrol (Geriye dönük uyumluluk için)
                 saved_ri = st.session_state['loaded_ri'].get(mat) or st.session_state['loaded_ri'].get(i)
                 if saved_ri and len(saved_ri) == len(elek_serisi): 
                     ri_data["Kalan (g)"] = saved_ri
            
            ri_df = st.data_editor(pd.DataFrame(ri_data), hide_index=True, key=f"ri_ed_{i}", disabled=not is_active)
            all_ri_values[mat] = ri_df.iloc[:, 1].tolist()
            computed_passing[mat] = calculate_passing(m1_val, ri_df.iloc[:, 1].tolist()) if is_active else [0.0]*len(elek_serisi)

    st.session_state['computed_passing'] = computed_passing
    st.session_state['active_mats'] = active_mats
    st.dataframe(pd.DataFrame(computed_passing).style.format(precision=2), use_container_width=True, hide_index=True)
    return current_rhos, current_was, current_las, current_mbs, computed_passing, active_mats, all_ri_values

def render_tab_2(proje, tesis_adi, hedef_sinif, litoloji, elek_serisi, materials, active_mats, 
                 current_rhos, current_was, current_las, current_mbs,
                 current_site_factor, get_global_qc_history):
    st.subheader("2. Karışım Oranları ve 1m³ Reçete")

    # --- OPTİMİZASYON TETİKLEYİCİ (Widget Hatasını Önleme & AI Motoru) ---
    if st.session_state.get('trigger_optimize'):
        dmax_opt = st.session_state.get('dmax_select', 31.5)
        curve_opt = st.session_state.get('target_curve_select', 'B (İdeal)')
        computed_opt = st.session_state.get('computed_passing', {})
        
        # 1. Gradasyon Optimizasyonu (Agrega Oranları)
        best_p = optimize_mix(curve_opt, dmax_opt, active_mats, computed_opt, elek_serisi, materials)
        if best_p is not None:
            active_indices = [i for i, x in enumerate(active_mats) if x]
            for k, idx in enumerate(active_indices):
                st.session_state[f"p{idx+1}"] = int(best_p[k])
            
            # 2. AI Tabanlı Çimento ve Su Optimizasyonu (Global Hafıza Kullanımı)
            pool_data = havuz_yukle()
            if len(pool_data) >= 5:
                # Başarılı projelerin ortalama W/C oranını bul
                from logic.engineering import best_wc_estimate
                ai_wc = best_wc_estimate(pool_data, hedef_sinif)
                if ai_wc:
                    # En son kullanılan su miktarını referans al veya standart 180L'den başla
                    ref_water = st.session_state.get('su_val', 180)
                    suggested_cem = int(ref_water / ai_wc)
                    # Limitlere çek (250-500 kg arası)
                    suggested_cem = max(250, min(500, suggested_cem))
                    st.session_state['cimento_val'] = suggested_cem
                    st.session_state['su_val'] = ref_water
                    st.success(f"🤖 **AI Analizi:** '{hedef_sinif}' için benzer başarılı projelerdeki W/C={ai_wc} baz alınarak Çimento={suggested_cem} kg olarak güncellendi.")
            
            st.session_state.pop('trigger_optimize')
            st.success("🎯 Optimizasyon tamamlandı! Tüm değerler senkronize edildi.")
            st.rerun()
        else:
            st.error("Optimizasyon başarısız oldu. Lütfen aktif malzemeleri kontrol edin.")
            st.session_state.pop('trigger_optimize')

    # Karışım Ayarları (Dinamik Seçiciler)
    c_hdr1, c_hdr2 = st.columns(2)
    with c_hdr1:
        dmax_val = st.selectbox("Dmax (mm)", [31.5, 22.4, 16.0], index=0, key="dmax_select")
    with c_hdr2:
        target_curve = st.selectbox("Hedef Eğri", ["A (Alt)", "B (İdeal)", "C (Üst)"], index=1, key="target_curve_select")

    # Karışım Geçen Hesapla (Sliders)
    st.markdown("##### 🧪 Agrega Harman Oranları (%)")
    c_sld1, c_sld2, c_sld3, c_sld4 = st.columns(4)
    with c_sld1: p1 = st.slider(f"{materials[0]}", 0, 100, key="p1")
    with c_sld2: p2 = st.slider(f"{materials[1]}", 0, 100, key="p2")
    with c_sld3: p3 = st.slider(f"{materials[2]}", 0, 100, key="p3")
    with c_sld4: p4 = st.slider(f"{materials[3]}", 0, 100, key="p4")
    
    computed_passing = st.session_state.get('computed_passing', {})
    karisim_gecen = np.zeros(len(elek_serisi))
    for i, p in enumerate([p1, p2, p3, p4]):
        mat_name = materials[i]
        if active_mats[i] and mat_name in computed_passing:
            karisim_gecen += (np.array(computed_passing[mat_name]) * p / 100.0)

    st.markdown("---")
    c_wc_sets, c_grad_plot = st.columns([1, 1])
    with c_wc_sets:
        st.markdown("##### 💧 Su / Çimento Ayarları")
        selected_cem = st.selectbox("Çimento Tipi", ["CEM I 42.5 R", "CEM I 52.5 R", "CEM II/A-LL 42.5 R", "CEM IV/B (P) 32.5 N", "SR"], key="cem_type")
        cimento = st.number_input("Çimento (kg/m³)", key='cimento_val')
        su_hedef = st.number_input("Net Su (L/m³)", key='su_val')
        katki = st.number_input("Plastikleştirici Katkı (%)", key='katki_val')
        hava_katki_yuzde = st.number_input("Hava Sürükleyici Katkı (%)", value=0.0, step=0.01, format="%.3f", key='hava_katki_yuzde')
        ucucu_kul = st.number_input("Uçucu Kül (kg/m³)", value=0.0, key='ucucu_kul')
        hava_yuzde = st.number_input("Hedef Hava Miktarı (%)", value=1.0, step=0.1, key='hava_yuzde')

        if cimento > 0:
            wc_ratio_eff = su_hedef / (cimento + (0.35 * ucucu_kul))
            theo_mpa = calculate_theoretical_mpa(wc_ratio_eff, hava_yuzde)
            # Litoloji Katsayısı Uygula
            from logic.engineering import LITHOLOGY_FACTORS
            lith_factor = LITHOLOGY_FACTORS.get(litoloji, 1.0)
            predicted_mpa = theo_mpa * current_site_factor * lith_factor
            
            # --- TAHMİN BİLGİLERİ ---
            st.markdown("---")
            st.info(f"**Tahmin Edilen Dayanım (28 Gün):** {predicted_mpa:.1f} MPa")
            if lith_factor != 1.0:
                st.caption(f"ℹ️ Litoloji Aderans Etkisi: x{lith_factor:.2f} ({litoloji})")
            st.write(f"Saha Faktörü: x{current_site_factor:.3f} | {tesis_adi}")
            
            # Global AI Brain (Automatic check)
            pool_data = havuz_yukle()
            if len(pool_data) >= 5:
                g_coeffs, g_intercept, g_r2 = train_prediction_model(pool_data)
                if g_coeffs is not None:
                    katki_kg_val = (cimento * katki / 100)
                    g_inputs = np.array([float(cimento), float(su_hedef), float(ucucu_kul), float(hava_yuzde), float(katki_kg_val)])
                    g_pred = predict_strength_ai(g_coeffs, g_intercept, g_inputs)
                    st.success(f"🌐 **Global AI Tahmini:** {g_pred:.1f} MPa")
        else: wc_ratio_eff, predicted_mpa = 0.6, 0.0

    with c_grad_plot:
        fig = go.Figure()
        
        # Standart Eğrileri Çek (A, B, C)
        alt_a, _ = get_std_limits(dmax_val, "A (Kaba)", elek_serisi)
        alt_b, _ = get_std_limits(dmax_val, "B (İdeal)", elek_serisi)
        alt_c, _ = get_std_limits(dmax_val, "C (İnce)", elek_serisi)

        # 1. Min (A Eğrisi) - Mavi
        fig.add_trace(go.Scatter(x=elek_serisi, y=alt_a, mode='lines+markers', name='Min (A)', line=dict(color='#1e3a8a', width=2), marker=dict(symbol='square', size=6)))
        # 2. Ort (B Eğrisi) - Yeşil
        fig.add_trace(go.Scatter(x=elek_serisi, y=alt_b, mode='lines+markers', name='Ort (B)', line=dict(color='#15803d', width=2), marker=dict(symbol='diamond', size=6)))
        # 3. Max (C Eğrisi) - Mor/Lacivert
        fig.add_trace(go.Scatter(x=elek_serisi, y=alt_c, mode='lines+markers', name='Max (C)', line=dict(color='#6b21a8', width=2), marker=dict(symbol='triangle-up', size=6)))
        # 4. Tasarım (Karma) - Kırmızı (Ön Planda)
        fig.add_trace(go.Scatter(x=elek_serisi, y=karisim_gecen, mode='lines+markers', name='Karışım', line=dict(color='#dc2626', width=4), marker=dict(symbol='circle', size=8)))
        
        fig.update_layout(
            title=f"Dmax {dmax_val} mm. Gradasyon Eğrisi",
            paper_bgcolor='white', plot_bgcolor='white',
            margin=dict(l=40, r=20, t=60, b=40),
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            font=dict(family="Arial", size=12)
        )
        
        # Ekseleri Düzenle (Logaritmik x, Ters Çevrilmiş, Gridli)
        fig.update_xaxes(
            type='log', 
            title='Elek Boyutu (mm)', 
            autorange="reversed", 
            gridcolor='#d1d5db', 
            linecolor='black',
            tickvals=[0.063, 0.15, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 11.2, 16.0, 22.4, 31.5, 40.0],
            ticktext=["0.063", "0.15", "0.25", "0.5", "1", "2", "4", "8", "11.2", "16", "22.4", "31.5", "40"]
        )
        fig.update_yaxes(
            title='Elekten Geçen % (Yığışımlı)', 
            range=[0, 105], 
            gridcolor='#d1d5db', 
            linecolor='black',
            dtick=10
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- HESAPLA VE KİLİTLE BUTONU VE SONUÇLAR ---
    st.divider()
    if st.button("🧮 Dizaynı Hesapla ve Kilitle", type="primary", use_container_width=True):
        active_p = st.session_state.get('active_plant', 'merkez')
        all_qc_data = veriyi_yukle(plant_id=active_p)
        proj_history = all_qc_data.get(proje, {}).get("qc_history", [])
        
        # --- GLOBAL AI FALLBACK ---
        # Eğer bu projenin yerel verisi azsa (<5), global havuzdan destek al
        training_data = proj_history
        if len(proj_history) < 5:
            pool_data = havuz_yukle()
            if pool_data:
                # Hem yerel (varsa) hem global veriyi birleştir
                training_data = proj_history + pool_data
        
        model_coeffs, intercept, r2_score = train_prediction_model(training_data)
        
        # Karar ve Analiz
        current_inputs = np.array([cimento, su_hedef, ucucu_kul, hava_yuzde, (cimento*katki/100)])
        # Kullanıcının seçtiği hedef eğriyi ve dmax'ı kullan
        t_alt, t_ust = get_std_limits(dmax_val, target_curve, elek_serisi)
        
        grade_violation = False
        grade_dev_total = 0.0
        for i, sieve in enumerate(elek_serisi):
            passing = karisim_gecen[i]
            if sieve < 0.1: continue
            diff = max(0, t_alt[i] - passing) + max(0, passing - t_ust[i])
            if diff > 1.0:
                grade_dev_total += diff
                if diff > 3.0: grade_violation = True

        total_ratio = 100
        w_la = (current_las[0]*p1 + current_las[1]*p2 + current_las[2]*p3 + current_las[3]*p4) / total_ratio
        w_mb = (current_mbs[0]*p1 + current_mbs[1]*p2 + current_mbs[2]*p3 + current_mbs[3]*p4) / total_ratio
        
        comp_data = {
            "class": hedef_sinif, "wc": wc_ratio_eff, "pred_mpa": predicted_mpa,
            "grading_violation": grade_violation, "grading_dev": grade_dev_total,
            "lithology": litoloji, "cement": cimento, "air": hava_yuzde,
            "wa_risk": any([w > 2.0 for w in current_was if w > 0]),
            "avg_la": w_la, "avg_mb": w_mb,
            "exposure_class": st.session_state.get('exposure_class', 'XC3'),
            "asr_status": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor')
        }
        decision = evaluate_mix_compliance(comp_data)
        st.session_state['last_decision'] = decision

        # Hacim ve Reçete
        vol_cem = cimento / 3.15
        vol_water = su_hedef / 1.0
        vol_ash = ucucu_kul / 2.25
        vol_air = hava_yuzde * 10
        vol_chem = (cimento * katki / 100) / 1.12
        V_agg_tot = 1000 - (vol_cem + vol_water + vol_ash + vol_air + vol_chem)
        m_kgs = [V_agg_tot * (p/100) * r for p, r in zip([p1,p2,p3,p4], current_rhos)]

        # Snapshot
        st.session_state['mix_snapshot'] = {
            "project_name": proje, 
            "plant_name": tesis_adi, 
            "mix_data": comp_data.copy(),
            "decision": decision, 
            "recipe": {
                "çimento": cimento, "su": su_hedef, "kül": ucucu_kul, 
                "katkı": round(cimento * katki / 100, 2), "hava": hava_yuzde,
                "agrega_miktarları": {mat: round(m_kgs[i], 1) for i, mat in enumerate(materials) if active_mats[i]}
            },
            "material_data": {
                "rhos": current_rhos, "was": current_was, 
                "las": current_las, "mbs": current_mbs, "active": active_mats
            }, 
            "sieves": elek_serisi.copy(),
            "passing": karisim_gecen.tolist(), 
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # --- AI MÜHENDİSLİK VE LİTOLOJİK DEĞERLENDİRME (Görsel Panel) ---
        st.markdown("### 🧠 AI Mühendislik ve Litolojik Değerlendirme")
        
        # Su Telafisi Hesaplama
        total_agg_kg = sum(m_kgs)
        weighted_wa = (current_was[0]*p1 + current_was[1]*p2 + current_was[2]*p3 + current_was[3]*p4) / total_ratio
        wa_liters = (weighted_wa / 100) * total_agg_kg
        
        # 1. Su Telafisi Analizi Kutusu
        st.info(f"💧 **Su Telafisi Analizi:**\n\nSeçilen aktif malzemelere göre karma agrega su emme oranı: **%{weighted_wa:.2f}**\n\nAgregaların 1m³ betonda bünyesine çekeceği toplam su: **{wa_liters:.1f} Litre**")

        c_eval1, c_eval2 = st.columns(2)
        with c_eval1:
            st.markdown("##### 🏗️ Yapısal Durum")
            # Aşınma Kartı
            if w_la > 35:
                st.error(f"❌ **Aşınma:** LA %{w_la:.1f} yüksek.")
            elif w_la > 30:
                st.warning(f"⚠️ **Aşınma:** LA %{w_la:.1f} sınırda.")
            else:
                st.success(f"✅ **Aşınma:** LA %{w_la:.1f} uygun.")
            
            # Gradasyon Kartı
            if grade_violation:
                st.error(f"❌ **Gradasyon:** {dmax_val}mm limitleri dışı.")
            elif grade_dev_total > 1.0:
                st.warning(f"⚠️ **Gradasyon:** Standart bölge sınırında.")
            else:
                st.success(f"✅ **Gradasyon:** TS 802'ye tam uygun.")

        with c_eval2:
            st.markdown("##### 🧪 Kimyasal Analiz")
            # MB Kartı
            if w_mb > 1.5:
                st.error(f"❌ **MB Uyarısı:** {w_mb:.2f} g/kg yüksek!")
            elif w_mb > 1.0:
                st.warning(f"⚠️ **MB Uyarısı:** {w_mb:.2f} g/kg (Kil riski).")
            else:
                st.success(f"✅ **MB Temizliği:** {w_mb:.2f} g/kg ideal.")
                
            # Litoloji Kartı
            st.info(f"💡 **Litoloji:** {litoloji} karakteristiği inceleniyor.")

        # --- YENİ KTŞ & BETON YOL DENETİMİ (0.063mm ve 4mm) ---
        st.markdown("##### 🛣️ KTŞ & Beton Yol Gradasyon Hassasiyeti")
        c_kts1, c_kts2 = st.columns(2)
        
        # 0.063mm (Filler) Oranı - Index 12
        filler_val = karisim_gecen[12]
        with c_kts1:
            if filler_val > 3.0:
                st.error(f"❌ **Filler (<0.063mm):** %{filler_val:.2f} (Max %3 olmalı!)")
            elif filler_val > 2.0:
                st.warning(f"⚠️ **Filler (<0.063mm):** %{filler_val:.2f} (Sınırda)")
            else:
                st.success(f"✅ **Filler (<0.063mm):** %{filler_val:.2f} (Uygun)")
        
        # 4mm (Kum) Oranı - Index 6
        sand_val = karisim_gecen[6]
        with c_kts2:
            if sand_val < 33.0 or sand_val > 42.0:
                st.error(f"❌ **Kum (<4mm):** %{sand_val:.1f} (KTŞ: %33-42 arası)")
            elif sand_val < 35.0 or sand_val > 40.0:
                st.warning(f"⚠️ **Kum (<4mm):** %{sand_val:.1f} (İdeal dışı)")
            else:
                st.success(f"✅ **Kum (<4mm):** %{sand_val:.1f} (İdeal)")

        # --- 3. DURABİLİTE VE ASR ANALİZİ (YENİ BÖLÜM) ---
        st.markdown("##### 🌋 Durabilite ve ASR Analizi")
        c_dur1, c_dur2 = st.columns(2)
        with c_dur1:
            exp_val = st.session_state.get('exposure_class', 'XC3')
            # Evaluate durability against exposure class inside the UI for visual feedback
            from logic.engineering import EXPOSURE_CLASSES
            e_lim = EXPOSURE_CLASSES.get(exp_val, {})
            if wc_ratio_eff > e_lim.get('max_wc', 1.0) or cimento < e_lim.get('min_cem', 0):
                st.error(f"❌ **Maruziyet ({exp_val}):** Limitler ihlal edildi!")
            else:
                st.success(f"✅ **Maruziyet ({exp_val}):** KTŞ/EN 206 uyumlu.")
        
        with c_dur2:
            asr_val = st.session_state.get('asr_status', 'İnert')
            if "Reaktif" in asr_val:
                st.warning(f"⚠️ **ASR Riski:** {asr_val}. Önlem alınmalı!")
            else:
                st.success(f"✅ **ASR Riski:** {asr_val} (Güvenli).")

        # Sonuç Özeti
        st.markdown("---")
        c_res1, c_res2 = st.columns([1, 1])
        with c_res1:
            st.subheader("📋 Analiz Sonuçları")
            if decision['status'] == "RED":
                st.error(f"### {decision['title']}\n{decision['main_msg']}")
            elif decision['status'] == "YELLOW":
                st.warning(f"### {decision['title']}\n{decision['main_msg']}")
            else:
                st.success(f"### {decision['title']}\n{decision['main_msg']}")
            
            for r in decision.get("rationales", []):
                st.info(f"💡 {r}")
            
        with c_res2:
            st.markdown("### 📋 1m³ Reçete")
            katki_kg = round(cimento * katki / 100, 2)
            hava_katki_kg = round(cimento * hava_katki_yuzde / 100, 3)
            rec_tab = {
                "Bileşen": ["Çimento", "Su", "Uçucu Kül", "Kimyasal Katkı", "Hava Sürükleyici", "Hava (Hacim)"], 
                "Miktar": [
                    round(cimento, 1), round(su_hedef, 1), round(ucucu_kul, 1), 
                    katki_kg, hava_katki_kg, f"%{hava_yuzde:.1f}"
                ]
            }
            for i, mat in enumerate(materials):
                if active_mats[i]: 
                    rec_tab["Bileşen"].append(mat)
                    rec_tab["Miktar"].append(round(m_kgs[i], 1))
            st.table(pd.DataFrame(rec_tab))

    # Optimizasyon Butonu
    if st.button("⚡ EN İYİ KARIŞIMI BUL (HEDEFE GÖRE)", type="secondary", use_container_width=True):
        st.session_state['trigger_optimize'] = True
        st.rerun()

    # Global AI Bölümü (Temizlendi, yukarıya otomatik alındı)
    st.divider()

def render_tab_3(proje, selected_provider, TS_STANDARDS_CONTEXT):
    st.header(f"🧠 {selected_provider} - Profesyonel Teknik Rapor")
    
    if 'mix_snapshot' not in st.session_state or st.session_state['mix_snapshot'] is None:
        st.warning("⚠️ Rapor oluşturmak için önce 'Karışım Dizaynı' sekmesinde hesaplama yapmalısınız.")
        return

    snap = st.session_state['mix_snapshot']
    s_mix = snap['mix_data']
    decision = snap['decision']

    # --- 1. ÖN BİLGİLER VE RAPOR METADATA ---
    st.markdown("### 📋 Resmî Rapor Bilgileri")
    
    with st.expander("✒️ Rapor Kapak Bilgilerini Düzenle", expanded=True):
        c_meta1, c_meta2 = st.columns(2)
        with c_meta1:
            employer = st.text_input("İdare Adı", value="T.C. ULAŞTIRMA VE ALTYAPI BAKANLIĞI", key="rep_employer")
            contractor = st.text_input("Yüklenici Adı", value="YÜKLENİCİ FİRMA A.Ş.", key="rep_contractor")
        with c_meta2:
            revision_no = st.text_input("Revizyon No", value="R0", key="rep_rev")
            report_date = st.date_input("Rapor Tarihi", value=datetime.datetime.now())
    
    # Snapshot'ı metadata ile güncelle
    snap['employer'] = employer
    snap['contractor'] = contractor
    snap['revision'] = revision_no
    snap['report_date'] = report_date.strftime("%d-%m-%Y")

    st.markdown("---")
    st.markdown("#### 📑 Dizayn Özeti ve Teknik Uygunluk")

    # --- YENİ: ANALİTİK VERİ İNCELEMESİ (Sistematik Analiz) ---
    st.markdown("#### 🔬 Analitik Veri İncelemesi")
    c_ana1, c_ana2, c_ana3 = st.columns(3)
    
    # W/C Verimliliği
    wc_val = s_mix.get('wc', 0)
    with c_ana1:
        st.metric("Su/Çimento Oranı", f"{wc_val:.2f}", delta="-İdeal" if 0.40 <= wc_val <= 0.50 else "Riskli", delta_color="normal")
    
    # Filler Oranı
    filler_val = snap.get('passing', [])[12] if len(snap.get('passing', [])) > 12 else 0
    with c_ana2:
        st.metric("Filler Oranı (<0.063)", f"%{filler_val:.2f}", delta="Uygun" if filler_val <= 3.0 else "Yüksek", delta_color="inverse")
        
    # Agrega Matrisi (Kum Oranı)
    sand_val = snap.get('passing', [])[6] if len(snap.get('passing', [])) > 6 else 0
    with c_ana3:
        st.metric("Kum Oranı (<4mm)", f"%{sand_val:.1f}", delta="Stabil" if 33 <= sand_val <= 42 else "Dengesiz")

    # Uyarılar ve Gerekçeler (Geliştirildi)
    if decision['violations'] or decision['warnings'] or decision.get('rationales'):
        st.markdown("#### ⚠️ Teknik Bulgular ve Gerekçeler")
        for v in decision['violations']: st.error(v)
        for w in decision['warnings']: st.warning(w)
        
        # Mühendislik Gerekçelerini her zaman göster (Kullanıcı Talebi)
        if decision.get('rationales'):
            with st.expander("🔬 Derinlemesine Mühendislik Analizi (Neden?)", expanded=True):
                for r in decision.get('rationales', []):
                    st.info(f"💡 {r}")

    # --- 2. RESMİ SANTRAL RAPORU ---
    st.divider()
    plant_display_name = snap.get('plant_name', 'KGM')
    st.subheader(f"🇹🇷 {plant_display_name} Resmi Beton Kontrol Raporu")
    if st.button(f"📄 {plant_display_name.upper()} RAPORU (PDF/HTML) OLUŞTUR", use_container_width=True):
        try:
            html_report = generate_kgm_raporu(snap)
            st.components.v1.html(html_report, height=600, scrolling=True)
            st.download_button("📥 Raporu .html Olarak İndir", html_report, file_name=f"KGM_Rapor_{proje}.html", mime="text/html")
        except Exception as e:
            st.error(f"Rapor oluşturulurken hata: {e}")

    # --- 3. AI TEKNİK RAPOR ---
    st.divider()
    st.subheader("🤖 AI Teknik Rapor Oluşturucu")
    st.caption("Bu bölüm, verileri teknik bir makale dilinde özetler.")
    
    if st.button("🪄 AI İle Teknik Özet Yazdır"):
        # Elek Analizi Metni
        sieve_data = ", ".join([f"{s}mm: %{p:.1f}" for s, p in zip(snap['sieves'], snap['passing'])])
        recipe_text = f"Çimento: {snap['recipe']['çimento']}kg, Su: {snap['recipe']['su']}L, Kül: {snap['recipe']['kül']}kg, Katkı: {snap['recipe']['katkı']}kg. Agregalar: {snap['recipe']['agrega_miktarları']}"
        
        prompt = f"""
        BİRİNCİL GÖREV: Aşağıdaki beton dizayn verilerini SİSTEMATİK ve ANALİTİK bir yaklaşımla, 'Baş Mühendis' perspektifinden analiz et. 
        Analizini rastgele cümlelerle değil, aşağıdaki yapılandırmaya (Mühendislik Protokolü) göre oluştur.

        ANALİZ YAPISI (BU SIRAYLA OLACAK):
        1. TEKNİK ÖZET: Dizaynın genel başarısı ve hedeflenen dayanım sınıfı ({s_mix['class']}) ile uyumu.
        2. SU/ÇİMENTO VE DAYANIKLILIK (DURABİLİTE) ANALİZİ: W/C oranının ({s_mix['wc']}) TS EN 206 kısıtları ve betonun servis ömrü (korozyon, karbonatlaşma) açısından değerlendirilmesi.
        3. GRADASYON VE KOMPAKTLIK: 4mm altı kum oranı (%{sand_val:.1f}) ve 0.063mm filler miktarının (%{filler_val:.2f}) taze beton işlenebilirliği ve boşluk yapısı üzerindeki etkisi.
        4. MALZEME RİSKLERİ: Litolojik köken ({s_mix['lithology']}) ile LA Aşınma (%{s_mix['avg_la']:.1f}) ve MB Kirlilik ({s_mix['avg_mb']:.2f}) değerlerinin mekanik performans üzerindeki korelasyonu.
        5. NİHAİ MÜHENDİSLİK GÖRÜŞÜ: Karışımın spesifik kullanım alanı (Beton yol/Yapısal beton) için onay durumu ve optimizasyon önerileri.

        VERİ SETİ DETAYLARI:
        - Standartlar: {TS_STANDARDS_CONTEXT}
        - Proje/Tesis: {snap['project_name']} / {snap['plant_name']}
        - Tahmin Edilen Dayanım: {s_mix['pred_mpa']} MPa
        - Reçete: {recipe_text}
        - Karma Gradasyon: {sieve_data}
        - Karar Sonucu: {decision['status']} ({decision['main_msg']})
        
        FORMAT: Teknik rapor dili kullan. Paragraflar arası başlıklar koy. Duygusal ifadelerden kaçın, tamamen sayısal verilere ve standartlara dayalı analitik bir dil kullan.
        """
        st.info("AI Raporu oluşturuluyor... (Yan paneldeki API anahtarı kullanılır)")
        # This part will be handled by returning a request or directly if we pass the model.
        # For simplicity, we keep the AI prompt generation in app.py or pass it as a callback.
        st.session_state['ai_report_prompt'] = prompt
        st.rerun()

    if 'ai_report_output' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state['ai_report_output'])

def render_tab_4(proje, tesis_adi, TARGET_LIMITS, hedef_sinif, get_global_qc_history, is_admin=False):
    # Verileri Yükle
    active_p = st.session_state.get('active_plant', 'merkez')
    all_data_json = veriyi_yukle(plant_id=active_p)
    proj_data = all_data_json.get(proje, {})
    qc_history = proj_data.get("qc_history", [])
    current_site_factor = tesis_faktor_yukle(tesis_adi, plant_id=active_p)
    
    # --- SAHA AKLI (LEARNING SYSTEM) ---
    global_qc_hist = get_global_qc_history()
    plant_class, plant_color = classify_plant(global_qc_hist)
    
    # Dinamik Saha Faktörü Gelişimi
    evolved_factor = evolve_site_factor(qc_history, current_site_factor)
    if evolved_factor != current_site_factor:
        tesis_faktor_kaydet(tesis_adi, evolved_factor, plant_id=active_p)
        current_site_factor = evolved_factor

    st.info(f"**🏭 Santral Profili (Saha Aklı):** {plant_class} | **{tesis_adi} Saha Faktörü:** x{current_site_factor:.3f}")

    # Akıllı Uyarılar Paneli
    smart_alerts = generate_smart_alerts(qc_history, proj_data)
    if smart_alerts:
        with st.container():
            st.markdown("### 🧠 Mühendislik Akıllı Uyarıları")
            for alert in smart_alerts:
                with st.expander(alert['title']):
                    st.write(alert['msg'])
                    if st.button(f"🔍 Neden?", key=f"why_{alert['id']}"):
                        reason = explain_ai_logic(alert['id'])
                        st.info(f"**AI Analizi:** {reason}")
                    st.caption(f"Dayanak: {alert['rationale']}")

    # --- 1. VERİ GİRİŞ FORMU ---
    with st.expander("➕ Yeni Numune Kaydı / Kırım Verisi Ekle", expanded=len(qc_history) == 0):
        if st.button("📋 Mevcut Dizayndan Bilgileri Kopyala"):
            if 'mix_snapshot' in st.session_state:
                snap = st.session_state['mix_snapshot']
                m_data = snap['mix_data']
                st.session_state['qc_cem'] = m_data.get('cement', 350)
                st.session_state['qc_wat'] = m_data.get('water', 180)
                st.session_state['qc_ash'] = m_data.get('ash', 0)
                st.session_state['qc_air'] = m_data.get('air', 1.5)
                st.session_state['qc_chem'] = m_data.get('chem_kg', 4.0)
                st.session_state['qc_pred'] = m_data.get('pred_mpa', 0.0)
                st.success("Dizayn verileri forma çekildi!")
                st.rerun()
            else:
                st.warning("Önce 'Karışım Dizaynı' sekmesinde hesaplama yapmalısınız.")

        c1, c2, c3 = st.columns(3)
        with c1:
            qc_date = st.date_input("Döküm Tarihi", key="qc_date")
            qc_no = st.text_input("Numune No / Kod", value=f"N-{len(qc_history)+1}", key="qc_no")
            qc_d7 = st.number_input("7 Günlük (MPa)", value=0.0, key="qc_d7")
        with c2:
            qc_cem = st.number_input("Çimento (kg)", key="qc_cem")
            qc_wat = st.number_input("Su (L)", key="qc_wat")
            qc_d28 = st.number_input("28 Günlük (MPa)", value=0.0, key="qc_d28")
        with c3:
            qc_air = st.number_input("Hava (%)", key="qc_air")
            qc_slump = st.number_input("Slump (cm)", value=18.0, key="qc_slump")
            qc_pred = st.number_input("Tahmin Edilen (MPa)", key="qc_pred")

        if st.button("💾 Kaydı Veritabanına Ekle"):
            new_record = {
                "id": len(qc_history) + 1,
                "date": str(qc_date),
                "no": qc_no,
                "cement": qc_cem,
                "water": qc_wat,
                "air": qc_air,
                "slump": qc_slump,
                "d7": qc_d7,
                "d28": qc_d28,
                "predicted_mpa": qc_pred,
                "measured_mpa": qc_d28
            }
            qc_history.append(new_record)
            proj_data["qc_history"] = qc_history
            all_data_json[proje] = proj_data
            veriyi_kaydet(proje, proj_data, plant_id=active_p)
            
            # --- ZENGİN AI OTOMATİK ÖĞRENME (DEEP LEARNING) ---
            if qc_d28 > 0:
                try:
                    pool_data = havuz_yukle()
                    # Mevcut projenin dizayn verilerini topla
                    rich_entry = {
                        "cement": qc_cem, "water": qc_wat,
                        "ash": proj_data.get("ucucu", 0),
                        "air": qc_air,
                        "admixture": proj_data.get("kat", 1.0),
                        "d28": qc_d28,
                        "p1": proj_data.get("p", [25]*4)[0],
                        "p2": proj_data.get("p", [25]*4)[1],
                        "p3": proj_data.get("p", [25]*4)[2],
                        "p4": proj_data.get("p", [25]*4)[3],
                        "target_class": hedef_sinif,
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "source": f"Auto-From-{proje}"
                    }
                    pool_data.append(rich_entry)
                    havuz_kaydet(pool_data)
                except Exception as ai_e:
                    st.error(f"AI Otomatik Öğrenme Hatası: {ai_e}")
            
            # Saha Faktörü Güncelleme (Opsiyonel/Otomatik)
            if qc_d28 > 0 and qc_pred > 0:
                new_f = update_site_factor(qc_pred, qc_d28, current_site_factor)
                tesis_faktor_kaydet(tesis_adi, new_f, plant_id=active_p)
                st.success(f"Kaydedildi! Yeni Saha Faktörü: x{new_f}")
            else:
                st.success("Kayıt eklendi.")
            st.rerun()

    # --- 2. KAYITLI VERİLER VE YÖNETİM ---
    if qc_history:
        st.subheader("📊 Kayıtlı Numuneler")
        df_qc = pd.DataFrame(qc_history)
        
        # Sütunları güvenli şekilde seç (Eksi verilerde 'no' veya 'predicted_mpa' olmayabilir)
        # Mevcut sütunlardan seçim yap veya reindex ile NaN ata
        target_cols = ["date", "no", "cement", "water", "d7", "d28", "predicted_mpa"]
        # Eğer eski verilerde farklı isimler varsa onları da ekleyebiliriz
        present_cols = [c for c in target_cols if c in df_qc.columns]
        
        # DataFrame'i güvenli göster
        st.dataframe(df_qc[present_cols], use_container_width=True)

        # Silme ve Düzenleme Bölümü
        st.markdown("---")
        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            selected_id = st.selectbox("İşlem Yapılacak Kayıt (ID)", df_qc["id"].tolist())
        with col_del2:
            if is_admin:
                if st.button("🗑️ Seçili Kaydı Sil", type="secondary"):
                    updated_history = [r for r in qc_history if r["id"] != selected_id]
                    for i, r in enumerate(updated_history): r["id"] = i + 1
                    proj_data["qc_history"] = updated_history
                    # Update DB
                    veriyi_kaydet(proje, proj_data, plant_id=active_p)
                    st.warning(f"Kayıt {selected_id} silindi.")
                    st.rerun()
            else:
                st.button("🗑️ Silme Yetkisi Yok", disabled=True)
        
        # --- GLOBAL HAFIZAYA AKTAR ---
        if is_admin:
            if st.button("🧠 Bu Kaydı Global AI Hafızasına Gönder", use_container_width=True):
                selected_row = [r for r in qc_history if r["id"] == selected_id][0]
                pool_data = havuz_yukle()
                new_entry = {
                    "cement": selected_row.get("cement"), "water": selected_row.get("water"),
                    "ash": selected_row.get("ash", 0), "air": selected_row.get("air", 1.5),
                    "admixture": selected_row.get("admixture", 0), "d28": selected_row.get("d28"),
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d")
                }
                pool_data.append(new_entry)
                havuz_kaydet(pool_data)
                st.success(f"🚀 Kayıt #{selected_id} Global Eğitim Havuzuna başarıyla eklendi!")
        else:
            st.info("💡 Kayıtları Global Hafızaya (Eğitim Havuzu) sadece Yöneticiler ekleyebilir.")

        # --- 3. ANALİZ VE GRAFİKLER ---
        st.divider()
        st.subheader("📈 Performans Analizi")
        
        # Analiz için gerekli sütunların varlığını garanti et
        analysis_df = df_qc.reindex(columns=target_cols).fillna(0)
        
        # --- PERFORMANS ANALİZİ ---
        valid_qc = analysis_df[analysis_df["d28"] > 0]
        target_mpa = TARGET_LIMITS.get(hedef_sinif, {}).get("min_mpa", 0)
        low_results = valid_qc[valid_qc["d28"] < target_mpa]

        c_an1, c_an2 = st.columns(2)
        with c_an1:
            # Gerçekleşen vs Tahmin Grafiği
            if not valid_qc.empty and valid_qc["predicted_mpa"].sum() > 0:
                fig_qc = go.Figure()
                fig_qc.add_trace(go.Scatter(
                    x=valid_qc["predicted_mpa"], y=valid_qc["d28"],
                    mode='markers', name='Kırımlar',
                    marker=dict(size=10, color='blue', opacity=0.7)
                ))
                # 45 Derece Çizgisi
                m_max = max(valid_qc["predicted_mpa"].max(), valid_qc["d28"].max()) + 5
                fig_qc.add_trace(go.Scatter(x=[0, m_max], y=[0, m_max], mode='lines', name='İdeal Doğru', line=dict(color='red', dash='dash')))
                fig_qc.update_layout(title="Gerçekleşen vs Tahmin (28 Gün)", xaxis_title="Tahmin (MPa)", yaxis_title="Ölçülen (MPa)")
                st.plotly_chart(fig_qc, use_container_width=True)
            else:
                st.info("Kıyaslama grafiği için tahmini mpa verisi eksik.")
        
        with c_an2:
            if not low_results.empty:
                st.error(f"🚨 {len(low_results)} adet kırım sonucu hedef limitin altında!")
            else:
                st.success("✅ Tüm kırım sonuçları hedef limitlerin üzerindedir.")
    else:
        st.warning("Henüz şantiye QC verisi girilmemiş.")

def render_tab_5(is_admin=False):
    st.header("🧠 Yapay Zeka Eğitim Hafızası (Global Pool)")
    st.info("Bu sekme, yapay zekayı eğitmek için projelerden bağımsız tecrübeleri yüklemeyi sağlar.")
    
    pool_data = havuz_yukle()
    
    # Veri Giriş Formu
    with st.expander("➕ Yeni Tecrübe Kaydı Ekle", expanded=len(pool_data) == 0):
        c1, c2, c3 = st.columns(3)
        with c1:
            g_cem = st.number_input("Çimento (kg)", value=350, key="g_cem")
            g_wat = st.number_input("Su (L)", value=180, key="g_wat")
        with c2:
            g_ash = st.number_input("Uçucu Kül (kg)", value=0, key="g_ash")
            g_air = st.number_input("Hava (%)", value=1.5, key="g_air")
        with c3:
            g_chem = st.number_input("Katkı (KG - Bir Metreküpteki Toplam)", value=4.0, key="g_chem")
            g_d28 = st.number_input("28 Günlük Dayanım (MPa)", value=35.0, key="g_d28")
        
        if st.button("📥 Havuza Ekle"):
            new_entry = {
                "cement": g_cem, "water": g_wat, "ash": g_ash, 
                "air": g_air, "admixture": g_chem, "d28": g_d28,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d")
            }
            pool_data.append(new_entry)
            havuz_kaydet(pool_data)
            st.success("Veri global havuza eklendi.")
            st.rerun()

    if pool_data:
        st.subheader(f"📊 Mevcut Eğitim Havuzu ({len(pool_data)} Kayıt)")
        df_pool = pd.DataFrame(pool_data)
        
        # BEYİN SAĞLIĞI (İstatistikler)
        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            avg_d28 = df_pool["d28"].mean()
            st.metric("Ortalama Dayanım", f"{avg_d28:.1f} MPa")
        with col_st2:
            from logic.ai_model import train_prediction_model
            _, _, r2 = train_prediction_model(pool_data)
            st.metric("AI Tahmin Hassasiyeti (R²)", f"%{r2*100:.1f}")
        with col_st3:
            st.metric("Toplam Tecrübe", len(pool_data))

        st.dataframe(df_pool, use_container_width=True)
        
        st.markdown("---")
        # Global Havuz temizleme sadece Admin yetkisindedir
        user_info = st.session_state.get('user_info', {})
        if user_info.get('role') == "Admin":
            if st.checkbox("Havuza sıfırla (Tehlikeli!)"):
                if st.button("🗑️ TÜM HAVUZU SİL"):
                     havuz_kaydet([])
                     st.success("Havuz temizlendi.")
                     st.rerun()
        else:
            st.info("💡 Global hafıza yönetimi sadece Yöneticilere açıktır.")
    else:
        st.warning("Eğitim havuzu şu an boş. Veri ekleyerek başlayın.")

def render_tab_management(is_super_admin=False):
    from logic.auth_manager import load_users, add_user, delete_user, save_users, update_user
    st.subheader("👥 Kullanıcı ve Yetki Yönetimi")
    
    users = load_users()
    
    # 0. Bekleyen Onaylar
    pending_users = {u: d for u, d in users.items() if d.get("status") == "pending"}
    if pending_users:
        st.markdown("### ⏳ Bekleyen Üyelik Onayları")
        for p_uname, p_data in pending_users.items():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                c1.write(f"**{p_data.get('full_name')}** (@{p_uname})")
                c2.info("Onay bekliyor...")
                if c3.button("✅ Onayla", key=f"app_{p_uname}"):
                    users[p_uname]["status"] = "active"
                    save_users(users)
                    st.success(f"{p_uname} onaylandı.")
                    st.rerun()
                if c4.button("❌ Reddet", key=f"rej_{p_uname}"):
                    del users[p_uname]
                    save_users(users)
                    st.warning(f"{p_uname} başvurusu reddedildi.")
                    st.rerun()
        st.markdown("---")
    
    users = load_users()
    
    # 1. Kullanıcı Listesi
    st.markdown("### Mevcut Kullanıcılar")
    df_users = []
    for uname, data in users.items():
        df_users.append({
            "Kullanıcı Adı": uname, 
            "Ad Soyad": data.get('full_name', '-'), 
            "Yetki": data.get('role', 'User'),
            "Durum": data.get('status', 'active')
        })
    st.table(pd.DataFrame(df_users))
    
    # 1.5. Santral Yönetimi (Sadece SuperAdmin)
    plants = santralleri_yukle()
    if is_super_admin:
        st.markdown("---")
        st.markdown("### 🏭 Santral Yönetimi")
        
        with st.expander("🏢 Santral Yönetim Paneli", expanded=True):
            # Santralleri tablo olarak göster
            df_plants = [{"ID": pid, "Ad": pd["name"], "Konum": pd.get("location", "-")} for pid, pd in plants.items()]
            st.table(pd.DataFrame(df_plants))
            
            st.markdown("#### ➕ Yeni Santral Ekle")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                new_pid = st.text_input("Santral ID (Örn: ankara_1)", key="new_pid")
                new_pname = st.text_input("Santral Adı", key="new_pname")
            with c_p2:
                new_ploc = st.text_input("Konum/Şehir", key="new_ploc")
                if st.button("🚀 Santrali Kaydet", use_container_width=True):
                    if new_pid and new_pname:
                        santral_kaydet(new_pid, {"name": new_pname, "location": new_ploc})
                        st.success(f"Santral '{new_pname}' eklendi.")
                        st.rerun()
                    else: st.error("ID ve Ad zorunludur.")
            
            st.markdown("---")
            st.markdown("#### 📝 Santral Düzenle / Sil")
            edit_p_list = list(plants.keys())
            edit_pid = st.selectbox("Düzenlenecek Santral", edit_p_list, key="edit_pid_sel")
            if edit_pid:
                p_data = plants[edit_pid]
                ce_p1, ce_p2 = st.columns(2)
                with ce_p1:
                    edit_pname = st.text_input("Yeni Santral Adı", value=p_data["name"], key="edit_pname")
                with ce_p2:
                    edit_ploc = st.text_input("Yeni Konum", value=p_data.get("location", ""), key="edit_ploc")
                
                ce_btns1, ce_btns2 = st.columns(2)
                with ce_btns1:
                    if st.button("💾 Değişiklikleri Kaydet", key="btn_save_plant"):
                        santral_kaydet(edit_pid, {"name": edit_pname, "location": edit_ploc})
                        st.success("Santral bilgileri güncellendi.")
                        st.rerun()
                with ce_btns2:
                    if st.button("🗑️ Santrali Sil", key="btn_del_plant", type="primary"):
                        success, msg = santral_sil(edit_pid)
                        if success:
                            st.warning(msg)
                            st.rerun()
                        else: st.error(msg)
    else:
        st.info("💡 Santral tanımlama yetkisi sadece SuperAdmin'e aittir.")
    
    # 2. Yeni Kullanıcı Ekle
    with st.expander("➕ Yeni Kullanıcı Tanımla"):
        c_u1, c_u2 = st.columns(2)
        with c_u1:
            new_u = st.text_input("Kullanıcı Adı", key="new_u_name")
            new_p = st.text_input("Şifre", type="password", key="new_u_pass")
        with c_u2:
            new_f = st.text_input("Ad Soyad", key="new_u_full")
            new_r = st.selectbox("Yetki Seviyesi", ["User", "Admin", "SuperAdmin"], key="new_u_role")
            
        new_up = st.multiselect("Yetkili Olacağı Santraller", options=list(plants.keys()), 
                                 default=["merkez"], format_func=lambda x: plants[x]["name"],
                                 key="new_u_plants")

        if st.button("✅ Kullanıcıyı Kaydet", use_container_width=True):
            if new_u and new_p:
                success, msg = add_user(new_u, new_p, new_r, new_f, assigned_plants=new_up)
                if success: 
                    st.success(msg)
                    st.rerun()
                else: 
                    st.error(msg)
            else: 
                st.error("Kullanıcı adı ve şifre boş bırakılamaz!")
            
    # 2.5. Kullanıcı Bilgilerini Düzenle (Sadece SuperAdmin veya Admin kısıtlı)
    if is_super_admin:
        with st.expander("📝 Kullanıcı Bilgilerini Düzenle"):
            edit_u = st.selectbox("Düzenlenecek Kullanıcı", list(users.keys()), key="edit_u_sel")
            if edit_u:
                u_data = users[edit_u]
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_f = st.text_input("Yeni Ad Soyad", value=u_data.get('full_name', ''), key="edit_u_f")
                    edit_r = st.selectbox("Yeni Yetki", ["User", "Admin", "SuperAdmin"], 
                                          index=["User", "Admin", "SuperAdmin"].index(u_data.get('role', 'User')), 
                                          key="edit_u_r")
                with col_e2:
                    edit_s = st.selectbox("Yeni Durum", ["active", "pending", "suspended"],
                                          index=["active", "pending", "suspended"].index(u_data.get('status', 'active')),
                                          key="edit_u_s")
                    
                # Santral Yetkileri (Multiselect)
                st.markdown("**🌐 Yetkili Olduğu Santraller**")
                current_plants = u_data.get("assigned_plants", ["merkez"])
                edit_plants = st.multiselect("Santraller", options=list(plants.keys()), 
                                             default=[p for p in current_plants if p in plants],
                                             format_func=lambda x: plants[x]["name"],
                                             key="edit_u_p")

                if st.button("💾 Güncellemeleri Kaydet", use_container_width=True):
                    success, msg = update_user(edit_u, role=edit_r, status=edit_s, full_name=edit_f, assigned_plants=edit_plants)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.info("💡 Kullanıcı yetkilerini ve santral atamalarını düzenleme yetkisi sadece SuperAdmin'e aittir.")
            
    # 3. Kullanıcı Sil
    with st.expander("🗑️ Kullanıcı Sil"):
        current_user = st.session_state.get('username')
        other_users = [u for u in users.keys() if u != current_user]
        if other_users:
            del_u = st.selectbox("Silinecek Kullanıcı", other_users)
            if st.button("❌ Kullanıcıyı Sistemden Kaldır", type="primary"):
                success, msg = delete_user(del_u)
                if success: 
                    st.success(msg)
                    st.rerun()
                else: 
                    st.error(msg)
        else:
            st.info("Sistemde silinebilecek başka kullanıcı bulunmuyor.")

def render_tab_5(is_admin=False):
    st.header("📊 Kurumsal Performans Paneli (Yönetici Özeti)")
    
    if not is_admin:
        st.warning("⚠️ Bu panel sadece yönetici yetkisine sahip kullanıcılar içindir.")
        return

    # Verileri Çek
    with st.spinner("Tüm tesis verileri analiz ediliyor..."):
        df_corp = get_corp_performance_stats()

    if df_corp.empty:
        st.info("📊 Analiz edilecek yeterli veri bulunamadı.")
        return

    # --- 1. ÜST METRİKLER ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Tesis", len(df_corp))
    m2.metric("Toplam Numune", df_corp["samples"].sum())
    # Ortalama sigma (örnek ağırlıklı olmayan)
    m3.metric("Kurumsal Sigma", f"{df_corp['sigma'].mean():.2f}")
    
    # Kritik Tesis Sayısı
    critical_count = len(df_corp[df_corp["status"] == "🔴 Kritik"])
    m4.metric("Kritik Tesis", critical_count, delta=critical_count, delta_color="inverse")

    # --- 2. PERFORMANS TABLOSU ---
    st.subheader("🏭 Tesis Bazlı Performans Matrisi")
    
    # Renklendirme fonksiyonu
    def highlight_status(val):
        color = 'red' if 'Kritik' in val else ('orange' if 'Riskli' in val else 'green')
        return f'color: {color}; font-weight: bold'

    styled_df = df_corp.style.applymap(highlight_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # --- 3. ANALİTİK GRAFİKLER ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📉 Standart Sapma (Sigma) Dağılımı")
        fig_sigma = go.Figure(data=[
            go.Bar(x=df_corp["name"], y=df_corp["sigma"], 
                   marker_color=['red' if s > 5 else ('orange' if s > 3.5 else 'green') for s in df_corp["sigma"]])
        ])
        fig_sigma.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Sigma (MPa)")
        st.plotly_chart(fig_sigma, use_container_width=True)
        st.caption("Not: Sigma < 3.5 ise 'A Sınıfı', 3.5-5.0 arası 'B Sınıfı', > 5.0 ise 'C Sınıfı' tutarlılık gösterir.")

    with c2:
        st.subheader("💎 Çimento Verimliliği (kg / MPa)")
        # Çimento Verimliliği: 1 MPa dayanım için harcanan çimento (düşük olması daha iyi)
        eff_df = calculate_cement_efficiency_stats(df_corp)
        fig_eff = go.Figure(data=[
            go.Bar(x=eff_df["name"], y=eff_df["cement_eff"], marker_color="royalblue")
        ])
        fig_eff.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="kg Çimento / 1 MPa")
        st.plotly_chart(fig_eff, use_container_width=True)
        st.caption("Düşük değerler, aynı dayanım için daha az çimento harcandığını (yüksek verimlilik) gösterir.")

    # --- 4. RİSK ISI HARİTASI ---
    st.markdown("---")
    st.subheader("🔥 Risk Isı Haritası (Saha Aklı)")
    risk_data = generate_risk_heatmap_data(df_corp)
    
    # Basit bir scatter plot ile Sigma vs Ortalama Dayanım (Risk vs Performans)
    fig_risk = go.Figure()
    fig_risk.add_trace(go.Scatter(
        x=df_corp["avg_mpa"], 
        y=df_corp["sigma"],
        mode='markers+text',
        text=df_corp["name"],
        textposition="top center",
        marker=dict(size=15, color=df_corp["sigma"], colorscale='RdYlGn', reversescale=True, showscale=True),
        hovertemplate="<b>%{text}</b><br>Ort. Dayanım: %{x} MPa<br>Sigma: %{y}<extra></extra>"
    ))
    fig_risk.update_layout(
        xaxis_title="Ortalama Dayanım (MPa)",
        yaxis_title="Standart Sapma (Sigma)",
        height=450
    )
    # Risk bölgelerini çizelgeye ekle (opsiyonel ama şık durur)
    fig_risk.add_hrect(y0=0, y1=3.5, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Güvenli Bölge")
    fig_risk.add_hrect(y0=5.0, y1=8.0, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Kritik Bölge")
    
    st.plotly_chart(fig_risk, use_container_width=True)
