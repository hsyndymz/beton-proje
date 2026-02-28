import numpy as np
import pandas as pd
import streamlit as st

@st.cache_data(ttl=600)
def train_prediction_model(qc_history):
    """
    QC geçmişini kullanarak lineer regresyon modeli eğitir.
    Returns: (coeffs, intercept, r2_score)
    """
    X = []
    y = []
    valid_count = 0
    for record in qc_history:
        if not all(k in record for k in ['cement', 'water']) or record.get('d28', 0) <= 0:
            continue
            
        cem = float(record.get('cement', 0))
        wat = float(record.get('water', 0))
        ash = float(record.get('ash', 0))
        slag = float(record.get('slag', 0)) # Yüklenebilir/Öğrenilebilir data
        air = float(record.get('air', 0))
        chem = float(record.get('admixture', 0))
        
        if cem < 100 or wat < 50: continue
        
        row = [cem, wat, ash, slag, air, chem]
        # Ağırlıklandırma (Approved ormuller 10x etkili)
        weight = 10 if record.get('is_approved') else 1
        
        for _ in range(weight):
            X.append(row)
            y.append(float(record['d28']))
            valid_count += 1

    if valid_count < 5:
        return None, None, 0.0

    try:
        X_arr = np.array(X)
        y_arr = np.array(y)
        A = np.c_[X_arr, np.ones(X_arr.shape[0])]
        result = np.linalg.lstsq(A, y_arr, rcond=None)
        coeffs = result[0]
        
        w_full = coeffs
        y_pred = A.dot(w_full)
        rss = np.sum((y_arr - y_pred) ** 2)
        mean_y = np.mean(y_arr)
        tss = np.sum((y_arr - mean_y) ** 2)
        r2_score = 1 - (rss / tss) if tss > 0 else 0.0
        
        return coeffs[:-1], coeffs[-1], r2_score
    except Exception as e:
        print(f"Model error: {e}")
        return None, None, 0.0

def predict_strength_ai(model_coeffs, intercept, inputs):
    if model_coeffs is None: return 0.0
    val = np.dot(inputs, model_coeffs) + intercept
    return max(0, val)

def predict_90d_strength(d28_mpa, cement_pct=100.0, slag_pct=0.0, ash_pct=0.0):
    """
    Puzolanik aktiviteye göre 90 günlük dayanım tahmini.
    (Dairesel bağımlılığı önlemek için engineering.py'den çağırılır)
    """
    from logic.engineering import predict_90d_strength as predict_90d_eng
    return predict_90d_eng(d28_mpa, cement_pct, slag_pct, ash_pct)

def generate_suggestions(target_mpa, pred_mpa, inputs, model_coeffs):
    if model_coeffs is None: return []
    
    diff = target_mpa - pred_mpa
    suggestions = []
    
    c_cem = model_coeffs[0]
    c_wat = model_coeffs[1]
    
    if abs(c_cem) > 0.01:
        delta_cem = diff / c_cem
        if abs(delta_cem) < 100:
            action = "artırmalısın" if delta_cem > 0 else "azaltmalısın"
            suggestions.append(f"Çimentoyu yaklaşık **{abs(delta_cem):.1f} kg** {action}.")

    if abs(c_wat) > 0.01:
        delta_wat = diff / c_wat
        # Su genelde negatif etkilidir (c_wat < 0).
        if abs(delta_wat) < 50:
             action = "artırmalısın" if delta_wat > 0 else "azaltmalısın"
             suggestions.append(f"Su miktarını yaklaşık **{abs(delta_wat):.1f} litre** {action}.")
             
    return suggestions

def get_model_insights(coeffs, feature_names):
    """
    Model katsayılarını mühendislik diline çevirir.
    """
    if coeffs is None or len(coeffs) != len(feature_names):
        return "Model henüz yeterli veriyle eğitilmedi."
    
    insights = []
    # Indexler: 0=cem, 1=wat, 2=ash, 3=slag, 4=air, 5=chem
    # Su etkisi (Negatif olmalı)
    if coeffs[1] < 0:
        insights.append(f"💧 **Su Etkisi:** 1 lt su artışı dayanımı yaklaşık **{abs(coeffs[1]):.2f} MPa** düşürüyor.")
    
    # Cüruf Etkisi
    if coeffs[3] > 0:
        insights.append(f"🏭 **Cüruf (YFC):** Reçetedeki cüruf kullanımı dayanımı pozitif yönde (**{coeffs[3]*10:.2f} MPa / 10kg**) etkiliyor.")
    
    # MB Etkisi (Su ihtiyacı vs üzerinden dolaylı ama burada direkt dayanım etkisi)
    if coeffs[4] < 0: # Hava etkisi
         insights.append(f"☁️ **Hava Etkisi:** %1 hava artışı dayanımı **{abs(coeffs[4]):.1f} MPa** azaltıyor.")

    return insights

def calculate_match_score(inputs, pool_data, target_class):
    """
    Mevcut dizaynın onaylı (Approved) reçetelere olan benzerliğini hesaplar.
    """
    approved_pool = [r for r in pool_data if r.get('is_approved') and r.get('target_class') == target_class]
    if not approved_pool:
        # Daha genel bir onaylı havuzda dene
        approved_pool = [r for r in pool_data if r.get('is_approved')]
        if not approved_pool: return 0.0 # Başlangıç aşaması
    
    # Ortalama Onaylı Değerler
    # Indexler: 0=cem, 1=wat, 2=ash, 3=slag, 4=air, 5=chem
    df = pd.DataFrame(approved_pool)
    try:
        # Önemli özelliklerin (Cem, Wat, Slag) ortalama ve standart sapması
        # Girdi 'inputs' [cem, wat, ash, slag, air, chem]
        ref_cem = df['cement'].mean()
        ref_wat = df['water'].mean()
        
        # Basit bir yüzde yakınlık hesabı
        err_cem = abs(inputs[0] - ref_cem) / ref_cem if ref_cem > 0 else 0
        err_wat = abs(inputs[1] - ref_wat) / ref_wat if ref_wat > 0 else 0
        
        score = max(0, 100 - (err_cem + err_wat) * 100)
        return round(score, 1)
    except:
        return 50.0 # Fallback

def derive_local_engineering_constants(pool_data):
    """
    Havuz verilerinden yerel Bolomey katsayılarını (A, B) ve puzolan verimliliklerini türetir.
    """
    if len(pool_data) < 20:
        return None # Yeterli veri yoksa standart katsayılar kullanılır
    
    valid_data = []
    for r in pool_data:
        cem = r.get('cement', 0)
        wat = r.get('water', 0)
        d28 = r.get('d28', 0)
        if cem > 200 and wat > 100 and d28 > 10:
            wc = wat / (cem + r.get('ash', 0)*0.4 + r.get('slag', 0)*0.8)
            valid_data.append((wc, d28))
            
    if len(valid_data) < 15: return None
    
    # fcm = A * exp(-B * wc) -> log(fcm) = log(A) - B * wc
    # y = c + m*x (Linear Regression in log space)
    try:
        x = np.array([v[0] for v in valid_data])
        y = np.log([v[1] for v in valid_data])
        
        A_mat = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A_mat, y, rcond=None)[0]
        
        B_derived = -m
        A_derived = np.exp(c)
        
        return {
            "A": round(float(A_derived), 2),
            "B": round(float(B_derived), 2),
            "count": len(valid_data)
        }
    except:
        return None

def find_similar_recipes(current_inputs, pool_data, top_n=3):
    """
    k-NN mantığı ile havuzdaki en benzer onaylı reçeteleri bulur.
    current_inputs: [cem, wat, ash, slag, air, chem]
    """
    approved = [r for r in pool_data if r.get('is_approved')]
    if not approved: return []
    
    results = []
    for r in approved:
        # Karşılaştırma vektörü
        v = [
            r.get('cement', 0), r.get('water', 0), 
            r.get('ash', 0), r.get('slag', 0),
            r.get('air', 0), r.get('admixture', 0)
        ]
        
        # Ağırlıklı Öklid Mesafesi (Çimento ve Su daha önemli)
        weights = np.array([1.0, 1.5, 0.5, 0.5, 0.2, 0.2])
        dist = np.sqrt(np.sum(weights * (np.array(current_inputs) - np.array(v))**2))
        
        # Benzerlik Skoru (0-100)
        # 0 mesafe = 100 skor. 50 birim fark = ~%70 skor (logaritmik veya doğrusal)
        similarity = max(0, 100 - (dist / 2)) 
        
        results.append({
            "record": r,
            "similarity": round(similarity, 1),
            "dist": dist
        })
        
    # En benzerleri getir
    results.sort(key=lambda x: x['dist'])
    return results[:top_n]

def get_local_knowledge_stats(pool_data):
    """
    Yerel havuzdan API gerektirmeyen teknik istatistikler üretir.
    """
    if not pool_data: return {}
    
    df = pd.DataFrame(pool_data)
    stats = {
        "total_count": len(df),
        "approved_count": len(df[df.get('is_approved', False) == True]) if 'is_approved' in df else 0,
        "avg_strength": round(df['d28'].mean(), 1) if 'd28' in df else 0,
        "best_efficiency": 0
    }
    
    if 'cement' in df and 'd28' in df:
        # MPa başına çimento tüketimi (Verimlilik)
        df['eff'] = df['cement'] / df['d28']
        stats["avg_efficiency"] = round(df['eff'].mean(), 1)
        stats["best_efficiency"] = round(df['eff'].min(), 1)
        
    return stats
