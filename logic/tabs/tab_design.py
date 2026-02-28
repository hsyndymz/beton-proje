import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from logic.engineering import (
    optimize_mix, best_wc_estimate, calculate_theoretical_mpa, 
    evaluate_mix_compliance, calculate_fm, get_std_limits, 
    generate_pro_expert_analysis, LITHOLOGY_FACTORS, EXPOSURE_CLASSES,
    calculate_effective_wc
)
from logic.data_manager import havuz_yukle, havuz_kaydet, veriyi_yukle
from logic.ai_model import (
    train_prediction_model, predict_strength_ai, calculate_match_score, 
    predict_90d_strength, derive_local_engineering_constants, find_similar_recipes
)

def render_tab_design(proje, tesis_adi, hedef_sinif, litoloji, elek_serisi, materials, active_mats, 
                 current_rhos, current_was, current_las, current_mbs, current_moists,
                 current_site_factor, get_global_qc_history):
    st.subheader("2. Karışım Oranları ve 1m³ Reçete")
    
    # Yerel Otonom Zeka: Katsayı Türetme
    pool_data = havuz_yukle()
    local_const = derive_local_engineering_constants(pool_data)

    # --- DEBUG: Session State Check ---
    # if 'transferred_recipe' in st.session_state:
    #    st.write("DEBUG: Recipe found in logic/tabs/tab_design.py")
    
    # --- SMART MIX ENTEGRASYONU ---
    if 'transferred_recipe' in st.session_state:
        recipe = st.session_state['transferred_recipe']
        st.info(f"📥 **Smart Mix'ten Gelen Reçete:** {recipe.get('name')}")
        
        c_imp1, c_imp2 = st.columns([3, 1])
        with c_imp1:
            st.caption(f"Detay: {recipe.get('cement')} kg Çimento | S/Ç: {recipe.get('wc_ratio')} | Maliyet: {recipe.get('cost_per_m3', '-')} TL")
        with c_imp2:
            if st.button("✅ Uygula", key="btn_apply_smart_mix"):
                # Değerleri Session State'e aktar
                st.session_state['cimento_val'] = float(recipe.get('cement', 300))
                st.session_state['su_val'] = float(recipe.get('water', 160))
                st.session_state['ucucu_kul'] = float(recipe.get('ash', 0))
                st.session_state['slag_val'] = float(recipe.get('slag', 0)) # Yeni State
                
                # Agrega Yüzdelerini Aktar
                pcts = recipe.get('weights_pct', {})
                # Eşleştirme yap (Sıralı varsayım - Geliştirilebilir)
                active_indices = [i for i, x in enumerate(active_mats) if x]
                keys = list(pcts.keys())
                
                # Malzeme isimlerine göre eşleştirmeye çalış, yoksa sırayla
                for idx, mat_name in enumerate(materials):
                    if active_mats[idx]:
                        val = pcts.get(mat_name, 0.0)
                        # Eğer isim eşleşmezse ve sayı tutuyorsa sıradan al (Fallback)
                        if val == 0.0 and len(keys) > active_indices.index(idx):
                             # Bu basit bir fallback, idealde isimler tutmalı
                             pass 
                        
                        st.session_state[f"p{idx+1}"] = int(val)

                del st.session_state['transferred_recipe']
                st.success("Reçete başarıyla uygulandı! Sayfa yenileniyor...")
                st.rerun()
    if st.session_state.get('trigger_optimize'):
        dmax_opt = st.session_state.get('dmax_select', 31.5)
        curve_opt = st.session_state.get('target_curve_select', 'B (İdeal)')
        computed_opt = st.session_state.get('computed_passing', {})
        
        # 1. Gradasyon Optimizasyonu
        best_p = optimize_mix(curve_opt, dmax_opt, active_mats, computed_opt, elek_serisi, materials)
        if best_p is not None:
            active_indices = [i for i, x in enumerate(active_mats) if x]
            for k, idx in enumerate(active_indices):
                st.session_state[f"p{idx+1}"] = int(best_p[k])
            
            # 2. AI Tabanlı Çimento ve Su Optimizasyonu
            pool_data = havuz_yukle()
            if len(pool_data) >= 5:
                ai_wc = best_wc_estimate(pool_data, hedef_sinif)
                if ai_wc:
                    ref_water = st.session_state.get('su_val', 180)
                    suggested_cem = int(ref_water / ai_wc)
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

    # Karışım Ayarları
    c_hdr1, c_hdr2 = st.columns(2)
    with c_hdr1:
        dmax_val = st.selectbox("Dmax (mm)", [31.5, 22.4, 16.0], index=0, key="dmax_select")
    with c_hdr2:
        target_curve = st.selectbox("Hedef Eğri", ["A (Alt)", "B (İdeal)", "C (Üst)", "KGM TİP-1", "KGM TİP-2"], index=1, key="target_curve_select")

    # Karışım Geçen Hesapla (Sliders)
    st.markdown("##### 🧪 Agrega Harman Oranları (%)")
    c_sld1, c_sld2, c_sld3, c_sld4 = st.columns(4)
    with c_sld1: p1 = st.slider(f"{materials[0]}", 0, 100, key="p1")
    with c_sld2: p2 = st.slider(f"{materials[1]}", 0, 100, key="p2")
    with c_sld3: p3 = st.slider(f"{materials[2]}", 0, 100, key="p3")
    with c_sld4: p4 = st.slider(f"{materials[3]}", 0, 100, key="p4")
    
    computed_passing = st.session_state.get('computed_passing', {})
    karisim_gecen = np.zeros(len(elek_serisi))
    individual_passing = {}
    
    for i, p in enumerate([p1, p2, p3, p4]):
        mat_name = materials[i]
        if active_mats[i] and mat_name in computed_passing:
            mat_pass = np.array(computed_passing[mat_name])
            karisim_gecen += (mat_pass * p / 100.0)
            individual_passing[mat_name] = mat_pass

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
        slag_val = st.number_input("Cüruf (kg/m³)", value=0.0, key='slag_val')
        hava_yuzde = st.number_input("Hedef Hava Miktarı (%)", value=1.0, step=0.1, key='hava_yuzde')

        predicted_mpa = 0.0 # Varsayılan (UnboundLocalError önlemi)
        if cimento > 0:
            wc_ratio_eff = calculate_effective_wc(su_hedef, cimento, slag=slag_val, fly_ash=ucucu_kul, cement_type=selected_cem)
            
            theo_mpa = calculate_theoretical_mpa(wc_ratio_eff, hava_yuzde, cement_type=selected_cem, has_pozzolan=(slag_val + ucucu_kul > 0), local_constants=local_const)
            lith_factor = LITHOLOGY_FACTORS.get(litoloji, 1.0)
            predicted_mpa = theo_mpa * current_site_factor * lith_factor
            
            # 90 Günlük Tahmin
            total_binder = cimento + slag_val + ucucu_kul
            pred_90d = predict_90d_strength(predicted_mpa, 
                                            cement_pct=(cimento/total_binder*100), 
                                            slag_pct=(slag_val/total_binder*100), 
                                            ash_pct=(ucucu_kul/total_binder*100))
            st.session_state['predicted_mpa_val'] = predicted_mpa

            st.markdown("---")
            d1, d2 = st.columns(2)
            with d1:
                st.metric("Tahmin (28 Gün)", f"{predicted_mpa:.1f} MPa", delta=f"{predicted_mpa - 30:.1f}" if "C30" in hedef_sinif else None)
            with d2:
                st.metric("Tahmin (90 Gün)", f"{pred_90d:.1f} MPa", delta="+%12-30", delta_color="normal")
            
            st.caption(f"ℹ️ **Saha & Lokal:** x{current_site_factor:.2f} (Tesis) | x{lith_factor:.2f} ({litoloji})")
            
            # 2. Global AI Modeli (Lineer Regresyon)
            pool_data = havuz_yukle()
            if len(pool_data) >= 5:
                g_coeffs, g_intercept, _ = train_prediction_model(pool_data)
                if g_coeffs is not None:
                    katki_kg_val = (cimento * katki / 100)
                    # Girdi sırası ai_model.py ile uyumlu olmalı: [cem, wat, ash, slag, air, chem]
                    g_inputs = np.array([float(cimento), float(su_hedef), float(ucucu_kul), float(slag_val), float(hava_yuzde), float(katki_kg_val)])
                    g_pred = predict_strength_ai(g_coeffs, g_intercept, g_inputs)
                    
                    e1, e2 = st.columns(2)
                    with e1:
                        st.success(f"🌐 **Global AI Analizi:** {g_pred:.1f} MPa")
                    with e2:
                        match_score = calculate_match_score(g_inputs, pool_data, hedef_sinif)
                        st.metric("Pattern Uyumu (Onaylılar)", f"%{match_score}")
                        if match_score > 85: st.caption("✅ Onaylı dökümlere çok yakın.")
                        elif match_score > 60: st.caption("⚠️ Küçük sapmalar mevcut.")
                        else: st.caption("❗ Sıra dışı değerler saptandı.")
                    
                    # Yerel Benzer Reçete Listesi
                    with st.expander("📚 Benzer Geçmiş Tecrübeler", expanded=False):
                        similar = find_similar_recipes(g_inputs, pool_data, top_n=3)
                        if similar:
                            for s in similar:
                                rec = s['record']
                                st.write(f"📝 **%{s['similarity']} Uyum** | {rec.get('target_class')} | {rec.get('d28')} MPa | S/Ç: {round(rec.get('water',0)/rec.get('cement',1), 2)}")
                        else:
                            st.caption("Henüz benzer onaylı kayıt yok.")
        else: wc_ratio_eff, predicted_mpa = 0.6, 0.0

    with c_grad_plot:
        plot_mode = st.radio("Grafik Görünümü", ["Yığışımlı Geçen (Standart)", "Elekte Kalan (8-18 Kuralı)"], horizontal=True, label_visibility="collapsed")
        
        if "Standart" in plot_mode:
            fig = go.Figure()
            alt_a, _ = get_std_limits(dmax_val, "A (Alt)", elek_serisi)
            alt_b, _ = get_std_limits(dmax_val, "B (İdeal)", elek_serisi)
            alt_c, _ = get_std_limits(dmax_val, "C (Üst)", elek_serisi)

            fig.add_trace(go.Scatter(x=elek_serisi, y=alt_a, mode='lines', name='Alt Limit', line=dict(color='#2563eb', width=1.5, dash='dash')))
            fig.add_trace(go.Scatter(x=elek_serisi, y=alt_c, mode='lines', name='Üst Limit', line=dict(color='#2563eb', width=1.5, dash='dash')))
            fig.add_trace(go.Scatter(x=elek_serisi, y=alt_b, mode='lines', name='Şartname', line=dict(color='#b91c1c', width=2)))

            excel_colors = ['#1E3A8A', '#15803D', '#334155', '#B91C1C', '#4B5563']
            for i, mat_name in enumerate(materials):
                if mat_name in individual_passing:
                    fig.add_trace(go.Scatter(
                        x=elek_serisi, y=individual_passing[mat_name],
                        mode='lines', name=f"Seri {i+1} ({mat_name})",
                        line=dict(color=excel_colors[i], width=1.5, dash='dash'),
                        opacity=0.6
                    ))

            if np.any(karisim_gecen > 0):
                fig.add_trace(go.Scatter(
                    x=elek_serisi, y=karisim_gecen, mode='lines+markers', 
                    name='Karışım Gradasyonu', 
                    line=dict(color='#F97316', width=5), 
                    marker=dict(symbol='circle', size=10, line=dict(color='white', width=1))
                ))
            
            fig.update_layout(
                title=f"Dmax {dmax_val} mm. Gradasyon Eğrisi",
                paper_bgcolor='white', plot_bgcolor='white',
                margin=dict(l=40, r=20, t=60, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(family="Fira Sans", size=12),
                height=450
            )
            
            fig.update_xaxes(
                type='log', title='Elek Boyutu (mm)', autorange="reversed", gridcolor='#d1d5db', linecolor='black',
                tickvals=elek_serisi, ticktext=[str(s) for s in elek_serisi]
            )
            fig.update_yaxes(
                title='Elekten Geçen % (Yığışımlı)', range=[0, 105], gridcolor='#d1d5db', linecolor='black', dtick=10
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("##### 📊 Toplam Karışım Geçen (%)")
            full_grad_data = {f"{s} mm": f"%{karisim_gecen[i]:.1f}" for i, s in enumerate(elek_serisi)}
            mix_fm = calculate_fm(elek_serisi, karisim_gecen.tolist())
            st.markdown(f"📐 **Harman İncelik Modülü (İM): {mix_fm:.2f}**")
            st.dataframe(pd.DataFrame([full_grad_data]), hide_index=True, use_container_width=True)
        else:
            retained = []
            prev_p = 100.0
            for p in karisim_gecen:
                val = max(0, prev_p - p)
                retained.append(val)
                prev_p = p
            
            x_labels = [f"{s}" for s in elek_serisi]
            fig_ret = go.Figure()
            fig_ret.add_trace(go.Bar(
                x=x_labels, y=retained, marker_color='#0e7490', text=[f"%{v:.1f}" for v in retained],
                textposition='auto', name="Tasarım"
            ))
            fig_ret.add_hline(y=18, line_dash="dash", line_color="#b91c1c", annotation_text="Max %18", annotation_position="top left")
            fig_ret.add_hline(y=8, line_dash="dash", line_color="#b45309", annotation_text="Min %8", annotation_position="bottom left")
            
            fig_ret.update_layout(
                title="Bireysel Elek Kalıntı Analizi (8-18 Yasası)",
                xaxis_title="Elek Boyutu (mm)", yaxis_title="Elekte Kalan %",
                paper_bgcolor='white', plot_bgcolor='white', height=450,
                margin=dict(l=40, r=20, t=60, b=40)
            )
            fig_ret.update_yaxes(range=[0, max(max(retained or [0]), 25)])
            st.plotly_chart(fig_ret, use_container_width=True)
            st.caption("ℹ️ Betonun işlenebilirliği ve kohezyonu için her elekte %8 ile %18 arasında malzeme kalması ideal kabul edilir.")

    st.divider()
    col_lock1, col_lock2 = st.columns([2, 1])
    with col_lock2:
        is_approved_design = st.checkbox("🏛️ Mühendislik Onaylı", help="Bu dizaynı 'Altın Standart' olarak AI havuzuna kaydeder (10x Ağırlık).")
    
    if st.button("🧮 Dizaynı Hesapla ve Kilitle", type="primary", use_container_width=True):
        try:
            pool_data = havuz_yukle()
            ai_entry = {
                "cement": float(cimento), "water": float(su_hedef), "ash": float(ucucu_kul),
                "slag": float(slag_val), # Yeni
                "air": float(hava_yuzde), "admixture": float(cimento * katki / 100),
                "d28": float(predicted_mpa), 
                "is_approved": is_approved_design, # Yeni
                "p": [float(p1), float(p2), float(p3), float(p4)],
                "lithology": litoloji,
                "material_chars": {
                    "rhos": current_rhos, "was": current_was, "las": current_las, "mbs": current_mbs
                },
                "target_class": hedef_sinif,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                "source": f"Design-Learn-{proje}"
            }
            pool_data.append(ai_entry)
            havuz_kaydet(pool_data)
            st.toast("🤖 AI Motoru bu dizayndan yeni bilgiler öğrendi!", icon="🧠")
        except Exception as e:
            st.error(f"AI Öğrenme Hatası: {e}")

        active_p = st.session_state.get('active_plant', 'merkez')
        all_qc_data = veriyi_yukle(plant_id=active_p)
        proj_history = all_qc_data.get(proje, {}).get("qc_history", [])
        
        training_data = proj_history
        if len(proj_history) < 5:
            pool_data = havuz_yukle()
            if pool_data: training_data = proj_history + pool_data
        
        # Karar ve Analiz
        current_inputs = np.array([cimento, su_hedef, ucucu_kul, hava_yuzde, (cimento*katki/100)])
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
        
        idx_filler = elek_serisi.index(0.063) if 0.063 in elek_serisi else -1
        idx_sand = elek_serisi.index(4.0) if 4.0 in elek_serisi else -1
        
        agg_filler_pct = karisim_gecen[idx_filler] if idx_filler != -1 else 0.0
        sand_val = karisim_gecen[idx_sand] if idx_sand != -1 else 0.0
        
        vol_cem = cimento / 3.15
        vol_water = su_hedef / 1.0
        vol_ash = ucucu_kul / 2.25
        vol_air = hava_yuzde * 10
        vol_chem = (cimento * katki / 100) / 1.12
        V_agg_tot = 1000 - (vol_cem + vol_water + vol_ash + vol_air + vol_chem)
        m_kgs = [V_agg_tot * (p/100) * r for p, r in zip([p1,p2,p3,p4], current_rhos)]
        total_agg_kg = sum(m_kgs)
        
        comp_data = {
            "class": hedef_sinif, "wc": wc_ratio_eff, "pred_mpa": predicted_mpa,
            "grading_violation": grade_violation, "grading_dev": grade_dev_total,
            "lithology": litoloji, "cement": cimento, "air": hava_yuzde, "ash": ucucu_kul,
            "wa_risk": any([w > 2.0 for w in current_was if w > 0]),
            "avg_la": w_la, "avg_mb": w_mb,
            "filler_content": agg_filler_pct,
            "sand_content": sand_val,
            "exposure_class": st.session_state.get('exposure_class', 'XC3'),
            "asr_status": st.session_state.get('asr_status', 'Düzeltme Gerekmiyor')
        }
        decision = evaluate_mix_compliance(comp_data)
        st.session_state['last_decision'] = decision

        weighted_wa = (current_was[0]*p1 + current_was[1]*p2 + current_was[2]*p3 + current_was[3]*p4) / total_ratio
        wa_liters = (weighted_wa / 100) * total_agg_kg
        
        total_mix_weight_kg = cimento + ucucu_kul + (cimento * katki / 100) + su_hedef + total_agg_kg
        agg_filler_kg = (agg_filler_pct / 100) * total_agg_kg
        total_filler_kg = agg_filler_kg + cimento + ucucu_kul
        total_filler_pct_relative = (total_filler_kg / total_mix_weight_kg * 100) if total_mix_weight_kg > 0 else 0.0
        
        filler_val = total_filler_pct_relative

        retained = []
        prev_p = 100.0
        for p in karisim_gecen:
            retained.append(max(0, prev_p - p))
            prev_p = p

        idx_8 = elek_serisi.index(8.0) if 8.0 in elek_serisi else 4
        idx_2 = elek_serisi.index(2.0) if 2.0 in elek_serisi else 7
        ret_above_8 = 100 - (karisim_gecen[idx_8] if len(karisim_gecen) > idx_8 else 0)
        ret_above_2 = 100 - (karisim_gecen[idx_2] if len(karisim_gecen) > idx_2 else 0)
        cf = (ret_above_8 / ret_above_2 * 100) if ret_above_2 > 0 else 0
        wf = (karisim_gecen[idx_2] + ((cimento - 335) / 55) * 2.5) if len(karisim_gecen) > idx_2 else 0

        wc_status = "Riskli" if not (0.40 <= wc_ratio_eff <= 0.50) else "İdeal"
        
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
            "moisture_info": {
                "moists": current_moists,
                "total_water_from_moist": sum([m_kgs[i] * (current_moists[i]/100.0) for i in range(len(materials)) if active_mats[i]])
            },
            "ai_analysis": {
                "wa_liters": wa_liters, "weighted_wa": weighted_wa,
                "filler_val": filler_val, "sand_val": sand_val,
                "w_la": w_la, "w_mb": w_mb,
                "cf": cf, "wf": wf,
                "retained": retained,
                "wc_status": wc_status,
                "filler_status": "Yüksek" if filler_val > 5.0 else ("Düşük" if filler_val < 1.0 else "Uygun"),
                "sand_status": "Dengesiz" if not (37 <= sand_val <= 56) else "Stabil"
            },
            "material_data": {
                "rhos": current_rhos, "was": current_was, 
                "las": current_las, "mbs": current_mbs, "active": active_mats
            }, 
            "sieves": elek_serisi.copy(),
            "passing": karisim_gecen.tolist(), 
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        mix_fm = calculate_fm(elek_serisi, karisim_gecen.tolist())
        comp_data.update({
            "water": su_hedef, "fm": mix_fm, "retained": retained,
            "sieves": elek_serisi, "passing": karisim_gecen.tolist()
        })
        
        pro_analysis = generate_pro_expert_analysis(comp_data)
        st.session_state['expert_insights'] = pro_analysis
        st.session_state['mix_snapshot']['expert_insights'] = pro_analysis

        st.markdown("### 🧠 AI Mühendislik ve Litolojik Değerlendirme")
        
        su_farklar = [m_kgs[i] * (current_was[i] - current_moists[i]) / 100.0 for i in range(len(materials)) if active_mats[i]]
        total_su_fark = sum(su_farklar)
        eklenecek_su = su_hedef + total_su_fark
        
        c_water1, c_water2 = st.columns(2)
        with c_water1:
            st.info(f"💧 **Hacimsel Su Dengesi:**\n\nNet Dizayn Suyu: **{su_hedef:.1f} L**\n\nAgrega Su Emme Telafisi (SSD): **+{wa_liters:.1f} L**")
        with c_water2:
            st.success(f"⚖️ **Kantar/Üretim Ayarı:**\n\nExcel Bazlı Su Düzeltmesi: **{total_su_fark:+.1f} L**\n\nKantar için eklenecek su: **{eklenecek_su:.1f} L**")

        c_eval1, c_eval2 = st.columns(2)
        with c_eval1:
            st.markdown("##### 🏗️ Yapısal Durum")
            if w_la > 35: st.error(f"❌ **Aşınma:** LA %{w_la:.1f} yüksek.")
            elif w_la > 30: st.warning(f"⚠️ **Aşınma:** LA %{w_la:.1f} sınırda.")
            else: st.success(f"✅ **Aşınma:** LA %{w_la:.1f} uygun.")
            
            if grade_violation: st.error(f"❌ **Gradasyon:** {dmax_val}mm limitleri dışı.")
            elif grade_dev_total > 1.0: st.warning(f"⚠️ **Gradasyon:** Standart bölge sınırında.")
            else: st.success(f"✅ **Gradasyon:** TS 802'ye tam uygun.")

        with c_eval2:
            st.markdown("##### 🧪 Kimyasal Analiz")
            if w_mb > 1.5: st.error(f"❌ **MB Uyarısı:** {w_mb:.2f} g/kg yüksek!")
            elif w_mb > 1.0: st.warning(f"⚠️ **MB Uyarısı:** {w_mb:.2f} g/kg (Kil riski).")
            else: st.success(f"✅ **MB Temizliği:** {w_mb:.2f} g/kg ideal.")
            st.info(f"💡 **Litoloji:** {litoloji} karakteristiği inceleniyor.")

        st.markdown("##### 🛣️ KTŞ & Beton Yol Gradasyon Hassasiyeti")
        c_kts1, c_kts2 = st.columns(2)
        with c_kts1:
            if filler_val > 5.0: st.error(f"❌ **Filler (<0.063mm):** %{filler_val:.2f} (Max %5!)")
            elif filler_val < 1.0: st.warning(f"⚠️ **Filler (<0.063mm):** %{filler_val:.2f} (Min %1!)")
            else: st.success(f"✅ **Filler (<0.063mm):** %{filler_val:.2f}")
        
        with c_kts2:
            if sand_val < 37.0 or sand_val > 56.0: st.error(f"❌ **Kum (<4mm):** %{sand_val:.1f} (KGM: %37-56)")
            elif sand_val < 39.0 or sand_val > 54.0: st.warning(f"⚠️ **Kum (<4mm):** %{sand_val:.1f} (Sınırda)")
            else: st.success(f"✅ **Kum (<4mm):** %{sand_val:.1f}")
        
        st.markdown("##### 🌋 Durabilite ve ASR Analizi")
        c_dur1, c_dur2 = st.columns(2)
        with c_dur1:
            exp_val = st.session_state.get('exposure_class', 'XC3')
            e_lim = EXPOSURE_CLASSES.get(exp_val, {})
            if wc_ratio_eff > e_lim.get('max_wc', 1.0) or cimento < e_lim.get('min_cem', 0):
                st.error(f"❌ **Maruziyet ({exp_val}):** İhlal!")
            else: st.success(f"✅ **Maruziyet ({exp_val}):** Uyumlu.")
        
        with c_dur2:
            asr_val = st.session_state.get('asr_status', 'İnert')
            if "Reaktif" in asr_val:
                st.warning(f"⚠️ **ASR Riski:** {asr_val}.")
                suggested_ash = total_agg_kg * 0.05
                st.info(f"💡 **ASR Önlemi:** ~{suggested_ash:.1f} kg Uçucu Kül önerilir.")
            else: st.success(f"✅ **ASR Riski:** {asr_val}.")

        st.markdown("---")
        c_res1, c_res2 = st.columns([1, 1])
        with c_res1:
            st.subheader("📋 Analiz Sonuçları")
            if decision['status'] == "RED": st.error(f"### {decision['title']}\n{decision['main_msg']}")
            elif decision['status'] == "YELLOW": st.warning(f"### {decision['title']}\n{decision['main_msg']}")
            else: st.success(f"### {decision['title']}\n{decision['main_msg']}")
            
            for r in decision.get("rationales", []): st.info(f"💡 {r}")
            
            compliance_result = evaluate_mix_compliance(comp_data, st.session_state.get('standard_mode', 'KTŞ 2023'))
            if compliance_result["status"] == "RED": st.error(f"**{compliance_result['title']}**")
            elif compliance_result["status"] == "YELLOW": st.warning(f"**{compliance_result['title']}**")
            else: st.success(f"**{compliance_result['title']}**")
            st.caption(compliance_result["main_msg"])

        with c_res2:
            st.markdown("### 📋 1m³ Reçete")
            katki_kg = round(cimento * katki / 100, 2)
            hava_katki_kg = round(cimento * hava_katki_yuzde / 100, 3)
            # Reçete hesaplamaları (Tekrar hesapla)
            m_kantar = [m_kgs[i] * (1 + (current_moists[i] - current_was[i]) / 100.0) if active_mats[i] else 0.0 for i in range(4)]

            rec_tab = {
                "Bileşen": ["Çimento", "Net Su", "Eklenecek Su", "Uçucu Kül", "Kimyasal Katkı", "Hava Sürükleyici", "Hava (Hacim)"], 
                "Miktar": [
                    round(cimento, 1), round(su_hedef, 1), f"🧪 {eklenecek_su:.1f}", round(ucucu_kul, 1), 
                    katki_kg, hava_katki_kg, f"%{hava_yuzde:.1f}"
                ]
            }
            for i, mat in enumerate(materials):
                if active_mats[i]: 
                    rec_tab["Bileşen"].append(f"{mat} (Kantar)")
                    rec_tab["Miktar"].append(f"⚖️ {m_kantar[i]:.1f}")
            st.table(pd.DataFrame(rec_tab))

    if st.button("⚡ EN İYİ KARIŞIMI BUL (HEDEFE GÖRE)", type="secondary", use_container_width=True):
        st.session_state['trigger_optimize'] = True
        st.rerun()

    if st.session_state.get('expert_insights'):
        st.markdown("---")
        st.markdown("### 🏛️ Pro-Expert: Yapay Zeka Mühendislik Kararı")
        for ins in st.session_state['expert_insights']:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; border-left: 6px solid #1e293b; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="background-color: #1e293b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 10px;">UZMAN GÖRÜŞÜ</span>
                        <h4 style="margin: 0; color: #1e293b;">{ins['topic']}</h4>
                    </div>
                    <div style="margin-left: 10px;">
                        <p style="color: #475569; font-size: 14px; margin-bottom: 8px;"><b>🔍 Gözlem:</b> {ins.get('observation', ins.get('problem'))}</p>
                        <p style="color: #b91c1c; font-size: 14px; margin-bottom: 8px;"><b>⚠️ Mühendislik Riski:</b> {ins.get('risk', ins.get('rationale'))}</p>
                        <div style="background-color: #f0fdf4; padding: 10px; border-radius: 6px; border-left: 3px solid #16a34a;">
                            <p style="color: #166534; font-size: 14px; margin: 0;"><b>🛡️ Protokol Önerisi:</b> {ins.get('protocol', ins.get('solution'))}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
