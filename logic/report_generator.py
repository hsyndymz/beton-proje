def generate_kgm_raporu(snapshot):
    """
    KGM Formatında (HTML) Beton Kontrol Raporu Oluşturur.
    """
    project_name = snapshot.get("project_name", "Bilinmeyen Proje")
    mix_data = snapshot.get("mix_data", {})
    decision_data = snapshot.get("decision", {})
    material_data = snapshot.get("material_data", {})
    import datetime
    bugun = datetime.datetime.now().strftime("%d-%m-%Y")
    
    # Karar Renklendirme
    status_color = "black"
    if decision_data["status"] == "RED": status_color = "red"
    elif decision_data["status"] == "YELLOW": status_color = "#D4AC0D"
    elif decision_data["status"] == "GREEN": status_color = "green"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 2px solid black;">
        <!-- BAŞLIK -->
        <table style="width:100%; border-bottom: 2px solid black; margin-bottom: 20px;">
            <tr>
                <td style="width: 20%; text-align:center;"><span style="font-size:40px;">🇹🇷</span></td>
                <td style="width: 60%; text-align:center;">
                    <h3 style="margin:0;">T.C.<br>KARAYOLLARI GENEL MÜDÜRLÜĞÜ</h3>
                    <h4 style="margin:5px;">BETON DİZAYN KONTROL RAPORU</h4>
                </td>
                <td style="width: 20%; text-align:center; font-size:12px;">
                    Tarih: {bugun}<br>
                    Form No: KGM-BTN-01
                </td>
            </tr>
        </table>
        
        <!-- PROJE BILGILERI -->
        <div style="margin-bottom: 20px;">
            <table style="width:100%; border: 1px solid #ccc; border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;"><th colspan="4" style="text-align:left; padding:5px; border:1px solid #999;">1. PROJE VE NUMUNE BİLGİLERİ</th></tr>
                <tr>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">Proje Adı:</td>
                    <td style="padding:5px; border:1px solid #ccc;">{project_name}</td>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">Beton Sınıfı:</td>
                    <td style="padding:5px; border:1px solid #ccc;">{mix_data.get('class', '-')}</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">Litoloji:</td>
                    <td style="padding:5px; border:1px solid #ccc;">{mix_data.get('lithology', '-')}</td>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">Karar Standartı:</td>
                    <td style="padding:5px; border:1px solid #ccc;">TS EN 206 / KTŞ 2013</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">Çevresel Etki:</td>
                    <td style="padding:5px; border:1px solid #ccc;">{mix_data.get('exposure_class', '-')}</td>
                    <td style="padding:5px; border:1px solid #ccc; font-weight:bold;">ASR Durumu:</td>
                    <td style="padding:5px; border:1px solid #ccc;">{mix_data.get('asr_status', '-')}</td>
                </tr>
                <tr style="font-size: 11px; color: #555;">
                    <td colspan="4" style="padding:2px 5px; border:1px solid #ccc; background-color: #fafafa;">
                        <b>Revizyon Geçmişi:</b> R0-İlk Yayın ({bugun}) | Uygulama Sürümü: v5.2-Professional
                    </td>
                </tr>
            </table>
        </div>

        <!-- MALZEME OZELLIKLERI -->
        <div style="margin-bottom: 20px;">
            <table style="width:100%; border: 1px solid black; border-collapse: collapse; text-align:center;">
                <tr style="background-color: #f0f0f0;"><th colspan="6" style="text-align:left; padding:5px; border:1px solid black;">2. AGREGA FİZİKSEL ÖZELLİKLERİ</th></tr>
                <tr style="background-color: #ddd;">
                    <th style="border:1px solid black;">Malzeme</th>
                    <th style="border:1px solid black;">Aktif</th>
                    <th style="border:1px solid black;">Yoğunluk</th>
                    <th style="border:1px solid black;">Su Emme (%)</th>
                    <th style="border:1px solid black;">LA (Aşınma)</th>
                    <th style="border:1px solid black;">MB (Metilen)</th>
                </tr>
    """
    
    # Malzeme Satırları
    mats = ["No:2", "No:1", "K.Kum", "D.Kum"]
    rhos = material_data.get("rhos", [0]*4)
    was = material_data.get("was", [0]*4)
    las = material_data.get("las", [0]*4)
    mbs = material_data.get("mbs", [0]*4)
    acts = material_data.get("active", [True]*4)
    
    for i in range(4):
        bg = "#fff" if acts[i] else "#eee"
        txt = "black" if acts[i] else "#999"
        html += f"""
        <tr style="background-color: {bg}; color: {txt};">
            <td style="border:1px solid black;">{mats[i]}</td>
            <td style="border:1px solid black;">{'✅' if acts[i] else '-'}</td>
            <td style="border:1px solid black;">{rhos[i]:.3f}</td>
            <td style="border:1px solid black;">{was[i]:.2f}</td>
            <td style="border:1px solid black;">{las[i]:.1f}</td>
            <td style="border:1px solid black;">{mbs[i]:.2f}</td>
        </tr>
        """
        
    html += f"""
        <!-- KARIŞIM DIZAYNI -->
        <div style="margin-bottom: 20px;">
            <table style="width:100%; border: 1px solid black; border-collapse: collapse; text-align:center;">
                <tr style="background-color: #f0f0f0;"><th colspan="4" style="text-align:left; padding:5px; border:1px solid black;">3. 1 m3 KARIŞIM REÇETESİ</th></tr>
                <tr style="background-color: #ddd;">
                    <th style="border:1px solid black;">Bileşen</th>
                    <th style="border:1px solid black;">Miktar (kg)</th>
                    <th style="border:1px solid black;">Bileşen</th>
                    <th style="border:1px solid black;">Miktar</th>
                </tr>
                <tr>
                    <td style="border:1px solid black; font-weight:bold;">Çimento</td>
                    <td style="border:1px solid black;">{mix_data.get('cement', 0)}</td>
                    <td style="border:1px solid black; font-weight:bold;">Su (Net)</td>
                    <td style="border:1px solid black;">{mix_data.get('water', 0)} Lt</td>
                </tr>
                <tr>
                    <td style="border:1px solid black; font-weight:bold;">Toplam Agrega</td>
                    <td style="border:1px solid black;">{int(mix_data.get('total_agg', 0))}</td>
                    <td style="border:1px solid black; font-weight:bold;">Hava</td>
                    <td style="border:1px solid black;">%{mix_data.get('air', 0)}</td>
                </tr>
                 <tr>
                    <td style="border:1px solid black; font-weight:bold;">Kimyasal Katkı</td>
                    <td style="border:1px solid black;">{mix_data.get('chem_kg', 0)} ({mix_data.get('chem_pct', 0)}%)</td>
                    <td style="border:1px solid black; font-weight:bold;">W/C Oranı</td>
                    <td style="border:1px solid black;">{mix_data.get('wc', 0):.2f}</td>
                </tr>
            </table>
        </div>
        
        <!-- DEĞERLENDİRME VE SONUÇ (MEVZUAT ATIFLI) -->
        <div style="margin-bottom: 20px; border: 2px solid {status_color}; padding: 10px;">
            <h4 style="margin-top:0; color:{status_color};">4. TEKNİK DEĞERLENDİRME SONUCU (TS EN 206'ya Göre)</h4>
            <div style="font-weight:bold; font-size:1.1em; color:{status_color};">{decision_data['title']}</div>
            <p style="font-style:italic; margin-bottom:5px;">{decision_data['main_msg']}</p>
            
            <p style="margin-top:10px; border-top: 1px solid #eee; padding-top:5px;">
                <strong>Bulgular ve Standart Uygunluk Notları:</strong>
            </p>
            <ul style="font-size: 13px;">
    """
    
    if not decision_data['violations'] and not decision_data['warnings']:
        html += "<li>Tüm parametreler TS EN 206 ve KGM Teknik Şartnamesi limitleri dahilindedir.</li>"
    else:
        for v in decision_data['violations']: html += f"<li style='color:red;'><b>İHLAL:</b> {v}</li>"
        for w in decision_data['warnings']: html += f"<li style='color:#D4AC0D;'><b>UYARI:</b> {w}</li>"
        
    html += """
            </ul>
            <p style="font-size: 10px; color: #666; margin-top:10px;">
                * Bu rapor TS EN 206 (Madde 10: Uygunluk Kontrolü) ve TS 802 hesap esaslarına göre otomatik olarak üretilmiştir.
            </p>
        </div>
        
        <!-- İMZALAR (RESMİ FORMAT) -->
        <table style="width:100%; text-align:center; margin-top:40px; border-top: 1px solid black; padding-top:10px;">
            <tr style="font-size:14px; font-weight:bold;">
                <td style="width:33%;">HAZIRLAYAN</td>
                <td style="width:34%;">KONTROL EDEN</td>
                <td style="width:33%;">ONAYLAYAN</td>
            </tr>
            <tr style="height:60px;">
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr style="font-size:12px;">
                <td>(İmza / Kaşe)<br>Laboratuvar Teknik Personeli</td>
                <td>(İmza / Kaşe)<br>Kalite Kontrol Şefi / Mühendisi</td>
                <td>(Mühür / İmza)<br>Proje Müdürü / İdare Yetkilisi</td>
            </tr>
        </table>
    </div>
    """
    return html
