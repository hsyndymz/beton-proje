from logic.report_engine import generate_regulatory_text, build_grading_comment, build_strength_decision
import datetime

def generate_kgm_raporu(snapshot):
    """
    TSE ve KTŞ standartlarına tam uyumlu, profesyonel beton kontrol raporu oluşturur.
    Snapshot içinden metadata (İdare, Yüklenici vb.) verilerini de kullanır.
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
    
    # Engine'den Mevzuat ve Teknik Metinleri Çek
    reg_text = generate_regulatory_text(decision_data)
    grading_text = build_grading_comment(mix_data.get('grading_violation', False), mix_data.get('grading_dev', 0.0))
    strength_text = build_strength_decision(mix_data.get('pred_mpa', 0), 37) # Varsayılan C30/37 için 37 hedef

    # Karar Renklendirme
    status_color = "black"
    if decision_data["status"] == "RED": status_color = "#C0392B"
    elif decision_data["status"] == "YELLOW": status_color = "#D4AC0D"
    elif decision_data["status"] == "GREEN": status_color = "#27AE60"
    
    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: auto; color: #333; line-height: 1.6;">
        
        <!-- SAYFA 1: KAPAK -->
        <div style="height: 1000px; border: 15px double #2C3E50; padding: 50px; text-align: center; display: flex; flex-direction: column; justify-content: center; margin-bottom: 50px; background: white; page-break-after: always;">
            <div style="font-size: 50px;">🇹🇷</div>
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
                Bu rapor TS EN 206, TS 802 ve KTŞ 2013 standartları çerçevesinde <br>
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
                ve Karayolları Teknik Şartnamesi (KTŞ 2013) hükümleri doğrultusunda, belirtilen beton sınıfı için yapılan
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
    mats = ["No:2 (15-25)", "No:1 (5-15)", "K.Kum (0-5)", "D.Kum (0-7)"]
    
    for i in range(4):
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
                <h5 style="margin: 0; color: {status_color}; font-size: 16px;">SONUÇ: {decision_data['title']}</h5>
                <p style="font-size: 14px; margin-top: 10px;"><b>{reg_text}</b></p>
                
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

            <!-- İMZA BLOĞU -->
            <table style="width:100%; text-align:center; margin-top:80px; font-size:13px;">
                <tr style="font-weight:bold;">
                    <td style="width:33%;">HAZIRLAYAN</td>
                    <td style="width:34%;">KONTROL EDEN</td>
                    <td style="width:33%;">ONAYLAYAN</td>
                </tr>
                <tr style="height:80px;">
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
