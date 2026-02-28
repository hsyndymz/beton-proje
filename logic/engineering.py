import numpy as np
from scipy.optimize import minimize
def predict_90d_strength(d28_mpa, cement_pct=100.0, slag_pct=0.0, ash_pct=0.0):
    """
    Puzolanik aktiviteye göre 90 günlük dayanım tahmini.
    CEM I: +%10-15
    Cüruf: +%25-35 (Geç dayanım kazancı yüksektir)
    """
    # Baz katsayılar (Öğrenilen Mühendislik Verisi)
    k_cem = 1.12
    k_slag = 1.35
    k_ash = 1.25
    
    total = cement_pct + slag_pct + ash_pct
    if total <= 0: return d28_mpa * k_cem
    
    # Ağırlıklı katsayı
    composite_k = (cement_pct * k_cem + slag_pct * k_slag + ash_pct * k_ash) / total
    return round(d28_mpa * composite_k, 1)

# --- 2.1 KURAL MOTORU VERİTABANI (Decision Engine Rules) ---
CONCRETE_RULES = {
    "C20/25": {"min_mpa": 25, "max_wc": 0.60, "min_cem": 260, "desc": "Düşük dayanım sınıfı. Çevresel etki: X0"},
    "C25/30": {"min_mpa": 30, "max_wc": 0.60, "min_cem": 280, "desc": "Orta dayanım sınıfı. Çevresel etki: XC1"},
    "C30/37": {"min_mpa": 37, "max_wc": 0.55, "min_cem": 300, "desc": "Yaygın yapısal beton. Çevresel etki: XC2/XC3"},
    "C35/45": {"min_mpa": 45, "max_wc": 0.50, "min_cem": 320, "desc": "Yüksek dayanım ve dayanıklılık. Çevresel etki: XD1/XS1"},
    "C40/50": {"min_mpa": 50, "max_wc": 0.45, "min_cem": 340, "desc": "Özel projeler, köprüler. Çevresel etki: XD2/XS2"},
    "C50/60+": {"min_mpa": 60, "max_wc": 0.40, "min_cem": 360, "desc": "Çok yüksek dayanım."}
}

# --- TS 802 HEDEF DAYANIM (fcm) HESAPLAMA ---
def get_target_strength_fcm(fck, sigma=None):
    """
    TS 802 - Çizelge 7: Hedef Basınç Dayanımı Belirleme (MPa)
    sigma: Standart Sapma (MPa)
    """
    if sigma is not None and sigma > 0:
        # sigma biliniyorsa (Çizelge 7.a)
        fcm = fck + 1.48 * sigma
    else:
        # sigma bilinmiyorsa (Çizelge 7.b - Muhafazakar yaklaşım)
        if fck <= 20: fcm = fck + 8
        elif fck <= 35: fcm = fck + 10
        else: fcm = fck + 12
    return round(fcm, 1)

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

# TSE 802 Dmax Bağımlı Elek Serileri (Standart 13 Elek - Büyükten Küçüğe)
SIEVE_SETS = {
    31.5: [40, 31.5, 22.4, 16, 11.2, 8, 4, 2, 1, 0.5, 0.25, 0.15, 0.063],
    22.4: [40, 31.5, 22.4, 16, 11.2, 8, 4, 2, 1, 0.5, 0.25, 0.15, 0.063],
    16.0: [16, 11.2, 8, 4, 2, 1, 0.5, 0.25, 0.15, 0.063]
}

# TS 802 STANDART GRANÜLOMETRİ EĞRİLERİ (DIN 1045 Referanslı)
STD_GRADING_DB = {
    31.5: {
        # KTŞ 2023 / TS 802 Genel Beton (Alt, İdeal, Üst Limitler)
        "A (Alt)":   {40.0: [100,100], 31.5: [90,90], 22.4: [72,72], 16.0: [58,58], 11.2: [45,45], 8.0: [35,35], 4.0: [22,22], 2.0: [14,14], 1.0: [9,9],   0.5: [5,5],   0.25: [1,1],   0.15: [0,0], 0.063: [0,0], 0.0: [0,0]},
        "B (İdeal)": {40.0: [100,100], 31.5: [96,96], 22.4: [91,91], 16.0: [82,82], 11.2: [70,70], 8.0: [56,56], 4.0: [45,45], 2.0: [35,35], 1.0: [26,26], 0.5: [19,19], 0.25: [12,12], 0.15: [7,7], 0.063: [3,3], 0.0: [0,1]},
        "C (Üst)":   {40.0: [100,100], 31.5: [100,100], 22.4: [100,100], 16.0: [95,95], 11.2: [85,85], 8.0: [75,75], 4.0: [65,65], 2.0: [52,52], 1.0: [40,40], 0.5: [30,30], 0.25: [22,22], 0.15: [15,15], 0.063: [7,7], 0.0: [0,2]}
    },
    22.4: {
        "A (Alt)":   {40.0: [100,100],31.5: [94,94], 22.4: [86,86], 16.0: [72,72], 11.2: [57,57], 8.0: [41,41], 4.0: [29,29], 2.0: [20,20], 1.0: [14,14], 0.5: [10,10], 0.25: [6,6],   0.15: [3,3], 0.063: [1,1], 0.0: [0,0]},
        "B (İdeal)": {40.0: [100,100],31.5: [96,96], 22.4: [91,91], 16.0: [82,82], 11.2: [70,70], 8.0: [56,56], 4.0: [45,45], 2.0: [35,35], 1.0: [26,26], 0.5: [19,19], 0.25: [12,12], 0.15: [7,7], 0.063: [3,3], 0.0: [0,0]},
        "C (Üst)":   {40.0: [100,100],31.5: [98,98], 22.4: [96,96], 16.0: [91,91], 11.2: [82,82], 8.0: [71,71], 4.0: [59,59], 2.0: [48,48], 1.0: [38,38], 0.5: [28,28], 0.25: [18,18], 0.15: [10,10], 0.063: [5,5], 0.0: [0,0]}
    },
    "KGM TİP-1": { # Dmax 31.5 için
        31.5: [100, 100], 16.0: [55, 80], 8.0: [35, 60], 4.0: [25, 45], 2.0: [18, 35], 1.0: [10, 25], 0.25: [2, 10], 0.063: [1, 5]
    },
    "KGM TİP-2": { # Dmax 22.4 için
        22.4: [100, 100], 16.0: [70, 95], 8.0: [45, 75], 4.0: [35, 55], 2.0: [25, 45], 1.0: [15, 30], 0.25: [3, 12], 0.063: [1, 5]
    },
    16.0: {
        "A (Alt)":   {16.0: [100,100], 8.0: [55,55], 4.0: [35,35], 2.0: [22,22], 1.0: [12,12], 0.25: [4,4], 0.0: [0,0]},
        "B (İdeal)": {16.0: [100,100], 8.0: [70,70], 4.0: [50,50], 2.0: [35,35], 1.0: [22,22], 0.25: [8,8], 0.0: [2,2]},
        "C (Üst)":   {16.0: [100,100], 8.0: [85,85], 4.0: [62,62], 2.0: [48,48], 1.0: [32,32], 0.25: [14,14], 0.0: [4,4]}
    }
}

def calculate_passing(m1, weights):
    if m1 <= 0: return [100.0] * len(weights)
    cumulative_retained = np.cumsum(weights)
    passing_pct = 100 - (cumulative_retained / m1 * 100)
    return np.clip(passing_pct, 0, 100)

def calculate_fm(sieves, passing_pct):
    """
    İncelik Modülü (FM) hesaplar.
    Standard elekler (ASTM C136): 0.15, 0.3, 0.6, 1.18, 2.36, 4.75, 9.5, 19, 37.5, 75 mm
    Bizim serideki en yakınları kullanıyoruz.
    """
    fm_sieves = [31.5, 16.0, 8.0, 4.0, 2.0, 1.0, 0.5, 0.25, 0.15]
    total_retained = 0.0
    found_any = False
    
    for fs in fm_sieves:
        # Elek serisinde bu eleğe en yakın olanı bul
        if fs in sieves:
            idx = sieves.index(fs)
            retained_pct = 100.0 - passing_pct[idx]
            total_retained += retained_pct
            found_any = True
        else:
            # Eğer tam elek yoksa, serideki değerleri kontrol et (Enterpolasyon gerekebilir ama şimdilik pas)
            pass
            
    return round(total_retained / 100.0, 2) if found_any else 0.0

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

def evaluate_mix_compliance(mix_data, standard_mode="KTS"):
    target_class = mix_data.get("class", "C30/37")
    rules = CONCRETE_RULES.get(target_class, CONCRETE_RULES["C30/37"])
    
    # --- Durabilite Kısıtları (TS EN 206 / KTŞ) ---
    exp_class = mix_data.get("exposure_class", "XC3")
    exp_limits = EXPOSURE_CLASSES.get(exp_class, EXPOSURE_CLASSES["XC3"])
    
    violations = []
    warnings = []
    rationales = []
    
    # 1. Çevresel Etki Denetimi (KTŞ 2023 / KGM Beton Yol Odaklı)
    # KTŞ 2023 Modu Aktifse ve Proje "Yol" ise katı kurallar uygulanır.
    is_road_project = "Yol" in target_class
    enforce_kts_road = (standard_mode == "KTS") and is_road_project

    # KTŞ Limitleri (XF4/XWS)
    kts_road_wc = 0.45
    kts_road_cem = 340

    if enforce_kts_road:
        limit_wc_exp = kts_road_wc
        limit_cem_exp = kts_road_cem
    else:
        # TS EN 206 Modu veya Yol olmayan proje
        limit_wc_exp = exp_limits["max_wc"]
        limit_cem_exp = exp_limits["min_cem"]

    current_wc = mix_data.get("wc", 0.0)
    if current_wc > limit_wc_exp:
        if enforce_kts_road:
            violations.append(f"🔴 Durabilite İhlali: S/Ç {current_wc:.2f} > {limit_wc_exp} (KTŞ 2023 Tablo 308-26)")
            rationales.append(f"KTŞ 2023 (XF4/XWS) gereği yol kaplamalarında servis ömrü ve donma direnci için S/Ç oranı en fazla {limit_wc_exp} olmalıdır.")
        else:
             violations.append(f"🔴 Durabilite İhlali: S/Ç {current_wc:.2f} > {limit_wc_exp} ({exp_class} Sınırı)")

    curr_cem = mix_data.get("cement", 0)
    if curr_cem < limit_cem_exp:
        if enforce_kts_road:
            violations.append(f"🔴 Durabilite İhlali: Çimento {curr_cem} < {limit_cem_exp} kg (KTŞ 2023 Min)")
            rationales.append(f"KTŞ 2023 Tablo 308-26 uyarınca XF4 (Yol) sınıfı için minimum {limit_cem_exp} kg/m³ çimento şarttır.")
        else:
             violations.append(f"🔴 Durabilite İhlali: Çimento {curr_cem} < {limit_cem_exp} kg ({exp_class} Sınırı)")

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
         
    # 4. KTŞ 2023 / KGM Genel Esaslar (Filler ve Kum)
    if is_road_project and standard_mode == "KTS":
        filler_val = mix_data.get("filler_content", 0.0)
        if filler_val < 1.0 or filler_val > 5.0:
            warnings.append(f"⚠️ Filler Oranı ({filler_val:.1f}%) İdeal Limit Dışı! (KTŞ Genel: %1-%5)")
            rationales.append("Karayolları teknik esaslarına göre yol betonunda 0.063mm altı filler oranı %1-5 aralığında önerilir.")
        
        sand_val = mix_data.get("sand_content", 0.0)
        if sand_val < 37.0 or sand_val > 56.0:
            warnings.append(f"⚠️ Kum Oranı ({sand_val:.1f}%) İdeal Aralığın Dışında! (İdeal %37-%56)")
            rationales.append("Yol betonu işlenebilirliği için ince malzeme oranı idarece belirlenen ideal aralıkta olmalıdır.")

    if len(violations) > 0:
        status, title, main_msg = "RED", "UYGUN DEĞİLDİR (RED)", "Durabilite ve Standart limitleri aşıldı."
    elif len(warnings) > 0:
        status, title, main_msg = "YELLOW", "ŞARTLI KABUL", "ASR veya performans riskleri mevcut."
    else:
        status, title, main_msg = "GREEN", "UYGUNDUR (KABUL)", "Tüm KGM 2016 ve TS EN 206 limitlerine uygun."
    
    # KGM Rapora dahil et
    if enforce_kts_road:
        title = "📐 KTŞ 2023 UYUMLU: " + title
        
    return {
        "status": status, 
        "title": title, 
        "main_msg": main_msg, 
        "violations": violations, 
        "warnings": warnings,
        "rationales": rationales
    }

def generate_pro_expert_analysis(mix_data):
    """
    Profesyonel düzeyde sistematik beton analizi. 
    İlişkisel veri madenciliği ve mühendislik protokollerini baz alır.
    """
    target_class = mix_data.get("class", "C30/37")
    wc = mix_data.get("wc", 0.0)
    cem = mix_data.get("cement", 0)
    ash = mix_data.get("ash", 0)
    water = mix_data.get("water", 0)
    pred_mpa = mix_data.get("pred_mpa", 0.0)
    is_yol = "Yol" in target_class
    filler = mix_data.get("filler_content", 0.0)
    sand = mix_data.get("sand_content", 0.0)
    asr = mix_data.get("asr_status", "")
    lith = mix_data.get("lithology", "Kireçtaşı")
    la = mix_data.get("avg_la", 0.0)
    fm = mix_data.get("fm", 0.0)
    retained = mix_data.get("retained", [])
    sieves = mix_data.get("sieves", [])
    
    analysis_report = []
    
    # 1. Karmaşıklık Analizi: S/Ç + İnce Madde + Ayrışma Riski
    if wc > 0.48 and filler < 1.5:
        analysis_report.append({
            "topic": "Taze Beton Kararlılığı ve Kohezyon",
            "observation": f"Yüksek efektif S/Ç ({wc:.2f}) ve kritik düzeyde düşük filler (%{filler:.1f}) kombinasyonu.",
            "risk": "Hamur fazının düşük viskozitesi nedeniyle agrega segmentasyonu ve yüzeyde aşırı terleme (bleeding) riski yüksektir.",
            "protocol": "İnce malzeme (0.063mm altı) oranını artırın veya VMA katkı kullanarak stabilitesini sağlayın."
        })
    elif wc < 0.40 and sand < 35:
        analysis_report.append({
            "topic": "İşlenebilirlik ve Yerleştirme Riskleri",
            "observation": "Düşük S/Ç ve düşük kum oranı kombinasyonu.",
            "risk": "Betonun içsel sürtünmesi yüksek olacaktır; vibrasyon zorluğu ve 'balling' etkisi görülebilir.",
            "protocol": "Kum oranını %38-40 bandına çekerek 'fat' miktarını artırın veya poli karboksilat dozajını optimize edin."
        })

    # 2. Su Talebi Analizi
    if water > 185 and not is_yol:
        analysis_report.append({
            "topic": "Hacimsel Su Talebi ve Porozite",
            "observation": f"Net su miktarının ({water} L) standart limitlerin üzerinde olduğu görülmektedir.",
            "risk": "Aşırı su kullanımı, sertleşmiş betonda kapiler boşluk yapısını büyüterek geçirgenliği artırır ve nihai dayanımı baskılar.",
            "protocol": "Katkı verimliliğini artırarak su miktarını 175-180 L bandına çekmeyi hedefleyin."
        })

    # 3. İM (Fineness Modulus) ve Gradasyon Analizi
    fm_ideal = 5.4 if (31.5 in sieves) else 5.0
    if abs(fm - fm_ideal) > 0.4:
        obs = "İncelik Modülü (İM) kaba" if fm > fm_ideal else "İncelik Modülü (İM) çok ince"
        risk = "Pompa basıncında artış ve yüzey bitirme zorluğu" if fm > fm_ideal else "Yüksek su talebi ve rötre çatlağı eğilimi"
        analysis_report.append({
            "topic": "Gradasyon ve İM Optimizasyonu",
            "observation": f"{obs} ({fm:.2f}) tespit edildi.",
            "risk": f"{risk} riski mevcuttur.",
            "protocol": "Agrega harman oranlarını İM değerini 5.0-5.5 (Dmax 31.5 için) bandına getirecek şekilde revize edin."
        })

    # 4. 8-18 Kuralı ve Boşluk Yapısı
    bad_sieves = [f"{sieves[i]}mm" for i, r in enumerate(retained) if (r < 8 or r > 18) and sieves[i] > 0.5]
    if len(bad_sieves) > 3:
        analysis_report.append({
            "topic": "Agrega İskelet Stabilitesi (8-18 Analizi)",
            "observation": f"{', '.join(bad_sieves[:3])} eleklerinde süreksizlik (gap-grading) riski.",
            "risk": "Betonun iskelet yapısında 'bal peteği' (honeycombing) oluşma ihtimali ve kohezyon kaybı.",
            "protocol": "Ara grup agrega (4-8mm veya 8-16mm) ekleyerek elek kalıntılarını dengeleyin."
        })

    # 5. Durabilite Analizi: ASR + Alkali
    if "Reaktif" in asr:
        if ash < (cem * 0.2):
            analysis_report.append({
                "topic": "ASR ve Uzun Vade Durabilite",
                "observation": "Reaktif agrega varlığına rağmen mineral katkı oranı yetersiz.",
                "risk": "Yıllar içinde oluşacak jelleşme ve içsel basınç nedeniyle yapısal ömür kaybı.",
                "protocol": "F sınıfı uçucu kül oranını en az %25'e çıkarın."
            })

    # 6. Ekonomik Verimlilik ve Karbon Ayak İzi
    target_mpa = CONCRETE_RULES.get(target_class, {}).get("min_mpa", 30)
    efficiency = cem / pred_mpa if pred_mpa > 0 else 0
    if efficiency > 11:
        analysis_report.append({
            "topic": "Çimento Verimliliği ve Sürdürülebilirlik",
            "observation": f"Dayanım verimliliği düşük ({efficiency:.1f} kg/MPa).",
            "risk": "Gereksiz hammadde maliyeti ve yüksek hidrasyon ısısı kaynaklı termal çatlak riski.",
            "protocol": "Çimento miktarını düşürüp S/Ç oranını mineral katkılarla stabilize edin."
        })
    elif pred_mpa > (target_mpa + 12):
        analysis_report.append({
            "topic": "Aşırı Dayanım ve Maliyet Optimizasyonu",
            "observation": f"Tahmini dayanım ({pred_mpa:.1f}) hedef sınıfın ({target_mpa}) çok üzerinde.",
            "risk": "Ticari kayıp ve betonun gevrek (brittle) davranış sergilemesi.",
            "protocol": "Güvenlik katsayısını koruyarak çimento dozajında %5 reduction (azaltma) değerlendirilmelidir."
        })

    # 7. KGM 2016 Spesifik Denetim
    if is_yol:
        if filler > 5.0:
             analysis_report.append({
                "topic": "KGM 2016 Yüzey Hassasiyeti",
                "observation": "Filler oranı (%{filler:.1f}) KGM limitinin üzerinde.",
                "risk": "Yüzeyde tozuma ve kuruma büzülmesi çatlakları.",
                "protocol": "Filler içeriğini ivedilikle %5 altına çekin."
            })

    if not analysis_report or len(analysis_report) < 2:
        analysis_report.append({
            "topic": "Sistem Gözlemi",
            "observation": "Genel parametreler uyumlu görünmekle birlikte, saha faktörü ve agrega nem değişimleri yakından izlenmelidir.",
            "risk": "Anlık hammadde değişkenliği dışında bir risk öngörülmemektedir.",
            "protocol": "Pilot döküm ile taze beton verimliliğini teyit edin."
        })
        
    return analysis_report

    return analysis_report

# --- 4. MÜHENDİSLİK AI MOTORU (TS 802 / TS EN 206) ---

def calculate_theoretical_mpa(wc_ratio, air_content=2.0, cement_type="CEM I", has_pozzolan=False, local_constants=None):
    """
    TS 802 - Şekil 9: S/Ç Oranı ve Basınç Dayanımı İlişkisi (Eksponansiyel Model)
    Formül: fcm = A * e^(-B * wc_ratio)
    local_constants: (A, B) şeklinde dışarıdan (Yerel Veri Havuzundan) gelebilir.
    """
    if wc_ratio <= 0: return 0.0
    
    # 1. Katsayı Belirleme (Yerel yoksa Standart TS 802)
    if local_constants and "A" in local_constants and "B" in local_constants:
        A = local_constants["A"]
        B = local_constants["B"]
    else:
        # TS 802 (2016) Verilerinden Türetilen Standart Katsayılar
        if air_content > 3.0: # Hava sürüklenmiş (Hava %3+)
            A, B = 105.94, 2.80
        else: # Hava sürüklenmemiş
            A, B = 113.18, 2.50
        
    # Baz Dayanım (28 Günlük)
    base_mpa = A * np.exp(-B * wc_ratio)
    
    # Çimento Tipi ve Puzolan Faktörü (Öğrenilmiş Bilgi)
    type_factor = 1.0
    if cement_type == "CEM I": type_factor = 1.05
    elif "CEM II" in cement_type: type_factor = 0.95
    
    # Hava Cezası (Her %1 ekstra hava için ~%5 kayıp - Feret Kuralı Modifiye)
    air_penalty = 1.0
    if air_content > 2.0:
        air_penalty = 1 - (air_content - 2.0) * 0.05
        
    return round(base_mpa * type_factor * air_penalty, 1)

def calculate_effective_wc(water, cement, slag=0.0, fly_ash=0.0, cement_type="CEM I"):
    """
    TS EN 206 - 'k' Değeri Kavramı ile Efektif Su/Bağlayıcı Oranı
    k = 0.4 (Uçucu Kül için - CEM I), 0.2 (CEM II/A)
    k = 0.8 (GBS - Cüruf için - CEM I), 0.6 (CEM II/A)
    """
    k_ash = 0.4 if cement_type == "CEM I" else 0.2
    k_slag = 0.8 if cement_type == "CEM I" else 0.6
    
    effective_binder = cement + (k_ash * fly_ash) + (k_slag * slag)
    if effective_binder <= 0: return water
    return round(water / effective_binder, 3)

def evaluate_core_test_ts13791(measured_mpa, fck, n_samples=3, moisture_state="Wet"):
    """
    TS EN 13791 - Karot Dayanımı Uygunluk Değerlendirmesi
    moisture_state: "Wet" (Suda doygun), "Dry" (Hava kurusu), "As-is" (Şantiye hali)
    """
    # 1. Nem Düzeltmesi (FR)
    fr = 1.0
    if moisture_state == "Wet": fr = 1.10
    elif moisture_state == "Dry": fr = 0.96
    
    adj_mpa = measured_mpa * fr
    
    # 2. Uygunluk Kriterleri (Kriter B - Azaltılmış numune sayısı için)
    # fis_min >= 0.85 * (fck - 4)
    criterion_1 = 0.85 * (fck - 4)
    
    status = adj_mpa >= criterion_1
    return {
        "adjusted_mpa": round(adj_mpa, 1),
        "target_min": round(criterion_1, 1),
        "is_compliant": status,
        "msg": "UYGUN" if status else "YETERSİZ (Müdahale Gerekebilir)"
    }

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

def calculate_recipe_details(target_class, opt_weights, materials, standard_mode, exposure_class, curve_name, all_grads, elek_serisi, dmax, slag_pct=0.0, fly_ash_pct=0.0, local_constants=None):
    """
    Optimum agrega ağırlıklarına göre çimento ve su hesabını yaparak tam reçete çıkarır.
    slag_pct, fly_ash_pct: Bağlayıcı içindeki oranlar (Opsiyonel)
    """
    # 1. Çimento ve Su Limitlerini Belirle (TS EN 206 / KTŞ)
    rules = CONCRETE_RULES.get(target_class, CONCRETE_RULES["C20/25"])
    exp = EXPOSURE_CLASSES.get(exposure_class, EXPOSURE_CLASSES["X0"])
    
    # En katı kısıtı seç
    max_wc = min(rules["max_wc"], exp["max_wc"])
    min_cem = max(rules["min_cem"], exp["min_cem"])
    
    # 2. Bağlayıcı Dağılımı ve Etkin S/Ç (k-faktörü)
    # Varsayılan S/Ç oranını -0.02 emniyetle al
    target_wc_eff = max_wc - 0.02
    
    # Başlangıç Çimento Tahmini
    cem_total = min_cem + 20
    
    # Cüruf ve Kül miktarları (Bağlayıcı toplamı üzerinden)
    slag_weight = cem_total * (slag_pct / 100.0)
    ash_weight = cem_total * (fly_ash_pct / 100.0)
    cement_pure = cem_total - (slag_weight + ash_weight)
    
    # Efektif Su Hesabı (k-faktörü)
    k_ash = 0.4
    k_slag = 0.8
    effective_binder = cement_pure + (k_ash * ash_weight) + (k_slag * slag_weight)
    
    # Gereken Su (Efektif S/Ç * Efektif Bağlayıcı)
    water_weight = target_wc_eff * effective_binder
    
    # 3. Hacimsel Hesaplama (1 m3 = 1000 Litre)
    vol_cem = cement_pure / 3.10
    vol_slag = slag_weight / 2.85 # YFC özgül ağırlığı genelde daha düşüktür
    vol_ash = ash_weight / 2.25   # Uçucu kül özgül ağırlığı
    vol_water = water_weight / 1.0
    vol_air = 20.0
    
    vol_agg_tot = 1000 - (vol_cem + vol_slag + vol_ash + vol_water + vol_air)
    
    # 4. Agrega Ağırlıkları
    agg_masses = {}
    weights_pct = {}
    for i, mat in enumerate(materials):
        pct = opt_weights[i] * 100
        weights_pct[mat] = round(pct, 1)
        rho = 2.65
        agg_masses[mat] = round(vol_agg_tot * opt_weights[i] * rho, 0)
        
    # 5. Dayanım Tahmini (Eksponansiyel)
    wc_real = water_weight / (cement_pure + slag_weight + ash_weight)
    pred_mpa = calculate_theoretical_mpa(wc_real, air_content=2.0, has_pozzolan=(slag_weight+ash_weight > 0), local_constants=local_constants)
    pred_90d = predict_90d_strength(pred_mpa, cement_pct=100-slag_pct-fly_ash_pct, slag_pct=slag_pct, ash_pct=fly_ash_pct)

    return {
        "name": f"{target_class} - {curve_name} Optimizasyon",
        "cement": round(cement_pure, 0),
        "slag": round(slag_weight, 0),
        "ash": round(ash_weight, 0),
        "water": round(water_weight, 0),
        "wc_ratio": round(wc_real, 3),
        "pred_mpa": pred_mpa,
        "pred_90d": pred_90d,
        "aggregates": agg_masses,
        "weights_pct": weights_pct,
        "cost_per_m3": 0.0 # Tab'da hesaplanacak
    }

def suggest_smart_recipes(target_class, quarry_materials, dmax=31.5, standard_mode="KTS", exposure_class="XC3", slag_pct=0.0, fly_ash_pct=0.0, local_constants=None):
    """
    Verilen ocak malzemeleri ile hedef beton sınıfı için en uygun reçeteleri türetir.
    Returns: List of dict (recipes)
    """
    available_mats = list(quarry_materials.keys())
    active_mask = [True] * len(available_mats)
    
    # Import locally to avoid potential circular dependency if any
    from logic.engineering import SIEVE_SETS
    elek_serisi = SIEVE_SETS.get(dmax, SIEVE_SETS[31.5])
    
    results = []
    # İdeal (B) ve Sınır (A, C) eğrileri için ayrı ayrı dene
    for curve_type in ["A (Alt)", "B (İdeal)", "C (Üst)"]:
        opt_weights = optimize_mix(curve_type, dmax, active_mask, quarry_materials, elek_serisi, available_mats)
        
        if opt_weights is not None:
            recipe = calculate_recipe_details(
                target_class, opt_weights, available_mats, 
                standard_mode, exposure_class, curve_type, 
                quarry_materials, elek_serisi, dmax,
                slag_pct=slag_pct, fly_ash_pct=fly_ash_pct,
                local_constants=local_constants
            )
            if recipe: results.append(recipe)
            
    results.sort(key=lambda x: (x.get('cost_mass', 999), x.get('error_score', 999)))
    return results

