import numpy as np

def generate_regulatory_text(decision_data):
    """
    TS EN 206 ve TS 802 standartlarına göre uygunluk metni üretir.
    """
    status = decision_data.get('status', 'YELLOW')
    
    if status == "GREEN":
        return "TS EN 206 ve Karayolları Teknik Şartnamesi (KTŞ 2013) hükümlerine göre yapılan teknik inceleme sonucunda; karışım tasarımı ve mevcut kalite kontrol verilerinin ilgili standart limitlerini tam olarak karşıladığı ve 'UYGUN' olduğu mütalaa edilmiştir."
    elif status == "YELLOW":
        return "Yapılan teknik incelemede, temel kriterlerin (dayanım vb.) sağlandığı görülmüştür. Ancak bazı yardımcı metriklerde (gradasyon sapması, kirlilik vb.) sınır değerlere yaklaşıldığı tespit edilmiştir. Bu durumun beton performansını kritik düzeyde etkilemeyeceği öngörülmekle birlikte, saha uygulamasında hassasiyet gösterilmesi kaydıyla 'ŞARTLI UYGUN' olarak değerlendirilmiştir."
    else:
        return "TS EN 206 ve KTŞ standartları çerçevesinde yapılan değerlendirmede; tasarım parametrelerinin (W/C, çimento dozajı veya dayanım öngörüsü) belirtilen teknik kısıtları sağlamadığı tespit edilmiştir. Mevcut haliyle betonun servis ömrü ve yapısal güvenliği açısından risk oluşturabileceği değerlendirildiğinden tasarım 'UYGUN DEĞİL' (RED) olarak raporlanmıştır."

def build_grading_comment(grade_violation, grade_dev):
    """
    Gradasyon (TS 802) durumuna göre teknik yorum üretir.
    """
    if not grade_violation and grade_dev < 1.0:
        return "Karma agrega gradasyonu TS 802 standart bölgeleri ve ideal eğri ile tam uyum içerisindedir. Kompakt yapının sağlanmasıyla taze beton işlenebilirliğinin olumlu etkileneceği öngörülmektedir."
    elif grade_violation:
        return f"Karma gradasyon eğrisinde belirlenen limitlerin dışına (Sapma: {grade_dev:.1f}) çıkıldığı görülmüştür. Bu durum, betonun boşluk yapısını ve segregasyon direncini etkileyebilir. Granülometri iyileştirmesi önerilir."
    else:
        return "Gradasyon eğrisi standart bölge sınırları içerisinde kalmakta olup kabul edilebilir düzeydedir."

def build_strength_decision(pred_mpa, target_mpa):
    """
    Dayanım performansı için sonuç metni üretir.
    """
    diff = pred_mpa - target_mpa
    if diff >= 0:
        return f"28 günlük öngörülen basınç dayanımı ({pred_mpa:.1f} MPa), hedeflenen {target_mpa} MPa değerinin üzerinde gerçekleşmiştir. Tasarım, yapısal dayanım kriterlerini güvenle karşılamaktadır."
    elif diff > -3.0:
        return f"Öngörülen dayanım ({pred_mpa:.1f} MPa) hedef değerin ({target_mpa} MPa) bir miktar altında kalsa da, istatistiksel toleranslar dahilinde değerlendirilebilir."
    else:
        return f"Hesaplanan beton dayanımı ({pred_mpa:.1f} MPa), hedeflenen {target_mpa} MPa değerinin kritik düzeyde altındadır. Reçete revizyonu veya saha faktörü iyileştirmesi zaruridir."
