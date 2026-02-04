import numpy as np
from scipy.optimize import minimize

# --- 2.1 KURAL MOTORU VERİTABANI (Decision Engine Rules) ---
CONCRETE_RULES = {
    "C20/25": {"min_mpa": 25, "max_wc": 0.60, "min_cem": 260, "desc": "Düşük dayanım sınıfı. Çevresel etki: X0"},
    "C25/30": {"min_mpa": 30, "max_wc": 0.60, "min_cem": 280, "desc": "Orta dayanım sınıfı. Çevresel etki: XC1"},
    "C30/37": {"min_mpa": 37, "max_wc": 0.55, "min_cem": 300, "desc": "Yaygın yapısal beton. Çevresel etki: XC2/XC3"},
    "C35/45": {"min_mpa": 45, "max_wc": 0.50, "min_cem": 320, "desc": "Yüksek dayanım ve dayanıklılık. Çevresel etki: XD1/XS1"},
    "C40/50": {"min_mpa": 50, "max_wc": 0.45, "min_cem": 340, "desc": "Özel projeler, köprüler. Çevresel etki: XD2/XS2"},
    "C50/60+": {"min_mpa": 60, "max_wc": 0.40, "min_cem": 360, "desc": "Çok yüksek dayanım."}
}

# TS EN 206 Çevresel Etki Sınıfları ve Kısıtlar (KTŞ Uyumlu)
EXPOSURE_CLASSES = {
    "X0": {"max_wc": 1.00, "min_cem": 0, "min_class": "C12/15", "desc": "Korozyon Riski Yok"},
    "XC1": {"max_wc": 0.65, "min_cem": 260, "min_class": "C20/25", "desc": "Karbonatlaşma - Kuru/Sürekli Islak"},
    "XC2": {"max_wc": 0.60, "min_cem": 280, "min_class": "C25/30", "desc": "Karbonatlaşma - Islak, Nadiren Kuru"},
    "XC3": {"max_wc": 0.55, "min_cem": 280, "min_class": "C30/37", "desc": "Karbonatlaşma - Orta Rutubet"},
    "XC4": {"max_wc": 0.50, "min_cem": 300, "min_class": "C30/37", "desc": "Karbonatlaşma - Periyodik Islak/Kuru"},
    "XD1": {"max_wc": 0.55, "min_cem": 300, "min_class": "C30/37", "desc": "Klorür - Orta Rutubet"},
    "XD2": {"max_wc": 0.50, "min_cem": 320, "min_class": "C30/37", "desc": "Klorür - Islak, Nadiren Kuru"},
    "XD3": {"max_wc": 0.45, "min_cem": 340, "min_class": "C35/45", "desc": "Klorür - Islak/Kuru Döngüsü"},
    "XF1": {"max_wc": 0.55, "min_cem": 300, "min_class": "C30/37", "desc": "Donma-Çözülme - Orta Doygunluk, Buz çözücü yok"},
    "XF2": {"max_wc": 0.55, "min_cem": 300, "min_class": "C25/30", "desc": "Donma-Çözülme - Orta Doygunluk + Buz çözücü"},
    "XF3": {"max_wc": 0.50, "min_cem": 320, "min_class": "C30/37", "desc": "Donma-Çözülme - Yüksek Doygunluk, Buz çözücü yok"},
    "XF4": {"max_wc": 0.45, "min_cem": 340, "min_class": "C30/37", "desc": "Donma-Çözülme - Yüksek Doygunluk + Buz çözücü (Hava Gerekli)"}
}

# Litolojiye Bağlı Otomatik ASR Risk Matrisi
ASR_LITHOLOGY_RISK = {
    "Bazalt (Diyarbakır/Gaziantep)": "Düşük (İnert)",
    "Kalker (Mardin/Şanlıurfa)": "Düşük-Orta",
    "Dere Malzemesi (Dicle/Fırat)": "Yüksek (Potansiyel Reaktif)",
    "Kalker (Standart)": "Düşük",
    "Bazalt (Standart)": "Düşük",
    "Granit": "Orta"
}

# Litolojiye Bağlı Performans Katsayıları (Güneydoğu Anadolu & Standart)
LITHOLOGY_FACTORS = {
    "Bazalt (Diyarbakır/Gaziantep)": 1.07,
    "Kalker (Mardin/Şanlıurfa)": 0.98,
    "Dere Malzemesi (Dicle/Fırat)": 0.95,
    "Kalker (Standart)": 1.00,
    "Bazalt (Standart)": 1.05,
    "Granit": 1.02
}

# TS 802 STANDART GRANÜLOMETRİ EĞRİLERİ (DIN 1045 Referanslı)
STD_GRADING_DB = {
    31.5: {
        "A (Kaba)":   {40.0: [100,100], 31.5: [94,94], 22.4: [86,86], 16.0: [72,72], 11.2: [57,57], 8.0: [41,41], 4.0: [29,29], 2.0: [20,20], 1.0: [14,14], 0.5: [10,10], 0.25: [6,6], 0.15: [3,3], 0.063: [1,1], 0.0: [0,0]},
        "B (İdeal)":  {40.0: [100,100], 31.5: [100,100], 22.4: [100,100], 16.0: [92,92], 11.2: [79,79], 8.0: [63,63], 4.0: [49,49], 2.0: [37,37], 1.0: [28,28], 0.5: [20,20], 0.25: [13,13], 0.15: [7,7], 0.063: [3,3], 0.0: [0,1]},
        "C (İnce)":   {40.0: [100,100], 31.5: [98,98], 22.4: [96,96], 16.0: [91,91], 11.2: [82,82], 8.0: [71,71], 4.0: [59,59], 2.0: [48,48], 1.0: [38,38], 0.5: [28,28], 0.25: [18,18], 0.15: [10,10], 0.063: [5,5], 0.0: [0,2]}
    },
    22.4: {
        "A (Kaba)":   {40.0: [100,100], 31.5: [94,94], 22.4: [86,86], 16.0: [72,72], 11.2: [57,57], 8.0: [41,41], 4.0: [29,29], 2.0: [20,20], 1.0: [14,14], 0.5: [10,10], 0.25: [6,6], 0.15: [3,3], 0.063: [1,1], 0.0: [0,0]},
        "B (İdeal)":  {40.0: [100,100], 31.5: [100,100], 22.4: [100,100], 16.0: [92,92], 11.2: [79,79], 8.0: [63,63], 4.0: [49,49], 2.0: [37,37], 1.0: [28,28], 0.5: [20,20], 0.25: [13,13], 0.15: [7,7], 0.063: [3,3], 0.0: [0,1]},
        "C (İnce)":   {40.0: [100,100], 31.5: [98,98], 22.4: [96,96], 16.0: [91,91], 11.2: [82,82], 8.0: [71,71], 4.0: [59,59], 2.0: [48,48], 1.0: [38,38], 0.5: [28,28], 0.25: [18,18], 0.15: [10,10], 0.063: [5,5], 0.0: [0,2]}
    },
    16.0: {
        "A (Kaba)":   {16.0: [100,100], 8.0: [55,70], 4.0: [35,50], 2.0: [22,38], 1.0: [12,25], 0.25: [4,12], 0.0: [0,5]},
        "B (İdeal)":  {16.0: [100,100], 8.0: [70,85], 4.0: [50,62], 2.0: [35,48], 1.0: [22,32], 0.25: [8,15], 0.0: [2,6]},
        "C (İnce)":   {16.0: [100,100], 8.0: [85,95], 4.0: [62,75], 2.0: [48,60], 1.0: [32,45], 0.25: [14,24], 0.0: [4,10]}
    }
}

def calculate_passing(m1, weights):
    if m1 <= 0: return [100.0] * len(weights)
    cumulative_retained = np.cumsum(weights)
    passing_pct = 100 - (cumulative_retained / m1 * 100)
    return np.clip(passing_pct, 0, 100)

def get_std_limits(dmax, curve_type, elek_serisi):
    limits_dict = STD_GRADING_DB.get(dmax, {}).get(curve_type, {})
    std_sieves = sorted(list(limits_dict.keys()), reverse=True)
    
    alt_points = []
    ust_points = []
    
    for e in elek_serisi:
        if e in limits_dict:
            alt_points.append(limits_dict[e][0])
            ust_points.append(limits_dict[e][1])
            continue
            
        s1, s2 = None, None
        for s in std_sieves:
            if s > e: s1 = s
            else: s2 = s; break
        
        if s1 is not None and s2 is not None:
            log_e, log_s1, log_s2 = np.log(e), np.log(s1), np.log(s2)
            denom = log_s2 - log_s1
            
            if denom != 0:
                ratio = (log_e - log_s1) / denom
                # Alt Limit
                y1, y2 = limits_dict[s1][0], limits_dict[s2][0]
                alt_points.append(y1 + ratio * (y2 - y1))
                # Üst Limit
                y1, y2 = limits_dict[s1][1], limits_dict[s2][1]
                ust_points.append(y1 + ratio * (y2 - y1))
            else:
                alt_points.append(limits_dict[s1][0])
                ust_points.append(limits_dict[s1][1])
            
        elif s1 is None: 
            alt_points.append(100.0); ust_points.append(100.0)
        elif s2 is None:
             alt_points.append(limits_dict[s1][0]); ust_points.append(limits_dict[s1][1])

    return alt_points, ust_points

def optimize_mix(target_curve_type, dmax, active_mats, all_passing_dfs, elek_serisi, materials):
    alt, ust = get_std_limits(dmax, target_curve_type, elek_serisi)
    target_y = (np.array(alt) + np.array(ust)) / 2 
    
    active_indices = [i for i, x in enumerate(active_mats) if x]
    if not active_indices: return None
    
    A = []
    for mat_idx in active_indices:
        mat_name = materials[mat_idx]
        vals = all_passing_dfs.get(mat_name, [0]*len(elek_serisi))
        A.append(vals)
        
    A = np.array(A).T 
    
    def cost_fn(weights):
        mix_grading = np.dot(A, weights)
        # Kareler toplamı hatası + Mühendislik kısıtı (Kum oranı cezası)
        error = np.sum((mix_grading - target_y)**2)
        return error

    n = len(active_indices)
    init_guess = [100/n] * n
    
    # Kısıtlar: Toplam %100 olmalı
    cons = [{'type': 'eq', 'fun': lambda x:  np.sum(x) - 100}]
    
    # Sınırlar: %0 - %100 arası, ancak kum (0-5 veya 0-7) için min %30 kısıtı ekleyelim (Gerçekçi olması için)
    bnds = []
    for idx in active_indices:
        mat_lower = 0.0
        # Eğer malzeme adında "Kum" geçiyorsa, genellikle en az %25-30 gerekir.
        if "Kum" in materials[idx]: mat_lower = 25.0
        bnds.append((mat_lower, 100.0))
    
    res = minimize(cost_fn, init_guess, method='SLSQP', bounds=tuple(bnds), constraints=cons)
    return res.x if res.success else None

def evaluate_mix_compliance(mix_data):
    target_class = mix_data.get("class", "C30/37")
    rules = CONCRETE_RULES.get(target_class, CONCRETE_RULES["C30/37"])
    
    # --- Durabilite Kısıtları (TS EN 206 / KTŞ) ---
    exp_class = mix_data.get("exposure_class", "XC3")
    exp_limits = EXPOSURE_CLASSES.get(exp_class, EXPOSURE_CLASSES["XC3"])
    
    violations = []
    warnings = []
    rationales = []
    
    # 1. Çevresel Etki Denetimi
    limit_wc_exp = exp_limits["max_wc"]
    current_wc = mix_data.get("wc", 0.0)
    if current_wc > limit_wc_exp:
        violations.append(f"🔴 Durabilite İhlali ({exp_class}): Su/Çimento {current_wc:.2f} > {limit_wc_exp} (Max) - [TS EN 206]")
        rationales.append(f"{exp_class} çevresel etki sınıfı için gereken maksimum W/C oranı aşıldı. Bu durum betonun servis ömrünü (donma, korozyon vb.) kritik düzeyde azaltır.")

    limit_cem_exp = exp_limits["min_cem"]
    curr_cem = mix_data.get("cement", 0)
    if curr_cem < limit_cem_exp:
        violations.append(f"🔴 Durabilite İhlali ({exp_class}): Çimento {curr_cem} < {limit_cem_exp} (Min) - [KTŞ 2013]")
        rationales.append(f"{exp_class} sınıfı için gerekli olan minimum çimento dozajı sağlanamadı. Agregaların yeterince sarılmaması durabilite riski yaratır.")

    # 2. ASR Risk Denetimi
    asr_status = mix_data.get("asr_status", "Düzeltme Gerekmiyor")
    if "Reaktif" in asr_status:
        warnings.append(f"⚠️ ASR Riski: Agrega '{asr_status}' olarak işaretlendi. [KTŞ Bölüm 414]")
        rationales.append("Alkali-Silika Reaksiyonu riskine karşı düşük alkalili çimento veya mineral katkı (Uçucu Kül/Silis Dumanı) kullanımı şarttır.")

    # 3. Genel Standart Denetimi (Önceki kısımlar korunur)
    limit_wc = rules["max_wc"]
    if current_wc > (limit_wc + 0.02):
        violations.append(f"🔴 Dayanım Sınıfı İhlali: W/C {current_wc:.2f} > {limit_wc} - [TS EN 206]")
        
    limit_mpa = rules["min_mpa"]
    pred_mpa = mix_data.get("pred_mpa", 0.0)
    if pred_mpa < (limit_mpa - 2.0):
        violations.append(f"🔴 Dayanım Yetersiz: Tahmin {pred_mpa:.1f} MPa < Hedef {limit_mpa} MPa")
        
    if mix_data.get("grading_violation", False):
        dev = mix_data.get("grading_dev", 0.0)
        if dev > 5.0: 
            violations.append(f"🔴 TS 802 Gradasyon İhlali (Sapma: {dev:.1f})")
            
    avg_la = mix_data.get("avg_la", 0.0)
    if avg_la > 35.0: 
        violations.append(f"🔴 Yüksek Aşınma (LA): {avg_la:.1f} > 35. Uygun değil.")
        
    avg_mb = mix_data.get("avg_mb", 0.0)
    if avg_mb > 1.5: 
        violations.append(f"🔴 Kirli Agrega (MB): {avg_mb:.2f} > 1.5 (Kil var).")
         
    if len(violations) > 0:
        status, title, main_msg = "RED", "UYGUN DEĞİLDİR (RED)", "Durabilite ve Standart limitleri aşıldı."
    elif len(warnings) > 0:
        status, title, main_msg = "YELLOW", "ŞARTLI KABUL", "ASR veya performans riskleri mevcut."
    else:
        status, title, main_msg = "GREEN", "UYGUNDUR (KABUL)", "Tüm KTŞ ve TS EN 206 limitlerine uygun."
        
    return {
        "status": status, 
        "title": title, 
        "main_msg": main_msg, 
        "violations": violations, 
        "warnings": warnings,
        "rationales": rationales
    }

# --- 4. MÜHENDİSLİK AI MOTORU ---

def calculate_theoretical_mpa(wc_ratio, air_content):
    if wc_ratio <= 0: return 0.0
    base_mpa = 37.0 * (0.55 / wc_ratio)
    air_penalty_pct = (air_content - 1.5) * 5.0 if air_content > 1.5 else 0.0
    final_mpa = base_mpa * (1 - (air_penalty_pct / 100.0))
    return max(0, final_mpa)

def update_site_factor(predicted, measured, old_factor):
    if predicted <= 0 or measured <= 0: return old_factor
    ratio = measured / predicted
    clamped_ratio = max(0.9, min(1.1, ratio))
    new_factor = old_factor * clamped_ratio
    return round(max(0.80, min(1.20, new_factor)), 3)

def evolve_site_factor(qc_history, current_factor):
    """
    Geçmiş kırım verilerini analiz ederek saha faktörünü dinamik olarak evrimleştirir.
    """
    if not qc_history or len(qc_history) < 5:
        return current_factor
    
    ratios = []
    for r in qc_history[-10:]:
        measured = r.get('d28') or r.get('measured_mpa')
        predicted = r.get('predicted_mpa')
        if measured and predicted and float(predicted) > 0:
            ratios.append(float(measured) / float(predicted))
            
    if not ratios:
        return current_factor
        
    avg_ratio = sum(ratios) / len(ratios)
    # Yumuşatma (Smoothing): Mevcut faktörü yavaşça değiştir
    new_factor = current_factor * (0.7 + 0.3 * avg_ratio)
    return round(max(0.70, min(1.30, new_factor)), 3)

def classify_plant(records):
    """
    Santralin tutarlılığını (standart sapma) ölçer.
    'records' hem yerel QC geçmişi hem de global havuz verilerini içerebilir.
    """
    valid_diffs = []
    for r in records:
        # Hem 'measured_mpa' (eski) hem 'd28' (yeni) desteği
        measured = r.get('d28') or r.get('measured_mpa')
        predicted = r.get('predicted_mpa')
        
        if measured and predicted:
            if float(measured) > 0 and float(predicted) > 0:
                valid_diffs.append(float(measured) - float(predicted))
    
    if len(valid_diffs) < 5: 
        # Eğer sistematik sapma ölçülemiyorsa ama havuz verisi varsa 'Global AI' diyelim
        if len(records) >= 5:
            return "🧠 Global AI Aktif", "blue"
        return "Veri Yetersiz", "gray"
    
    sigma = np.std(valid_diffs, ddof=1)
    if sigma < 3.0: return "🟢 A Sınıfı (Güvenilir)", "green"
    elif sigma < 5.0: return "🟡 B Sınıfı (Orta)", "orange"
    else: return "🔴 C Sınıfı (Riskli)", "red"

def best_wc_estimate(records, target_class):
    good_wcs = []
    target_mpa = 30
    if "C30" in target_class: target_mpa = 37
    elif "C25" in target_class: target_mpa = 30
    elif "C35" in target_class: target_mpa = 45
    elif "C40" in target_class: target_mpa = 50
    
    for r in records:
        m = float(r.get('d28', 0)); w = float(r.get('water', 0)); c = float(r.get('cement', 0))
        if m >= target_mpa and c > 0 and w > 0:
            wc = w / c
            if 0.3 < wc < 0.8: good_wcs.append(wc)
    return round(sum(good_wcs)/len(good_wcs), 3) if good_wcs else None

def qc_analysis_engine(expected_mpa, measured_mpa, wc_ratio, air_content, fines_ratio, curing_condition="Normal"):
    reasons = []
    diff = measured_mpa - expected_mpa
    if diff < -3.0:
        if wc_ratio > 0.55: 
            reasons.append("Su/Çimento oranı kritik düzeyin üzerinde. Fazla su, betonun iç yapısında daha fazla kapiler boşluk oluşturarak dayanımı düşürmüştür.")
        if air_content > 2.0: 
            reasons.append("Sürüklenmiş veya hapsolmuş hava miktarı yüksek. Her %1 fazla hava, basınç dayanımında yaklaşık %5 kayba yol açar.")
        if fines_ratio > 45.0: 
            reasons.append("İnce agrega (kum) oranı çok yüksek. Bu durum agregaların toplam yüzey alanını artırarak çimento hamurunun yetersiz kalmasına neden olmuş olabilir.")
        if curing_condition != "Normal": 
            reasons.append("Kür koşulları yetersiz. Betonun erken yaşta su kaybetmesi hidratasyonun durmasına ve yüzeyel çatlaklarla dayanım kaybına yol açar.")
        
        if not reasons: 
            reasons.append("Belirsiz hata. Agrega kirliliği, çimento kalitesi veya hatalı numune alma/test süreci incelenmelidir.")
            
    elif diff > 3.0:
        reasons.append("Dayanım beklentinin üzerinde. Bu durum ekonomik açıdan reçetenin optimize edilebileceğini (çimento azaltımı) gösterir.")
        
    return reasons, diff
