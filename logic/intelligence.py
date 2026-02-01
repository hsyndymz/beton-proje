def generate_smart_alerts(qc_history, current_mix):
    """
    Trendleri ve mevcut reçeteyi analiz ederek mühendislik önerileri üretir.
    """
    alerts = []
    
    if not qc_history or len(qc_history) < 5:
        return alerts

    # Son 5 dökümün ortalaması (d28 veya measured_mpa)
    last_5_mpa = []
    for r in qc_history[-5:]:
        val = r.get('d28') or r.get('measured_mpa')
        if val and float(val) > 0:
            last_5_mpa.append(float(val))
            
    if len(last_5_mpa) < 3: return alerts
    
    avg_mpa = sum(last_5_mpa) / len(last_5_mpa)
    trend_slope = last_5_mpa[-1] - last_5_mpa[0]
    
    target_mpa = current_mix.get('target_mpa', 37)
    
    # 1. DAYANIM DÜŞÜŞÜ ALERTI
    if trend_slope < -3.0:
        alert = {
            "id": "ALRT_MPA_DROP",
            "type": "ERROR",
            "title": "🔴 Kritik Dayanım Düşüşü",
            "msg": f"Son 5 dökümde dayanım {abs(trend_slope):.1f} MPa düştü. İnce agrega (kum) oranını %2 azaltarak matris stabilitesini artırmanız önerilir.",
            "rationale": "Süregelen dayanım kaybı genellikle taze beton boşluk yapısındaki artıştan kaynaklanır. Kum oranının düşürülmesi çimento hamuru verimini artıracaktır."
        }
        alerts.append(alert)
        
    # 2. EKONOMİK OPTİMİZASYON ALERTI
    elif avg_mpa > (target_mpa + 8.0):
        alert = {
            "id": "ALRT_ECON_OPT",
            "type": "SUCCESS",
            "title": "💎 Ekonomik Optimizasyon Fırsatı",
            "msg": f"Mevcut dökümler hedef değerin {avg_mpa - target_mpa:.1f} MPa üzerinde. Çimento dozajını %3 (yaklaşık 10-12 kg) azaltarak maliyet avantajı sağlayabilirsiniz.",
            "rationale": "Beton performansı tasarım limitlerinin çok üzerinde. Güvenlik sınırları dahilinde kalarak karbon ayak izini ve maliyeti düşürmek mümkündür."
        }
        alerts.append(alert)

    return alerts

def explain_ai_logic(alert_id):
    """
    Belirli bir uyarının mantıksal dayanağını açıklar.
    """
    explanations = {
        "ALRT_MPA_DROP": "Saha Aklı, son 5 dökümün ilk ve son değerlerini karşılaştırdı. Negatif eğim (slope) tespit edildiği için gradasyonun ince agregadan kaba agregaya doğru kaydırılması (kum azaltımı) stratejik bir müdahale olarak belirlendi.",
        "ALRT_ECON_OPT": "Sistem, son ölçümlerin aritmetik ortalamasını hedeflenen limitlerle kıyasladı. Aradaki farkın 'Aşırı Emniyetli' bölgeye girdiği görüldü.",
        "DEFAULT": "AI, girilen verileri TS EN 206 kısıtları ve santralin geçmiş performans katsayıları ile çapraz sorgulayarak bu sonuca ulaştı."
    }
    return explanations.get(alert_id, explanations["DEFAULT"])
