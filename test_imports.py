import sys
import os

try:
    print("Testing imports...")
    from logic.data_manager import veriyi_yukle, veriyi_kaydet, projesi_sil, DB_FILE
    print("Data Manager OK")
    
    from logic.engineering import (
        calculate_passing, get_std_limits, optimize_mix, evaluate_mix_compliance,
        calculate_theoretical_mpa, update_site_factor, classify_plant, 
        best_wc_estimate, qc_analysis_engine, CONCRETE_RULES, STD_GRADING_DB
    )
    print("Engineering OK")
    
    from logic.ai_model import train_prediction_model, predict_strength_ai, generate_suggestions
    print("AI Model OK")
    
    from logic.report_generator import generate_kgm_report
    print("Report Generator OK")

    from logic.state_manager import SessionStateInitializer
    print("State Manager OK")
    
    from logic.standards_db import TS_STANDARDS_CONTEXT
    print("Standards DB OK")
    
    # Check if app.py has syntax errors
    import py_compile
    py_compile.compile('app.py')
    print("app.py Syntax OK")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
