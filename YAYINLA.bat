@echo off
echo --- BETON PROJE OTOMATIK YUKLEYICI ---

echo [1/3] Guncellemeler kontrol ediliyor...
git pull --rebase --autostash origin main
if %ERRORLEVEL% NEQ 0 (
    echo [HATA] GitHub'dan guncellemeler alinirken bir hata olustu.
    echo Lutfen once SYNC.bat dosyasini calistirmayi deneyin.
    pause
    exit /b
)

echo [2/3] Degisiklikler hazirlaniyor...
git add .
set /p msg="Guncelleme Notu (Bos birakilabilir): "
if "%msg%"=="" set msg="Guncelleme: %date% %time%"
git commit -m "%msg%"

echo [3/3] GitHub'a gonderiliyor...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Yukleme sirasinda bir hata olustu.
) else (
    echo --- YUKLEME TAMAMLANDI! BULUT 2 DK ICINDE GUNCELENECEKTIR. ---
)

pause
