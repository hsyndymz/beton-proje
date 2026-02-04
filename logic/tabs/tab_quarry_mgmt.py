import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from logic.data_manager import ocaklari_yukle, ocak_kaydet, ocak_sil
from logic.error_handler import handle_exceptions
from logic.logger import logger

@handle_exceptions(show_error_to_user=True)
def render_quarry_tab():
    st.header("🏔️ Ocak ve Malzeme Yönetimi")
    st.info("Bölgedeki agrega ocaklarını, litolojik özelliklerini ve test sonuçlarını buradan yönetebilirsiniz.")
    
    ocaklar = ocaklari_yukle()
    
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
                # ASR riskini litolojiye göre de belirleyebiliriz ama formda manuel seçilebilir kalsın
                o_asr = st.selectbox("ASR Riski", ["İnert", "Potansiyel Reaktif", "Yüksek Reaktif"])
                o_cem = st.number_input("Çimentolaşma İndeksi", value=1.0, format="%.2f")
                o_desc = st.text_area("Notlar", "Kaliteli malzeme.")
            
            submit = st.form_submit_button("🚀 Ocağı Kaydet")
            if submit:
                if o_name:
                    o_id = o_name.lower().replace(" ", "_")
                    o_data = {
                        "name": o_name, "lat": o_lat, "lon": o_lon,
                        "lithology": o_litho, "la_wear": o_la, "mb_value": o_mb,
                        "asr_risk": o_asr, "cementation_index": o_cem,
                        "description": o_desc,
                        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    ocak_kaydet(o_id, o_data)
                    logger.info(f"Ocak kaydedildi: {o_name}", user=st.session_state.get('username'))
                    st.success(f"'{o_name}' başarıyla kaydedildi.")
                    st.rerun()
                else:
                    st.error("Lütfen ocak adını giriniz.")

    if ocaklar:
        # 2. Harita Gösterimi
        st.subheader("📍 Ocak Haritası")
        map_data = []
        for oid, info in ocaklar.items():
            map_data.append({
                "Ocak": info.get("name", oid),
                "Lat": info.get("lat", 37.0),
                "Lon": info.get("lon", 38.0),
                "Litoloji": info.get("lithology", "Bazalt"),
                "LA": info.get("la_wear", 20.0),
                "ASR": info.get("asr_risk", "İnert")
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
        df_list = pd.DataFrame.from_dict(ocaklar, orient='index')
        target_cols = ["name", "lithology", "la_wear", "asr_risk", "updated_at"]
        present_cols = [c for c in target_cols if c in df_list.columns]
        st.dataframe(df_list[present_cols], use_container_width=True)
        
        # 4. Ocak Silme
        with st.expander("🗑️ Ocak Sil"):
            del_oid = st.selectbox("Silinecek Ocak", list(ocaklar.keys()), format_func=lambda x: ocaklar[x].get("name", x))
            if st.button("❌ Ocağı Sil", type="primary"):
                if ocak_sil(del_oid):
                    logger.warning(f"Ocak silindi: {del_oid}", user=st.session_state.get('username'))
                    st.warning(f"Ocak silindi.")
                    st.rerun()
    else:
        st.warning("Henüz kayıtlı ocak bulunmuyor.")
