import streamlit as st
import datetime
from logic.report_generator import generate_kgm_raporu, generate_pdf_raporu
import plotly.graph_objects as go

def render_tab_reports(proje, selected_provider, TS_STANDARDS_CONTEXT):
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
    
    snap['employer'] = employer
    snap['contractor'] = contractor
    snap['revision'] = revision_no
    snap['report_date'] = report_date.strftime("%d-%m-%Y")

    st.markdown("---")
    st.markdown("#### 📑 Dizayn Özeti ve Teknik Uygunluk")

    # --- YENİ: ANALİTİK VERİ İNCELEMESİ ---
    st.markdown("#### 🔬 Analitik Veri İncelemesi")
    c_ana1, c_ana2, c_ana3 = st.columns(3)
    
    wc_val = s_mix.get('wc', 0)
    with c_ana1: st.metric("Su/Çimento Oranı", f"{wc_val:.2f}", delta="-İdeal" if 0.40 <= wc_val <= 0.50 else "Riskli", delta_color="normal")
    
    agg_filler_val = snap.get('passing', [])[12] if len(snap.get('passing', [])) > 12 else 0
    with c_ana2: st.metric("Agrega Filler (<0.063)", f"%{agg_filler_val:.2f}", delta="Uygun" if agg_filler_val <= 5.0 else "Yüksek", delta_color="inverse")
        
    sand_val = snap.get('passing', [])[6] if len(snap.get('passing', [])) > 6 else 0
    with c_ana3: st.metric("Kum Oranı (<4mm)", f"%{sand_val:.1f}", delta="Stabil" if 33 <= sand_val <= 42 else "Dengesiz")

    # --- YENİ: ANALİTİK GRAFİKLER ---
    st.markdown("#### 📊 İleri Analitik Görselleştirme")
    g_col1, g_col2 = st.columns(2)
    
    passing = snap.get('passing', [])
    sieves = snap.get('sieves', [])
    
    retained = []
    prev_p = 100.0
    for p in passing:
        retained.append(max(0, prev_p - p))
        prev_p = p
    
    with g_col1:
        x_labels = [f"{s} mm" for s in sieves]
        fig_ret = go.Figure()
        fig_ret.add_trace(go.Bar(
            x=x_labels, y=retained, marker_color='rgba(0, 128, 128, 0.7)', 
            name="Seçili Karışım", text=[f"%{v:.1f}" for v in retained], textposition='auto'
        ))
        fig_ret.add_hline(y=18, line_dash="dash", line_color="red", annotation_text="Max %18", annotation_position="top left")
        fig_ret.add_hline(y=8, line_dash="dash", line_color="orange", annotation_text="Min %8", annotation_position="bottom left")
        fig_ret.update_layout(title="Individual Percent Retained (TSE Serisi)", xaxis_title="Elek Boyutu (mm)", yaxis_title="Kalan Yüzde (%)", height=400, margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(range=[0, max(max(retained or [0]), 25)]))
        st.plotly_chart(fig_ret, use_container_width=True)
        st.caption("Not: Betonun işlenebilirliği için her elekte %8-18 arası malzeme kalması (8-18 kuralı) tercih edilir.")

    with g_col2:
        idx_8 = sieves.index(8.0) if 8.0 in sieves else 4
        idx_2 = sieves.index(2.0) if 2.0 in sieves else 7
        ret_above_8 = 100 - passing[idx_8]
        ret_above_2 = 100 - passing[idx_2]
        cf = (ret_above_8 / ret_above_2 * 100) if ret_above_2 > 0 else 0
        
        cement = snap.get('recipe', {}).get('çimento', 350)
        wf_base = passing[idx_2]
        wf_adj = ((cement - 335) / 55) * 2.5
        wf = wf_base + wf_adj
        
        fig_shil = go.Figure()
        fig_shil.add_trace(go.Scatter(x=[100, 45], y=[36, 44], mode='lines', line=dict(color='black', width=1), showlegend=False))
        fig_shil.add_trace(go.Scatter(x=[75, 75, 45, 45, 75], y=[28, 40, 44, 33, 28], fill="toself", fillcolor="rgba(0, 255, 0, 0.05)", line=dict(color="green", width=2), name="Zon II (İyi Gradasyon)"))
        fig_shil.add_trace(go.Scatter(x=[70, 70, 50, 50, 70], y=[32, 36, 38.5, 34, 32], fill="toself", fillcolor="rgba(0, 0, 255, 0.1)", line=dict(color="blue", width=2), name="Optimum Bölge"))
        fig_shil.add_trace(go.Scatter(x=[cf], y=[wf], mode='markers+text', text=["Dizayn"], textposition="top center", marker=dict(size=14, color='red', symbol='x'), name="Mevcut Karışım"))
        
        # Zon annotasyonları
        for x, y, t in [(90, 32, "I"), (60, 41, "II"), (35, 38, "III"), (90, 42, "IV"), (40, 28, "V")]:
            fig_shil.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(size=20, weight="bold"))

        fig_shil.update_layout(title="Shilstone İşlenebilirlik Matrisi", xaxis=dict(title="İRİLİK ENDEKSİ", range=[100, 0], gridcolor="lightgray"), yaxis=dict(title="İŞLENEBİLİRLİK ENDEKSİ", range=[20, 45], gridcolor="lightgray"), height=400, margin=dict(l=20, r=20, t=40, b=20), showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig_shil, use_container_width=True)

    if decision['violations'] or decision['warnings'] or decision.get('rationales'):
        st.markdown("#### ⚠️ Teknik Bulgular ve Gerekçeler")
        for v in decision['violations']: st.error(v)
        for w in decision['warnings']: st.warning(w)
        if decision.get('rationales'):
            with st.expander("🔬 Derinlemesine Mühendislik Analizi (Neden?)", expanded=True):
                for r in decision.get('rationales', []): st.info(f"💡 {r}")

    if snap.get('expert_insights'):
        st.markdown("#### 📜 AI Mühendislik Kararı ve Protokoller")
        for ins in snap['expert_insights']:
            st.markdown(f"""<div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; border-left: 4px solid #1e293b; margin-bottom: 12px; border: 1px solid #e2e8f0;"><b style="color: #1e293b; font-size: 15px;">{ins['topic']}</b><br><div style="margin-top: 5px; font-size: 13px;"><span style="color: #475569;"><b>🔍 Gözlem:</b> {ins.get('observation', ins.get('problem'))}</span><br><span style="color: #b91c1c;"><b>⚠️ Risk:</b> {ins.get('risk', ins.get('rationale'))}</span><br><div style="margin-top: 4px; color: #166534; background-color: #f0fdf4; padding: 5px; border-radius: 4px;"><b>🛡️ Protokol:</b> {ins.get('protocol', ins.get('solution'))}</div></div></div>""", unsafe_allow_html=True)

    st.divider()
    plant_display_name = snap.get('plant_name', 'KGM')
    st.subheader(f"🇹🇷 {plant_display_name} Resmi Beton Kontrol Raporu")
    if st.button(f"📄 {plant_display_name.upper()} HTML RAPORU OLUŞTUR", use_container_width=True):
        try:
            html_report = generate_kgm_raporu(snap)
            st.components.v1.html(html_report, height=600, scrolling=True)
            st.download_button("📥 Raporu .html Olarak İndir", html_report, file_name=f"KGM_Rapor_{proje}.html", mime="text/html")
        except Exception as e: st.error(f"HTML Rapor oluşturulurken hata: {e}")

    if st.button(f"📜 {plant_display_name.upper()} RESMİ TEKNİK RAPORU (PDF) İNDİR", use_container_width=True):
        try:
            pdf_bytes = generate_pdf_raporu(snap)
            st.download_button("📥 Resmi Teknik Raporu (.pdf) Kaydet", data=pdf_bytes, file_name=f"Resmi_Teknik_Rapor_{proje}.pdf", mime="application/pdf")
            st.success("✅ Resmi PDF raporu başarıyla oluşturuldu.")
        except Exception as e: st.error(f"PDF Rapor oluşturulurken hata: {e}. 'Arial' fontunun yüklü olduğundan emin olun.")

    st.divider()
    st.subheader("🤖 AI Teknik Rapor Oluşturucu")
    st.caption("Bu bölüm, verileri teknik bir makale dilinde özetler.")
    
    if st.button("🪄 AI İle Teknik Özet Yazdır"):
        sieve_data = ", ".join([f"{s}mm: %{p:.1f}" for s, p in zip(snap['sieves'], snap['passing'])])
        recipe_text = f"Çimento: {snap['recipe']['çimento']}kg, Su: {snap['recipe']['su']}L, Kül: {snap['recipe']['kül']}kg, Katkı: {snap['recipe']['katkı']}kg. Agregalar: {snap['recipe']['agrega_miktarları']}"
        prompt = f"""BİRİNCİL GÖREV: Aşağıdaki beton dizayn verilerini SİSTEMATİK ve ANALİTİK bir yaklaşımla, 'Baş Mühendis' perspektifinden analiz et.\n\nANALİZ YAPISI:\n1. TEKNİK ÖZET\n2. SU/ÇİMENTO VE DURABİLİTE\n3. GRADASYON VE KOMPAKTLIK\n4. MALZEME RİSKLERİ\n5. NİHAİ MÜHENDİSLİK GÖRÜŞÜ\n\nVERİ SETİ:\n- Proje/Tesis: {snap['project_name']} / {snap['plant_name']}\n- Reçete: {recipe_text}\n- Karma Gradasyon: {sieve_data}\n- Karar: {decision['status']} ({decision['main_msg']})"""

        if selected_provider == "Yerel (Ollama / LM Studio)":
            from logic.local_ai_helper import stream_ollama_response
            local_api = st.session_state.get('local_api_base', 'http://localhost:11434')
            local_model = st.session_state.get('local_model_name', 'llama3')
            
            # Streaming UI
            with st.status("🤖 Yerel AI Raporu Hazırlıyor...", expanded=True) as status:
                resp_container = st.empty()
                full_response = ""
                for chunk in stream_ollama_response(local_api, local_model, prompt):
                    full_response += chunk
                    resp_container.markdown(full_response + "▌")
                resp_container.markdown(full_response)
                st.session_state['ai_report_output'] = full_response
                status.update(label="✅ Rapor Tamamlandı!", state="complete")
        else:
            st.session_state['ai_report_prompt'] = prompt
            st.info("AI Raporu oluşturuluyor... (Yan paneldeki API anahtarı kullanılır)")
            st.rerun()

    if 'ai_report_output' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state['ai_report_output'])
        if st.button("🗑️ Analizi Temizle"):
            del st.session_state['ai_report_output']
            st.rerun()
