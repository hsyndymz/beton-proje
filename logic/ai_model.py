import numpy as np

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
        air = float(record.get('air', 0))
        chem = float(record.get('admixture', 0))
        
        if cem < 100 or wat < 50: continue
        
        row = [cem, wat, ash, air, chem]
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
