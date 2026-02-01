@echo off
echo --- BETON PROJE OTOMATIK YUKLEYICI ---
git add .
set /p msg="Guncelleme Notu (Bos birakilabilir): "
if "%msg%"=="" set msg="Guncelleme: %date% %time%"
git commit -m "%msg%"
git push origin main
echo --- YUKLEME TAMAMLANDI! BULUT 2 DK ICINDE GUNCELENECEKTIR. ---
pause
