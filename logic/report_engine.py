import numpy as np

def generate_regulatory_text(decision_data):
    """
    TS EN 206 ve KTŞ 2016 (Bölüm 406) standartlarına göre resmi uygunluk metni üretir.
    """
    status = decision_data.get('status', 'YELLOW')
    
    if status == "GREEN":
        return "TS EN 206 Tablo 11 (Uygunluk Kriterleri) ve Karayolları Teknik Şartnamesi (KTŞ 2016) Bölüm 406.4 hükümleri çerçevesinde yapılan teknik inceleme sonucunda; tasarım parametrelerinin ve kalite kontrol toleranslarının ilgili standart limitlerini tam olarak karşıladığı ve 'TEKNİK OLARAK UYGUN' olduğu mütalaa edilmiştir."
    elif status == "YELLOW":
        return "Yapılan teknik tetkik sonucunda, temel karakteristiklerin (basınç dayanımı vb.) TS EN 206 limitleri dahilinde olduğu görülmüştür. Ancak gradasyon sapmaları veya mineral yapı limitlerinde sınır değerlere yaklaşıldığı (KTŞ 2016 Madde 406.2.2) tespit edilmiştir. Bu durumun yapısal güvenliği tehdit etmediği öngörüldüğünden, saha uygulamasında kalite kontrol sıklığının artırılması kaydıyla 'KOŞULLU UYGUNLUK' verilmiştir."
    else:
        return "TS EN 206 Bölüm 5 (Teknik Özellikler) ve KTŞ 2016 Madde 406 kısıtları dahilinde yapılan değerlendirmede; tasarımın (W/C oranı, asgari çimento dozajı veya tahmini dayanım) zorunlu teknik kriterleri sağlamadığı tespit edilmiştir. Mevcut haliyle betonun durabilite (servis ömrü) ve yapısal güvenlik açısından risk teşkil ettiği değerlendirildiğinden tasarım 'RED' (UYGUN DEĞİL) olarak raporlanmıştır."

def build_grading_comment(grade_violation, grade_dev):
    """
    Gradasyon (TS 802 ve KTŞ 406) durumuna göre teknik yorum üretir.
    """
    if not grade_violation and grade_dev < 1.0:
        return "Karma agrega gradasyonu TS 802 ve KTŞ 2016 Tablo 406-1 ideal granulometri sınırları ile tam uyum içerisindedir. Kompakt iskelet yapısının taze beton kararlılığını ve nihai dayanımı olumlu yönde maksimize edeceği mütalaa edilmektedir."
    elif grade_violation:
        return f"Karma gradasyon eğrisinde KTŞ 2016 Bölüm 406.2.1'de belirlenen limitlerin dışına (Sapma: {grade_dev:.1f}) çıkıldığı tespit edilmiştir. Bu durumun boşluk yapısı üzerinde 'gap-grading' riski oluşturabileceği değerlendirilmektedir."
    else:
        return "Gradasyon eğrisi, TS 802 standart bölge sınırları içerisinde kalarak mühendislik kriterlerini asgari düzeyde karşılamaktadır."

def build_strength_decision(pred_mpa, target_mpa):
    """
    Dayanım performansı için TS EN 206 tabanlı teknik sonuç metni üretir.
    """
    diff = pred_mpa - target_mpa
    if diff >= 0:
        return f"Öngörülen 28 günlük basınç dayanımı ({pred_mpa:.1f} MPa), TS EN 206 uyarınca hedeflenen {target_mpa} MPa (fck,cube) kriterini güvenle sağlamaktadır. Tasarım, yapısal yükleme kısıtlarını mühendislik emniyet katsayıları dahilinde karşılamaktadır."
    elif diff > -3.0:
        return f"Öngörülen dayanım ({pred_mpa:.1f} MPa) hedef değerin ({target_mpa} MPa) nominal düzeyde altında kalsa da, saha faktörü ve istatistiksel standart sapma toleransları dahilinde değerlendirilebilir."
    else:
        return f"Hesaplanan beton dayanımı ({pred_mpa:.1f} MPa), hedeflenen {target_mpa} MPa değerinin kritik düzeyde altındadır. TS EN 206 Bölüm 8 hükümleri uyarınca tasarımın revize edilmesi veya çimento dozajının/su-çimento oranının iyileştirilmesi zaruridir."
