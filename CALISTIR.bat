@echo off
color 0b
title Beton Dizayn Paneli Baslatiliyor...
echo -------------------------------------------------------
echo      YAZILIMCI ASISTAN: BETON DIZAYN PANELI
echo -------------------------------------------------------
echo.
echo [1/2] Kutuphaneler kontrol ediliyor...
python -m pip install streamlit pandas numpy plotly openpyxl xlsxwriter google-generativeai openai scipy --quiet

echo [2/2] Tarayici uzerinde uygulama baslatiliyor...
echo.
echo Lutfen bekleyin, yerel sunucu kuruluyor...
python -m streamlit run app.py

pause