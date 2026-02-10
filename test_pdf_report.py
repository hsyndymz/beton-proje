import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from logic.report_generator import generate_pdf_raporu, generate_kgm_raporu

# Create a mock snapshot with all new fields
dummy_snapshot = {
    "project_name": "Antigravity Enriched Test",
    "plant_name": "KGM-ARGE TEST",
    "employer": "T.C. ULASTIRMA VE ALTYAPI BAKANLIGI",
    "contractor": "BAHADIR GRUP",
    "revision": "R2-Final",
    "mix_data": {
        "class": "C30/37",
        "wc": 0.42,
        "lithology": "Bazalt",
        "asr_status": "Inert",
        "exposure_class": "XC4"
    },
    "decision": {
        "title": "TEKNIK OLARAK UYGUN",
        "status": "GREEN",
        "violations": [],
        "warnings": ["Su icerigi ideal sinirda."]
    },
    "material_data": {
        "rhos": [2.78, 2.77, 2.71, 2.69],
        "was": [1.7, 2.1, 4.6, 4.4],
        "las": [17.0, 0.0, 0.0, 0.0],
        "mbs": [0.0, 0.0, 1.0, 1.75]
    },
    "recipe": {
        "çimento": 390,
        "su": 137,
        "kül": 0,
        "katkı": 3.12,
        "hava": 2.0,
        "agrega_miktarları": {
            "No:2": 450,
            "No:1": 550,
            "Kum": 800
        }
    },
    "ai_analysis": {
        "weighted_wa": 3.03,
        "wa_liters": 59.6,
        "w_la": 6.8,
        "w_mb": 0.60,
        "wc_status": "Ideal",
        "filler_val": 4.84,
        "filler_status": "Uygun",
        "sand_val": 38.3,
        "sand_status": "Stabil",
        "cf": 71,
        "wf": 31,
        "retained": [0, 0, 4.0, 28.6, 11.7, 6.1, 11.3, 9.6, 8.4, 6.0, 4.4, 3.1]
    },
    "sieves": [40, 31.5, 22.4, 16, 11.2, 8, 4, 2, 1, 0.5, 0.25, 0.15],
    "expert_insights": [
        {
            "topic": "Su Emilimi Uyumlulugu",
            "observation": "Bazalt agrega su emme oranlari yuksektir.",
            "risk": "Karism su talebinde dalgalanma.",
            "protocol": "Nem olcumu her vardiyada tekrarlanmali."
        }
    ]
}

try:
    print("PDF Üretimi başlatılıyor...")
    pdf_bytes = generate_pdf_raporu(dummy_snapshot)
    with open("test_enriched_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("Test PDF'i kaydedildi: test_enriched_report.pdf")

    print("HTML Üretimi başlatılıyor...")
    html_report = generate_kgm_raporu(dummy_snapshot)
    with open("test_enriched_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    print("Test HTML raporu kaydedildi: test_enriched_report.html")
    
except Exception as e:
    print(f"Hata oluştu: {e}")
    import traceback
    traceback.print_exc()
