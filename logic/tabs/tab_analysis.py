import streamlit as st
import datetime
import pandas as pd
from logic.data_manager import veriyi_yukle, veriyi_kaydet, havuz_yukle, havuz_kaydet, tesis_faktor_yukle, tesis_faktor_kaydet, shared_insight_yukle, shared_insight_kaydet, shared_insight_sil
from logic.engineering import classify_plant, evolve_site_factor
from logic.intelligence import generate_smart_alerts, explain_ai_logic
import plotly.graph_objects as go

def render_tab_analysis(proje, tesis_adi, TARGET_LIMITS, hedef_sinif, get_global_qc_history, is_admin=False):
    # Verileri Yükle
    active_p = st.session_state.get('active_plant', 'merkez')
    all_data_json = veriyi_yukle(plant_id=active_p)
    proj_data = all_data_json.get(proje, {})
    qc_history = proj_data.get("qc_history", [])
    current_site_factor = tesis_faktor_yukle(tesis_adi, plant_id=active_p)
    
    # --- SAHA AKLI (LEARNING SYSTEM) ---
    global_qc_hist = get_global_qc_history()
    plant_class, _ = classify_plant(global_qc_hist)
    
    # Dinamik Saha Faktörü Gelişimi
    evolved_factor = evolve_site_factor(qc_history, current_site_factor)
    if evolved_factor != current_site_factor:
        tesis_faktor_kaydet(tesis_adi, evolved_factor, plant_id=active_p)
        current_site_factor = evolved_factor

    st.info(f"**🏭 Santral Profili (Saha Aklı):** {plant_class} | **{tesis_adi} Saha Faktörü:** x{current_site_factor:.3f}")

    # --- 🤖 SAHA AKLI - AI GÜNLÜK TEKNİK BÜLTENİ ---
    st.markdown("---")
    with st.container():
        st.markdown("### 🤖 Saha Aklı - AI Teknik Bülteni")
        all_insights = shared_insight_yukle()
        
        if all_insights:
            for idx, insight in enumerate(reversed(all_insights)):
                with st.chat_message("assistant", avatar="🧠"):
                    st.write(f"**{insight.get('author', 'Global AI Model')}** - {insight.get('timestamp', '')}")
                    st.info(insight.get('content', ''))
                    if is_admin:
                        if st.button(f"🗑️ Bülteni Kaldır #{len(all_insights)-1-idx}", key=f"del_ins_{len(all_insights)-1-idx}"):
                            shared_insight_sil(len(all_insights)-1-idx)
                            st.rerun()
        else:
            st.caption("Şu an paylaşılan küresel bir teknik bülten bulunmuyor.")

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
                    
                    if st.button(f"📢 Bültene Ekle", key=f"share_{alert['id']}"):
                        new_insight = {
                            "author": tesis_adi,
                            "content": alert['msg'],
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        shared_insight_kaydet(new_insight)
                        st.success("Bültene eklendi!")
                        st.rerun()
                    st.caption(f"Dayanak: {alert['rationale']}")

    # --- 1. VERİ GİRİŞ FORMU ---
    with st.expander("💜 Yeni Numune / Tam Reçete Kaydı", expanded=len(qc_history) == 0):
        if st.button("📋 Mevcut Dizayn Verilerini Kopyala", use_container_width=False):
            snap = st.session_state.get('mix_snapshot')
            if snap is not None:
                m_data = snap['mix_data']
                st.session_state['qc_cem'] = m_data.get('cement', 350)
                st.session_state['qc_wat'] = m_data.get('water', 180)
                st.session_state['qc_ash'] = m_data.get('ash', 0)
                st.session_state['qc_chem'] = m_data.get('admixture', 4.0)
                st.session_state['qc_air'] = m_data.get('air', 1.5)
                # Reçete oranlarını da kopyala
                st.session_state['qc_p1'] = st.session_state.get('p1', 25)
                st.session_state['qc_p2'] = st.session_state.get('p2', 25)
                st.session_state['qc_p3'] = st.session_state.get('p3', 25)
                st.session_state['qc_p4'] = st.session_state.get('p4', 25)
                st.success("Tüm dizayn ve reçete verileri forma çekildi!")
                st.rerun()
            else:
                st.warning("Önce 'Karışım Dizaynı' sekmesinde hesaplama yapmalısınız.")

        with st.form("new_control_form_premium"):
            st.markdown('<div style="border: 1px solid #f0f0f0; padding: 25px; border-radius: 15px; background-color: #ffffff;">', unsafe_allow_html=True)
            
            st.markdown("#### 📅 Numune Kimliği")
            c_id1, c_id2, c_id3 = st.columns(3)
            with c_id1: qc_date = st.date_input("Döküm Tarihi", key="qc_date")
            with c_id2: qc_no = st.text_input("Numune No", value=f"N-{len(qc_history)+1}", key="qc_no")
            with c_id3: qc_target = st.number_input("Tasarım Hedef Dayanımı (MPa)", value=0.0, step=0.1, key="qc_target")
            
            st.markdown("#### 💧 Saha Reçete Detayları (1m³)")
            c_rec1, c_rec2, c_rec3, c_rec4 = st.columns(4)
            with c_rec1: qc_cem = st.number_input("Çimento (kg)", key="qc_cem")
            with c_rec2: qc_wat = st.number_input("Su (L)", key="qc_wat")
            with c_rec3: qc_ash = st.number_input("Uçucu Kül (kg)", key="qc_ash")
            with c_rec4: qc_chem = st.number_input("Katkı (kg)", key="qc_chem")
                
            st.markdown("#### 🧪 Agrega Dağılımı (Saha)")
            c_agg1, c_agg2, c_agg3, c_agg4 = st.columns(4)
            with c_agg1: qc_p1 = st.number_input("No:2 %", value=st.session_state.get('qc_p1', 25), key="qc_p1")
            with c_agg2: qc_p2 = st.number_input("No:1 %", value=st.session_state.get('qc_p2', 25), key="qc_p2")
            with c_agg3: qc_p3 = st.number_input("K.Kum %", value=st.session_state.get('qc_p3', 25), key="qc_p3")
            with c_agg4: qc_p4 = st.number_input("D.Kum %", value=st.session_state.get('qc_p4', 25), key="qc_p4")
                
            st.markdown("#### 🏁 Taze Beton ve Kırım Verileri")
            c_qc1, c_qc2, c_qc3, c_qc4 = st.columns(4)
            with c_qc1: qc_slump = st.number_input("Slump (cm)", value=18.0, step=0.5, key="qc_slump")
            with c_qc2: qc_air = st.number_input("Hava (%)", value=1.5, step=0.1, key="qc_air")
            with c_qc3: qc_d7 = st.number_input("7 Günlük (MPa)", value=0.0, step=0.1, key="qc_d7")
            with c_qc4: qc_d28 = st.number_input("28 Günlük (MPa)", value=0.0, step=0.1, key="qc_d28")
                
            st.markdown("<br>", unsafe_allow_html=True)
            submit_control = st.form_submit_button("💾 Tam Sistemi Kaydet")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_control:
                new_record = {
                    "id": len(qc_history) + 1, "date": str(qc_date), "no": qc_no,
                    "target_mpa": qc_target, "cement": qc_cem, "water": qc_wat,
                    "ash": qc_ash, "admixture": qc_chem, "p_ratios": [qc_p1, qc_p2, qc_p3, qc_p4],
                    "air": qc_air, "slump": qc_slump, "d7": qc_d7, "d28": qc_d28, "measured_mpa": qc_d28,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                qc_history.append(new_record)
                proj_data["qc_history"] = qc_history
                all_data_json[proje] = proj_data
                veriyi_kaydet(proje, proj_data, plant_id=active_p)
                
                # AI Learning (Automatic)
                if qc_d28 > 0:
                    try:
                        pool_data = havuz_yukle()
                        pool_data.append({
                            "cement": qc_cem, "water": qc_wat, "ash": qc_ash,
                            "air": qc_air, "admixture": qc_chem, "d28": qc_d28,
                            "p": [qc_p1, qc_p2, qc_p3, qc_p4],
                            "lithology": proj_data.get("lithology", "Bazalt"),
                            "source": f"Control-Tab-{proje}"
                        })
                        havuz_kaydet(pool_data)
                    except: pass
                
                st.success("✅ Kayıt başarıyla sisteme işlendi.")
                st.rerun()

    # --- 2. KAYITLI VERİLER ---
    if qc_history:
        st.subheader("📊 Kayıtlı Numuneler")
        df_qc = pd.DataFrame(qc_history)
        target_cols = ["date", "no", "cement", "water", "d7", "d28", "measured_mpa"]
        present_cols = [c for c in target_cols if c in df_qc.columns]
        st.dataframe(df_qc[present_cols], use_container_width=True)

        st.markdown("---")
        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            selected_id = st.selectbox("İşlem Yapılacak Kayıt (ID)", df_qc["id"].tolist())
        with col_del2:
            if is_admin and st.button("🗑️ Seçili Kaydı Sil", type="secondary"):
                updated_history = [r for r in qc_history if r["id"] != selected_id]
                for i, r in enumerate(updated_history): r["id"] = i + 1
                proj_data["qc_history"] = updated_history
                veriyi_kaydet(proje, proj_data, plant_id=active_p)
                st.warning(f"Kayıt {selected_id} silindi.")
                st.rerun()
        
        # --- PERFORMANS ANALİZİ ---
        st.divider()
        st.subheader("📈 Performans Analizi")
        analysis_df = df_qc.fillna(0)
        valid_qc = analysis_df[analysis_df["d28"] > 0]
        
        c_an1, c_an2 = st.columns(2)
        with c_an1:
            # Gerçekleşen vs Tahmin Grafiği (Eğer varsa)
            if "predicted_mpa" in valid_qc.columns and valid_qc["predicted_mpa"].sum() > 0:
                fig_qc = go.Figure()
                fig_qc.add_trace(go.Scatter(x=valid_qc["predicted_mpa"], y=valid_qc["d28"], mode='markers', name='Kırımlar'))
                m_max = max(valid_qc["predicted_mpa"].max(), valid_qc["d28"].max()) + 5
                fig_qc.add_trace(go.Scatter(x=[0, m_max], y=[0, m_max], mode='lines', name='İdeal Doğru', line=dict(dash='dash')))
                fig_qc.update_layout(title="Gerçekleşen vs Tahmin (28 Gün)", xaxis_title="Tahmin", yaxis_title="Ölçülen")
                st.plotly_chart(fig_qc, use_container_width=True)
            else:
                 # Basit Zaman Serisi
                 fig_ts = go.Figure()
                 fig_ts.add_trace(go.Scatter(x=valid_qc["date"], y=valid_qc["d28"], mode='lines+markers', name='28 Günlük'))
                 fig_ts.update_layout(title="28 Günlük Dayanım Gelişimi", xaxis_title="Tarih", yaxis_title="MPa")
                 st.plotly_chart(fig_ts, use_container_width=True)

        with c_an2:
            target_mpa = TARGET_LIMITS.get(hedef_sinif, {}).get("min_mpa", 0)
            low_results = valid_qc[valid_qc["d28"] < target_mpa]
            if not low_results.empty:
                st.error(f"🚨 {len(low_results)} adet kırım sonucu hedef limitin altında!")
            else:
                st.success("✅ Tüm kırım sonuçları hedef limitlerin üzerindedir.")
    else:
        st.warning("Henüz şantiye QC verisi girilmemiş.")
