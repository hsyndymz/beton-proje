import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from logic.ocak_manager import ocaklari_yukle, ocak_kaydet, ocak_sil
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_quarry_tab_ai(google_key=None, groq_key=None, deepseek_key=None):
    st.header("🏔️ Ocak ve Malzeme Yönetimi")
    st.info("Bölgedeki agrega ocaklarını, litolojik özelliklerini ve test sonuçlarını buradan yönetebilirsiniz.")
    
    ocaklar = ocaklari_yukle()
    
    # AI Analiz verilerini tutmak için session state
    if "quarry_ai_report" not in st.session_state:
        st.session_state.quarry_ai_report = None

    # 1. Yeni Ocak Ekleme Formu
    with st.expander("➕ Yeni Ocak Kaydı Ekle"):
        with st.form("new_quarry_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                o_name = st.text_input("Ocak Adı", help="Örn: Karadağ Taş Ocağı")
                o_lat = st.number_input("Enlem (Lat)", value=37.0, format="%.6f")
                o_lon = st.number_input("Boylam (Lon)", value=38.0, format="%.6f")
            with c2:
                o_litho = st.selectbox("Litoloji", ["Bazalt", "Kalker", "Dere Malzemesi", "Granit", "Andezit"])
                o_la = st.number_input("Los Angeles (LA) Aşınma (%)", value=20.0)
                o_mb = st.number_input("Metilen Mavisi (MB)", value=0.5, format="%.2f")
            with c3:
                o_asr = st.selectbox("ASR Riski", ["İnert", "Potansiyel Reaktif", "Yüksek Reaktif"], 
                                     index=0 if not st.session_state.quarry_ai_report else 
                                     (["İnert", "Potansiyel Reaktif", "Yüksek Reaktif"].index(st.session_state.quarry_ai_report.get("risk_level", "İnert"))))
                o_cem = st.number_input("Çimentolaşma İndeksi", value=1.0, format="%.2f")
                o_desc = st.text_area("Notlar", st.session_state.quarry_ai_report.get("geological_insight", "Kaliteli malzeme.") if st.session_state.quarry_ai_report else "Kaliteli malzeme.")
            
            # AI Tahmini Butonu (Form dışında veya içinde özel yönetim)
            # Streamlit form içindeki butonlar sadece formu submit eder. AI tahmini için form dışı bir buton daha iyi olurdu ama tasarımı koruyalım.
            ai_clicked = st.form_submit_button("✨ AI ile Jeolojik Risk Tahmini Yap")
            if ai_clicked:
                from logic.pdf_processor import analyze_asr_risk_with_geological_ai
                with st.spinner("🤖 AI Jeolojik Verileri Analiz Ediyor..."):
                    report = analyze_asr_risk_with_geological_ai(
                        o_litho, o_lat, o_lon, o_name,
                        google_key=google_key, groq_key=groq_key, deepseek_key=deepseek_key
                    )
                    if "error" not in report:
                        st.session_state.quarry_ai_report = report
                        st.success("✅ AI Analizi Tamamlandı! Form güncellendi.")
                        st.rerun()
                    else:
                        st.error(f"❌ AI Hatası: {report['error']}")

            submit = st.form_submit_button("🚀 Ocağı Kaydet")
            if submit:
                if o_name:
                    o_id = o_name.lower().replace(" ", "_")
                    o_data = {
                        "name": o_name, "lat": o_lat, "lon": o_lon,
                        "lithology": o_litho, "la_wear": o_la, "mb_value": o_mb,
                        "asr_risk": o_asr, "cementation_index": o_cem,
                        "description": o_desc,
                        "ai_geological_insight": st.session_state.quarry_ai_report if st.session_state.quarry_ai_report else None,
                        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    ocak_kaydet(o_id, o_data)
                    st.session_state.quarry_ai_report = None # Temizle
                    st.success(f"'{o_name}' başarıyla kaydedildi.")
                    st.rerun()
                else:
                    st.error("Lütfen ocak adını giriniz.")

    if ocaklar:
        # 2. Harita Gösterimi
        st.subheader("📍 Ocak Haritası")
        map_data = []
        for oid, info in ocaklar.items():
            if isinstance(info, dict):
                map_data.append({
                    "Ocak": info.get("name", oid),
                    "Lat": info.get("lat", 37.0),
                    "Lon": info.get("lon", 38.0),
                    "Litoloji": info.get("lithology", "Bazalt"),
                    "LA": info.get("la_wear", 20.0),
                    "ASR": info.get("asr_risk", "İnert")
                })
            else:
                # Malformed data handling
                map_data.append({
                    "Ocak": str(info),
                    "Lat": 37.0, "Lon": 38.0,
                    "Litoloji": "Bilinmiyor", "LA": 0, "ASR": "Bilinmiyor"
                })
        df_map = pd.DataFrame(map_data)
        
        fig = px.scatter_mapbox(df_map, lat="Lat", lon="Lon", hover_name="Ocak", 
                                hover_data=["Litoloji", "LA", "ASR"],
                                color="Litoloji", zoom=7, height=500)
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Ocak Listesi ve Detaylar
        st.subheader("📊 Ocak Test Verileri")
        # Filter valid dict items for dataframe
        valid_ocaks = {k: v for k, v in ocaklar.items() if isinstance(v, dict)}
        df_list = pd.DataFrame.from_dict(valid_ocaks, orient='index')
        
        # AI Insight column cleanup
        if "ai_geological_insight" in df_list.columns:
            df_list["AI Görüşü"] = df_list["ai_geological_insight"].apply(lambda x: x.get("geological_insight", "-") if isinstance(x, dict) else "-")
        
        target_cols = ["name", "lithology", "la_wear", "asr_risk", "AI Görüşü", "updated_at"]
        present_cols = [c for c in target_cols if c in df_list.columns]
        st.dataframe(df_list[present_cols], use_container_width=True)
        
        # 4. Ocak Silme
        with st.expander("🗑️ Ocak Sil"):
            del_oid = st.selectbox("Silinecek Ocak", list(ocaklar.keys()), 
                                   format_func=lambda x: (ocaklar[x].get("name", x) if isinstance(ocaklar[x], dict) else str(ocaklar[x])))
            if st.button("❌ Ocağı Sil", type="primary"):
                success, msg = ocak_sil(del_oid)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.warning("Henüz kayıtlı ocak bulunmuyor. Elek analizi girişi yapabilmek için önce yukarıdan yeni bir ocak kaydı oluşturmalısınız.")

    # 4. Ocak Bilgilerini Düzenleme (Yeni Talep)
    if ocaklar:
        st.divider()
        with st.expander("✏️ Seçili Ocak Bilgilerini Düzenle (Konum & Litoloji)"):
            edit_quarry_id = st.selectbox("Düzenlenecek Ocak", list(ocaklar.keys()), 
                                          format_func=lambda x: (ocaklar[x].get("name", x) if isinstance(ocaklar[x], dict) else str(ocaklar[x])),
                                          key="edit_quarry_sel")
            
            if edit_quarry_id:
                edited_data = ocaklar[edit_quarry_id]
                if not isinstance(edited_data, dict):
                    st.error("Seçilen ocak verisi bozuk.")
                else:
                    with st.form(f"edit_form_{edit_quarry_id}"):
                        ce1, ce2, ce3 = st.columns(3)
                        with ce1:
                            e_name = st.text_input("Ocak Adı", value=edited_data.get("name", ""), key=f"e_name_{edit_quarry_id}")
                            e_lat = st.number_input("Enlem (Lat)", value=float(edited_data.get("lat", 37.0)), format="%.6f", key=f"e_lat_{edit_quarry_id}")
                            e_lon = st.number_input("Boylam (Lon)", value=float(edited_data.get("lon", 38.0)), format="%.6f", key=f"e_lon_{edit_quarry_id}")
                        with ce2:
                            litho_list = ["Bazalt", "Kalker", "Dere Malzemesi", "Granit", "Andezit"]
                            current_litho = edited_data.get("lithology", "Bazalt")
                            e_litho = st.selectbox("Litoloji", litho_list, index=litho_list.index(current_litho) if current_litho in litho_list else 0, key=f"e_litho_{edit_quarry_id}")
                            e_la = st.number_input("Los Angeles (%)", value=float(edited_data.get("la_wear", 20.0)), key=f"e_la_{edit_quarry_id}")
                            e_mb = st.number_input("Metilen Mavisi", value=float(edited_data.get("mb_value", 0.5)), format="%.2f", key=f"e_mb_{edit_quarry_id}")
                        with ce3:
                            risk_list = ["İnert", "Potansiyel Reaktif", "Yüksek Reaktif"]
                            current_risk = edited_data.get("asr_risk", "İnert")
                            e_asr = st.selectbox("ASR Riski", risk_list, index=risk_list.index(current_risk) if current_risk in risk_list else 0, key=f"e_asr_{edit_quarry_id}")
                            e_cem = st.number_input("Çimentolaşma İndeksi", value=float(edited_data.get("cementation_index", 1.0)), format="%.2f", key=f"e_cem_{edit_quarry_id}")
                            e_desc = st.text_area("Notlar", value=edited_data.get("description", ""), key=f"e_desc_{edit_quarry_id}")
                        
                        do_ai_reanalysis = st.checkbox("🔄 Konum/Litoloji Değişikliği İçin AI'yı Tekrar Çalıştır", value=False)
                        
                        btn_save = st.form_submit_button("💾 Değişiklikleri Kaydet")
                        if btn_save:
                            # AI Analizi tetikleme
                            ai_report = edited_data.get("ai_geological_insight")
                            if do_ai_reanalysis:
                                from logic.pdf_processor import analyze_asr_risk_with_geological_ai
                                with st.spinner("🤖 AI Yeni Jeolojik Verileri Analiz Ediyor..."):
                                    report = analyze_asr_risk_with_geological_ai(
                                        e_litho, e_lat, e_lon, e_name,
                                        google_key=google_key, groq_key=groq_key, deepseek_key=deepseek_key
                                    )
                                    if "error" not in report:
                                        ai_report = report
                                        st.toast("AI Analizi güncellendi!", icon="✨")
                                    else:
                                        st.error(f"AI Hatası: {report['error']}")
                            
                            # Veriyi Güncelle
                            updated_quarry_data = edited_data.copy()
                            updated_quarry_data.update({
                                "name": e_name, "lat": e_lat, "lon": e_lon,
                                "lithology": e_litho, "la_wear": e_la, "mb_value": e_mb,
                                "asr_risk": e_asr, "cementation_index": e_cem,
                                "description": e_desc,
                                "ai_geological_insight": ai_report,
                                "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            
                            ocak_kaydet(edit_quarry_id, updated_quarry_data)
                            st.success(f"'{e_name}' ocağı başarıyla güncellendi.")
                            st.rerun()

    # 5. Elek Analizi (Gradasyon) Yönetimi
    st.divider()
    st.subheader("🧪 Elek Analizi (Gradasyon) Yönetimi")
    
    if not ocaklar:
        st.info("ℹ️ Elek verilerini girmek için önce bir **Ocak** eklemeniz gerekmektedir. Yeni bir ocak eklediğinizde bu bölüm otomatik olarak aktifleşecektir.")
    else:
        st.caption("Bu bölümdeki veriler 'Akıllı Reçete' motoru tarafından hesaplamalarda kullanılır.")
        
        selected_quarry = st.selectbox(
            "📍 Verileri Düzenlenecek Ocak", 
            list(ocaklar.keys()), 
            format_func=lambda x: (ocaklar[x].get("name", x) if isinstance(ocaklar[x], dict) else str(ocaklar[x])), 
            key="grad_quarry_mgmt_sel"
        )
        
        if selected_quarry:
            q_data = ocaklar[selected_quarry]
            if isinstance(q_data, dict):
                existing_grads = q_data.get("material_gradations", {})
            else:
                existing_grads = {}
            
            # Standart Elekler
            sieves = [31.5, 22.4, 16.0, 11.2, 8.0, 4.0, 2.0, 1.0, 0.5, 0.25, 0.15, 0.063, 0.0]
            m_names = ["Kaba Agrega", "Orta Agrega", "İnce Agrega", "Kırma Kum"]
            
            # Tablo Hazırla
            st.info("ℹ️ **Veri Giriş Formatı:** Değerler **'Elekten Geçen (%)'** olarak girilmelidir. (Örn: En büyük elekte %100, en küçükte %0)")
            grad_dict = {"Elek (mm)": sieves}
            for m in m_names:
                # Eğer veri yoksa varsayılan 100->0 dağılımı (geçen yüzdeler)
                grad_dict[m] = existing_grads.get(m, [100.0 if s > 0 else 0.0 for s in sieves])
            
            df_grads = pd.DataFrame(grad_dict)
            
            # Benzersiz key oluşturarak state çakışmasını önle
            editor_key = f"grad_editor_{selected_quarry}"
            edited_df = st.data_editor(df_grads, hide_index=True, use_container_width=True, key=editor_key)
            
            if st.button("💾 Gradasyon Verilerini Kaydet", key=f"btn_save_grad_{selected_quarry}", use_container_width=True):
                new_grads = {}
                for m in m_names:
                    # Değerleri float'a çevirerek listeye al
                    new_grads[m] = [float(x) for x in edited_df[m].tolist()]
                
                q_data["material_gradations"] = new_grads
                ocak_kaydet(selected_quarry, q_data)
                st.success(f"'{q_data.get('name')}' ocağı için gradasyon verileri güncellendi.")
                # st.rerun() yerine bazen st.success yeterli olabilir ama verinin yenilenmesi için rerun iyidir.
                st.rerun()
