import pandas as pd
import numpy as np
from logic.data_manager import santralleri_yukle, veriyi_yukle

def get_corp_performance_stats():
    """
    Tüm santralleri tarar ve kurumsal performans metriklerini toplar.
    """
    plants = santralleri_yukle()
    corp_data = []

    for p_id, p_info in plants.items():
        projects = veriyi_yukle(p_id)
        
        total_samples = 0
        all_diffs = []
        total_cement = 0
        total_strength = 0
        strength_count = 0
        
        for proj_name, proj_data in projects.items():
            history = proj_data.get("qc_history", [])
            total_samples += len(history)
            
            for rec in history:
                measured = rec.get("d28") or rec.get("measured_mpa")
                predicted = rec.get("predicted_mpa")
                cement = rec.get("cement")
                
                if measured and float(measured) > 0:
                    total_strength += float(measured)
                    strength_count += 1
                    if cement: total_cement += float(cement)
                    
                    if predicted and float(predicted) > 0:
                        all_diffs.append(float(measured) - float(predicted))

        sigma = np.std(all_diffs, ddof=1) if len(all_diffs) > 1 else 0
        avg_strength = total_strength / strength_count if strength_count > 0 else 0
        cement_eff = total_cement / strength_count if strength_count > 0 and total_cement > 0 else 0

        corp_data.append({
            "id": p_id,
            "name": p_info.get("name", p_id),
            "manager": p_info.get("manager", "-"),
            "location": p_info.get("location", "-"),
            "samples": total_samples,
            "sigma": round(sigma, 2),
            "avg_mpa": round(avg_strength, 1),
            "cement_eff": round(cement_eff, 1), # kg cement per mpa-m3 conceptually
            "status": "🟢 Güvenli" if sigma < 3.5 else ("🟡 Riskli" if sigma < 5.0 else "🔴 Kritik")
        })

    return pd.DataFrame(corp_data)

def calculate_cement_efficiency_stats(df):
    """
    Tesisler arası çimento verimliliği analizi.
    """
    if df.empty: return None
    # Verimlilik = Ortalama Dayanım / Çimento Dozajı (Ne kadar az çimento ile çok dayanım)
    # Burada basitleştirilmiş bir metrik kullanıyoruz.
    return df.sort_values(by="cement_eff", ascending=True)

def generate_risk_heatmap_data(df):
    """
    Sigma bazlı risk matrisi verisi.
    """
    if df.empty: return None
    return df[["name", "sigma", "status"]].sort_values(by="sigma", ascending=False)
