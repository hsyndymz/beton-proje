from fpdf import FPDF
import datetime
import io
import os
from fpdf.fonts import FontFace
from logic.report_engine import generate_regulatory_text, build_grading_comment, build_strength_decision

class KGM_PDF_Report(FPDF):
    def header(self):
        # Header - Official Logo Placeholder or Title
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "T.C. ULASTIRMA VE ALTYAPI BAKANLIGI", border=0, ln=1, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 5, "KARAYOLLARI GENEL MUDURLUGU - TEKNIK RAPOR SISTEMI", border=0, ln=1, align="C")
        self.set_draw_color(44, 62, 80)
        self.line(10, 27, 200, 27)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Sayfa {self.page_no()}/{{nb}} - AI Beton Teknoloji Platformu", 0, 0, "C")

def generate_pdf_raporu(snapshot):
    """
    snapshot verilerinden profesyonel bir PDF raporu üretir.
    HTML raporu ile birebir aynı yapıdadır (Kapak Sayfası + Görsel Grafikler).
    """
    pdf = KGM_PDF_Report()
    pdf.alias_nb_pages()
    
    # Font path (Windows standard)
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    
    if os.path.exists(font_path):
        pdf.add_font("Arial", "", font_path)
        if os.path.exists(font_bold_path):
            pdf.add_font("Arial", "B", font_bold_path)
        else:
            pdf.add_font("Arial", "B", font_path)
    else:
        pdf.set_font("helvetica", size=12)

    project_name = snapshot.get("project_name", "-")
    plant_name = snapshot.get("plant_name", "-")
    employer = snapshot.get("employer", "T.C. ULASTIRMA VE ALTYAPI BAKANLIGI")
    contractor = snapshot.get("contractor", "YUKLENICI FIRMA A.S.")
    revision = snapshot.get("revision", "R0")
    bugun = datetime.datetime.now().strftime("%d-%m-%Y")
    
    mix_data = snapshot.get("mix_data", {})
    material_data = snapshot.get("material_data", {})
    recipe = snapshot.get("recipe", {})
    s_ai = snapshot.get('ai_analysis', {})

    # --- SAYFA 1: KAPAK ---
    pdf.add_page()
    eff_w = pdf.w - 2 * pdf.l_margin
    
    pdf.ln(60)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(eff_w, 10, employer, align="C")
    
    pdf.ln(10)
    pdf.set_draw_color(44, 62, 80)
    pdf.line(pdf.l_margin + 30, pdf.get_y(), pdf.w - pdf.l_margin - 30, pdf.get_y())
    
    pdf.ln(15)
    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(eff_w, 8, "BETON KARIŞIM TASARIMI VE KALİTE KONTROL DEĞERLENDİRME RAPORU", align="C")
    
    pdf.ln(50)
    pdf.set_font("Arial", "B", 12)
    
    cover_info = [
        ("PROJE ADI:", project_name),
        ("YÜKLENİCİ:", contractor),
        ("BETON SINIFI:", mix_data.get('class', '-')),
        ("TEKNİK SANTRAL:", plant_name),
        ("TARİH:", bugun),
        ("REVİZYON:", revision),
    ]
    
    start_x = pdf.l_margin + 30
    for label, val in cover_info:
        pdf.set_x(start_x)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, label, 0)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, str(val), ln=1)
        
    pdf.set_y(-40)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(eff_w, 5, "Bu rapor TS EN 206, TS 802 ve KTS 2016 standartlari cercevesinde\nAI Destekli Beton Teknolojisi Platformu tarafindan uretilmistir.", align="C")
    pdf.set_text_color(0, 0, 0)

    # --- SAYFA 2: İÇERİK ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(236, 240, 241)
    
    # 1. Rapor Amacı
    pdf.cell(eff_w, 8, " 1. RAPOR AMACI VE DAYANAGI", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    amacy_text = (
        "Bu rapor, TS EN 206 'Beton - Ozellik, performans, imalat ve uygunluk', TS 802 'Beton karisim hesabı esaslari' "
        "ve Karayollari Teknik Sartnamesi (KTS 2016) hukumleri dogrultusunda, belirtilen beton sinifi icin yapilan "
        "karisim tasarimi ve kalite kontrol sonuclarinin degerlendirilmesi amaciyla hazirlanmistir."
    )
    pdf.multi_cell(eff_w, 5, amacy_text)
    pdf.ln(5)

    # 2. Malzeme Analizi
    pdf.set_font("Arial", "B", 11)
    pdf.cell(eff_w, 8, " 2. MALZEME ANALIZI", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(eff_w, 7, f"Litolojik Koken: {mix_data.get('lithology', '-')} | ASR Riski: {mix_data.get('asr_status', '-')} | Maruziyet: {mix_data.get('exposure_class', '-')}", ln=1)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 7, "Bilesen", 1, 0, "C", fill=True)
    pdf.cell(35, 7, "Ozgul Agir.", 1, 0, "C", fill=True)
    pdf.cell(35, 7, "Su Emme (%)", 1, 0, "C", fill=True)
    pdf.cell(35, 7, "Asinma (LA)", 1, 0, "C", fill=True)
    pdf.cell(eff_w - 145, 7, "Metilen (MB)", 1, 1, "C", fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    rhos = material_data.get("rhos", [0.0]*4)
    was = material_data.get("was", [0.0]*4)
    las = material_data.get("las", [0.0]*4)
    mbs = material_data.get("mbs", [0.0]*4)
    mats = ["Kaba Elek (19-25)(15-25)", "Orta Kaba (7-19)(5-15)", "İnce No:1 (0-7)(0-5)", "İnce No:2 (0-5)(0-7)"]
    
    for i in range(len(mats)):
        r = rhos[i] if i < len(rhos) else 0.0
        w = was[i] if i < len(was) else 0.0
        l = las[i] if i < len(las) else 0.0
        m = mbs[i] if i < len(mbs) else 0.0
        pdf.cell(40, 6, mats[i], 1)
        pdf.cell(35, 6, f"{r:.3f}", 1, 0, "C")
        pdf.cell(35, 6, f"{w:.2f}", 1, 0, "C")
        pdf.cell(35, 6, f"{l:.1f}", 1, 0, "C")
        pdf.cell(eff_w - 145, 6, f"{m:.2f}", 1, 1, "C")
    pdf.ln(5)

    # 3. Reçete
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(eff_w, 8, " 3. KARISIM ORANLARI (1 m3)", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(eff_w/3, 7, f"Cimento: {recipe.get('çimento', 0)} kg", 0)
    pdf.cell(eff_w/3, 7, f"Su: {recipe.get('su', 0)} Lt", 0)
    pdf.cell(eff_w/3, 7, f"W/C Orani: {mix_data.get('wc', 0):.2f}", ln=1)
    pdf.cell(eff_w/3, 7, f"Katki: {recipe.get('katkı', 0)} kg", 0)
    pdf.cell(eff_w/3, 7, f"Kul: {recipe.get('kül', 0)} kg", 0)
    pdf.cell(eff_w/3, 7, f"Hava: %{recipe.get('hava', 0)}", ln=1)
    pdf.ln(5)

    # 4. Karar
    decision = snapshot.get("decision", {})
    status_text = decision.get("title", "BELIRSIZ")
    reg_metin = generate_regulatory_text(decision)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(eff_w, 8, f" 4. TEKNIK DEGERLENDIRME VE KARAR", ln=1, fill=True)
    
    st_color = (44, 62, 80)
    if decision.get("status") == "RED": st_color = (192, 57, 43)
    elif decision.get("status") == "YELLOW": st_color = (212, 172, 13)
    elif decision.get("status") == "GREEN": st_color = (39, 174, 96)
    
    pdf.set_draw_color(*st_color)
    pdf.set_line_width(0.5)
    pdf.rect(pdf.get_x(), pdf.get_y()+2, eff_w, 35)
    pdf.set_line_width(0.2)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*st_color)
    pdf.cell(eff_w, 7, f" SONUC: {status_text}", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(eff_w, 4, reg_metin)
    pdf.ln(10)

    # 5. AI Durabilite
    pdf.set_font("Arial", "B", 11)
    pdf.cell(eff_w, 8, " 5. AI MUHENDISLIK VE DURABILITE ANALIZI", ln=1, fill=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(eff_w/2, 6, f"Su Telafisi (Emme): %{s_ai.get('weighted_wa',0):.2f}", 0)
    pdf.cell(eff_w/2, 6, f"Asinma (LA): %{s_ai.get('w_la',0):.1f}", ln=1)
    pdf.cell(eff_w/2, 6, f"Toplam Su Cekme: {s_ai.get('wa_liters',0):.1f} Lt", 0)
    pdf.cell(eff_w/2, 6, f"Kirlilik (MB): {s_ai.get('w_mb',0):.2f} g/kg", ln=1)
    pdf.ln(5)

    # 6. Analitik Grafikler (Full Parity)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(eff_w, 8, " 6. ILERI ANALITIK GORSELLESTIRME (8-18 & SHILSTONE)", ln=1, fill=True)
    
    chart_y = pdf.get_y() + 5
    _draw_pdf_retained_chart(pdf, pdf.l_margin, chart_y, snapshot.get('sieves', []), s_ai.get('retained', []))
    _draw_pdf_shilstone_matrix(pdf, pdf.l_margin + 100, chart_y, s_ai.get('cf', 0), s_ai.get('wf', 0))
    
    pdf.set_y(chart_y + 60)
    
    # İmza Bölümü
    pdf.set_font("Arial", "B", 10)
    pdf.ln(10)
    pdf.cell(eff_w/3, 6, "HAZIRLAYAN", 0, 0, "C")
    pdf.cell(eff_w/3, 6, "KONTROL", 0, 0, "C")
    pdf.cell(eff_w/3, 6, "ONAYLAYAN", 0, 1, "C")
    pdf.ln(15)
    pdf.set_font("Arial", "", 8)
    pdf.cell(eff_w/3, 4, "(Imza / Kase)", 0, 0, "C")
    pdf.cell(eff_w/3, 4, "(Imza / Kase)", 0, 0, "C")
    pdf.cell(eff_w/3, 4, "(Muher / Imza)", 0, 1, "C")

    return bytes(pdf.output())

def generate_kgm_raporu(snapshot):
    """
    TSE ve KTŞ standartlarına tam uyumlu, profesyonel beton kontrol raporu oluşturur.
    Referans HTML raporundaki tüm detay verileri (Kapak, LA/MB değerleri, Shilstone vb.) içerir.
    """
    project_name = snapshot.get("project_name", "Bilinmeyen Proje")
    plant_name = snapshot.get("plant_name", "BETON SANTRALİ")
    employer = snapshot.get("employer", "T.C. ULAŞTIRMA VE ALTYAPI BAKANLIĞI")
    contractor = snapshot.get("contractor", "YÜKLENİCİ FİRMA A.Ş.")
    revision = snapshot.get("revision", "R0")
    
    mix_data = snapshot.get("mix_data", {})
    decision_data = snapshot.get("decision", {})
    material_data = snapshot.get("material_data", {})
    recipe = snapshot.get("recipe", {})
    
    bugun = datetime.datetime.now().strftime("%d-%m-%Y")
    
    reg_text = generate_regulatory_text(decision_data)
    grading_text = build_grading_comment(mix_data.get('grading_violation', False), mix_data.get('grading_dev', 0.0))
    strength_text = build_strength_decision(mix_data.get('pred_mpa', 0), 37)

    status_color = "#2C3E50"
    if decision_data["status"] == "RED": status_color = "#C0392B"
    elif decision_data["status"] == "YELLOW": status_color = "#D4AC0D"
    elif decision_data["status"] == "GREEN": status_color = "#27AE60"
    
    s_ai = snapshot.get('ai_analysis', {})
    retained_svg = _generate_retained_svg(snapshot.get('sieves', []), s_ai.get('retained', []))
    shilstone_svg = _generate_shilstone_svg(s_ai.get('cf', 0), s_ai.get('wf', 0))

    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: auto; color: #333; line-height: 1.6;">
        
        <!-- SAYFA 1: KAPAK -->
        <div style="height: 1000px; border: 15px double #2C3E50; padding: 50px; text-align: center; display: flex; flex-direction: column; justify-content: center; margin-bottom: 50px; background: white; page-break-after: always;">
            <h1 style="font-size: 28px; margin-top: 20px; color: #2C3E50;">{employer}</h1>
            <hr style="width: 50%; border: 1px solid #2C3E50;">
            <h2 style="font-size: 22px; margin-top: 40px;">BETON KARIŞIM TASARIMI VE KALİTE KONTROL DEĞERLENDİRME RAPORU</h2>
            
            <div style="margin-top: 100px; font-size: 18px; text-align: left; padding-left: 20%; line-height: 2;">
                <b>PROJE ADI:</b> {project_name}<br>
                <b>YÜKLENİCİ:</b> {contractor}<br>
                <b>BETON SINIFI:</b> {mix_data.get('class', '-')}<br>
                <b>TEKNİK SANTRAL:</b> {plant_name}<br>
                <b>TARİH:</b> {bugun}<br>
                <b>REVİZYON:</b> {revision}
            </div>
            
            <div style="margin-top: auto; font-size: 14px; color: #7F8C8D;">
                Bu rapor TS EN 206, TS 802 ve KTŞ 2016 standartları çerçevesinde <br>
                AI Destekli Beton Teknolojisi Platformu tarafından üretilmiştir.
            </div>
        </div>

        <!-- SAYFA 2: İÇERİK -->
        <div style="padding: 20px; background: white; border: 1px solid #ddd; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
            
            <!-- HEADER -->
            <table style="width:100%; border-bottom: 3px solid #2C3E50; margin-bottom: 20px;">
                <tr>
                    <td style="width: 70%;">
                        <h3 style="margin:0; color: #2C3E50;">{plant_name.upper()}</h3>
                        <div style="font-size: 12px;">Beton Laboratuvarı ve Kalite Kontrol Birimi</div>
                    </td>
                    <td style="width: 30%; text-align:right; font-size:12px;">
                        Rapor No: BTN-{revision}-{bugun.replace("-", "")}<br>
                        Tarih: {bugun}
                    </td>
                </tr>
            </table>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">1. RAPOR AMACI VE DAYANAĞI</h4>
            <p style="font-size: 14px; text-align: justify;">
                Bu rapor, TS EN 206 "Beton - Özellik, performans, imalat ve uygunluk", TS 802 "Beton karışım hesabı esasları" 
                ve Karayolları Teknik Şartnamesi (KTŞ 2016) hükümleri doğrultusunda, belirtilen beton sınıfı için yapılan
                karışım tasarımı ve kalite kontrol sonuçlarının değerlendirilmesi amacıyla hazırlanmıştır.
            </p>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">2. MALZEME ANALİZİ</h4>
            <div style="font-size: 13px;">
                <b>Litolojik Köken:</b> {mix_data.get('lithology', '-')} | 
                <b>ASR Riski:</b> {mix_data.get('asr_status', '-')} | 
                <b>Maruziyet:</b> {mix_data.get('exposure_class', '-')}
            </div>
            <table style="width:100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; text-align: center;">
                <tr style="background: #2C3E50; color: white;">
                    <th style="border: 1px solid #bdc3c7; padding: 5px;">Bileşen</th>
                    <th style="border: 1px solid #bdc3c7; padding: 5px;">Özgül Ağırlık</th>
                    <th style="border: 1px solid #bdc3c7; padding: 5px;">Su Emme (%)</th>
                    <th style="border: 1px solid #bdc3c7; padding: 5px;">Aşınma (LA)</th>
                    <th style="border: 1px solid #bdc3c7; padding: 5px;">Metilen (MB)</th>
                </tr>
                """
    
    rhos = material_data.get("rhos", [0]*4)
    was = material_data.get("was", [0]*4)
    las = material_data.get("las", [0]*4)
    mbs = material_data.get("mbs", [0]*4)
    mats = ["Kaba Elek (19-25)(15-25)", "Orta Kaba (7-19)(5-15)", "İnce No:1 (0-7)(0-5)", "İnce No:2 (0-5)(0-7)"]
    
    for i in range(4):
        if i < len(rhos):
            html += f"""
                    <tr>
                        <td style="border: 1px solid #bdc3c7; padding: 5px; font-weight: bold;">{mats[i]}</td>
                        <td style="border: 1px solid #bdc3c7; padding: 5px;">{rhos[i]:.3f}</td>
                        <td style="border: 1px solid #bdc3c7; padding: 5px;">{was[i]:.2f}</td>
                        <td style="border: 1px solid #bdc3c7; padding: 5px;">{las[i]:.1f}</td>
                        <td style="border: 1px solid #bdc3c7; padding: 5px;">{mbs[i]:.2f}</td>
                    </tr>
            """

    html += f"""
            </table>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">3. KARIŞIM ORANLARI (1 m³)</h4>
            <table style="width:100%; border-collapse: collapse; font-size: 13px;">
                <tr>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>Çimento:</b> {recipe.get('çimento', 0)} kg</td>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>Su:</b> {recipe.get('su', 0)} Lt</td>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>W/C Oranı:</b> {mix_data.get('wc', 0):.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>Kimyasal Katkı:</b> {recipe.get('katkı', 0)} kg</td>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>Uçucu Kül:</b> {recipe.get('kül', 0)} kg</td>
                    <td style="padding: 5px; border-bottom: 1px solid #eee;"><b>Hava:</b> %{recipe.get('hava', 0)}</td>
                </tr>
            </table>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">4. TEKNİK DEĞERLENDİRME VE KARAR</h4>
            
            <div style="border: 2px solid {status_color}; padding: 15px; border-radius: 8px; margin-top: 10px;">
                <h3 style="margin: 0; color: {status_color};">SONUÇ: {decision_data['title']}</h3>
                <p style="font-size: 14px; margin-top: 10px; text-align: justify;"><b>{reg_text}</b></p>
                
                <div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #ccc; font-size: 13px;">
                    <p><b>🔍 Detaylı Analiz Notları:</b></p>
                    <ul style="padding-left: 20px;">
                        <li>{grading_text}</li>
                        <li>{strength_text}</li>
                        {"".join([f"<li style='color: #C0392B;'><b>İhlal:</b> {v}</li>" for v in decision_data['violations']])}
                        {"".join([f"<li style='color: #D4AC0D;'><b>Uyarı:</b> {w}</li>" for w in decision_data['warnings']])}
                    </ul>
                </div>
            </div>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">5. AI MÜHENDİSLİK VE DURABİLİTE ANALİZİ</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px;">
                <div style="background: #F4F6F7; padding: 10px; border-radius: 5px; border-top: 3px solid #3498DB;">
                    <b>💧 Su Telafisi Analizi</b><br>
                    Karma Agrega Su Emme: %{snapshot.get('ai_analysis', {}).get('weighted_wa', 0):.2f}<br>
                    1m³ Toplam Su Çekme: <b>{snapshot.get('ai_analysis', {}).get('wa_liters', 0):.1f} Litre</b>
                </div>
                <div style="background: #F4F6F7; padding: 10px; border-radius: 5px; border-top: 3px solid #E67E22;">
                    <b>🏗️ Yapısal Ve Kimyasal Durum</b><br>
                    Ortalama Aşınma (LA): %{snapshot.get('ai_analysis', {}).get('w_la', 0):.1f}<br>
                    Metilen Mavisi (MB): {snapshot.get('ai_analysis', {}).get('w_mb', 0):.2f} g/kg
                </div>
            </div>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">6. ANALİTİK VERİ İNCELEMESİ</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; text-align: center; margin-bottom: 20px;">
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <span style="font-size: 11px; color: #666;">Su/Çimento Oranı</span><br>
                    <b style="font-size: 16px;">{mix_data.get('wc', 0):.2f}</b><br>
                    <span style="color: {'#27AE60' if snapshot.get('ai_analysis', {}).get('wc_status') == 'İdeal' else '#C0392B'}; font-size: 11px;">
                        {snapshot.get('ai_analysis', {}).get('wc_status', '-')}
                    </span>
                </div>
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <span style="font-size: 11px; color: #666;">Filler Oranı (<0.063)</span><br>
                    <b style="font-size: 16px;">%{snapshot.get('ai_analysis', {}).get('filler_val', 0):.2f}</b><br>
                    <span style="color: {'#27AE60' if snapshot.get('ai_analysis', {}).get('filler_status') == 'Uygun' else '#C0392B'}; font-size: 11px;">
                        {snapshot.get('ai_analysis', {}).get('filler_status', '-')}
                    </span>
                </div>
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <span style="font-size: 11px; color: #666;">Kum Oranı (<4mm)</span><br>
                    <b style="font-size: 16px;">%{snapshot.get('ai_analysis', {}).get('sand_val', 0):.1f}</b><br>
                    <span style="color: {'#27AE60' if snapshot.get('ai_analysis', {}).get('sand_status') == 'Stabil' else '#C0392B'}; font-size: 11px;">
                        {snapshot.get('ai_analysis', {}).get('sand_status', '-')}
                    </span>
                </div>
            </div>

            <h4 style="background: #ECF0F1; padding: 8px; border-left: 5px solid #2C3E50;">7. İLERİ ANALİTİK GÖRSELLEŞTİRME (SHILSTONE)</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="font-size: 12px;">
                    <b>Bireysel Kalan Yüzde (8-18 Kuralı)</b>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 10px;">
                        <tr style="background: #eee;">
                            <th style="border: 1px solid #ddd; padding: 2px;">Elek (mm)</th>
                            <th style="border: 1px solid #ddd; padding: 2px;">Kalan (%)</th>
                            <th style="border: 1px solid #ddd; padding: 2px;">Durum</th>
                        </tr>
                        {"".join([f"<tr><td style='border: 1px solid #ddd; padding: 2px;'>{s}</td><td style='border: 1px solid #ddd; padding: 2px;'>{r:.1f}</td><td style='border: 1px solid #ddd; padding: 2px; color: {'red' if not (8 <= r <= 18) else 'green'}'>{'!' if not (8 <= r <= 18) else '✓'}</td></tr>" for s, r in zip(snapshot.get('sieves', []), snapshot.get('ai_analysis', {}).get('retained', [])) if s > 0.063])}
                    </table>
                    <div style="margin-top: 15px; text-align: center;">
                        {retained_svg}
                    </div>
                </div>
                <div style="text-align: center; display: flex; flex-direction: column; justify-content: flex-start; gap: 10px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div style="background: #1f77b4; color: white; padding: 10px; border-radius: 5px;">
                            <span style="font-size: 10px;">WF: <b>{snapshot.get('ai_analysis', {}).get('wf', 0):.0f}</b></span>
                        </div>
                        <div style="background: #2ca02c; color: white; padding: 10px; border-radius: 5px;">
                            <span style="font-size: 10px;">CF: <b>{snapshot.get('ai_analysis', {}).get('cf', 0):.0f}</b></span>
                        </div>
                    </div>
                    <div style="margin-top: 5px; border: 1px solid #eee; padding: 5px; border-radius: 5px; background: white;">
                        {shilstone_svg}
                    </div>
                    <p style="font-size: 10px; color: #666; margin-top: 2px;">* Shilstone İşlenebilirlik Matrisi Analizi</p>
                </div>
            </div>

            <!-- İMZA BLOĞU -->
            <table style="width:100%; text-align:center; margin-top:60px; font-size:13px;">
                <tr style="font-weight:bold;">
                    <td style="width:33%;">HAZIRLAYAN</td>
                    <td style="width:34%;">KONTROL EDEN</td>
                    <td style="width:33%;">ONAYLAYAN</td>
                </tr>
                <tr style="height:60px;">
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td>(İmza / Kaşe)<br>Laboratuvar Teknik Personeli</td>
                    <td>(İmza / Kaşe)<br>Kalite Kontrol Mühendisi</td>
                    <td>(Mühür / İmza)<br>Santral / Proje Müfredatı</td>
                </tr>
            </table>
            
            <div style="margin-top: 50px; font-size: 10px; color: #95A5A6; text-align: center; border-top: 1px solid #EEE;">
                Bu belge dijital olarak oluşturulmuştur ve ıslak imza sonrası resmiyet kazanır.
            </div>
        </div>
    </div>
    """
    return html

def _generate_retained_svg(sieves, retained):
    width, height = 350, 180
    labels = [s for s in sieves if s > 0.063]
    values = retained[:len(labels)]
    if not values: return ""
    max_val = max(max(values), 25)
    bar_width = (width - 40) / len(values)
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    svg += '<line x1="30" y1="20" x2="30" y2="150" stroke="#666" stroke-width="1"/>'
    svg += '<line x1="30" y1="150" x2="340" y2="150" stroke="#666" stroke-width="1"/>'
    y8 = 150 - (8 / max_val * 130)
    y18 = 150 - (18 / max_val * 130)
    svg += f'<line x1="30" y1="{y8}" x2="340" y2="{y8}" stroke="orange" stroke-dasharray="4" stroke-width="1"/>'
    svg += f'<line x1="30" y1="{y18}" x2="340" y2="{y18}" stroke="red" stroke-dasharray="4" stroke-width="1"/>'
    for i, v in enumerate(values):
        bw = bar_width * 0.7
        bh = (v / max_val) * 130
        x = 35 + i * bar_width
        y = 150 - bh
        color = "rgba(0, 128, 128, 0.7)"
        if not (8 <= v <= 18): color = "rgba(192, 57, 43, 0.6)"
        svg += f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{color}"/>'
        if i % 2 == 0:
            svg += f'<text x="{x + bw/2}" y="165" font-size="8" text-anchor="middle" fill="#333">{labels[i]}</text>'
    svg += '</svg>'
    return svg

def _generate_shilstone_svg(cf, wf):
    width, height = 300, 200
    def tx(v): return 280 - (v / 100 * 250)
    def ty(v): return 180 - ((v - 20) / 25 * 160)
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    svg += f'<rect x="30" y="20" width="250" height="160" fill="#f9f9f9" stroke="#ddd"/>'
    pts_ii = [(75, 28), (75, 40), (45, 44), (45, 33)]
    poly_ii = " ".join([f"{tx(p[0])},{ty(p[1])}" for p in pts_ii])
    svg += f'<polygon points="{poly_ii}" fill="rgba(39, 174, 96, 0.1)" stroke="green" stroke-width="1"/>'
    px, py = tx(cf), ty(wf)
    if 30 <= px <= 280 and 20 <= py <= 180:
        svg += f'<circle cx="{px}" cy="{py}" r="4" fill="red"/>'
    svg += f'<text x="150" y="195" font-size="9" text-anchor="middle">İrilik Endeksi (CF)</text>'
    svg += f'<text x="10" y="100" font-size="9" text-anchor="middle" transform="rotate(-90 10,100)">İşlenebilirlik (WF)</text>'
    svg += '</svg>'
    return svg
def _draw_pdf_retained_chart(pdf, x, y, sieves, retained):
    """PDF üzerine 8-18 kuralı bar grafiği çizer."""
    w, h = 90, 50
    pdf.set_draw_color(100, 100, 100)
    pdf.line(x, y + h, x + w, y + h) # X axis
    pdf.line(x, y, x, y + h) # Y axis
    
    labels = [s for s in sieves if s > 0.063]
    values = retained[:len(labels)]
    if not values: return
    
    max_val = max(max(values), 25)
    bw = (w - 10) / len(values)
    
    # 8-18 Lines
    pdf.set_draw_color(255, 165, 0) # Orange
    y8 = y + h - (8 / max_val * h)
    pdf.line(x, y8, x + w, y8)
    
    pdf.set_draw_color(255, 0, 0) # Red
    y18 = y + h - (18 / max_val * h)
    pdf.line(x, y18, x + w, y18)
    
    for i, v in enumerate(values):
        bh = (v / max_val) * h
        bx = x + 5 + i * bw
        by = y + h - bh
        
        if 8 <= v <= 18:
            pdf.set_fill_color(0, 128, 128)
        else:
            pdf.set_fill_color(192, 57, 43)
        
        pdf.rect(bx, by, bw * 0.7, bh, "F")
        
        if i % 2 == 0:
            pdf.set_font("Arial", "", 6)
            pdf.text(bx, y + h + 3, str(labels[i]))

def _draw_pdf_shilstone_matrix(pdf, x, y, cf, wf):
    """PDF üzerine Shilstone İşlenebilirlik Matrisi çizer."""
    w, h = 80, 50
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(x, y, w, h)
    
    # Simple zone plotting (Conceptual)
    pdf.set_draw_color(0, 255, 0) # Green for Zone II
    # tx = x + w - (val/100 * w)
    # ty = y + h - ((val-20)/25 * h)
    
    def tx(v): return x + w - (v / 100 * w)
    def ty(v): return y + h - ((v - 20) / 25 * h)
    
    # Draw Zone II polygon
    pts = [(75, 28), (75, 40), (45, 44), (45, 33)]
    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i+1)%len(pts)]
        pdf.line(tx(p1[0]), ty(p1[1]), tx(p2[0]), ty(p2[1]))
        
    # Draw Current Point
    px, py = tx(cf), ty(wf)
    if x <= px <= x+w and y <= py <= y+h:
        pdf.set_draw_color(255, 0, 0)
        pdf.circle(px, py, 1.5)
        pdf.line(px-2, py-2, px+2, py+2)
        pdf.line(px+2, py-2, px-2, py+2)
        
    pdf.set_font("Arial", "", 7)
    pdf.text(x + w/2 - 5, y + h + 5, "CF")
    pdf.set_font("Arial", "", 7)
    # Vertical text is tricky, skipping for core parity
    pdf.text(x - 5, y + h/2, "WF")
